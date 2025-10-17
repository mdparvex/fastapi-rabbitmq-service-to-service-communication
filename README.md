# fastapi-rabbitmq-service-to-service-communication

Lightweight example demonstrating a FastAPI-based producer and consumer communicating via RabbitMQ. The project is containerized with Docker Compose and includes robustness improvements so services can start when RabbitMQ is starting.

Contents
- `producer/` — FastAPI app that publishes JSON messages to a RabbitMQ queue (`/send` endpoint).
- `consumer/` — FastAPI app that consumes messages from the RabbitMQ queue and exposes them via `/messages`.
- `docker-compose.yaml` — starts RabbitMQ, producer, and consumer.

Sample `.env`
Create a `.env` file in the repo root (optional — defaults are provided):

```ini
# RabbitMQ host (within Docker Compose network)
RABBITMQ_HOST=rabbitmq

# RabbitMQ management credentials (used by the container on startup)
RABBITMQ_DEFAULT_USER=guest
RABBITMQ_DEFAULT_PASS=guest
```

Project setup

Prerequisites:
- Docker and Docker Compose installed on your machine.

Start the whole stack (build images and start containers):

```powershell
docker-compose up --build
```

Behavior and reliability notes
- Services default to connecting to `rabbitmq` (the docker-compose service name).
- Both producer and consumer attempt to connect to RabbitMQ with retries.
- The Docker images include a small `wait-for-rabbitmq.sh` entrypoint helper that waits for the AMQP port (5672) before starting the app. This prevents premature connection attempts when RabbitMQ is still starting.
- `docker-compose.yaml` contains a RabbitMQ healthcheck (`rabbitmq-diagnostics ping`) so the container is marked healthy when ready.

How to use

1. POST a JSON payload to the producer:

```powershell
curl -X POST http://localhost:8000/send -H "Content-Type: application/json" -d '{"msg":"hello"}'
```

Expected response (when successful):

```json
{"status":"Message sent","data":{"msg":"hello"}}
```

2. Retrieve messages from the consumer:

```powershell
curl http://localhost:8001/messages
```

Sample consumer output (when a message was consumed):

```json
{"received_messages":[{"msg":"hello"}]}
```

Troubleshooting
- If the producer returns HTTP 503 from `/send`, the app hasn't yet established a RabbitMQ channel — wait a few seconds and retry.
- Check all logs:

```powershell
docker-compose logs -f rabbitmq producer consumer
```

- If RabbitMQ repeatedly fails to become healthy, run:

```powershell
docker-compose up rabbitmq
```

