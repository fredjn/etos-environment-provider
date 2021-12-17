#!/bin/bash

exec opentelemetry-instrument \
	gunicorn environment_provider.webserver:FALCON_APP \
		--name environment_provider \
		--worker-class=gevent \
		--bind 0.0.0.0:8080 \
		--worker-connections=1000 \
		--workers=5 \
		--reload
