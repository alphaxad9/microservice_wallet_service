# src/domain/apps/wallet/events.py

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, Type
from uuid import UUID, uuid4

# Shared domain event base
from src.domain.shared.events import DomainEvent


# -----------------------
# Wallet Event Type Enum
# -----------------------
class WalletEventType(Enum):
    """Enumeration of all wallet domain event types."""
    WALLET_CREATED = "wallet.created"
    WALLET_ACTIVATED = "wallet.activated"
    WALLET_SUSPENDED = "wallet.suspended"
    WALLET_CLOSED = "wallet.closed"
    WALLET_DEPOSITED = "wallet.deposited"
    WALLET_WITHDRAWN = "wallet.withdrawn"
    WALLET_PAYMENT_MADE = "wallet.payment_made"
    WALLET_REFUNDED = "wallet.refunded"
    WALLET_PAYMENT_FAILED = "wallet.payment_failed"
    WALLET_REFUND_FAILED = "wallet.refund_failed"
    WALLET_ADJUSTED = "wallet.adjusted"


# -----------------------
# Base Wallet Event (Abstract)
# -----------------------
@dataclass(frozen=True, kw_only=True)
class WalletEvent(DomainEvent, ABC):
    """
    Base class for all wallet domain events.
    Inherits common fields from DomainEvent and adds wallet context.
    """
    wallet_id: UUID
    user_id: UUID

    def __post_init__(self) -> None:
        if not isinstance(self.wallet_id, UUID):
            raise TypeError("wallet_id must be a UUID")
        if not isinstance(self.user_id, UUID):
            raise TypeError("user_id must be a UUID")

    @property
    @abstractmethod
    def event_type(self) -> str:
        """Concrete subclasses return WalletEventType.value."""
        raise NotImplementedError()

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            "wallet_id": str(self.wallet_id),
            "user_id": str(self.user_id),
        })
        return base

    @classmethod
    def base_from_dict(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        occurred_at = (
            datetime.fromisoformat(data["occurred_at"])
            if "occurred_at" in data
            else datetime.now(timezone.utc)
        )

        return {
            "event_id": UUID(data.get("event_id", str(uuid4()))),
            "occurred_at": occurred_at,
            "schema_version": data.get("schema_version", 1),
            "wallet_id": UUID(data["wallet_id"]),
            "user_id": UUID(data["user_id"]),
        }
@dataclass(frozen=True, kw_only=True)
class WalletPaymentMadeEvent(WalletEvent):
    amount: Decimal
    currency: str
    booking_id: UUID | None = None  # Make optional

    @property
    def event_type(self) -> str:
        return WalletEventType.WALLET_PAYMENT_MADE.value

    def payload(self) -> Dict[str, Any]:
        payload_data = {
            "amount": str(self.amount),
            "currency": self.currency,
        }
        if self.booking_id:
            payload_data["booking_id"] = str(self.booking_id)
        return payload_data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WalletPaymentMadeEvent":
        base = cls.base_from_dict(data)
        payload = data.get("payload", {})
        base["amount"] = Decimal(payload.get("amount", "0"))
        base["currency"] = payload.get("currency", "USD")
        
        # Handle booking_id gracefully - it might be missing in older events
        booking_id = payload.get("booking_id")
        if booking_id:
            base["booking_id"] = UUID(booking_id)
        else:
            base["booking_id"] = None
            
        return cls(**base)

@dataclass(frozen=True, kw_only=True)
class WalletRefundedEvent(WalletEvent):
    amount: Decimal
    currency: str
    booking_id: UUID | None = None  # Already optional

    @property
    def event_type(self) -> str:
        return WalletEventType.WALLET_REFUNDED.value

    def payload(self) -> Dict[str, Any]:
        payload_data = {
            "amount": str(self.amount),
            "currency": self.currency,
        }
        if self.booking_id:
            payload_data["booking_id"] = str(self.booking_id)
        return payload_data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WalletRefundedEvent":
        base = cls.base_from_dict(data)
        payload = data.get("payload", {})
        base["amount"] = Decimal(payload.get("amount", "0"))
        base["currency"] = payload.get("currency", "USD")
        booking_id = payload.get("booking_id")
        base["booking_id"] = UUID(booking_id) if booking_id else None
        return cls(**base)

@dataclass(frozen=True, kw_only=True)
class WalletCreatedEvent(WalletEvent):
    currency: str

    @property
    def event_type(self) -> str:
        return WalletEventType.WALLET_CREATED.value

    def payload(self) -> Dict[str, Any]:
        return {"currency": self.currency}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WalletCreatedEvent":
        base = cls.base_from_dict(data)
        payload = data.get("payload", {})
        base["currency"] = payload.get("currency", "USD")
        return cls(**base)


@dataclass(frozen=True, kw_only=True)
class WalletActivatedEvent(WalletEvent):
    @property
    def event_type(self) -> str:
        return WalletEventType.WALLET_ACTIVATED.value

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WalletActivatedEvent":
        base = cls.base_from_dict(data)
        return cls(**base)


@dataclass(frozen=True, kw_only=True)
class WalletSuspendedEvent(WalletEvent):
    @property
    def event_type(self) -> str:
        return WalletEventType.WALLET_SUSPENDED.value

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WalletSuspendedEvent":
        base = cls.base_from_dict(data)
        return cls(**base)


@dataclass(frozen=True, kw_only=True)
class WalletClosedEvent(WalletEvent):
    @property
    def event_type(self) -> str:
        return WalletEventType.WALLET_CLOSED.value

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WalletClosedEvent":
        base = cls.base_from_dict(data)
        return cls(**base)


@dataclass(frozen=True, kw_only=True)
class WalletDepositedEvent(WalletEvent):
    amount: Decimal
    currency: str
    reference_id: UUID | None = None

    @property
    def event_type(self) -> str:
        return WalletEventType.WALLET_DEPOSITED.value

    def payload(self) -> Dict[str, Any]:
        return {
            "amount": str(self.amount),
            "currency": self.currency,
            "reference_id": str(self.reference_id) if self.reference_id else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WalletDepositedEvent":
        base = cls.base_from_dict(data)
        payload = data.get("payload", {})
        base["amount"] = Decimal(payload.get("amount", "0"))
        base["currency"] = payload.get("currency", "USD")
        ref_id = payload.get("reference_id")
        base["reference_id"] = UUID(ref_id) if ref_id else None
        return cls(**base)


@dataclass(frozen=True, kw_only=True)
class WalletWithdrawnEvent(WalletEvent):
    amount: Decimal
    currency: str
    reference_id: UUID | None = None

    @property
    def event_type(self) -> str:
        return WalletEventType.WALLET_WITHDRAWN.value

    def payload(self) -> Dict[str, Any]:
        return {
            "amount": str(self.amount),
            "currency": self.currency,
            "reference_id": str(self.reference_id) if self.reference_id else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WalletWithdrawnEvent":
        base = cls.base_from_dict(data)
        payload = data.get("payload", {})
        base["amount"] = Decimal(payload.get("amount", "0"))
        base["currency"] = payload.get("currency", "USD")
        ref_id = payload.get("reference_id")
        base["reference_id"] = UUID(ref_id) if ref_id else None
        return cls(**base)




@dataclass(frozen=True, kw_only=True)
class WalletAdjustedEvent(WalletEvent):
    amount: Decimal
    currency: str
    reason: str
    admin_id: UUID | None = None

    @property
    def event_type(self) -> str:
        return WalletEventType.WALLET_ADJUSTED.value

    def payload(self) -> Dict[str, Any]:
        return {
            "amount": str(self.amount),
            "currency": self.currency,
            "reason": self.reason,
            "admin_id": str(self.admin_id) if self.admin_id else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WalletAdjustedEvent":
        base = cls.base_from_dict(data)
        payload = data.get("payload", {})
        base["amount"] = Decimal(payload.get("amount", "0"))
        base["currency"] = payload.get("currency", "USD")
        base["reason"] = payload.get("reason", "")
        admin_id = payload.get("admin_id")
        base["admin_id"] = UUID(admin_id) if admin_id else None
        return cls(**base)


# ---------------------------------------------------------
# Event Type → Class Registry
# ---------------------------------------------------------
def normalize_wallet_event_type(event_type: str) -> str:
    """
    Normalize event type string to canonical WalletEventType.value.
    Supports:
      - canonical: "wallet.created"
      - enum name: "WALLET_CREATED"
      - class name: "WalletCreatedEvent"
    """
    # Already canonical
    if event_type in WALLET_EVENT_REGISTRY:
        return event_type

    # From enum name (e.g., "WALLET_CREATED")
    try:
        return WalletEventType[event_type].value
    except KeyError:
        pass

    # From class name (e.g., "WalletCreatedEvent" → "WALLET_CREATED")
    try:
        # Remove trailing "Event" if present
        class_name = event_type
        if class_name.endswith("Event"):
            class_name = class_name[:-5]  # strip "Event"
        # Convert WalletCreated → WALLET_CREATED
        enum_name = "".join(
            ["_" + c if c.isupper() else c for c in class_name]
        ).upper().lstrip("_")
        return WalletEventType[enum_name].value
    except KeyError:
        pass

    raise ValueError(f"Unknown wallet event type: {event_type}")


WALLET_EVENT_REGISTRY: Dict[str, Type[WalletEvent]] = {
    WalletEventType.WALLET_CREATED.value: WalletCreatedEvent,
    WalletEventType.WALLET_ACTIVATED.value: WalletActivatedEvent,
    WalletEventType.WALLET_SUSPENDED.value: WalletSuspendedEvent,
    WalletEventType.WALLET_CLOSED.value: WalletClosedEvent,
    WalletEventType.WALLET_DEPOSITED.value: WalletDepositedEvent,
    WalletEventType.WALLET_WITHDRAWN.value: WalletWithdrawnEvent,
    WalletEventType.WALLET_PAYMENT_MADE.value: WalletPaymentMadeEvent,
    WalletEventType.WALLET_REFUNDED.value: WalletRefundedEvent,
    WalletEventType.WALLET_ADJUSTED.value: WalletAdjustedEvent,
}


# ---------------------------------------------------------
# Event Reconstruction
# ---------------------------------------------------------
def event_from_dict(
    *,
    event_type: str,
    event_payload: Dict[str, Any],
) -> WalletEvent:
    normalized_type = normalize_wallet_event_type(event_type)
    event_cls = WALLET_EVENT_REGISTRY.get(normalized_type)
    if not event_cls:
        raise ValueError(f"Unknown wallet event type: {event_type}")
    return event_cls.from_dict(event_payload)