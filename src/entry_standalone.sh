#!/bin/bash

export ETOS_DATABASE_HOST=$(docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' etos-environment-provider_redis-sentinel_1)
export ETOS_DATABASE_PASSWORD="str0ng_passw0rd"
export ETOS_DATABASE_PORT="26379"

exec gunicorn environment_provider.webserver:FALCON_APP \
	--name environment_provider \
	--worker-class=gevent \
	--bind 0.0.0.0:8080 \
	--worker-connections=1000 \
	--workers=5 \
	--reload
