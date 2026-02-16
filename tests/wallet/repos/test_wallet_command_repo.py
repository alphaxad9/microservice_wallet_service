# tests/wallet/repos/test_wallet_command_repo.py

import pytest
from decimal import Decimal
from uuid import uuid4
from unittest.mock import Mock, AsyncMock
from asgiref.sync import sync_to_async

from src.domain.apps.wallet.aggregate import WalletAggregate
from src.domain.apps.wallet.exceptions import WalletNotFoundError
from src.domain.apps.wallet.events import WalletCreatedEvent, WalletDepositedEvent
from src.domain.apps.wallet.models import WalletStatus
from src.infrastructure.apps.eventstore.models import EventStore
from src.infrastructure.repos.wallet.wallet_command_repo import WalletEventSourcedRepository
from src.infrastructure.repos.event_store_repo import EventStoreRepository


@pytest.mark.django_db(transaction=True)
class TestWalletEventSourcedRepository:

    @pytest.fixture
    def event_store_repo(self):
        return Mock(spec=EventStoreRepository)

    @pytest.fixture
    def repo(self, event_store_repo):
        return WalletEventSourcedRepository(event_store_repo)

    @pytest.fixture
    def user_id(self):
        return uuid4()

    @pytest.fixture
    def wallet_id(self):
        return uuid4()

    @pytest.mark.asyncio
    async def test_load_success(self, repo, wallet_id, user_id):
        event1 = WalletCreatedEvent(
            wallet_id=wallet_id,
            user_id=user_id,
            currency="USD"
        )
        event2 = WalletDepositedEvent(
            wallet_id=wallet_id,
            user_id=user_id,
            amount=Decimal("100.00"),
            currency="USD"
        )

        await sync_to_async(EventStore.objects.create)(
            aggregate_id=wallet_id,
            aggregate_type="Wallet",
            aggregate_version=1,
            event_type=event1.event_type,
            event_payload=event1.to_dict(),
        )
        await sync_to_async(EventStore.objects.create)(
            aggregate_id=wallet_id,
            aggregate_type="Wallet",
            aggregate_version=2,
            event_type=event2.event_type,
            event_payload=event2.to_dict(),
        )

        aggregate = await repo.load(wallet_id)

        assert aggregate.wallet_id == wallet_id
        assert aggregate.user_id == user_id
        assert aggregate.currency == "USD"
        # ✅ WalletStatus.ACTIVE.value is 'active' (lowercase)
        assert aggregate.status == WalletStatus.ACTIVE
        # Or if you prefer string comparison:
        # assert aggregate.status.value == "active"

    @pytest.mark.asyncio
    async def test_load_not_found_raises_wallet_not_found_error(self, repo, wallet_id):
        with pytest.raises(WalletNotFoundError) as exc_info:
            await repo.load(wallet_id)
        assert exc_info.value.wallet_id == str(wallet_id)

    @pytest.mark.asyncio
    async def test_load_invalid_first_event_raises_value_error(self, repo, wallet_id):
        event = WalletDepositedEvent(
            wallet_id=wallet_id,
            user_id=uuid4(),
            amount=Decimal("50.00"),
            currency="USD"
        )
        await sync_to_async(EventStore.objects.create)(
            aggregate_id=wallet_id,
            aggregate_type="Wallet",
            aggregate_version=1,
            event_type=event.event_type,
            event_payload=event.to_dict(),
        )

        with pytest.raises(ValueError, match="Expected WalletCreatedEvent as first event"):
            await repo.load(wallet_id)

    @pytest.mark.asyncio
    async def test_save_persists_events_via_event_store_repo(self, repo, wallet_id, user_id):
        aggregate = WalletAggregate.create(user_id=user_id, currency="USD", wallet_id=wallet_id)
        aggregate.deposit(Decimal("50.00"))

        # Use AsyncMock because repo.save() is async, and we're mocking it indirectly via _event_store.append
        # But note: _event_store.append is SYNC, so we mock it as a regular Mock, but called via sync_to_async
        # So we can just use Mock (it works inside sync_to_async)
        repo._event_store.append = Mock()

        await repo.save(aggregate)

        repo._event_store.append.assert_called_once()
        call_kwargs = repo._event_store.append.call_args.kwargs
        assert call_kwargs["aggregate_id"] == wallet_id
        assert call_kwargs["aggregate_type"] == "Wallet"
        assert call_kwargs["expected_version"] == 2  # create → v1, deposit → v2
        assert len(call_kwargs["events"]) == 2

        # ✅ Fix: Call .event_type on an INSTANCE or use the string value directly
        # Option 1: Compare to string
        assert call_kwargs["events"][0].event_type == "wallet.created"
        assert call_kwargs["events"][1].event_type == "wallet.deposited"

        # Option 2 (alternative): 
        # event1 = WalletCreatedEvent(wallet_id=..., user_id=..., currency="USD")
        # assert call_kwargs["events"][0].event_type == event1.event_type

        assert aggregate.version == 4  # 2 + 2

    @pytest.mark.asyncio
    async def test_save_no_events_does_nothing(self, repo, wallet_id, user_id):
        aggregate = WalletAggregate.create(user_id=user_id, currency="USD", wallet_id=wallet_id)
        aggregate.pop_events()  # removes uncommitted events, version remains 1

        repo._event_store.append = Mock()

        await repo.save(aggregate)

        repo._event_store.append.assert_not_called()
        assert aggregate.version == 1

    @pytest.mark.asyncio
    async def test_create_delegates_to_save(self, repo, wallet_id, user_id):
        aggregate = WalletAggregate.create(user_id=user_id, currency="EUR", wallet_id=wallet_id)

        # ✅ Use AsyncMock because repo.save() is an async method
        repo.save = AsyncMock()

        await repo.create(aggregate)

        repo.save.assert_awaited_once_with(aggregate)