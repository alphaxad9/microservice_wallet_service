# tests/infrastructure/repos/test_event_store_repo.py

import pytest
from unittest.mock import Mock, patch
from uuid import uuid4
from django.conf import settings
from django.test import TestCase, override_settings

from src.domain.shared.events import DomainEvent
from src.domain.shared.exceptions import OptimisticConcurrencyError
from src.infrastructure.apps.eventstore.models import EventStore
from src.domain.outbox.events import OutboxEvent
from src.domain.outbox.repositories import OutboxRepository
from src.infrastructure.repos.event_store_repo import EventStoreRepository


class SampleDomainEvent(DomainEvent):
    def __init__(self, amount: float = 100.0):
        super().__init__()
        self._amount = amount

    @property
    def event_type(self) -> str:
        return "test.event.created"

    def payload(self) -> dict:
        return {"amount": self._amount}

    @classmethod
    def from_dict(cls, data: dict):
        return cls(amount=data["payload"]["amount"])


class TestEventStoreRepository(TestCase):

    def setUp(self):
        self.outbox_repo = Mock(spec=OutboxRepository)
        self.repo = EventStoreRepository(outbox_repo=self.outbox_repo)
        self.aggregate_id = uuid4()
        self.aggregate_type = "Wallet"

    def test_append_persists_event_and_calls_outbox(self):
        event = SampleDomainEvent(amount=75.0)
        self.repo.append(
            aggregate_id=self.aggregate_id,
            aggregate_type=self.aggregate_type,
            expected_version=0,
            events=[event],
        )
        stored = EventStore.objects.get(aggregate_id=self.aggregate_id)
        assert stored.aggregate_version == 1
        self.outbox_repo.save.assert_called_once()

    def test_append_with_empty_events_does_nothing(self):
        self.repo.append(
            aggregate_id=self.aggregate_id,
            aggregate_type=self.aggregate_type,
            expected_version=0,
            events=[],
        )
        assert EventStore.objects.count() == 0
        self.outbox_repo.save.assert_not_called()

    def test_append_handles_multiple_events_sequentially(self):
        events = [SampleDomainEvent(10), SampleDomainEvent(20)]
        self.repo.append(
            aggregate_id=self.aggregate_id,
            aggregate_type=self.aggregate_type,
            expected_version=0,
            events=events,
        )
        assert EventStore.objects.count() == 2
        assert self.outbox_repo.save.call_count == 2

    def test_append_raises_optimistic_concurrency_error_on_duplicate_version(self):
        EventStore.objects.create(
            aggregate_id=self.aggregate_id,
            aggregate_type=self.aggregate_type,
            aggregate_version=1,
            event_type="test.duplicate",
            event_payload={"test": "data"},
        )
        with pytest.raises(OptimisticConcurrencyError):
            self.repo.append(
                aggregate_id=self.aggregate_id,
                aggregate_type=self.aggregate_type,
                expected_version=0,
                events=[SampleDomainEvent()],
            )
        self.outbox_repo.save.assert_not_called()

    @override_settings(DEBUG=True)
    @patch("src.infrastructure.projectors.wallet.projector.WalletProjectionRunner")
    def test_append_calls_synchronous_projection_in_debug_mode(self, mock_runner_class):
        mock_runner_instance = Mock()
        mock_runner_class.return_value = mock_runner_instance
        event = SampleDomainEvent()

        self.repo.append(
            aggregate_id=self.aggregate_id,
            aggregate_type=self.aggregate_type,
            expected_version=0,
            events=[event],
        )

        mock_runner_class.assert_called_once()
        mock_runner_instance.apply_from_event.assert_called_once_with(
            event, self.aggregate_id, 1
        )

    @override_settings(DEBUG=False)
    def test_append_does_not_call_projection_in_non_debug_mode(self):
        event = SampleDomainEvent()
        self.repo.append(
            aggregate_id=self.aggregate_id,
            aggregate_type=self.aggregate_type,
            expected_version=0,
            events=[event],
        )
        self.outbox_repo.save.assert_called_once()