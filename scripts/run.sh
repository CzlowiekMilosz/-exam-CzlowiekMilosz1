#!/usr/bin/env bash
set -e

IMAGE_NAME=book-app
CONTAINER_NAME=book-app-ci

docker run -d -p 8080:5000 --name $CONTAINER_NAME $IMAGE_NAME