import os
import json
import asyncio
import random
import secrets
import string
import logging
from datetime import datetime

import aio_pika
from sqlalchemy import select

from app.database import async_session
from app.models import Server

logger = logging.getLogger(__name__)



def generate_password(length=12):
    chars = string.ascii_letters + string.digits
    return "".join(secrets.choice(chars) for _ in range(length))


def generate_ip():
    return f"10.0.{random.randint(1, 254)}.{random.randint(1, 254)}"


def generate_hostname(server_id):
    return f"vps-{server_id}.hosting.local"


async def provision_server(server_id: int):
    """Simulate server provisioning."""
    async with async_session() as db:
        # Set status to provisioning
        result = await db.execute(select(Server).where(Server.id == server_id))
        server = result.scalar_one_or_none()
        if not server:
            logger.error(f"Server {server_id} not found")
            return

        # Redelivery must not recreate an already provisioned server.
        if server.ip_address:
            return
        server.status = "provisioning"
        await db.commit()
        logger.info(f"Server {server_id} status set to 'provisioning'")

        result = await db.execute(select(Server).where(Server.id == server_id).with_for_update())
        server = result.scalar_one()
        await db.refresh(server)
        if server.ip_address:
            return
        # Simulate OS installation
        await asyncio.sleep(5)

        # Generate server details
        server.ip_address = generate_ip()
        server.root_password = generate_password()
        server.hostname = generate_hostname(server_id)
        server.status = "active"
        server.updated_at = datetime.utcnow()
        await db.commit()

        logger.info(f"Server {server_id} provisioned successfully - IP: {server.ip_address}, hostname: {server.hostname}")


async def on_message(message: aio_pika.abc.AbstractIncomingMessage):
    async with message.process(requeue=True):
        body = json.loads(message.body.decode())
        order_id = body.get("order_id")
        server_id = body.get("server_id")
        logger.info(f"Received order.paid message: order_id={order_id}, server_id={server_id}")
        await provision_server(server_id)


async def start_consumer():
    """Reconnect to either broker; unacknowledged messages are redelivered."""
    while True:
        for url in os.environ["RABBITMQ_URLS"].split(","):
            connection = None
            try:
                connection = await aio_pika.connect(url, timeout=3)
                disconnected = asyncio.Event()
                connection.close_callbacks.add(lambda *_: disconnected.set())
                channel = await connection.channel()
                await channel.set_qos(prefetch_count=1)
                exchange = await channel.declare_exchange("orders", aio_pika.ExchangeType.DIRECT, durable=True)
                queue = await channel.declare_queue("provisioning_queue", durable=True)
                await queue.bind(exchange, routing_key="order.paid")
                await queue.consume(on_message)
                logger.info("Connected to broker; waiting for paid orders")
                await disconnected.wait()
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.warning("Broker connection lost; trying next node")
            finally:
                if connection is not None and not connection.is_closed:
                    await connection.close()
        await asyncio.sleep(2)
