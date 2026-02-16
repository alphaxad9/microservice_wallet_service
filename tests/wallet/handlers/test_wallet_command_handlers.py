from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, patch
from decimal import Decimal
from uuid import UUID, uuid4

from src.application.wallet.handlers.wallet_command_handler import WalletCommandHandler
from src.application.wallet.services.interfaces.wallet_command_service_interface import WalletCommandServiceInterface
from src.application.wallet.services.wallet_query_services import WalletQueryService
from src.domain.apps.wallet.exceptions import (
    WalletDomainError,
    WalletNotFoundError,
)
from src.domain.apps.wallet.models import WalletView


# Fixtures
@pytest.fixture
def mock_command_service() -> AsyncMock:
    return AsyncMock(spec=WalletCommandServiceInterface)


@pytest.fixture
def mock_query_service() -> AsyncMock:
    return AsyncMock(spec=WalletQueryService)


@pytest.fixture
def wallet_handler(mock_command_service, mock_query_service) -> WalletCommandHandler:
    return WalletCommandHandler(
        command_service=mock_command_service,
        query_service=mock_query_service,
    )


@pytest.fixture
def sample_wallet_view() -> WalletView:
    return WalletView(
        wallet_id=uuid4(),
        user_id=uuid4(),
        balance=Decimal("100.00"),
        currency="USD",
        status="ACTIVE",
        created_at="2025-01-01T00:00:00Z",
        updated_at="2025-01-01T00:00:00Z",
    )


# -------------------------
# create_wallet tests
# -------------------------

@pytest.mark.asyncio
async def test_create_wallet_success(wallet_handler, mock_command_service, mock_query_service, sample_wallet_view):
    user_id = uuid4()
    new_wallet_id = uuid4()

    mock_command_service.create_wallet.return_value = new_wallet_id
    mock_query_service.get_wallet.return_value = sample_wallet_view

    result = await wallet_handler.create_wallet(user_id=user_id, currency="USD")

    mock_command_service.create_wallet.assert_awaited_once_with(
        wallet_id=None, user_id=user_id, currency="USD"
    )
    mock_query_service.get_wallet.assert_awaited_once_with(new_wallet_id)
    assert result == sample_wallet_view


@pytest.mark.asyncio
async def test_create_wallet_domain_error_re_raised(wallet_handler, mock_command_service):
    user_id = uuid4()
    mock_command_service.create_wallet.side_effect = WalletDomainError("User not allowed")

    with pytest.raises(WalletDomainError, match="User not allowed"):
        await wallet_handler.create_wallet(user_id=user_id)

    mock_command_service.create_wallet.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_wallet_infrastructure_error_wrapped(wallet_handler, mock_command_service):
    user_id = uuid4()
    mock_command_service.create_wallet.side_effect = ValueError("DB timeout")

    with pytest.raises(WalletDomainError, match="Failed to create wallet"):
        await wallet_handler.create_wallet(user_id=user_id)


@pytest.mark.asyncio
async def test_create_wallet_read_not_found(wallet_handler, mock_command_service, mock_query_service):
    user_id = uuid4()
    wallet_id = uuid4()
    mock_command_service.create_wallet.return_value = wallet_id
    mock_query_service.get_wallet.side_effect = WalletNotFoundError(wallet_id=wallet_id)

    with pytest.raises(WalletDomainError, match=f"Wallet created.*{wallet_id}.*not found in read model"):
        await wallet_handler.create_wallet(user_id=user_id)


@pytest.mark.asyncio
async def test_create_wallet_read_infrastructure_error(wallet_handler, mock_command_service, mock_query_service):
    user_id = uuid4()
    wallet_id = uuid4()
    mock_command_service.create_wallet.return_value = wallet_id
    mock_query_service.get_wallet.side_effect = ConnectionError("Read DB down")

    with pytest.raises(WalletDomainError, match=f"Wallet created.*{wallet_id}.*failed to load view"):
        await wallet_handler.create_wallet(user_id=user_id)


# -------------------------
# Generic operation test helper
# -------------------------

async def _test_wallet_operation_success(
    handler_method,
    command_method_name,
    mock_command_service,
    mock_query_service,
    sample_wallet_view,
    **kwargs
):
    # Mock command success
    getattr(mock_command_service, command_method_name).return_value = None
    mock_query_service.get_wallet.return_value = sample_wallet_view

    result = await handler_method(**kwargs)

    # Assert command called
    getattr(mock_command_service, command_method_name).assert_awaited_once()
    # Assert view fetched
    mock_query_service.get_wallet.assert_awaited_once()
    assert result == sample_wallet_view


async def _test_wallet_operation_domain_error_re_raised(
    handler_method,
    command_method_name,
    mock_command_service,
    **kwargs
):
    getattr(mock_command_service, command_method_name).side_effect = WalletDomainError("Invalid state")

    with pytest.raises(WalletDomainError, match="Invalid state"):
        await handler_method(**kwargs)

    getattr(mock_command_service, command_method_name).assert_awaited_once()


async def _test_wallet_operation_infrastructure_error_wrapped(
    handler_method,
    command_method_name,
    mock_command_service,
    error_msg,
    **kwargs
):
    getattr(mock_command_service, command_method_name).side_effect = RuntimeError("Boom")

    with pytest.raises(WalletDomainError, match=error_msg):
        await handler_method(**kwargs)


