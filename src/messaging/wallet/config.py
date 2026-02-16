# src/messaging/wallet/config.py

from __future__ import annotations

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
from src.messaging.wallet.event_handlers import (
    WalletEventHandlerContext,
    WalletCreatedHandler,
    WalletActivatedHandler,
    WalletSuspendedHandler,
    WalletClosedHandler,
    WalletDepositedHandler,
    WalletWithdrawnHandler,
    WalletPaymentMadeHandler,
    WalletRefundedHandler,
    WalletAdjustedHandler,
)
from src.messaging.event_bus import event_bus  # or however you name your global instance


def configure_wallet_event_bus() -> None:
    """
    Configures the global wallet event bus with all logging-only handlers.
    
    Call this once during application startup (e.g., in FastAPI lifespan or Django AppConfig).
    """
    # Build shared handler context (currently empty, as handlers only log)
    ctx = WalletEventHandlerContext()

    # Instantiate handlers
    wallet_created_handler = WalletCreatedHandler(ctx=ctx)
    wallet_activated_handler = WalletActivatedHandler(ctx=ctx)
    wallet_suspended_handler = WalletSuspendedHandler(ctx=ctx)
    wallet_closed_handler = WalletClosedHandler(ctx=ctx)
    wallet_deposited_handler = WalletDepositedHandler(ctx=ctx)
    wallet_withdrawn_handler = WalletWithdrawnHandler(ctx=ctx)
    wallet_payment_made_handler = WalletPaymentMadeHandler(ctx=ctx)
    wallet_refunded_handler = WalletRefundedHandler(ctx=ctx)
    wallet_adjusted_handler = WalletAdjustedHandler(ctx=ctx)

    # Subscribe handlers to their respective events
    event_bus.subscribe(WalletCreatedEvent, wallet_created_handler.handle)
    event_bus.subscribe(WalletActivatedEvent, wallet_activated_handler.handle)
    event_bus.subscribe(WalletSuspendedEvent, wallet_suspended_handler.handle)
    event_bus.subscribe(WalletClosedEvent, wallet_closed_handler.handle)
    event_bus.subscribe(WalletDepositedEvent, wallet_deposited_handler.handle)
    event_bus.subscribe(WalletWithdrawnEvent, wallet_withdrawn_handler.handle)
    event_bus.subscribe(WalletPaymentMadeEvent, wallet_payment_made_handler.handle)
    event_bus.subscribe(WalletRefundedEvent, wallet_refunded_handler.handle)
    event_bus.subscribe(WalletAdjustedEvent, wallet_adjusted_handler.handle)