# src/infrastructure/repos/wallet/wallet_command_repo.py

from __future__ import annotations

from uuid import UUID
from asgiref.sync import sync_to_async

from src.domain.apps.wallet.repository import WalletCommandRepository
from src.domain.apps.wallet.aggregate import WalletAggregate
from src.domain.apps.wallet.events import (
    WalletCreatedEvent,
    event_from_dict,
)
from src.domain.apps.wallet.exceptions import WalletNotFoundError
from src.infrastructure.apps.eventstore.models import EventStore
from src.infrastructure.repos.event_store_repo import EventStoreRepository


class WalletEventSourcedRepository(WalletCommandRepository):
    """
    Command-side repository for WalletAggregates.
    Loads aggregates from event stream and delegates persistence to EventStoreRepository.
    """

    def __init__(self, event_store: EventStoreRepository):
        self._event_store = event_store

    async def load(self, wallet_id: UUID) -> WalletAggregate:
        # Wrap synchronous ORM query in sync_to_async
        events = await sync_to_async(list)(
            EventStore.objects.filter(
                aggregate_id=wallet_id,
                aggregate_type="Wallet",
            )
            .order_by("aggregate_version")
            .only("aggregate_version", "event_type", "event_payload")
        )

        if not events:
            raise WalletNotFoundError(wallet_id=str(wallet_id))

        first_event = event_from_dict(
            event_type=events[0].event_type,
            event_payload=events[0].event_payload,
        )

        if not isinstance(first_event, WalletCreatedEvent):
            raise ValueError(
                f"Expected WalletCreatedEvent as first event, got {type(first_event).__name__}"
            )

        aggregate = WalletAggregate(
            wallet_id=first_event.wallet_id,
            user_id=first_event.user_id,
            currency=first_event.currency,
        )

        for stored_event in events:
            domain_event = event_from_dict(
                event_type=stored_event.event_type,
                event_payload=stored_event.event_payload,
            )
            aggregate.when(domain_event)

        aggregate.version = events[-1].aggregate_version
        return aggregate

    async def save(self, aggregate: WalletAggregate) -> None:
        events = aggregate.pop_events()
        if not events:
            return

        expected_version = aggregate.version

        # EventStoreRepository.append is a synchronous method
        await sync_to_async(self._event_store.append)(
            aggregate_id=aggregate.wallet_id,
            aggregate_type="Wallet",
            expected_version=expected_version,
            events=events,
            metadata={
                "schema_version": events[0].schema_version if events else 1
            },
        )

        aggregate.version = expected_version + len(events)

    async def create(self, aggregate: WalletAggregate) -> None:
        await self.save(aggregate)