# src/application/wallet/services.interfaces/wallet_command_service_interface.py

from __future__ import annotations

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Optional
from uuid import UUID


# =========================
# WRITE INTERFACE (Commands)
# =========================
class WalletCommandServiceInterface(ABC):
    """
    Abstract interface for the write-side (command) of the wallet domain.
    Defines all operations that mutate wallet state.

    Implementations coordinate domain rules, aggregates, and the command repository.
    This interface is used by API controllers, message handlers, saga coordinators, etc.
    """

    @abstractmethod
    async def create_wallet(
        self,
        *,
        wallet_id: Optional[UUID] = None,
        user_id: UUID,
        currency: str = "USD",
    ) -> UUID:
        """Asynchronous version of create_wallet."""
        raise NotImplementedError


    @abstractmethod
    async def deposit(
        self,
        *,
        wallet_id: UUID,
        amount: Decimal,
        reference_id: Optional[UUID] = None,
    ) -> None:
        """Asynchronous version of deposit."""
        raise NotImplementedError


    @abstractmethod
    async def withdraw(
        self,
        *,
        wallet_id: UUID,
        amount: Decimal,
        reference_id: Optional[UUID] = None,
    ) -> None:
        """Asynchronous version of withdraw."""
        raise NotImplementedError



    @abstractmethod
    async def pay_with_wallet(
        self,
        *,
        wallet_id: UUID,
        amount: Decimal,
        booking_id: UUID,
    ) -> None:
        """Asynchronous version of pay_with_wallet."""
        raise NotImplementedError

    @abstractmethod
    async def refund(
        self,
        *,
        wallet_id: UUID,
        amount: Decimal,
        booking_id: Optional[UUID] = None,
    ) -> None:
        """Asynchronous version of refund."""
        raise NotImplementedError


    @abstractmethod
    async def adjustment(
        self,
        *,
        wallet_id: UUID,
        amount: Decimal,
        reason: str,
        admin_id: Optional[UUID] = None,
    ) -> None:
        """Asynchronous version of adjustment."""
        raise NotImplementedError


    @abstractmethod
    async def suspend_wallet(self, wallet_id: UUID) -> None:
        """Asynchronous version of suspend_wallet."""
        raise NotImplementedError


    @abstractmethod
    async def activate_wallet(self, wallet_id: UUID) -> None:
        """Asynchronous version of activate_wallet."""
        raise NotImplementedError



    @abstractmethod
    async def close_wallet(self, wallet_id: UUID) -> None:
        """Asynchronous version of close_wallet."""
        raise NotImplementedError