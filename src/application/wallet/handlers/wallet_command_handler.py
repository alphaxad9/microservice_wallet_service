from __future__ import annotations

from decimal import Decimal
from typing import Optional
from uuid import UUID

from src.application.wallet.services.interfaces.wallet_command_service_interface import WalletCommandServiceInterface
from src.application.wallet.services.wallet_query_services import WalletQueryService  # assumed to exist
from src.domain.apps.wallet.exceptions import (
    WalletDomainError,
    WalletNotFoundError,
)
from src.domain.apps.wallet.models import WalletView


class WalletCommandHandler:
    """
    Thin orchestration layer for wallet commands.
    - Delegates all mutations to WalletCommandServiceInterface.
    - Uses WalletQueryService for read-after-write (if needed).
    - Wraps infrastructure or unexpected errors into WalletDomainError.
    - No business logic. No event emission. No persistence details.
    """

    def __init__(
        self,
        command_service: WalletCommandServiceInterface,
        query_service: WalletQueryService,
    ):
        self._commands  = command_service
        self._queries = query_service

    # -------------------------
    # Wallet Lifecycle
    # -------------------------

    async def create_wallet(
        self,
        *,
        user_id: UUID,
        currency: str = "USD",
        wallet_id: Optional[UUID] = None,
    ) -> WalletView:
        try:
            wallet_id = await self._commands.create_wallet(
                wallet_id=wallet_id,
                user_id=user_id,
                currency=currency,
            )
        except WalletDomainError:
            raise
        except Exception as exc:
            raise WalletDomainError("Failed to create wallet") from exc

        try:
            return await self._queries.get_wallet(wallet_id)
        except WalletNotFoundError:
            raise WalletDomainError(f"Wallet created (ID: {wallet_id}) but not found in read model")
        except Exception as exc:
            raise WalletDomainError(f"Wallet created (ID: {wallet_id}) but failed to load view") from exc

    # -------------------------
    # Balance Operations
    # -------------------------

    async def deposit(
        self,
        *,
        wallet_id: UUID,
        amount: Decimal,
        reference_id: Optional[UUID] = None,
    ) -> WalletView:
        try:
            await self._commands.deposit(
                wallet_id=wallet_id,
                amount=amount,
                reference_id=reference_id,
            )
        except WalletDomainError:
            raise
        except Exception as exc:
            raise WalletDomainError("Failed to deposit into wallet") from exc

        return await self._safe_fetch_view(wallet_id)

    async def withdraw(
        self,
        *,
        wallet_id: UUID,
        amount: Decimal,
        reference_id: Optional[UUID] = None,
    ) -> WalletView:
        try:
            await self._commands.withdraw(
                wallet_id=wallet_id,
                amount=amount,
                reference_id=reference_id,
            )
        except WalletDomainError:
            raise
        except Exception as exc:
            raise WalletDomainError("Failed to withdraw from wallet") from exc

        return await self._safe_fetch_view(wallet_id)

    async def pay_with_wallet(
        self,
        *,
        wallet_id: UUID,
        amount: Decimal,
        booking_id: UUID,
    ) -> WalletView:
        try:
            await self._commands.pay_with_wallet(
                wallet_id=wallet_id,
                amount=amount,
                booking_id=booking_id,
            )
        except WalletDomainError:
            raise
        except Exception as exc:
            raise WalletDomainError("Failed to pay using wallet") from exc

        return await self._safe_fetch_view(wallet_id)

    async def refund(
        self,
        *,
        wallet_id: UUID,
        amount: Decimal,
        booking_id: Optional[UUID] = None,
    ) -> WalletView:
        try:
            await self._commands.refund(
                wallet_id=wallet_id,
                amount=amount,
                booking_id=booking_id,
            )
        except WalletDomainError:
            raise
        except Exception as exc:
            raise WalletDomainError("Failed to refund to wallet") from exc

        return await self._safe_fetch_view(wallet_id)

    async def adjustment(
        self,
        *,
        wallet_id: UUID,
        amount: Decimal,
        reason: str,
        admin_id: Optional[UUID] = None,
    ) -> WalletView:
        try:
            await self._commands.adjustment(
                wallet_id=wallet_id,
                amount=amount,
                reason=reason,
                admin_id=admin_id,
            )
        except WalletDomainError:
            raise
        except Exception as exc:
            raise WalletDomainError("Failed to adjust wallet balance") from exc

        return await self._safe_fetch_view(wallet_id)

    # -------------------------
    # Wallet State Management
    # -------------------------

    async def suspend_wallet(self, wallet_id: UUID) -> WalletView:
        try:
            await self._commands.suspend_wallet(wallet_id)
        except WalletDomainError:
            raise
        except Exception as exc:
            raise WalletDomainError("Failed to suspend wallet") from exc

        return await self._safe_fetch_view(wallet_id)

    async def activate_wallet(self, wallet_id: UUID) -> WalletView:
        try:
            await self._commands.activate_wallet(wallet_id)
        except WalletDomainError:
            raise
        except Exception as exc:
            raise WalletDomainError("Failed to activate wallet") from exc

        return await self._safe_fetch_view(wallet_id)

    async def close_wallet(self, wallet_id: UUID) -> WalletView:
        try:
            await self._commands.close_wallet(wallet_id)
        except WalletDomainError:
            raise
        except Exception as exc:
            raise WalletDomainError("Failed to close wallet") from exc

        return await self._safe_fetch_view(wallet_id)

    # -------------------------
    # Helpers
    # -------------------------

    async def _safe_fetch_view(self, wallet_id: UUID) -> WalletView:
        try:
            return await self._queries.get_wallet(wallet_id)
        except WalletNotFoundError:
            raise WalletDomainError(f"Wallet {wallet_id} not found after successful command")
        except Exception as exc:
            raise WalletDomainError(f"Failed to retrieve wallet view after command") from exc