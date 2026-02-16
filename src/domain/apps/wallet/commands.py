# src/domain/apps/wallet/commands.py

from __future__ import annotations
from decimal import Decimal
from enum import Enum
from typing import Optional, Dict, Any
from uuid import UUID

from pydantic import (
    Field,
    field_validator,
    model_validator,
    constr,
)

# Shared base command
from src.domain.shared.commands import DomainCommand


# ------------------------
# Shared Types & Enums
# ------------------------
class Currency(str, Enum):
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    JPY = "JPY"
    CAD = "CAD"
    AUD = "AUD"
    RWF = "RWF"

    def __str__(self) -> str:
        return self.value


class WalletPaymentMethod(str, Enum):
    WALLET = "wallet"
    CREDIT_CARD = "credit_card"
    BANK_TRANSFER = "bank_transfer"
    PAYPAL = "paypal"
    OTHER = "other"


# ------------------------
# Wallet Lifecycle Commands
# ------------------------

class CreateWalletCommand(DomainCommand):
    user_id: UUID = Field(..., description="ID of the user owning the wallet.")
    currency: Currency = Field(default=Currency.USD, description="Currency of the wallet.")

    @field_validator("currency", mode="before")
    @classmethod
    def normalize_currency(cls, v: str | Currency) -> Currency:
        if isinstance(v, str):
            return Currency(v.upper())
        return v


class ActivateWalletCommand(DomainCommand):
    wallet_id: UUID = Field(..., description="ID of the wallet to activate.")


class SuspendWalletCommand(DomainCommand):
    wallet_id: UUID = Field(..., description="ID of the wallet to suspend.")
    reason: Optional[constr(max_length=500)] = Field(default=None)


class CloseWalletCommand(DomainCommand):
    wallet_id: UUID = Field(..., description="ID of the wallet to close.")
    reason: Optional[constr(max_length=500)] = Field(default=None)


# ------------------------
# Wallet Transaction Commands
# ------------------------

class DepositIntoWalletCommand(DomainCommand):
    wallet_id: UUID
    user_id: UUID
    amount: Decimal = Field(..., gt=0, max_digits=19, decimal_places=4)
    currency: Currency
    reference_id: Optional[UUID] = Field(default=None, description="External ID (e.g., payment ID).")
    description: Optional[str] = Field(default=None, max_length=500)

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Deposit amount must be greater than zero.")
        if v.as_tuple().exponent < -4:
            raise ValueError("Amount cannot have more than 4 decimal places.")
        return v


class WithdrawFromWalletCommand(DomainCommand):
    wallet_id: UUID
    user_id: UUID
    amount: Decimal = Field(..., gt=0, max_digits=19, decimal_places=4)
    currency: Currency
    reference_id: Optional[UUID] = Field(default=None, description="External ID (e.g., withdrawal request).")
    description: Optional[str] = Field(default=None, max_length=500)

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Withdrawal amount must be greater than zero.")
        if v.as_tuple().exponent < -4:
            raise ValueError("Amount cannot have more than 4 decimal places.")
        return v


class PayWithWalletCommand(DomainCommand):
    wallet_id: UUID
    user_id: UUID
    action_id: UUID
    amount: Decimal = Field(..., gt=0, max_digits=19, decimal_places=4)
    currency: Currency
    description: Optional[str] = Field(default="Payment for action", max_length=500)

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Payment amount must be greater than zero.")
        if v.as_tuple().exponent < -4:
            raise ValueError("Amount cannot have more than 4 decimal places.")
        return v


class RefundToWalletCommand(DomainCommand):
    wallet_id: UUID
    user_id: UUID
    action_id: Optional[UUID] = Field(default=None)
    amount: Decimal = Field(..., gt=0, max_digits=19, decimal_places=4)
    currency: Currency
    reason: Optional[constr(max_length=300)] = Field(default="Refund")

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Refund amount must be greater than zero.")
        if v.as_tuple().exponent < -4:
            raise ValueError("Amount cannot have more than 4 decimal places.")
        return v


class AdjustWalletBalanceCommand(DomainCommand):
    wallet_id: UUID
    admin_id: UUID = Field(..., description="ID of the admin performing the adjustment.")
    amount: Decimal = Field(..., max_digits=19, decimal_places=4)  # Can be negative
    currency: Currency
    reason: constr(min_length=1, max_length=300) = Field(..., description="Justification for adjustment.")

    @field_validator("amount")
    @classmethod
    def validate_adjustment_amount(cls, v: Decimal) -> Decimal:
        if v.as_tuple().exponent < -4:
            raise ValueError("Adjustment amount cannot have more than 4 decimal places.")
        return v

    @field_validator("reason")
    @classmethod
    def reason_not_empty(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Adjustment reason must not be empty.")
        return stripped


# ------------------------
# Saga & Compensation Commands
# ------------------------

class ReserveWalletFundsCommand(DomainCommand):
    wallet_id: UUID
    user_id: UUID
    action_id: UUID
    amount: Decimal = Field(..., gt=0, max_digits=19, decimal_places=4)
    currency: Currency

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Reserved amount must be greater than zero.")
        if v.as_tuple().exponent < -4:
            raise ValueError("Amount cannot have more than 4 decimal places.")
        return v


class ReleaseWalletFundsCommand(DomainCommand):
    wallet_id: UUID
    action_id: UUID
    amount: Decimal = Field(..., gt=0, max_digits=19, decimal_places=4)
    currency: Currency

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Released amount must be greater than zero.")
        if v.as_tuple().exponent < -4:
            raise ValueError("Amount cannot have more than 4 decimal places.")
        return v


class CompleteWalletSagaCommand(DomainCommand):
    wallet_id: UUID
    action_id: UUID


class FailWalletSagaCommand(DomainCommand):
    wallet_id: UUID
    action_id: UUID
    reason: constr(min_length=1, max_length=500)

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Failure reason must not be empty or whitespace.")
        return stripped


class StartWalletCompensationCommand(DomainCommand):
    wallet_id: UUID
    action_id: UUID


class CompleteWalletCompensationCommand(DomainCommand):
    wallet_id: UUID
    action_id: UUID


# ------------------------
# Utility Commands
# ------------------------

class ExpireWalletReservationCommand(DomainCommand):
    wallet_id: UUID
    action_id: UUID


class UpdateWalletMetadataCommand(DomainCommand):
    wallet_id: UUID
    metadata_updates: Dict[str, Any] = Field(..., min_length=1)

    @model_validator(mode="after")
    def validate_metadata_keys(self) -> "UpdateWalletMetadataCommand":
        for key in self.metadata_updates:
            if not isinstance(key, str) or not key.strip():
                raise ValueError("Metadata keys must be non-empty strings.")
        return self