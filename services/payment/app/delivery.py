"""Retry paid orders until provisioning has accepted them (database-backed delivery)."""
import asyncio
import json
import logging
import os
import aio_pika
from sqlalchemy import text
from app.database import async_session

logger = logging.getLogger(__name__)


async def deliver_paid_orders():
    while True:
        try:
            async with async_session() as db:
                rows = (await db.execute(text("""
                    SELECT o.id, o.server_id FROM orders o JOIN servers s ON s.id=o.server_id
                    WHERE o.status='paid' AND s.status='pending'
                """))).all()
            if rows:
                for url in os.environ["RABBITMQ_URLS"].split(","):
                    try:
                        connection = await aio_pika.connect(url, timeout=3)
                        async with connection:
                            channel = await connection.channel(publisher_confirms=True)
                            exchange = await channel.declare_exchange("orders", aio_pika.ExchangeType.DIRECT, durable=True)
                            queue = await channel.declare_queue("provisioning_queue", durable=True)
                            await queue.bind(exchange, routing_key="order.paid")
                            for order_id, server_id in rows:
                                await exchange.publish(aio_pika.Message(
                                    body=json.dumps(dict(order_id=order_id, server_id=server_id)).encode(),
                                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT),
                                    routing_key="order.paid", mandatory=True, timeout=5)
                                logger.info("Published paid order %s for server %s", order_id, server_id)
                        break
                    except Exception:
                        logger.warning("Broker delivery unavailable; trying next node")
        except Exception:
            logger.exception("Delivery scan failed; retrying")
        await asyncio.sleep(3)
