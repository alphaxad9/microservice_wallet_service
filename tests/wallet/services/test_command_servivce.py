# tests/application/wallet/test_wallet_application_service.py

import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, patch, MagicMock
import pytest

from src.application.wallet.services.wallet_command_services import WalletApplicationService
from src.domain.apps.wallet.aggregate import WalletAggregate
from src.domain.apps.wallet.exceptions import (
    WalletClosedError,
    WalletSuspendedError,
    InvalidWalletCurrencyError,
    WalletNotFoundError,
    WalletDomainError,
)
from src.domain.apps.wallet.repository import WalletCommandRepository


@pytest.fixture
def mock_repo():
    return AsyncMock(spec=WalletCommandRepository)


@pytest.fixture
def wallet_service(mock_repo):
    return WalletApplicationService(repo=mock_repo)


@pytest.fixture
def sample_user_id():
    return uuid.uuid4()


@pytest.fixture
def sample_wallet_id():
    return uuid.uuid4()


@pytest.fixture
def sample_booking_id():
    return uuid.uuid4()


# ----------------------------
# create_wallet tests
# ----------------------------

@pytest.mark.asyncio
async def test_create_wallet_success(wallet_service, mock_repo, sample_user_id):
    # Arrange
    currency = "USD"

    # Act
    wallet_id = await wallet_service.create_wallet(user_id=sample_user_id, currency=currency)

    # Assert
    assert isinstance(wallet_id, uuid.UUID)
    mock_repo.create.assert_called_once()
    called_aggregate = mock_repo.create.call_args[0][0]
    assert called_aggregate.user_id == sample_user_id
    assert called_aggregate.currency == "USD"


@pytest.mark.asyncio
async def test_create_wallet_with_custom_id(wallet_service, mock_repo, sample_user_id, sample_wallet_id):
    # Act
    wallet_id = await wallet_service.create_wallet(
        wallet_id=sample_wallet_id,
        user_id=sample_user_id,
        currency="EUR"
    )

    # Assert
    assert wallet_id == sample_wallet_id
    called_aggregate = mock_repo.create.call_args[0][0]
    assert called_aggregate.wallet_id == sample_wallet_id
    assert called_aggregate.currency == "EUR"


@pytest.mark.asyncio
async def test_create_wallet_missing_user_id_raises(wallet_service):
    # Act & Assert
    with pytest.raises(ValueError, match="user_id is required"):
        await wallet_service.create_wallet(user_id=None)


@pytest.mark.asyncio
async def test_create_wallet_empty_currency_raises(wallet_service, sample_user_id):
    # Act & Assert
    with pytest.raises(ValueError, match="Currency is required"):
        await wallet_service.create_wallet(user_id=sample_user_id, currency="")


@pytest.mark.asyncio
async def test_create_wallet_invalid_aggregate_raises_domain_error(wallet_service, mock_repo, sample_user_id):
    # Arrange
    mock_repo.create.side_effect = ValueError("Invalid currency")
    with patch.object(WalletAggregate, 'create', side_effect=ValueError("Invalid currency")):
        # Act & Assert
        with pytest.raises(WalletDomainError, match="Invalid wallet creation parameters"):
            await wallet_service.create_wallet(user_id=sample_user_id, currency="XYZ")


@pytest.mark.asyncio
async def test_create_wallet_repo_failure_raises_runtime_error(wallet_service, mock_repo, sample_user_id):
    # Arrange
    mock_repo.create.side_effect = Exception("DB down")

    # Act & Assert
    with pytest.raises(RuntimeError, match="Failed to save wallet"):
        await wallet_service.create_wallet(user_id=sample_user_id)


# ----------------------------
# deposit tests
# ----------------------------

@pytest.mark.asyncio
async def test_deposit_success(wallet_service, mock_repo, sample_wallet_id):
    # Arrange
    mock_aggregate = AsyncMock(spec=WalletAggregate)
    mock_aggregate.wallet_id = sample_wallet_id
    mock_aggregate.user_id = uuid.uuid4()
    mock_aggregate.currency = "USD"
    mock_repo.load.return_value = mock_aggregate

    amount = Decimal("100.00")
    reference_id = uuid.uuid4()

    # Act
    await wallet_service.deposit(wallet_id=sample_wallet_id, amount=amount, reference_id=reference_id)

    # Assert
    mock_repo.load.assert_called_once_with(sample_wallet_id)
    mock_aggregate.deposit.assert_called_once_with(amount=amount, reference_id=reference_id)
    mock_repo.save.assert_called_once_with(mock_aggregate)


@pytest.mark.asyncio
async def test_deposit_zero_amount_raises(wallet_service, sample_wallet_id):
    # Act & Assert
    with pytest.raises(ValueError, match="Deposit amount must be positive"):
        await wallet_service.deposit(wallet_id=sample_wallet_id, amount=Decimal("0"))


@pytest.mark.asyncio
async def test_deposit_negative_amount_raises(wallet_service, sample_wallet_id):
    # Act & Assert
    with pytest.raises(ValueError, match="Deposit amount must be positive"):
        await wallet_service.deposit(wallet_id=sample_wallet_id, amount=Decimal("-10"))


