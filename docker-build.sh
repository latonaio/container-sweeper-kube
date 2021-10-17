#!/usr/bin/env bash

DATE="$(date "+%Y%m%d%H%M")"
IMAGE_NAME="container-sweeper-kube"

docker build -t ${IMAGE_NAME}:"${DATE}" .
docker tag ${IMAGE_NAME}:"${DATE}" ${IMAGE_NAME}:latest
