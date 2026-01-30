#!/usr/bin/env bash
set -e

IMAGE_NAME=book-app

docker build -t $IMAGE_NAME .