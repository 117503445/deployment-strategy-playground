#!/usr/bin/env bash

docker compose down

rm -r ./control/.venv
rm -r ./dind/data
rm -r ./k3s/data
rm -r ./kubepi/data
rm -r ./registry/data