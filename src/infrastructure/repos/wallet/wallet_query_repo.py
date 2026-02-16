# src/infrastructure/repos/wallet/wallet_query_repo.py

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

from src.domain.apps.wallet.repository import WalletQueryRepository
from src.domain.apps.wallet.models import WalletView
from src.domain.apps.wallet.exceptions import WalletNotFoundError
from src.infrastructure.apps.wallet.models import WalletReadModel
from src.infrastructure.apps.wallet.mappers import WalletReadModelMapper
import logging

logger = logging.getLogger(__name__)


class DjangoWalletQueryRepository(WalletQueryRepository):
    """
    Read-side repository (CQRS query side).
    Returns only WalletView DTOs — never domain entities or aggregates.
    """

    mapper = WalletReadModelMapper

    async def by_id(self, wallet_id: UUID) -> WalletView:
        try:
            logger.info(f"Fetching wallet with ID: {wallet_id}")
            read_model = await WalletReadModel.objects.aget(id=wallet_id)
            
            # Log the fetched wallet details
            logger.info(
                f"Successfully fetched wallet - ID: {read_model.id}, "
                f"Owner: {read_model.user_id}, "
                f"Balance: {read_model.balance}, "
                f"Currency: {read_model.currency}, "
                f"Status: {read_model.status}, "
                f"Created: {read_model.created_at}, "
                f"Updated: {read_model.updated_at}"
            )
            
            return WalletView(
                wallet_id = read_model.id,
                user_id = read_model.user_id,
                balance = read_model.balance,
                currency = read_model.currency,
                status = read_model.status,
                created_at = read_model.created_at,
                updated_at = read_model.updated_at,    
            )
        except ObjectDoesNotExist:
            logger.warning(f"Wallet not found with ID: {wallet_id}")
            raise WalletNotFoundError(wallet_id=wallet_id)
        except MultipleObjectsReturned:
            # This should never happen if id is a primary key
            # But included for explicitness and debugging
            logger.error(f"Data integrity error: multiple wallets found with ID {wallet_id}")
            raise RuntimeError(f"Data integrity error: multiple wallets found with ID {wallet_id}")

    async def by_user_id(self, user_id: UUID) -> WalletView:
        try:
            read_model = await WalletReadModel.objects.aget(user_id=user_id)
            return WalletView(
                wallet_id = read_model.id,
                user_id = read_model.user_id,
                balance = read_model.balance,
                currency = read_model.currency,
                status = read_model.status,
                created_at = read_model.created_at,
                updated_at = read_model.updated_at,    
            )
        except ObjectDoesNotExist:
            raise WalletNotFoundError(user_id=user_id)
        except MultipleObjectsReturned:
            # Violates business rule: one wallet per user
            # Indicates missing unique constraint on user_id
            raise RuntimeError(
                f"Data integrity violation: multiple wallets exist for user {user_id}. "
                "Ensure a unique constraint on user_id in wallet_read_model."
            )

    async def get_balance(self, wallet_id: UUID) -> Decimal:
        try:
            read_model = await WalletReadModel.objects.aget(id=wallet_id)
            return read_model.balance
        except ObjectDoesNotExist:
            raise WalletNotFoundError(wallet_id=wallet_id)
        except MultipleObjectsReturned:
            raise RuntimeError(f"Data integrity error: multiple wallets with ID {wallet_id}")

    async def exists(self, wallet_id: UUID) -> bool:
        # aexists() returns True/False; no exception expected
        return await WalletReadModel.objects.filter(id=wallet_id).aexists()