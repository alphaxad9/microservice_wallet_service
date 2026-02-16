from __future__ import annotations

from functools import cache

# ------------------------------------------------------------------
# Infrastructure / External Dependencies
# ------------------------------------------------------------------
@cache
def get_http_client():
    from src.application.external.services.http_client import HTTPClient
    return HTTPClient()


@cache
def get_user_api_client():
    from src.application.external.services.user_api_client import UserAPIClient
    return UserAPIClient(http_client=get_http_client())


# ------------------------------------------------------------------
# Kafka Publisher
# ------------------------------------------------------------------
@cache
def get_kafka_command_publisher():
    from src.messaging.kafka.command_publisher import KafkaCommandPublisher
    return KafkaCommandPublisher()

def get_outbox_repository():
    """
    Factory function for the shared OutboxRepository.
    """
    from src.infrastructure.repos.outbox.orm_repository import DjangoOutBoxORMRepository
    return DjangoOutBoxORMRepository()

# ------------------------------------------------------------------
# Repository Factories
# ------------------------------------------------------------------
@cache
def get_wallet_command_repository():
    from src.infrastructure.repos.wallet.wallet_command_repo import WalletEventSourcedRepository
    from src.infrastructure.repos.event_store_repo import EventStoreRepository

    event_store = EventStoreRepository(outbox_repo=get_outbox_repository())
    return WalletEventSourcedRepository(event_store=event_store)


@cache
def get_wallet_query_repository():
    from src.infrastructure.repos.wallet.wallet_query_repo import DjangoWalletQueryRepository

    return DjangoWalletQueryRepository()


# ------------------------------------------------------------------
# Service Factories
# ------------------------------------------------------------------
@cache
def get_wallet_application_service():
    from src.application.wallet.services.wallet_command_services import WalletApplicationService

    return WalletApplicationService(repo=get_wallet_command_repository())


@cache
def get_wallet_query_service():
    from src.application.wallet.services.wallet_query_services import WalletQueryService

    return WalletQueryService(query_repo=get_wallet_query_repository())


# ------------------------------------------------------------------
# Handler Factories
# ------------------------------------------------------------------
@cache
def get_wallet_query_handler():
    from src.application.wallet.handlers.wallet_query_handler import WalletQueryHandler

    return WalletQueryHandler(
        wallet_queries=get_wallet_query_service(),
        user_queries=get_user_api_client(),
    )


@cache
def get_wallet_command_handler():
    from src.application.wallet.handlers.wallet_command_handler import WalletCommandHandler

    return WalletCommandHandler(
        command_service=get_wallet_application_service(),
        query_service=get_wallet_query_service(),
    )