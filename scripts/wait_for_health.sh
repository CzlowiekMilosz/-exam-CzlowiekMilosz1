#!/usr/bin/env bash
set -e
CONTAINER_NAME=book-app-ci
URL="http://localhost:8080/health"

for i in $(seq 1 30); do
  if curl -fsS "$URL" > /tmp/health.json; then
    cat /tmp/health.json
    exit 0
  fi
  sleep 1
done

echo "Healthcheck did not become ready"
docker logs "$CONTAINER_NAME" || true
exit 1
