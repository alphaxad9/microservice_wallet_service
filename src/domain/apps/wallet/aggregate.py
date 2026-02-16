# src/domain/apps/wallet/aggregate.py

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from uuid import UUID, uuid4
from datetime import datetime, timezone
from typing import Optional, List

from src.domain.apps.wallet.models import (
    WalletStatus,
)
from src.domain.apps.wallet.events import (
    WalletEvent,
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
from src.domain.apps.wallet.exceptions import (
    WalletClosedError,
    WalletSuspendedError,
    InvalidWalletCurrencyError
    )
def _now_utc() -> datetime:
    return datetime.now(timezone.utc)
@dataclass
class WalletAggregate:
    # --- Identity & Core Immutable Fields ---
    wallet_id: UUID
    user_id: UUID
    currency: str
    # --- Mutable State ---
    status: WalletStatus = WalletStatus.ACTIVE
    # --- Metadata ---
    created_at: datetime = field(default_factory=_now_utc)
    updated_at: datetime = field(default_factory=_now_utc)
    version: int = 0
    # --- Event sourcing infrastructure ---
    _uncommitted_events: List[WalletEvent] = field(default_factory=list, init=False, repr=False)

    # ---------- PRIVATE CONSTRUCTOR ----------
    def __post_init__(self) -> None:
        if not self.currency.strip():
            raise ValueError("Currency is required")

    # ---------- FACTORY METHOD ----------
    @classmethod
    def create(
        cls,
        user_id: UUID,
        currency: str = "USD",
        wallet_id: Optional[UUID] = None,
    ) -> "WalletAggregate":
        if not user_id:
            raise ValueError("User ID is required")

        agg = cls(
            wallet_id=wallet_id or uuid4(),
            user_id=user_id,
            currency=currency.upper(),
            status=WalletStatus.ACTIVE,
        )

        agg._apply(
            WalletCreatedEvent(
                wallet_id=agg.wallet_id,
                user_id=agg.user_id,
                currency=agg.currency,
            )
        )
        return agg

    # ---------- INTERNAL EVENT SOURCING ----------
    def _apply(self, event: WalletEvent) -> None:
        """Apply event to state and record as uncommitted."""
        self.when(event)
        self._uncommitted_events.append(event)
        self.version += 1

    def when(self, event: WalletEvent) -> None:
        """Dispatch to specific event handler."""
        handler_name = f"when_{event.__class__.__name__}"
        handler = getattr(self, handler_name, None)
        if handler is None:
            raise NotImplementedError(f"No handler for event {event.__class__.__name__}")
        handler(event)
        # All events update timestamp
        self.updated_at = event.occurred_at if hasattr(event, "occurred_at") else _now_utc()

    # ---------- EVENT HANDLERS (State Mutation) ----------
    def when_WalletCreatedEvent(self, event: WalletCreatedEvent) -> None:
        # Core fields already set in constructor — idempotent for rehydration
        self.currency = event.currency
        self.status = WalletStatus.ACTIVE
        self.created_at = event.occurred_at

    def when_WalletActivatedEvent(self, event: WalletActivatedEvent) -> None:
        self.status = WalletStatus.ACTIVE

    def when_WalletSuspendedEvent(self, event: WalletSuspendedEvent) -> None:
        self.status = WalletStatus.SUSPENDED

    def when_WalletClosedEvent(self, event: WalletClosedEvent) -> None:
        self.status = WalletStatus.CLOSED

    def when_WalletDepositedEvent(self, event: WalletDepositedEvent) -> None:
        # No state change needed — balance computed in read model
        pass

    def when_WalletWithdrawnEvent(self, event: WalletWithdrawnEvent) -> None:
        pass

    def when_WalletPaymentMadeEvent(self, event: WalletPaymentMadeEvent) -> None:
        pass

    def when_WalletRefundedEvent(self, event: WalletRefundedEvent) -> None:
        pass

    def when_WalletAdjustedEvent(self, event: WalletAdjustedEvent) -> None:
        pass

    # ---------- COMMAND METHODS (Business Operations) ----------
    def _ensure_active(self, operation: str) -> None:
        if self.status == WalletStatus.CLOSED:
            raise WalletClosedError(wallet_id=self.wallet_id, attempted_operation=operation)
        if self.status == WalletStatus.SUSPENDED:
            raise WalletSuspendedError(wallet_id=self.wallet_id, attempted_operation=operation)

    def _ensure_currency_match(self, amount_currency: str, operation: str) -> None:
        if amount_currency.upper() != self.currency:
            raise InvalidWalletCurrencyError(
                wallet_id=self.wallet_id,
                wallet_currency=self.currency,
                operation_currency=amount_currency,
            )

    def deposit(
        self,
        amount: Decimal,
        reference_id: Optional[UUID] = None,
    ) -> None:
        if amount <= Decimal("0"):
            raise ValueError("Deposit amount must be positive")

        self._ensure_active("deposit")
        self._ensure_currency_match(self.currency, "deposit")

        self._apply(
            WalletDepositedEvent(
                wallet_id=self.wallet_id,
                user_id=self.user_id,
                amount=amount,
                currency=self.currency,
                reference_id=reference_id,
            )
        )

    def withdraw(
        self,
        amount: Decimal,
        reference_id: Optional[UUID] = None,
    ) -> None:
        if amount <= Decimal("0"):
            raise ValueError("Withdrawal amount must be positive")

        self._ensure_active("withdraw")
        self._ensure_currency_match(self.currency, "withdraw")

        # Note: Insufficient funds check MUST be done in application service using read model
        # Aggregate cannot enforce it reliably without balance state

        self._apply(
            WalletWithdrawnEvent(
                wallet_id=self.wallet_id,
                user_id=self.user_id,
                amount=amount,
                currency=self.currency,
                reference_id=reference_id,
            )
        )

    def pay_with_wallet(
        self,
        amount: Decimal,
        booking_id: UUID,
    ) -> None:
        if amount <= Decimal("0"):
            raise ValueError("Payment amount must be positive")

        self._ensure_active("pay_with_wallet")
        self._ensure_currency_match(self.currency, "pay_with_wallet")

        # Insufficient funds validation happens outside (read model)
        self._apply(
            WalletPaymentMadeEvent(
                wallet_id=self.wallet_id,
                user_id=self.user_id,
                amount=amount,
                currency=self.currency,
                booking_id=booking_id,
            )
        )

    def refund(
        self,
        amount: Decimal,
        booking_id: Optional[UUID] = None,
    ) -> None:
        if amount <= Decimal("0"):
            raise ValueError("Refund amount must be positive")

        self._ensure_active("refund")
        self._ensure_currency_match(self.currency, "refund")

        self._apply(
            WalletRefundedEvent(
                wallet_id=self.wallet_id,
                user_id=self.user_id,
                amount=amount,
                currency=self.currency,
                booking_id=booking_id,
            )
        )

    def adjustment(
        self,
        amount: Decimal,
        reason: str,
        admin_id: Optional[UUID] = None,
    ) -> None:
        if amount == Decimal("0"):
            raise ValueError("Adjustment amount cannot be zero")
        if not reason.strip():
            raise ValueError("Adjustment reason is required")

        self._ensure_active("adjustment")
        self._ensure_currency_match(self.currency, "adjustment")

        self._apply(
            WalletAdjustedEvent(
                wallet_id=self.wallet_id,
                user_id=self.user_id,
                amount=abs(amount),  # stored as positive; sign inferred from context if needed
                currency=self.currency,
                reason=reason.strip(),
                admin_id=admin_id,
            )
        )

    def suspend(self) -> None:
        if self.status == WalletStatus.CLOSED:
            raise WalletClosedError(wallet_id=self.wallet_id, attempted_operation="suspend")

        if self.status == WalletStatus.SUSPENDED:
            return  # idempotent

        self._apply(
            WalletSuspendedEvent(
                wallet_id=self.wallet_id,
                user_id=self.user_id,
            )
        )

    def activate(self) -> None:
        if self.status == WalletStatus.CLOSED:
            raise WalletClosedError(wallet_id=self.wallet_id, attempted_operation="activate")

        if self.status == WalletStatus.ACTIVE:
            return  # idempotent

        self._apply(
            WalletActivatedEvent(
                wallet_id=self.wallet_id,
                user_id=self.user_id,
            )
        )

    def close(self) -> None:
        """
        Closes the wallet permanently.
        Important: Zero-balance check must be performed in application service
        using a read model projection before calling this method.
        """
        if self.status == WalletStatus.CLOSED:
            return  # idempotent

        self._apply(
            WalletClosedEvent(
                wallet_id=self.wallet_id,
                user_id=self.user_id,
            )
        )

    # ---------- EVENT SOURCING UTILITIES ----------
    def pop_events(self) -> List[WalletEvent]:
        """Return and clear uncommitted events."""
        events = list(self._uncommitted_events)
        self._uncommitted_events.clear()
        return events

    def has_uncommitted_events(self) -> bool:
        return len(self._uncommitted_events) > 0



    def __repr__(self) -> str:
        return (
            f"WalletAggregate(id={self.wallet_id}, user={self.user_id}, "
            f"currency={self.currency}, status={self.status.value}, version={self.version})"
        )