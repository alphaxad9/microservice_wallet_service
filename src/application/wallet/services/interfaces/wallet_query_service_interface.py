# src/application/wallet/services.interfaces/wallet_query_service_interface.py

from __future__ import annotations

from abc import ABC, abstractmethod
from decimal import Decimal
from uuid import UUID

from src.domain.apps.wallet.models import WalletView


# =========================
# READ INTERFACE (Queries)
# =========================
class WalletQueryServiceInterface(ABC):
    """
    Abstract interface for the read-side of the wallet domain.
    Defines all query operations that can be performed on wallet data.

    Implementations should use denormalized read models (e.g., WalletView)
    for optimal performance. This interface is used by API layers, background jobs,
    dashboards, etc.

    NOTE: This interface must remain free of any command/mutation logic.
    """

   
    @abstractmethod
    async def get_wallet(self, wallet_id: UUID) -> WalletView:
        """
        Asynchronous version of get_wallet.
        Useful for async API handlers or web frameworks.
        """
        raise NotImplementedError


    @abstractmethod
    async def get_wallet_by_user(self, user_id: UUID) -> WalletView:
        """
        Asynchronous version of get_wallet_by_user.
        """
        raise NotImplementedError



    @abstractmethod
    async def get_wallet_balance(self, wallet_id: UUID) -> Decimal:
        """
        Asynchronous version of get_wallet_balance.
        """
        raise NotImplementedError


    @abstractmethod
    async def wallet_exists(self, wallet_id: UUID) -> bool:
        """
        Asynchronous version of wallet_exists.
        """
        raise NotImplementedError