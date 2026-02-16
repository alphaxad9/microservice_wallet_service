# src/domain/apps/wallet/repository.py

from __future__ import annotations
from abc import ABC, abstractmethod
from uuid import UUID
from decimal import Decimal

from src.domain.apps.wallet.models import WalletView
from src.domain.apps.wallet.aggregate import WalletAggregate


class WalletQueryRepository(ABC):
    """
    Pure query interface for wallet data.

    All methods return WalletView (read model), NOT the aggregate.
    Used only by query services or read-side logic.

    NOTE: Command handlers MUST NOT use this interface.
    """

    @abstractmethod
    async def by_id(self, wallet_id: UUID) -> WalletView:
        """
        Retrieve a wallet by its unique ID.

        Raises:
            WalletNotFoundError: If no wallet exists with the given ID.
        """
        raise NotImplementedError

    @abstractmethod
    async def by_user_id(self, user_id: UUID) -> WalletView:
        """
        Retrieve the wallet associated with a user.

        Assumes one wallet per user.

        Raises:
            WalletNotFoundError: If the user has no wallet.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_balance(self, wallet_id: UUID) -> Decimal:
        """
        Get the current balance of a wallet.

        Balance is derived from event projections or a dedicated balance table.

        Returns:
            Current balance as a Decimal; raises if wallet doesn't exist.
        """
        raise NotImplementedError

    @abstractmethod
    async def exists(self, wallet_id: UUID) -> bool:
        """
        Check whether a wallet exists.
        """
        raise NotImplementedError


















class WalletCommandRepository(ABC):
    """
    Async repository interface for loading and saving WalletAggregates.

    Used exclusively by command handlers and application services.
    """

    @abstractmethod
    async def load(self, wallet_id: UUID) -> WalletAggregate:
        """
        Reconstruct a WalletAggregate from its event stream or state snapshot.

        Raises:
            WalletNotFoundError: If no wallet exists with the given ID.
        """
        raise NotImplementedError

    @abstractmethod
    async def save(self, aggregate: WalletAggregate) -> None:
        """
        Persist uncommitted events and/or updated state of the aggregate.

        Responsibilities:
          - Append new domain events to the event store (in event-sourced systems)
          - Update versioning to prevent concurrent modifications (optional but recommended)
          - Clear uncommitted events after successful persistence

        Raises:
            ConcurrentUpdateError: If optimistic concurrency check fails.
        """
        raise NotImplementedError

    @abstractmethod
    async def create(self, aggregate: WalletAggregate) -> None:
        """
        Create a new wallet (typically by storing its initial event(s)).

        This may be redundant if `save()` handles creation, but explicitly
        separating it can improve clarity in some implementations.
        """
        raise NotImplementedError