# -------------------------
# deposit
# -------------------------

@pytest.mark.asyncio
async def test_deposit_success(wallet_handler, mock_command_service, mock_query_service, sample_wallet_view):
    wallet_id = uuid4()
    await _test_wallet_operation_success(
        wallet_handler.deposit,
        "deposit",
        mock_command_service,
        mock_query_service,
        sample_wallet_view,
        wallet_id=wallet_id,
        amount=Decimal("50.00"),
    )


@pytest.mark.asyncio
async def test_deposit_domain_error_re_raised(wallet_handler, mock_command_service):
    wallet_id = uuid4()
    await _test_wallet_operation_domain_error_re_raised(
        wallet_handler.deposit,
        "deposit",
        mock_command_service,
        wallet_id=wallet_id,
        amount=Decimal("10.00"),
    )


@pytest.mark.asyncio
async def test_deposit_infrastructure_error_wrapped(wallet_handler, mock_command_service):
    wallet_id = uuid4()
    await _test_wallet_operation_infrastructure_error_wrapped(
        wallet_handler.deposit,
        "deposit",
        mock_command_service,
        "Failed to deposit into wallet",
        wallet_id=wallet_id,
        amount=Decimal("20.00"),
    )


# -------------------------
# withdraw
# -------------------------

@pytest.mark.asyncio
async def test_withdraw_success(wallet_handler, mock_command_service, mock_query_service, sample_wallet_view):
    wallet_id = uuid4()
    await _test_wallet_operation_success(
        wallet_handler.withdraw,
        "withdraw",
        mock_command_service,
        mock_query_service,
        sample_wallet_view,
        wallet_id=wallet_id,
        amount=Decimal("30.00"),
    )


# -------------------------
# pay_with_wallet
# -------------------------

@pytest.mark.asyncio
async def test_pay_with_wallet_success(wallet_handler, mock_command_service, mock_query_service, sample_wallet_view):
    wallet_id = uuid4()
    booking_id = uuid4()
    await _test_wallet_operation_success(
        wallet_handler.pay_with_wallet,
        "pay_with_wallet",
        mock_command_service,
        mock_query_service,
        sample_wallet_view,
        wallet_id=wallet_id,
        amount=Decimal("25.50"),
        booking_id=booking_id,
    )


# -------------------------
# refund
# -------------------------

@pytest.mark.asyncio
async def test_refund_success(wallet_handler, mock_command_service, mock_query_service, sample_wallet_view):
    wallet_id = uuid4()
    await _test_wallet_operation_success(
        wallet_handler.refund,
        "refund",
        mock_command_service,
        mock_query_service,
        sample_wallet_view,
        wallet_id=wallet_id,
        amount=Decimal("15.00"),
    )


# -------------------------
# adjustment
# -------------------------

@pytest.mark.asyncio
async def test_adjustment_success(wallet_handler, mock_command_service, mock_query_service, sample_wallet_view):
    wallet_id = uuid4()
    admin_id = uuid4()
    await _test_wallet_operation_success(
        wallet_handler.adjustment,
        "adjustment",
        mock_command_service,
        mock_query_service,
        sample_wallet_view,
        wallet_id=wallet_id,
        amount=Decimal("10.00"),
        reason="Correction",
        admin_id=admin_id,
    )


# -------------------------
# State changes: suspend, activate, close
# -------------------------

@pytest.mark.asyncio
@pytest.mark.parametrize("method_name", ["suspend_wallet", "activate_wallet", "close_wallet"])
async def test_state_change_success(
    method_name,
    wallet_handler,
    mock_command_service,
    mock_query_service,
    sample_wallet_view
):
    wallet_id = uuid4()
    handler_method = getattr(wallet_handler, method_name)
    command_method = method_name

    await _test_wallet_operation_success(
        handler_method,
        command_method,
        mock_command_service,
        mock_query_service,
        sample_wallet_view,
        wallet_id=wallet_id,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("method_name", ["suspend_wallet", "activate_wallet", "close_wallet"])
async def test_state_change_domain_error(method_name, wallet_handler, mock_command_service):
    wallet_id = uuid4()
    handler_method = getattr(wallet_handler, method_name)
    await _test_wallet_operation_domain_error_re_raised(
        handler_method,
        method_name,
        mock_command_service,
        wallet_id=wallet_id,
    )


# -------------------------
# _safe_fetch_view error cases (generic)
# -------------------------

@pytest.mark.asyncio
async def test_safe_fetch_view_not_found(wallet_handler, mock_query_service):
    wallet_id = uuid4()
    mock_query_service.get_wallet.side_effect = WalletNotFoundError(wallet_id=wallet_id)

    with pytest.raises(WalletDomainError, match=f"Wallet.*{wallet_id}.*not found after successful command"):
        await wallet_handler._safe_fetch_view(wallet_id)


@pytest.mark.asyncio
async def test_safe_fetch_view_infrastructure_error(wallet_handler, mock_query_service):
    wallet_id = uuid4()
    mock_query_service.get_wallet.side_effect = TimeoutError("Read timeout")

    with pytest.raises(WalletDomainError, match="Failed to retrieve wallet view after command"):
        await wallet_handler._safe_fetch_view(wallet_id)