#!/bin/bash

unset http_proxy https_proxy

curl -X POST -H "Content-Type: application/json" -d "{\"execution_space_provider\": $(cat ../fake_providers/exec_space.json)}" http://localhost:8080/register
curl -X POST -H "Content-Type: application/json" -d "{\"log_area_provider\": $(cat ../fake_providers/logs.json)}" http://localhost:8080/register
curl -X POST -H "Content-Type: application/json" -d "{\"iut_provider\": $(cat ../fake_providers/iut.json)}" http://localhost:8080/register 