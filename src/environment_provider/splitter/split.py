# Copyright 2020 Axis Communications AB.
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
"""ETOS Environment Provider splitter module."""
from copy import deepcopy


class Splitter:
    """Environment provider test suite splitter."""

    def __init__(self, etos, ruleset):
        """Initialize with etos library and splitter ruleset.

        :param etos: ETOS library instance.
        :type etos: :obj:`etos_lib.etos.Etos`
        :param ruleset: JSONTas ruleset for handling splitter algorithms.
        :type ruleset: dict
        """
        self.etos = etos
        self.ruleset = ruleset

    @staticmethod
    def _iterator(iterable):
        """Create a generator from iterable."""
        yield from iterable

    def splitter(self, test_suite):
        """Iterate through all IUTs and assign a recipe in a round-robin fashion.

        :param test_suite: Test suite to iterate IUTs for.
        :type test_suite: dict
        """
        test_list = self._iterator(deepcopy(test_suite.get("unsplit_recipes")))
        while True:
            try:
                for _, iut_dict in test_suite.get("iuts").items():
                    test = next(test_list)
                    iut_dict["recipes"].append(test)
                    test_suite["unsplit_recipes"].remove(test)
            except StopIteration:
                break

    def split(self, test_suite):
        """Will only call the splitter of this object.

        In the future this might be where other splitter algorithms are evaluated.

        :param test_suite: Test suite to attach tests to.
        :type test_suite: dict
        """
        self.splitter(test_suite)

    def assign_iuts(self, test_runners, iuts):
        """Assign IUTs to test runners.

        :param test_runners: Test runners dictionary to attach IUTs to.
        :type test_runners: dict
        :param iuts: List of IUTs that need test runners.
        :type iuts: list
        :return: Any unassigned IUT.
        :rtype: list
        """
        iuts = deepcopy(iuts)
        for test_runner in test_runners.values():
            test_runner.setdefault("iuts", {})
            test_runner["percentage_of_tests"] = len(
                test_runner.get("unsplit_recipes")
            ) / self.etos.config.get("TOTAL_TEST_COUNT")
            number_of_iuts = round(
                self.etos.config.get("NUMBER_OF_IUTS")
                * test_runner["percentage_of_tests"]
            )
            if not number_of_iuts:
                number_of_iuts = 1

            number_of_tests = len(test_runner.get("unsplit_recipes"))
            number_of_iuts = (
                number_of_tests if number_of_tests < number_of_iuts else number_of_iuts
            )
            test_runner["number_of_iuts"] = number_of_iuts

        while True:
            try:
                for test_runner in test_runners.values():
                    if len(test_runner.get("iuts")) >= test_runner["number_of_iuts"]:
                        continue
                    test_runner["iuts"][iuts.pop(0)] = {"recipes": [], "executor": None}
                unfinished = [
                    test_runner
                    for test_runner in test_runners.values()
                    if len(test_runner.get("iuts")) != test_runner["number_of_iuts"]
                ]
                if not unfinished:
                    break
            except IndexError:
                break
        return iuts
