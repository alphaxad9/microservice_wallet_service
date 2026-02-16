# src/application/wallet/services/wallet_query_service.py

from __future__ import annotations

import logging
from decimal import Decimal
from uuid import UUID

from src.domain.apps.wallet.models import WalletView
from src.domain.apps.wallet.repository import WalletQueryRepository
from src.domain.apps.wallet.exceptions import WalletNotFoundError
from src.application.wallet.services.interfaces.wallet_query_service_interface import WalletQueryServiceInterface

logger = logging.getLogger(__name__)


class WalletQueryService(WalletQueryServiceInterface):
    """
    Concrete implementation of the wallet query interface with proper error handling,
    input validation, and logging. Delegates to a query repository for data access.
    """

    def __init__(self, query_repo: WalletQueryRepository):
        self._query_repo = query_repo

    def _validate_pagination(self, limit: int, offset: int) -> tuple[int, int]:
        """
        Validate and sanitize pagination parameters.
        Negative values are clamped to 0 to avoid unexpected behavior.
        """
        return max(limit, 0), max(offset, 0)

    async def get_wallet(self, wallet_id: UUID) -> WalletView:
        if not wallet_id:
            raise ValueError("wallet_id is required")

        try:
            return await self._query_repo.by_id(wallet_id)
        except WalletNotFoundError:
            # Re-raise expected domain exception
            raise
        except Exception as exc:
            logger.error("Unexpected error fetching wallet %s: %s", wallet_id, exc)
            raise WalletNotFoundError(wallet_id=str(wallet_id)) from exc

    async def get_wallet_by_user(self, user_id: UUID) -> WalletView:
        if not user_id:
            raise ValueError("user_id is required")

        try:
            return await self._query_repo.by_user_id(user_id)
        except WalletNotFoundError:
            raise
        except Exception as exc:  # ✅ Handle unexpected errors like other methods
            logger.error("Unexpected error fetching wallet for user %s: %s", user_id, exc)
            raise WalletNotFoundError(user_id=str(user_id)) from exc  # ✅ Convert to domain error

    async def get_wallet_balance(self, wallet_id: UUID) -> Decimal:
        if not wallet_id:
            raise ValueError("wallet_id is required")

        try:
            return await self._query_repo.get_balance(wallet_id)
        except WalletNotFoundError:
            raise
        except Exception as exc:
            logger.error("Failed to fetch balance for wallet %s: %s", wallet_id, exc)
            raise WalletNotFoundError(wallet_id=str(wallet_id)) from exc



    async def wallet_exists(self, wallet_id: UUID) -> bool:
        if not wallet_id:
            raise ValueError("wallet_id is required")

        try:
            return await self._query_repo.exists(wallet_id)
        except Exception as exc:
            logger.warning("Error checking existence of wallet %s: %s", wallet_id, exc)
            # Conservative: if check fails, assume it doesn't exist
            return False