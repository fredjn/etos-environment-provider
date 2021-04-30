#!/bin/bash

export ETOS_DATABASE_HOST=$(docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' etos-environment-provider_redis-sentinel_1)
export ETOS_DATABASE_PASSWORD="str0ng_passw0rd"
export ETOS_DATABASE_PORT="26379"
export CELERY_CMD_ARGS="-P eventlet -c 1000 -l DEBUG"
export ETOS_GRAPHQL_SERVER="fake"
export ETOS_API="fake"
export ETOS_ENVIRONMENT_PROVIDER="http://localhost:8080"

export LOCAL_SUITE="$PWD/../test_suite.json"

exec celery -A environment_provider.environment_provider.APP worker $CELERY_CMD_ARGS
