# src/application/wallet/handlers/wallet_query_handler.py
from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from src.application.external.services.user_api_client import UserAPIClient
from src.application.wallet.services.interfaces.wallet_query_service_interface import WalletQueryServiceInterface
from src.domain.apps.wallet.exceptions import WalletNotFoundError
from .dtos import WalletResponseDTO


class WalletQueryHandler:
    """
    Application-level query handler that orchestrates read-side queries for wallets.
    Handles both simple passthrough queries and enriched queries that require
    owner user data from the UserAPIClient.
    """

    def __init__(
        self,
        wallet_queries: WalletQueryServiceInterface,
        user_queries: UserAPIClient,
    ):
        self._wallets = wallet_queries
        self._users = user_queries

    async def get_wallet_with_owner(self, wallet_id: UUID) -> WalletResponseDTO:
        try:
            wallet = await self._wallets.get_wallet(wallet_id)
        except WalletNotFoundError:
            raise
        except Exception as exc:
            raise WalletNotFoundError(wallet_id=str(wallet_id)) from exc

        owner = None
        try:
            owner = self._users.get_user_by_id(wallet.user_id)
        except Exception as exc:
            # External service failure – not a domain error
            # We choose to degrade gracefully and return wallet without owner
            pass

        return WalletResponseDTO(wallet=wallet, ownr=owner)

    async def get_wallet_by_user_with_owner(self, user_id: UUID) -> WalletResponseDTO:
        try:
            wallet = await self._wallets.get_wallet_by_user(user_id)
        except WalletNotFoundError:
            raise
        except Exception as exc:
            raise WalletNotFoundError(user_id=str(user_id)) from exc

        owner = None
        try:
            owner = self._users.get_user_by_id(wallet.user_id)
        except Exception:
            pass  # Graceful degradation

        return WalletResponseDTO(wallet=wallet, ownr=owner)

 
 
    async def get_wallet_balance(self, wallet_id: UUID) -> Decimal:
        try:
            return await self._wallets.get_wallet_balance(wallet_id)
        except Exception as exc:
            raise WalletNotFoundError(
                wallet_id=str(wallet_id),
                message="Unable to retrieve wallet balance"
            ) from exc

 
    async def wallet_exists(self, wallet_id: UUID) -> bool:
        try:
            return await self._wallets.wallet_exists(wallet_id)
        except Exception:
            return False

  