# Copyright 2021-2022 Axis Communications AB.
#
# For a full list of individual contributors, please see the commit history.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Backend for the environment requests."""
import json
import traceback
from typing import Optional, Union

from celery import Celery
from etos_lib import ETOS
from falcon import Request
from jsontas.jsontas import JsonTas

from environment_provider.environment_provider import get_environment
from environment_provider.lib.database import ETCDPath
from environment_provider.lib.registry import ProviderRegistry
from execution_space_provider import ExecutionSpaceProvider
from execution_space_provider.execution_space import ExecutionSpace
from iut_provider import IutProvider
from iut_provider.iut import Iut
from log_area_provider import LogAreaProvider
from log_area_provider.log_area import LogArea


def get_environment_id(request: Request) -> Optional[str]:
    """Get the environment ID from request.

    :param request: The falcon request object.
    :return: The ID of the environment.
    """
    return request.get_param("id")


def get_release_id(request: Request) -> Optional[str]:
    """Get the task ID to release, from request.

    :param request: The falcon request object.
    :return: The ID of the environment to release.
    """
    return request.get_param("release")


def get_single_release_id(request: Request) -> Optional[str]:
    """Get the environment ID to release, from request.

    :param request: The falcon request object.
    :return: The ID of the environment to release.
    """
    return request.get_param("single_release")


def checkin_provider(
    item: dict, provider: Union[IutProvider, ExecutionSpaceProvider, LogAreaProvider]
) -> tuple[bool, Optional[Exception]]:
    """Check in a provider.

    :param item: Item to check in.
    :param provider: The provider to use for check in.
    :return: Whether or not the checkin was successful together with an exception
             if there was any.
    """
    failure = None
    try:
        provider.checkin(item)
    except Exception as exception:  # pylint:disable=broad-except
        failure = exception
    # If failure is None, return True.
    return not failure, failure


def release_environment(
    etos: ETOS, jsontas: JsonTas, provider_registry: ProviderRegistry, sub_suite: dict
) -> Optional[Exception]:
    """Release a single sub-suite environment.

    :param etos: ETOS library instance.
    :param jsontas: JSONTas instance.
    :param provider_registry: The provider registry to get environments from.
    :param sub_suite: The sub suite environment to release.
    :return: Whether or not the release was successful
    """
    etos.config.set("SUITE_ID", sub_suite.get("suite_id"))
    iut = sub_suite.get("iut")
    iut_ruleset = provider_registry.get_iut_provider_by_id(iut.get("provider_id")).get("iut")
    executor = sub_suite.get("executor")
    executor_ruleset = provider_registry.get_execution_space_provider_by_id(
        executor.get("provider_id")
    ).get("execution_space")

    log_area = sub_suite.get("log_area")
    log_area_ruleset = provider_registry.get_log_area_provider_by_id(
        log_area.get("provider_id")
    ).get("log")

    failure = None
    success, exception = checkin_provider(Iut(**iut), IutProvider(etos, jsontas, iut_ruleset))
    if not success:
        failure = exception

    success, exception = checkin_provider(
        LogArea(**log_area), LogAreaProvider(etos, jsontas, log_area_ruleset)
    )
    if not success:
        failure = exception
    success, exception = checkin_provider(
        ExecutionSpace(**executor),
        ExecutionSpaceProvider(etos, jsontas, executor_ruleset),
    )
    if not success:
        failure = exception
    return failure


def release_full_environment(etos: ETOS, jsontas: JsonTas, suite_id: str) -> tuple[bool, str]:
    """Release an already requested environment.

    :param etos: ETOS library instance.
    :param jsontas: JSONTas instance.
    :return: Release status and a message if status is False.
    """
    failure = None
    registry = ProviderRegistry(etos, jsontas, suite_id)
    for suite, metadata in registry.testrun.join("suite").read_all():
        suite = json.loads(suite)
        try:
            failure = release_environment(etos, jsontas, registry, suite)
        except json.JSONDecodeError as exception:
            failure = exception
        ETCDPath(metadata.get("key")).delete()
    registry.testrun.delete_all()

    if failure:
        # Return the traceback from exception stored in failure.
        return False, "".join(
            traceback.format_exception(failure, value=failure, tb=failure.__traceback__)
        )
    return True, ""


def check_environment_status(celery_worker: Celery, environment_id: str) -> dict:
    """Check the status of the environment that is being requested.

    :param celery_worker: The worker holding the task results.
    :param environment_id: The environment ID to check status on.
    :return: A dictionary of status and and result.
    """
    task_result = celery_worker.AsyncResult(environment_id)
    result = task_result.result
    status = task_result.status
    if isinstance(result, Exception):
        status = "FAILURE"
        result = str(result)
    elif result and result.get("error") is not None:
        status = "FAILURE"
    if result:
        task_result.get()
    return {"status": status, "result": result}


def request_environment(suite_id: str, suite_runner_ids: list[str]) -> str:
    """Request an environment for a test suite ID.

    :param suite_id: Suite ID to request an environment for.
    :param suite_runner_ids: Suite runner correlation IDs.
    :return: The task ID for the request.
    """
    return get_environment.delay(suite_id, suite_runner_ids).id
