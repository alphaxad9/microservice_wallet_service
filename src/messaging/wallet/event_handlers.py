from __future__ import annotations
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass

# Generic domain event base (global)
from src.domain.shared.events import DomainEvent

# Wallet-specific events (for isinstance checks and logging)
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
)

logger = logging.getLogger(__name__)


@dataclass
class WalletEventHandlerContext:
    """
    Context shared by all wallet event handlers.
    Currently empty—handlers only log—but can be extended with dependencies
    (e.g., repositories, external clients) if needed later.
    """
    pass


class BaseWalletEventHandler(ABC):
    """
    Abstract base for all wallet event handlers.
    Accepts DomainEvent to comply with global event bus contract.
    Concrete handlers filter by type using isinstance().
    """
    def __init__(self, ctx: WalletEventHandlerContext) -> None:
        self.ctx = ctx

    @abstractmethod
    async def handle(self, event: DomainEvent) -> None:
        """
        Handle a domain event.
        Implementations must first check if the event is of the expected type.
        """
        raise NotImplementedError()


class WalletCreatedHandler(BaseWalletEventHandler):
    async def handle(self, event: DomainEvent) -> None:
        if not isinstance(event, WalletCreatedEvent):
            return
        logger.info(
            "[🔑Wallet Event Handler] Received WalletCreatedEvent: wallet_id=%s, user_id=%s",
            event.wallet_id,
            event.user_id,
        )


class WalletActivatedHandler(BaseWalletEventHandler):
    async def handle(self, event: DomainEvent) -> None:
        if not isinstance(event, WalletActivatedEvent):
            return
        logger.info(
            "[🔑Wallet Event Handler] Received WalletActivatedEvent: wallet_id=%s, user_id=%s",
            event.wallet_id,
            event.user_id,
        )


class WalletSuspendedHandler(BaseWalletEventHandler):
    async def handle(self, event: DomainEvent) -> None:
        if not isinstance(event, WalletSuspendedEvent):
            return
        logger.info(
            "[🔑Wallet Event Handler] Received WalletSuspendedEvent: wallet_id=%s, user_id=%s",
            event.wallet_id,
            event.user_id,
        )


class WalletClosedHandler(BaseWalletEventHandler):
    async def handle(self, event: DomainEvent) -> None:
        if not isinstance(event, WalletClosedEvent):
            return
        logger.info(
            "[🔑Wallet Event Handler] Received WalletClosedEvent: wallet_id=%s, user_id=%s",
            event.wallet_id,
            event.user_id,
        )


class WalletDepositedHandler(BaseWalletEventHandler):
    async def handle(self, event: DomainEvent) -> None:
        if not isinstance(event, WalletDepositedEvent):
            return
        logger.info(
            "[🔑Wallet Event Handler] Received WalletDepositedEvent: wallet_id=%s, user_id=%s, amount=%s %s",
            event.wallet_id,
            event.user_id,
            event.amount,
            event.currency,
        )


class WalletWithdrawnHandler(BaseWalletEventHandler):
    async def handle(self, event: DomainEvent) -> None:
        if not isinstance(event, WalletWithdrawnEvent):
            return
        logger.info(
            "[🔑Wallet Event Handler] Received WalletWithdrawnEvent: wallet_id=%s, user_id=%s, amount=%s %s",
            event.wallet_id,
            event.user_id,
            event.amount,
            event.currency,
        )


class WalletPaymentMadeHandler(BaseWalletEventHandler):
    async def handle(self, event: DomainEvent) -> None:
        if not isinstance(event, WalletPaymentMadeEvent):
            return
        logger.info(
            "[🔑Wallet Event Handler] Received WalletPaymentMadeEvent: wallet_id=%s, user_id=%s, amount=%s %s, action_id=%s",
            event.wallet_id,
            event.user_id,
            event.amount,
            event.currency,
            event.booking_id,
        )


class WalletRefundedHandler(BaseWalletEventHandler):
    async def handle(self, event: DomainEvent) -> None:
        if not isinstance(event, WalletRefundedEvent):
            return
        logger.info(
            "[🔑Wallet Event Handler] Received WalletRefundedEvent: wallet_id=%s, user_id=%s, amount=%s %s",
            event.wallet_id,
            event.user_id,
            event.amount,
            event.currency,
        )


class WalletAdjustedHandler(BaseWalletEventHandler):
    async def handle(self, event: DomainEvent) -> None:
        if not isinstance(event, WalletAdjustedEvent):
            return
        logger.info(
            "[🔑Wallet Event Handler] Received WalletAdjustedEvent: wallet_id=%s, user_id=%s, amount=%s %s, reason=%s",
            event.wallet_id,
            event.user_id,
            event.amount,
            event.currency,
            event.reason,
        )