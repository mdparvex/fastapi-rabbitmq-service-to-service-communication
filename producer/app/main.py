from fastapi import FastAPI, HTTPException
import aio_pika
import asyncio
import os
import json
import time

app = FastAPI(title="Producer Service")

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
QUEUE_NAME = "data_stream"

@app.on_event("startup")
async def startup():
    # Connect to RabbitMQ in a background task so the app can start even if
    # RabbitMQ is not yet ready. This mirrors the consumer behaviour.
    async def connect_and_prepare():
        url = f"amqp://guest:guest@{RABBITMQ_HOST}/"

        async def connect_robust_with_retries(url: str, retries: int = 30, delay: float = 2.0):
            last_exc = None
            for attempt in range(1, retries + 1):
                try:
                    conn = await aio_pika.connect_robust(url)
                    print(f"Connected to RabbitMQ on attempt {attempt}")
                    return conn
                except Exception as e:
                    last_exc = e
                    print(f"AMQP connect attempt {attempt} failed: {e}; retrying in {delay}s")
                    await asyncio.sleep(delay)
                    delay = min(delay * 2, 30)
            raise last_exc

        try:
            app.state.connection = await connect_robust_with_retries(url)
            app.state.channel = await app.state.connection.channel()
            await app.state.channel.declare_queue(QUEUE_NAME, durable=True)
            print("Producer connected to RabbitMQ and declared queue")
        except Exception as e:
            # Don't crash the whole app if RabbitMQ is unavailable; log and exit the task.
            print(f"Producer failed to connect to RabbitMQ: {e}")

    asyncio.create_task(connect_and_prepare())

@app.on_event("shutdown")
async def shutdown():
    await app.state.connection.close()

@app.post("/send")
async def send_data(payload: dict):
    """Send JSON data to RabbitMQ."""
    if not hasattr(app.state, "channel") or app.state.channel is None:
        raise HTTPException(status_code=503, detail="RabbitMQ channel not ready")

    message = aio_pika.Message(body=json.dumps(payload).encode())
    await app.state.channel.default_exchange.publish(message, routing_key=QUEUE_NAME)
    return {"status": "Message sent", "data": payload}
