# tests/wallet/handlers/test_wallet_query_handler.py
import pytest
from unittest.mock import AsyncMock, Mock
from uuid import UUID, uuid4
from decimal import Decimal

from src.application.external.services.user_api_client import UserAPIClient
from src.application.wallet.handlers.wallet_query_handler import WalletQueryHandler
from src.application.wallet.services.interfaces.wallet_query_service_interface import WalletQueryServiceInterface
from src.domain.apps.wallet.models import WalletView
from src.domain.apps.wallet.exceptions import WalletNotFoundError
from src.application.wallet.handlers.dtos import WalletResponseDTO
from src.application.external.user_view import UserView


@pytest.fixture
def mock_wallet_queries():
    return AsyncMock(spec=WalletQueryServiceInterface)


@pytest.fixture
def mock_user_api():
    return Mock(spec=UserAPIClient)


@pytest.fixture
def wallet_handler(mock_wallet_queries, mock_user_api):
    return WalletQueryHandler(wallet_queries=mock_wallet_queries, user_queries=mock_user_api)


@pytest.fixture
def sample_wallet():
    return WalletView(
        wallet_id=uuid4(),
        user_id=uuid4(),
        balance="100.00",
        currency="USD",
        status="active",
        created_at=Mock(),
        updated_at=Mock(),
    )


@pytest.fixture
def sample_user():
    # UserView only accepts: user_id, username, first_name, last_name
    return UserView(
        user_id=uuid4(),
        username="testuser",
        first_name="Test",
        last_name="User"
    )


@pytest.mark.asyncio
async def test_get_wallet_with_owner_success(wallet_handler, mock_wallet_queries, mock_user_api, sample_wallet, sample_user):
    # Arrange
    mock_wallet_queries.get_wallet.return_value = sample_wallet
    mock_user_api.get_user_by_id.return_value = sample_user

    # Act
    result = await wallet_handler.get_wallet_with_owner(sample_wallet.wallet_id)

    # Assert
    assert isinstance(result, WalletResponseDTO)
    assert result.wallet == sample_wallet
    assert result.ownr == sample_user
    mock_wallet_queries.get_wallet.assert_awaited_once_with(sample_wallet.wallet_id)
    mock_user_api.get_user_by_id.assert_called_once_with(sample_wallet.user_id)


@pytest.mark.asyncio
async def test_get_wallet_with_owner_wallet_not_found_raises(wallet_handler, mock_wallet_queries, sample_wallet):
    # Arrange
    mock_wallet_queries.get_wallet.side_effect = WalletNotFoundError(wallet_id=str(sample_wallet.wallet_id))

    # Act & Assert
    with pytest.raises(WalletNotFoundError):
        await wallet_handler.get_wallet_with_owner(sample_wallet.wallet_id)

    mock_wallet_queries.get_wallet.assert_awaited_once_with(sample_wallet.wallet_id)


@pytest.mark.asyncio
async def test_get_wallet_with_owner_user_api_fails_gracefully(wallet_handler, mock_wallet_queries, mock_user_api, sample_wallet):
    # Arrange
    mock_wallet_queries.get_wallet.return_value = sample_wallet
    mock_user_api.get_user_by_id.side_effect = Exception("User service down")

    # Act
    result = await wallet_handler.get_wallet_with_owner(sample_wallet.wallet_id)

    # Assert
    assert isinstance(result, WalletResponseDTO)
    assert result.wallet == sample_wallet
    assert result.ownr is None
    mock_wallet_queries.get_wallet.assert_awaited_once_with(sample_wallet.wallet_id)
    mock_user_api.get_user_by_id.assert_called_once_with(sample_wallet.user_id)


@pytest.mark.asyncio
async def test_get_wallet_by_user_with_owner_success(wallet_handler, mock_wallet_queries, mock_user_api, sample_wallet, sample_user):
    # Arrange
    mock_wallet_queries.get_wallet_by_user.return_value = sample_wallet
    mock_user_api.get_user_by_id.return_value = sample_user

    # Act
    result = await wallet_handler.get_wallet_by_user_with_owner(sample_wallet.user_id)

    # Assert
    assert isinstance(result, WalletResponseDTO)
    assert result.wallet == sample_wallet
    assert result.ownr == sample_user
    mock_wallet_queries.get_wallet_by_user.assert_awaited_once_with(sample_wallet.user_id)
    mock_user_api.get_user_by_id.assert_called_once_with(sample_wallet.user_id)


@pytest.mark.asyncio
async def test_get_wallet_by_user_not_found_raises(wallet_handler, mock_wallet_queries, sample_wallet):
    # Arrange
    mock_wallet_queries.get_wallet_by_user.side_effect = WalletNotFoundError(user_id=str(sample_wallet.user_id))

    # Act & Assert
    with pytest.raises(WalletNotFoundError):
        await wallet_handler.get_wallet_by_user_with_owner(sample_wallet.user_id)

    mock_wallet_queries.get_wallet_by_user.assert_awaited_once_with(sample_wallet.user_id)


@pytest.mark.asyncio
async def test_get_wallet_balance_success(wallet_handler, mock_wallet_queries, sample_wallet):
    # Arrange
    balance = Decimal("150.75")
    mock_wallet_queries.get_wallet_balance.return_value = balance

    # Act
    result = await wallet_handler.get_wallet_balance(sample_wallet.wallet_id)

    # Assert
    assert result == balance
    mock_wallet_queries.get_wallet_balance.assert_awaited_once_with(sample_wallet.wallet_id)


@pytest.mark.asyncio
async def test_get_wallet_balance_failure_raises(wallet_handler, mock_wallet_queries, sample_wallet):
    # Arrange
    mock_wallet_queries.get_wallet_balance.side_effect = Exception("DB error")

    # Act & Assert
    with pytest.raises(WalletNotFoundError) as exc_info:
        await wallet_handler.get_wallet_balance(sample_wallet.wallet_id)

    # The exception message is "Unable to retrieve wallet balance"
    # But WalletNotFoundError does NOT include wallet_id in the message unless explicitly passed
    # In your handler, you do: raise WalletNotFoundError(wallet_id=str(...), message="...")
    # However, looking at your WalletNotFoundError definition, the __str__ only shows the message
    # So we **cannot** assert that the UUID is in the string representation.
    # Instead, check the attributes.

    exc = exc_info.value
    assert exc.wallet_id == str(sample_wallet.wallet_id)
    assert "Unable to retrieve wallet balance" in str(exc)
    mock_wallet_queries.get_wallet_balance.assert_awaited_once_with(sample_wallet.wallet_id)


@pytest.mark.asyncio
async def test_wallet_exists_true(wallet_handler, mock_wallet_queries, sample_wallet):
    # Arrange
    mock_wallet_queries.wallet_exists.return_value = True

    # Act
    result = await wallet_handler.wallet_exists(sample_wallet.wallet_id)

    # Assert
    assert result is True
    mock_wallet_queries.wallet_exists.assert_awaited_once_with(sample_wallet.wallet_id)


@pytest.mark.asyncio
async def test_wallet_exists_false_on_exception(wallet_handler, mock_wallet_queries, sample_wallet):
    # Arrange
    mock_wallet_queries.wallet_exists.side_effect = Exception("Network error")

    # Act
    result = await wallet_handler.wallet_exists(sample_wallet.wallet_id)

    # Assert
    assert result is False
    mock_wallet_queries.wallet_exists.assert_awaited_once_with(sample_wallet.wallet_id)