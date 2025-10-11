#!/usr/bin/env bash
# Simple wait-for script: waits for host:port to be reachable
set -e
HOST=${1:-rabbitmq}
PORT=${2:-5672}
TIMEOUT=${3:-60}

echo "Waiting for RabbitMQ at ${HOST}:${PORT} (timeout ${TIMEOUT}s)"
start_ts=$(date +%s)
while :; do
  if nc -z "$HOST" "$PORT" 2>/dev/null; then
    echo "RabbitMQ is available at ${HOST}:${PORT}"
    exit 0
  fi
  now=$(date +%s)
  elapsed=$((now - start_ts))
  if [ "$elapsed" -ge "$TIMEOUT" ]; then
    echo "Timeout waiting for RabbitMQ after ${TIMEOUT}s" >&2
    exit 1
  fi
  sleep 1
done
