# src/messaging/wallet/dispatchers.py

import logging
from typing import Callable, Awaitable, Any

from src.domain.apps.wallet.events import (
    WalletCreatedEvent,
    WalletActivatedEvent,
    WalletSuspendedEvent,
    WalletClosedEvent,
    WalletDepositedEvent,
    WalletWithdrawnEvent,
    WalletPaymentMadeEvent,
    WalletRefundedEvent,
    WalletAdjustedEvent,
    WalletEventType,
)
from src.messaging.event_bus import event_bus

logger = logging.getLogger(__name__)

# Handler registry: event_type.value -> async dispatcher function
WALLET_EVENT_HANDLERS: dict[str, Callable[[dict[str, Any]], Awaitable[None]]] = {}


def register_wallet_handler(event_type: WalletEventType):
    """Decorator to register a dispatcher function for a given WalletEventType."""
    def decorator(func: Callable[[dict[str, Any]], Awaitable[None]]):
        WALLET_EVENT_HANDLERS[event_type.value] = func
        return func
    return decorator


@register_wallet_handler(WalletEventType.WALLET_CREATED)
async def handle_wallet_created(data: dict[str, Any]) -> None:
    event = WalletCreatedEvent.from_dict(data)
    await event_bus.publish(event)
    logger.info("✅ WalletCreated dispatched: wallet_id=%s", event.wallet_id)


@register_wallet_handler(WalletEventType.WALLET_ACTIVATED)
async def handle_wallet_activated(data: dict[str, Any]) -> None:
    event = WalletActivatedEvent.from_dict(data)
    await event_bus.publish(event)
    logger.info("✅ WalletActivated dispatched: wallet_id=%s", event.wallet_id)


@register_wallet_handler(WalletEventType.WALLET_SUSPENDED)
async def handle_wallet_suspended(data: dict[str, Any]) -> None:
    event = WalletSuspendedEvent.from_dict(data)
    await event_bus.publish(event)
    logger.info("⏸️ WalletSuspended dispatched: wallet_id=%s", event.wallet_id)


@register_wallet_handler(WalletEventType.WALLET_CLOSED)
async def handle_wallet_closed(data: dict[str, Any]) -> None:
    event = WalletClosedEvent.from_dict(data)
    await event_bus.publish(event)
    logger.info("🔒 WalletClosed dispatched: wallet_id=%s", event.wallet_id)


@register_wallet_handler(WalletEventType.WALLET_DEPOSITED)
async def handle_wallet_deposited(data: dict[str, Any]) -> None:
    event = WalletDepositedEvent.from_dict(data)
    await event_bus.publish(event)
    logger.info("📥 WalletDeposited dispatched: wallet_id=%s, amount=%s %s", event.wallet_id, event.amount, event.currency)


@register_wallet_handler(WalletEventType.WALLET_WITHDRAWN)
async def handle_wallet_withdrawn(data: dict[str, Any]) -> None:
    event = WalletWithdrawnEvent.from_dict(data)
    await event_bus.publish(event)
    logger.info("📤 WalletWithdrawn dispatched: wallet_id=%s, amount=%s %s", event.wallet_id, event.amount, event.currency)


@register_wallet_handler(WalletEventType.WALLET_PAYMENT_MADE)
async def handle_wallet_payment_made(data: dict[str, Any]) -> None:
    event = WalletPaymentMadeEvent.from_dict(data)
    await event_bus.publish(event)
    logger.info("💳 WalletPaymentMade dispatched: wallet_id=%s, action_id=%s", event.wallet_id, event.action_id)


@register_wallet_handler(WalletEventType.WALLET_REFUNDED)
async def handle_wallet_refunded(data: dict[str, Any]) -> None:
    event = WalletRefundedEvent.from_dict(data)
    await event_bus.publish(event)
    logger.info("↩️ WalletRefunded dispatched: wallet_id=%s, amount=%s %s", event.wallet_id, event.amount, event.currency)


@register_wallet_handler(WalletEventType.WALLET_ADJUSTED)
async def handle_wallet_adjusted(data: dict[str, Any]) -> None:
    event = WalletAdjustedEvent.from_dict(data)
    await event_bus.publish(event)
    logger.info("🔧 WalletAdjusted dispatched: wallet_id=%s, reason='%s'", event.wallet_id, event.reason)