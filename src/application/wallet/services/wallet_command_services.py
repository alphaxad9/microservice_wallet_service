# src/application/wallet/services/wallet_command_service.py

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Optional
from uuid import UUID

from src.domain.apps.wallet.aggregate import WalletAggregate
from src.domain.apps.wallet.exceptions import (
    WalletClosedError,
    WalletSuspendedError,
    InvalidWalletCurrencyError,
    WalletNotFoundError,
    WalletDomainError,
)
from src.domain.apps.wallet.repository import WalletCommandRepository
from src.application.wallet.services.interfaces.wallet_command_service_interface import WalletCommandServiceInterface

logger = logging.getLogger(__name__)


class WalletApplicationService(WalletCommandServiceInterface):
    """
    Concrete implementation of the command-side wallet service with full domain validation
    and coordination between aggregates and the command repository.
    """

    def __init__(self, repo: WalletCommandRepository):
        self._repo = repo

    # ----------------------------
    # Commands
    # ----------------------------

    async def create_wallet(
        self,
        *,
        wallet_id: Optional[UUID] = None,
        user_id: UUID,
        currency: str = "USD",
    ) -> UUID:
        if not user_id:
            raise ValueError("user_id is required")

        if not currency or not currency.strip():
            raise ValueError("Currency is required")

        try:
            aggregate = WalletAggregate.create(
                user_id=user_id,
                currency=currency,
                wallet_id=wallet_id,
            )
        except ValueError as exc:
            logger.error("Failed to create wallet aggregate: %s", exc)
            raise WalletDomainError("Invalid wallet creation parameters") from exc

        try:
            await self._repo.create(aggregate)
        except Exception as exc:
            logger.error("Failed to persist new wallet %s: %s", aggregate.wallet_id, exc)
            raise RuntimeError("Failed to save wallet") from exc

        logger.info("Wallet created: %s for user %s", aggregate.wallet_id, user_id)
        return aggregate.wallet_id

    async def deposit(
        self,
        *,
        wallet_id: UUID,
        amount: Decimal,
        reference_id: Optional[UUID] = None,
    ) -> None:
        if not wallet_id:
            raise ValueError("wallet_id is required")
        if amount <= Decimal("0"):
            raise ValueError("Deposit amount must be positive")

        aggregate = await self._load_wallet(wallet_id)

        try:
            aggregate.deposit(amount=amount, reference_id=reference_id)
        except (WalletClosedError, WalletSuspendedError, InvalidWalletCurrencyError) as exc:
            raise exc
        except ValueError as exc:
            raise WalletDomainError(str(exc)) from exc

        await self._save_aggregate(aggregate, "deposit")

    async def withdraw(
        self,
        *,
        wallet_id: UUID,
        amount: Decimal,
        reference_id: Optional[UUID] = None,
    ) -> None:
        if not wallet_id:
            raise ValueError("wallet_id is required")
        if amount <= Decimal("0"):
            raise ValueError("Withdrawal amount must be positive")

        aggregate = await self._load_wallet(wallet_id)

        try:
            aggregate.withdraw(amount=amount, reference_id=reference_id)
        except (WalletClosedError, WalletSuspendedError, InvalidWalletCurrencyError) as exc:
            raise exc
        except ValueError as exc:
            raise WalletDomainError(str(exc)) from exc

        await self._save_aggregate(aggregate, "withdraw")

    async def pay_with_wallet(
        self,
        *,
        wallet_id: UUID,
        amount: Decimal,
        booking_id: UUID,
    ) -> None:
        if not wallet_id:
            raise ValueError("wallet_id is required")
        if not booking_id:
            raise ValueError("booking_id is required")
        if amount <= Decimal("0"):
            raise ValueError("Payment amount must be positive")

        aggregate = await self._load_wallet(wallet_id)

        try:
            aggregate.pay_with_wallet(amount=amount, booking_id=booking_id)
        except (WalletClosedError, WalletSuspendedError, InvalidWalletCurrencyError) as exc:
            raise exc
        except ValueError as exc:
            raise WalletDomainError(str(exc)) from exc

        await self._save_aggregate(aggregate, "pay_with_wallet")

    async def refund(
        self,
        *,
        wallet_id: UUID,
        amount: Decimal,
        booking_id: Optional[UUID] = None,
    ) -> None:
        if not wallet_id:
            raise ValueError("wallet_id is required")
        if amount <= Decimal("0"):
            raise ValueError("Refund amount must be positive")

        aggregate = await self._load_wallet(wallet_id)

        try:
            aggregate.refund(amount=amount, booking_id=booking_id)
        except (WalletClosedError, WalletSuspendedError, InvalidWalletCurrencyError) as exc:
            raise exc
        except ValueError as exc:
            raise WalletDomainError(str(exc)) from exc

        await self._save_aggregate(aggregate, "refund")

    async def adjustment(
        self,
        *,
        wallet_id: UUID,
        amount: Decimal,
        reason: str,
        admin_id: Optional[UUID] = None,
    ) -> None:
        if not wallet_id:
            raise ValueError("wallet_id is required")
        if amount == Decimal("0"):
            raise ValueError("Adjustment amount cannot be zero")
        if not reason or not reason.strip():
            raise ValueError("Adjustment reason is required")

        aggregate = await self._load_wallet(wallet_id)

        try:
            aggregate.adjustment(amount=amount, reason=reason, admin_id=admin_id)
        except (WalletClosedError, WalletSuspendedError, InvalidWalletCurrencyError) as exc:
            raise exc
        except ValueError as exc:
            raise WalletDomainError(str(exc)) from exc

        await self._save_aggregate(aggregate, f"adjustment (reason: {reason})")

    async def suspend_wallet(self, wallet_id: UUID) -> None:
        if not wallet_id:
            raise ValueError("wallet_id is required")

        aggregate = await self._load_wallet(wallet_id)

        try:
            aggregate.suspend()
        except WalletClosedError as exc:
            raise exc
        except ValueError as exc:
            raise WalletDomainError(str(exc)) from exc

        await self._save_aggregate(aggregate, "suspend_wallet")

    async def activate_wallet(self, wallet_id: UUID) -> None:
        if not wallet_id:
            raise ValueError("wallet_id is required")

        aggregate = await self._load_wallet(wallet_id)

        try:
            aggregate.activate()
        except WalletClosedError as exc:
            raise exc
        except ValueError as exc:
            raise WalletDomainError(str(exc)) from exc

        await self._save_aggregate(aggregate, "activate_wallet")

    async def close_wallet(self, wallet_id: UUID) -> None:
        if not wallet_id:
            raise ValueError("wallet_id is required")

        aggregate = await self._load_wallet(wallet_id)

        try:
            aggregate.close()
        except ValueError as exc:
            raise WalletDomainError(str(exc)) from exc

        await self._save_aggregate(aggregate, "close_wallet")

    # ----------------------------
    # Private Helpers
    # ----------------------------

    async def _load_wallet(self, wallet_id: UUID) -> WalletAggregate:
        try:
            return await self._repo.load(wallet_id)
        except WalletNotFoundError:
            raise
        except Exception as exc:
            logger.error("Unexpected error loading wallet %s: %s", wallet_id, exc)
            raise WalletNotFoundError(wallet_id=str(wallet_id)) from exc

    async def _save_aggregate(self, aggregate: WalletAggregate, operation: str) -> None:
        try:
            await self._repo.save(aggregate)
            logger.info("Wallet %s updated: %s", aggregate.wallet_id, operation)
        except Exception as exc:
            logger.error("Failed to save wallet %s after %s: %s", aggregate.wallet_id, operation, exc)
            raise RuntimeError(f"Failed to persist wallet after {operation}") from exc