from uuid import UUID, uuid4
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from dataclasses import dataclass
from decimal import Decimal
from src.domain.apps.wallet.exceptions import WalletClosedError, WalletSuspendedError


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


class WalletStatus(Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CLOSED = "closed"


class WalletPaymentMethod(Enum):
    WALLET = "wallet"
    CREDIT_CARD = "credit_card"
    BANK_TRANSFER = "bank_transfer"
    PAYPAL = "paypal"
    OTHER = "other"


@dataclass(frozen=True)
class WalletView:
    wallet_id: UUID
    user_id: UUID
    balance: Optional[Decimal]
    currency: str
    status: str
    created_at: datetime
    updated_at: datetime


class Wallet:
    def __init__(
        self,
        user_id: UUID,
        currency: str = "USD",
        status: WalletStatus = WalletStatus.ACTIVE,
        wallet_id: Optional[UUID] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        self.wallet_id = wallet_id or uuid4()
        self.user_id = user_id
        self.currency = currency.upper()
        self.status = status
        self.created_at = created_at or _now_utc()
        self.updated_at = updated_at or _now_utc()

    @classmethod
    def create(cls, user_id: UUID, currency: str = "USD") -> "Wallet":
        return cls(user_id=user_id, currency=currency)

    def _ensure_active(self) -> None:
        if self.status != WalletStatus.ACTIVE:
            if self.status == WalletStatus.CLOSED:
                raise WalletClosedError(
                    wallet_id=self.wallet_id,
                    attempted_operation="wallet operation"
                )
            else:
                raise WalletSuspendedError(
                    wallet_id=self.wallet_id,
                    attempted_operation="wallet operation"
                )

    def suspend(self) -> None:
        if self.status == WalletStatus.CLOSED:
            raise WalletClosedError(wallet_id=self.wallet_id, attempted_operation="suspend")
        self.status = WalletStatus.SUSPENDED
        self.updated_at = _now_utc()

    def activate(self) -> None:
        if self.status == WalletStatus.CLOSED:
            raise WalletClosedError(wallet_id=self.wallet_id, attempted_operation="activate")
        self.status = WalletStatus.ACTIVE
        self.updated_at = _now_utc()

    def close(self) -> None:
        if self.status == WalletStatus.CLOSED:
            return
        self.status = WalletStatus.CLOSED
        self.updated_at = _now_utc()

    def deposit(self, amount: Decimal, reference_id: Optional[UUID] = None) -> None:
        self._ensure_active()
        raise NotImplementedError("Direct mutations not supported in this minimal aggregate")

    def withdraw(self, amount: Decimal, reference_id: Optional[UUID] = None) -> None:
        self._ensure_active()
        raise NotImplementedError("Direct mutations not supported in this minimal aggregate")

    def pay_with_wallet(self, amount: Decimal, booking_id: UUID) -> None:
        self._ensure_active()
        raise NotImplementedError("Direct mutations not supported in this minimal aggregate")

    def refund(self, amount: Decimal, booking_id: Optional[UUID] = None) -> None:
        self._ensure_active()
        raise NotImplementedError("Direct mutations not supported in this minimal aggregate")

    def adjustment(self, amount: Decimal, reason: str, admin_id: Optional[UUID] = None) -> None:
        self._ensure_active()
        raise NotImplementedError("Direct mutations not supported in this minimal aggregate")

    def __repr__(self) -> str:
        return (
            f"Wallet(id={self.wallet_id}, user={self.user_id}, "
            f"currency={self.currency}, status={self.status.value})"
        )