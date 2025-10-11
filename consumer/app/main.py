from fastapi import FastAPI
import aio_pika
import asyncio
import json
import os
import time

app = FastAPI(title="Consumer Service")

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
QUEUE_NAME = "data_stream"
received_messages = []

async def consume():
    """Background task to consume messages from RabbitMQ."""
    url = f"amqp://guest:guest@{RABBITMQ_HOST}/"

    async def connect_with_retries(url: str, retries: int = 30, delay: float = 2.0):
        last_exc = None
        for attempt in range(1, retries + 1):
            try:
                conn = await aio_pika.connect_robust(url)
                print(f"Consumer connected to RabbitMQ on attempt {attempt}")
                return conn
            except Exception as e:
                last_exc = e
                print(f"Consumer AMQP connect attempt {attempt} failed: {e}; retrying in {delay}s")
                await asyncio.sleep(delay)
                delay = min(delay * 2, 30)
        raise last_exc

    connection = await connect_with_retries(url)
    channel = await connection.channel()
    queue = await channel.declare_queue(QUEUE_NAME, durable=True)
    print("Consumer connected to RabbitMQ and waiting for messages...")

    async with queue.iterator() as queue_iter:
        async for message in queue_iter:
            async with message.process():
                data = json.loads(message.body.decode())
                print(f"Received: {data}")
                received_messages.append(data)

@app.on_event("startup")
async def startup():
    # loop = asyncio.get_event_loop()
    # loop.create_task(consume())
    asyncio.create_task(consume())

@app.get("/messages")
async def get_messages():
    """Get all messages received so far."""
    return {"received_messages": received_messages}
