from __future__ import annotations

from typing import Callable, Dict
from uuid import UUID
from decimal import Decimal, InvalidOperation
from django.db import models, transaction
from src.infrastructure.apps.eventstore.models import ProjectionState, EventStore
from src.domain.shared.events import DomainEvent
from src.domain.apps.wallet.events import (
    WalletEvent,
    WalletEventType,
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
from src.infrastructure.apps.wallet.models import WalletReadModel
from src.domain.apps.wallet.models import WalletStatus
from src.domain.shared.exceptions import ProjectionInvariantViolation


# 🔒 Quantization context: 4 decimal places, standard for most fiat/crypto
_QUANTIZE_EXP = Decimal("0.0000")


def _quantize(amount: Decimal) -> Decimal:
    """
    Safely quantizes a Decimal to 4 decimal places.
    Raises ValueError if amount is not finite (e.g., NaN, Inf).
    """
    if not amount.is_finite():
        raise ValueError("Amount must be a finite number")
    try:
        return amount.quantize(_QUANTIZE_EXP)
    except InvalidOperation as e:
        raise ValueError(f"Cannot quantize amount {amount}: {e}")


def _validate_amount(amount: Decimal) -> None:
    """
    Enforce domain-level sanity on monetary amounts.
    Prevents absurd values that break DecimalField or business logic.
    Adjust limits as needed per your domain policy.
    """
    # Example: max $1 billion with 4 decimals → 1_000_000_000.0000
    MAX_AMOUNT = Decimal("1000000000.0000")  # 1B units
    MIN_AMOUNT = Decimal("-1000000000.0000")

    q_amount = _quantize(amount)
    if q_amount < MIN_AMOUNT or q_amount > MAX_AMOUNT:
        raise ValueError(
            f"Amount {q_amount} is outside allowed range [{MIN_AMOUNT}, {MAX_AMOUNT}]"
        )


class WalletProjector:
    """
    Pure projection logic for the wallet read model.
    Idempotent, atomic, and includes defensive invariant checks.
    Does NOT know about EventStore or ProjectionState.
    """

    EventHandler = Callable[[WalletEvent], None]

    @transaction.atomic
    def project(self, event: DomainEvent) -> None:
        if not isinstance(event, WalletEvent):
            return  # ignore non-wallet events

        handlers: Dict[str, WalletProjector.EventHandler] = {
            WalletEventType.WALLET_CREATED.value: self.on_wallet_created,
            WalletEventType.WALLET_ACTIVATED.value: self.on_wallet_activated,
            WalletEventType.WALLET_SUSPENDED.value: self.on_wallet_suspended,
            WalletEventType.WALLET_CLOSED.value: self.on_wallet_closed,
            WalletEventType.WALLET_DEPOSITED.value: self.on_wallet_deposited,
            WalletEventType.WALLET_WITHDRAWN.value: self.on_wallet_withdrawn,
            WalletEventType.WALLET_PAYMENT_MADE.value: self.on_wallet_payment_made,
            WalletEventType.WALLET_REFUNDED.value: self.on_wallet_refunded,
            WalletEventType.WALLET_ADJUSTED.value: self.on_wallet_adjusted,
        }

        handler = handlers.get(event.event_type)
        if handler is not None:
            handler(event)

    # -------------------------------------------------------------------------
    # Event Handlers (now with quantization & validation)
    # -------------------------------------------------------------------------

    def on_wallet_created(self, event: WalletCreatedEvent) -> None:
        WalletReadModel.objects.update_or_create(
            id=event.wallet_id,
            defaults={
                "user_id": event.user_id,
                "currency": event.currency.upper(),
                "status": WalletStatus.ACTIVE.name,
                "balance": Decimal("0.0000"),
            },
        )

    def on_wallet_activated(self, event: WalletActivatedEvent) -> None:
        updated = WalletReadModel.objects.filter(id=event.wallet_id).update(
            status=WalletStatus.ACTIVE.name
        )
        if updated == 0:
            raise ProjectionInvariantViolation(
                f"WalletActivatedEvent applied but wallet {event.wallet_id} does not exist"
            )

    def on_wallet_suspended(self, event: WalletSuspendedEvent) -> None:
        updated = WalletReadModel.objects.filter(id=event.wallet_id).update(
            status=WalletStatus.SUSPENDED.name
        )
        if updated == 0:
            raise ProjectionInvariantViolation(
                f"WalletSuspendedEvent applied but wallet {event.wallet_id} does not exist"
            )

    def on_wallet_closed(self, event: WalletClosedEvent) -> None:
        updated = WalletReadModel.objects.filter(id=event.wallet_id).update(
            status=WalletStatus.CLOSED.name
        )
        if updated == 0:
            raise ProjectionInvariantViolation(
                f"WalletClosedEvent applied but wallet {event.wallet_id} does not exist"
            )

    def on_wallet_deposited(self, event: WalletDepositedEvent) -> None:
        _validate_amount(event.amount)
        q_amount = _quantize(event.amount)
        updated = WalletReadModel.objects.filter(id=event.wallet_id).update(
            balance=models.F("balance") + q_amount
        )
        if updated == 0:
            raise ProjectionInvariantViolation(
                f"WalletDepositedEvent applied but wallet {event.wallet_id} does not exist"
            )

    def on_wallet_withdrawn(self, event: WalletWithdrawnEvent) -> None:
        _validate_amount(event.amount)
        q_amount = _quantize(event.amount)
        updated = WalletReadModel.objects.filter(
            id=event.wallet_id,
            balance__gte=q_amount,
        ).update(balance=models.F("balance") - q_amount)

        if updated == 0:
            raise ProjectionInvariantViolation(
                f"WalletWithdrawnEvent could not be applied – "
                f"wallet {event.wallet_id} does not exist or has insufficient funds"
            )

    def on_wallet_payment_made(self, event: WalletPaymentMadeEvent) -> None:
        _validate_amount(event.amount)
        q_amount = _quantize(event.amount)
        updated = WalletReadModel.objects.filter(
            id=event.wallet_id,
            balance__gte=q_amount,
        ).update(balance=models.F("balance") - q_amount)

        if updated == 0:
            raise ProjectionInvariantViolation(
                f"WalletPaymentMadeEvent could not be applied – "
                f"wallet {event.wallet_id} does not exist or has insufficient funds"
            )

    def on_wallet_refunded(self, event: WalletRefundedEvent) -> None:
        _validate_amount(event.amount)
        q_amount = _quantize(event.amount)
        updated = WalletReadModel.objects.filter(id=event.wallet_id).update(
            balance=models.F("balance") + q_amount
        )
        if updated == 0:
            raise ProjectionInvariantViolation(
                f"WalletRefundedEvent applied but wallet {event.wallet_id} does not exist"
            )

    def on_wallet_adjusted(self, event: WalletAdjustedEvent) -> None:
        _validate_amount(event.amount)
        q_amount = _quantize(event.amount)
        updated = WalletReadModel.objects.filter(id=event.wallet_id).update(
            balance=models.F("balance") + q_amount
        )
        if updated == 0:
            raise ProjectionInvariantViolation(
                f"WalletAdjustedEvent applied but wallet {event.wallet_id} does not exist"
            )


class WalletProjectionRunner:
    PROJECTION_NAME = "wallet"
    VERSION = 1

    def __init__(self):
        self.projector = WalletProjector()

    @transaction.atomic
    def apply(self, stored_event: EventStore) -> None:
        state, _ = ProjectionState.objects.select_for_update().get_or_create(
            projection_name=self.PROJECTION_NAME,
            defaults={"version": self.VERSION},
        )

        if state.version != self.VERSION:
            return

        from src.domain.apps.wallet.events import event_from_dict
        event = event_from_dict(
            event_type=stored_event.event_type,
            event_payload=stored_event.event_payload,
        )

        self.projector.project(event)

        state.last_event_id = stored_event.id
        state.save(update_fields=["last_event_id"])

    @transaction.atomic
    def apply_from_event(self, event: DomainEvent, aggregate_id: UUID, version: int) -> None:
        from src.infrastructure.apps.eventstore.models import ProjectionState

        state, _ = ProjectionState.objects.select_for_update().get_or_create(
            projection_name=self.PROJECTION_NAME,
            defaults={"version": self.VERSION},
        )

        if state.version != self.VERSION:
            return

        self.projector.project(event)

        state.last_event_id = None
        state.save(update_fields=["last_event_id"])