@pytest.mark.asyncio
async def test_deposit_wallet_not_found_raises(wallet_service, mock_repo, sample_wallet_id):
    # Arrange
    mock_repo.load.side_effect = WalletNotFoundError(wallet_id=sample_wallet_id)

    # Act & Assert
    with pytest.raises(WalletNotFoundError):
        await wallet_service.deposit(wallet_id=sample_wallet_id, amount=Decimal("10"))


@pytest.mark.asyncio
async def test_deposit_propagates_domain_exceptions(wallet_service, mock_repo, sample_wallet_id):
    # Arrange
    mock_aggregate = MagicMock(spec=WalletAggregate)
    mock_aggregate.wallet_id = sample_wallet_id
    mock_repo.load.return_value = mock_aggregate
    mock_aggregate.deposit.side_effect = WalletClosedError(wallet_id=sample_wallet_id, attempted_operation="deposit")

    # Act & Assert
    with pytest.raises(WalletClosedError):
        await wallet_service.deposit(wallet_id=sample_wallet_id, amount=Decimal("10"))


# ----------------------------
# withdraw tests
# ----------------------------

@pytest.mark.asyncio
async def test_withdraw_success(wallet_service, mock_repo, sample_wallet_id):
    # Arrange
    mock_aggregate = AsyncMock(spec=WalletAggregate)
    mock_aggregate.wallet_id = sample_wallet_id
    mock_repo.load.return_value = mock_aggregate

    amount = Decimal("50.00")

    # Act
    await wallet_service.withdraw(wallet_id=sample_wallet_id, amount=amount)

    # Assert
    mock_repo.load.assert_called_once_with(sample_wallet_id)
    mock_aggregate.withdraw.assert_called_once_with(amount=amount, reference_id=None)
    mock_repo.save.assert_called_once_with(mock_aggregate)


# ----------------------------
# pay_with_wallet tests
# ----------------------------

@pytest.mark.asyncio
async def test_pay_with_wallet_success(wallet_service, mock_repo, sample_wallet_id, sample_booking_id):
    # Arrange
    mock_aggregate = AsyncMock(spec=WalletAggregate)
    mock_aggregate.wallet_id = sample_wallet_id
    mock_repo.load.return_value = mock_aggregate

    amount = Decimal("25.00")

    # Act
    await wallet_service.pay_with_wallet(wallet_id=sample_wallet_id, amount=amount, booking_id=sample_booking_id)

    # Assert
    mock_repo.load.assert_called_once_with(sample_wallet_id)
    mock_aggregate.pay_with_wallet.assert_called_once_with(amount=amount, booking_id=sample_booking_id)
    mock_repo.save.assert_called_once_with(mock_aggregate)


@pytest.mark.asyncio
async def test_pay_with_wallet_missing_booking_id_raises(wallet_service, sample_wallet_id):
    # Act & Assert
    with pytest.raises(ValueError, match="booking_id is required"):
        await wallet_service.pay_with_wallet(wallet_id=sample_wallet_id, amount=Decimal("10"), booking_id=None)


# ----------------------------
# suspend/activate/close tests
# ----------------------------

@pytest.mark.asyncio
async def test_suspend_wallet_success(wallet_service, mock_repo, sample_wallet_id):
    # Arrange
    mock_aggregate = AsyncMock(spec=WalletAggregate)
    mock_aggregate.wallet_id = sample_wallet_id
    mock_repo.load.return_value = mock_aggregate

    # Act
    await wallet_service.suspend_wallet(wallet_id=sample_wallet_id)

    # Assert
    mock_aggregate.suspend.assert_called_once()
    mock_repo.save.assert_called_once_with(mock_aggregate)


@pytest.mark.asyncio
async def test_close_wallet_success(wallet_service, mock_repo, sample_wallet_id):
    # Arrange
    mock_aggregate = AsyncMock(spec=WalletAggregate)
    mock_aggregate.wallet_id = sample_wallet_id
    mock_repo.load.return_value = mock_aggregate

    # Act
    await wallet_service.close_wallet(wallet_id=sample_wallet_id)

    # Assert
    mock_aggregate.close.assert_called_once()
    mock_repo.save.assert_called_once_with(mock_aggregate)


# ----------------------------
# _load_wallet error handling
# ----------------------------

@pytest.mark.asyncio
async def test_load_wallet_generic_error_converted_to_not_found(wallet_service, mock_repo, sample_wallet_id):
    # Arrange
    mock_repo.load.side_effect = Exception("DB timeout")

    # Act & Assert
    with pytest.raises(WalletNotFoundError):
        await wallet_service._load_wallet(sample_wallet_id)


# ----------------------------
# _save_aggregate error handling
# ----------------------------

@pytest.mark.asyncio
async def test_save_aggregate_failure_raises_runtime_error(wallet_service, mock_repo, sample_wallet_id):
    # Arrange
    mock_aggregate = AsyncMock(spec=WalletAggregate)
    mock_aggregate.wallet_id = sample_wallet_id
    mock_repo.save.side_effect = Exception("DB connection lost")

    # Act & Assert
    with pytest.raises(RuntimeError, match="Failed to persist wallet after deposit"):
        await wallet_service._save_aggregate(mock_aggregate, "deposit")