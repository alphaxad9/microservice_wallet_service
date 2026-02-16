import os
import sys
import signal
import time
import json
import logging
import asyncio
from typing import Any, Dict, Optional

from dotenv import load_dotenv
load_dotenv()

# ---------------------------------------------------------------------
# Django bootstrap
# ---------------------------------------------------------------------
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "wallet_service.settings")
django.setup()

# ---------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------
# RabbitMQ
# ---------------------------------------------------------------------
import pika
from pika.adapters.blocking_connection import BlockingChannel
from pika.spec import Basic, BasicProperties

from src.messaging.rabbitMQ.config import (
    RABBIT_USER,
    RABBIT_PORT,
    RABBIT_HOST,
    RABBIT_PASSWORD,
    RABBIT_VHOST,
)

EXCHANGE_NAME = "microservice_one.commands"
RABBIT_QUEUE = "wallet_service.commands"
ROUTING_KEY = "wallet.*"

# ---------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------
from django.core.cache import cache

# ---------------------------------------------------------------------
# ACL + Handlers
# ---------------------------------------------------------------------
from src.messaging.rabbitMQ.dispatchers.booking_acl import (
    translate_booking_command,
)
from src.messaging.rabbitMQ.command_handlers.booking_command_handlers import (
    WALLET_COMMAND_HANDLERS,
)
from src.domain.shared.commands import DomainCommand
from src.messaging.rabbitMQ.command_handlers.base_handler import BaseCommandHandler

# ---------------------------------------------------------------------
# Globals
# ---------------------------------------------------------------------
_connection: Optional[pika.BlockingConnection] = None

# ---------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------
def is_duplicate(message_id: str) -> bool:
    if not message_id or message_id == "unknown":
        return False

    key = f"wallet_service:processed_command:{message_id}"
    if cache.get(key):
        return True

    cache.set(key, "1", timeout=7 * 24 * 3600)
    return False

# ---------------------------------------------------------------------
# Dispatch logic
# ---------------------------------------------------------------------
async def dispatch_wallet_command(command: DomainCommand) -> None:
    handler: BaseCommandHandler | None = WALLET_COMMAND_HANDLERS.get(type(command))

    if not handler:
        raise RuntimeError(
            f"No handler registered for command: {type(command).__name__}"
        )

    await handler.handle(command)

# ---------------------------------------------------------------------
# RabbitMQ callback
# ---------------------------------------------------------------------
def callback(
    ch: BlockingChannel,
    method: Basic.Deliver,
    properties: BasicProperties,
    body: bytes,
) -> None:
    message_id = properties.message_id or "unknown"

    if is_duplicate(message_id):
        ch.basic_ack(delivery_tag=method.delivery_tag)
        logger.info("🔁 Duplicate command ignored", extra={"message_id": message_id})
        return

    try:
        payload: Dict[str, Any] = json.loads(body.decode("utf-8"))

        command_name = (
            properties.headers.get("command_name")
            if properties.headers
            else None
        )

        if not command_name:
            raise RuntimeError("Missing command_name header")

        logger.info(
            "📬 COMMAND RECEIVED (wallet_service)",
            extra={
                "command_name": command_name,
                "message_id": message_id,
                "payload": payload,
            },
        )

        # ACL translation: turns raw dict into typed ACL command
        wallet_command = translate_booking_command(command_name, payload)

        # Dispatch to handler
        asyncio.run(dispatch_wallet_command(wallet_command))

        ch.basic_ack(delivery_tag=method.delivery_tag)
        logger.info("✅ Command processed", extra={"message_id": message_id})

    except Exception:
        logger.exception(
            "❌ Command processing failed",
            extra={"message_id": message_id},
        )
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

# ---------------------------------------------------------------------
# Connection helpers
# ---------------------------------------------------------------------
def create_connection() -> pika.BlockingConnection:
    credentials = pika.PlainCredentials(RABBIT_USER, RABBIT_PASSWORD)
    parameters = pika.ConnectionParameters(
        host=RABBIT_HOST,
        port=RABBIT_PORT,
        virtual_host=RABBIT_VHOST,
        credentials=credentials,
        heartbeat=600,
        blocked_connection_timeout=300,
    )
    return pika.BlockingConnection(parameters)

# ---------------------------------------------------------------------
# Consumer loop
# ---------------------------------------------------------------------
def start_consumer() -> None:
    global _connection

    logger.info(
        "🧠 Active Wallet Handlers: %s",
        [cls.__name__ for cls in WALLET_COMMAND_HANDLERS.keys()],
    )

    while True:
        try:
            _connection = create_connection()
            channel = _connection.channel()

            # Declare exchange and queue, then bind
            channel.exchange_declare(
                exchange=EXCHANGE_NAME,
                exchange_type="topic",
                durable=True,
            )

            channel.queue_declare(queue=RABBIT_QUEUE, durable=True)

            channel.queue_bind(
                exchange=EXCHANGE_NAME,
                queue=RABBIT_QUEUE,
                routing_key=ROUTING_KEY,
            )

            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(
                queue=RABBIT_QUEUE,
                on_message_callback=callback,
            )

            logger.info(f'[*] Waiting for commands on "{RABBIT_QUEUE}"')
            channel.start_consuming()

        except pika.exceptions.AMQPConnectionError as e:
            logger.error("RabbitMQ connection error: %s. Retrying in 5s...", e)
            time.sleep(5)

        except Exception:
            logger.exception("❌ Unexpected consumer crash. Restarting in 5s...")
            time.sleep(5)

# ---------------------------------------------------------------------
# Signals
# ---------------------------------------------------------------------
def signal_handler(sig, frame):
    logger.info("🛑 Shutdown signal received")
    if _connection and _connection.is_open:
        _connection.close()
    sys.exit(0)

# ---------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    start_consumer()