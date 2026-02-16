# tests/application/wallet/test_wallet_query_service.py

import pytest
from unittest.mock import AsyncMock, patch
from uuid import UUID, uuid4
from decimal import Decimal

from src.domain.apps.wallet.models import WalletView
from src.domain.apps.wallet.exceptions import WalletNotFoundError
from src.application.wallet.services.wallet_query_services import WalletQueryService


@pytest.fixture
def mock_query_repo():
    return AsyncMock()


@pytest.fixture
def wallet_query_service(mock_query_repo):
    return WalletQueryService(query_repo=mock_query_repo)


@pytest.fixture
def sample_wallet_view():
    return WalletView(
        wallet_id=uuid4(),
        user_id=uuid4(),
        balance="100.00",
        currency="USD",
        status="active",
        created_at="2024-01-01T00:00:00+00:00",
        updated_at="2024-01-02T00:00:00+00:00",
    )


@pytest.fixture
def sample_wallet_id():
    return uuid4()


@pytest.fixture
def sample_user_id():
    return uuid4()


# =========================
# get_wallet tests
# =========================

@pytest.mark.asyncio
async def test_get_wallet_success(wallet_query_service, mock_query_repo, sample_wallet_view, sample_wallet_id):
    mock_query_repo.by_id.return_value = sample_wallet_view

    result = await wallet_query_service.get_wallet(sample_wallet_id)

    mock_query_repo.by_id.assert_awaited_once_with(sample_wallet_id)
    assert result == sample_wallet_view


@pytest.mark.asyncio
async def test_get_wallet_not_found(wallet_query_service, mock_query_repo, sample_wallet_id):
    mock_query_repo.by_id.side_effect = WalletNotFoundError(wallet_id=str(sample_wallet_id))

    with pytest.raises(WalletNotFoundError):
        await wallet_query_service.get_wallet(sample_wallet_id)

    mock_query_repo.by_id.assert_awaited_once_with(sample_wallet_id)


@pytest.mark.asyncio
async def test_get_wallet_unexpected_error(wallet_query_service, mock_query_repo, sample_wallet_id):
    mock_query_repo.by_id.side_effect = Exception("DB connection failed")

    with pytest.raises(WalletNotFoundError):
        await wallet_query_service.get_wallet(sample_wallet_id)

    mock_query_repo.by_id.assert_awaited_once_with(sample_wallet_id)


@pytest.mark.asyncio
async def test_get_wallet_empty_wallet_id(wallet_query_service):
    with pytest.raises(ValueError, match="wallet_id is required"):
        await wallet_query_service.get_wallet(None)


# =========================
# get_wallet_by_user tests
# =========================

@pytest.mark.asyncio
async def test_get_wallet_by_user_success(wallet_query_service, mock_query_repo, sample_wallet_view, sample_user_id):
    mock_query_repo.by_user_id.return_value = sample_wallet_view

    result = await wallet_query_service.get_wallet_by_user(sample_user_id)

    mock_query_repo.by_user_id.assert_awaited_once_with(sample_user_id)
    assert result == sample_wallet_view


@pytest.mark.asyncio
async def test_get_wallet_by_user_not_found(wallet_query_service, mock_query_repo, sample_user_id):
    mock_query_repo.by_user_id.side_effect = WalletNotFoundError(user_id=str(sample_user_id))

    with pytest.raises(WalletNotFoundError):
        await wallet_query_service.get_wallet_by_user(sample_user_id)

    mock_query_repo.by_user_id.assert_awaited_once_with(sample_user_id)


@pytest.mark.asyncio
async def test_get_wallet_by_user_unexpected_error(wallet_query_service, mock_query_repo, sample_user_id):
    mock_query_repo.by_user_id.side_effect = Exception("DB timeout")

    with pytest.raises(WalletNotFoundError):
        await wallet_query_service.get_wallet_by_user(sample_user_id)

@pytest.mark.asyncio
async def test_get_wallet_by_user_empty_user_id(wallet_query_service):
    with pytest.raises(ValueError, match="user_id is required"):
        await wallet_query_service.get_wallet_by_user(None)


# =========================
# get_wallet_balance tests
# =========================

@pytest.mark.asyncio
async def test_get_wallet_balance_success(wallet_query_service, mock_query_repo, sample_wallet_id):
    mock_balance = Decimal("250.75")
    mock_query_repo.get_balance.return_value = mock_balance

    result = await wallet_query_service.get_wallet_balance(sample_wallet_id)

    mock_query_repo.get_balance.assert_awaited_once_with(sample_wallet_id)
    assert result == mock_balance


@pytest.mark.asyncio
async def test_get_wallet_balance_not_found(wallet_query_service, mock_query_repo, sample_wallet_id):
    mock_query_repo.get_balance.side_effect = WalletNotFoundError(wallet_id=str(sample_wallet_id))

    with pytest.raises(WalletNotFoundError):
        await wallet_query_service.get_wallet_balance(sample_wallet_id)

    mock_query_repo.get_balance.assert_awaited_once_with(sample_wallet_id)


@pytest.mark.asyncio
async def test_get_wallet_balance_unexpected_error(wallet_query_service, mock_query_repo, sample_wallet_id):
    mock_query_repo.get_balance.side_effect = Exception("Corrupt balance record")

    with pytest.raises(WalletNotFoundError):
        await wallet_query_service.get_wallet_balance(sample_wallet_id)

    mock_query_repo.get_balance.assert_awaited_once_with(sample_wallet_id)


@pytest.mark.asyncio
async def test_get_wallet_balance_empty_wallet_id(wallet_query_service):
    with pytest.raises(ValueError, match="wallet_id is required"):
        await wallet_query_service.get_wallet_balance(None)


# =========================
# wallet_exists tests
# =========================

@pytest.mark.asyncio
async def test_wallet_exists_true(wallet_query_service, mock_query_repo, sample_wallet_id):
    mock_query_repo.exists.return_value = True

    result = await wallet_query_service.wallet_exists(sample_wallet_id)

    mock_query_repo.exists.assert_awaited_once_with(sample_wallet_id)
    assert result is True


@pytest.mark.asyncio
async def test_wallet_exists_false(wallet_query_service, mock_query_repo, sample_wallet_id):
    mock_query_repo.exists.return_value = False

    result = await wallet_query_service.wallet_exists(sample_wallet_id)

    mock_query_repo.exists.assert_awaited_once_with(sample_wallet_id)
    assert result is False


@pytest.mark.asyncio
async def test_wallet_exists_error_failsafe(wallet_query_service, mock_query_repo, sample_wallet_id):
    mock_query_repo.exists.side_effect = Exception("Network partition")

    result = await wallet_query_service.wallet_exists(sample_wallet_id)

    mock_query_repo.exists.assert_awaited_once_with(sample_wallet_id)
    assert result is False  # failsafe behavior


@pytest.mark.asyncio
async def test_wallet_exists_empty_wallet_id(wallet_query_service):
    with pytest.raises(ValueError, match="wallet_id is required"):
        await wallet_query_service.wallet_exists(None)


# =========================
# Utility method tests
# =========================

def test_validate_pagination(wallet_query_service):
    assert wallet_query_service._validate_pagination(10, 20) == (10, 20)
    assert wallet_query_service._validate_pagination(-5, 0) == (0, 0)
    assert wallet_query_service._validate_pagination(0, -10) == (0, 0)
    assert wallet_query_service._validate_pagination(-1, -1) == (0, 0)