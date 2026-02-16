import pytest
from decimal import Decimal
from uuid import uuid4
from asgiref.sync import sync_to_async

from src.domain.apps.wallet.exceptions import WalletNotFoundError
from src.domain.apps.wallet.models import WalletStatus
from src.infrastructure.apps.wallet.models import WalletReadModel
from src.infrastructure.repos.wallet.wallet_query_repo import DjangoWalletQueryRepository


@pytest.mark.django_db(transaction=True)
class TestDjangoWalletQueryRepository:

    @pytest.fixture
    def repo(self):
        return DjangoWalletQueryRepository()

    @pytest.fixture
    def user_id(self):
        return uuid4()

    @pytest.fixture
    def wallet(self, user_id):
        return WalletReadModel.objects.create(
            user_id=user_id,
            balance=Decimal("150.75"),
            currency="USD",
            status=WalletStatus.ACTIVE.name,
        )

    @pytest.mark.asyncio
    async def test_by_id_success(self, repo, wallet):
        result = await repo.by_id(wallet.id)
        # Balance is Decimal per WalletView contract - assert as Decimal
        assert result.balance == Decimal("150.75")

    @pytest.mark.asyncio
    async def test_by_id_not_found(self, repo):
        invalid_id = uuid4()
        with pytest.raises(WalletNotFoundError) as exc_info:
            await repo.by_id(invalid_id)
        assert exc_info.value.wallet_id == str(invalid_id)

    @pytest.mark.asyncio
    async def test_by_user_id_success(self, repo, wallet):
        result = await repo.by_user_id(wallet.user_id)
        # Balance is Decimal per WalletView contract - assert as Decimal
        assert result.balance == Decimal("150.75")

    @pytest.mark.asyncio
    async def test_by_user_id_not_found(self, repo):
        invalid_user_id = uuid4()
        with pytest.raises(WalletNotFoundError) as exc_info:
            await repo.by_user_id(invalid_user_id)
        assert exc_info.value.user_id == str(invalid_user_id)

    @pytest.mark.asyncio
    async def test_by_user_id_multiple_wallets_raises_runtime_error(self, repo, user_id):
        await sync_to_async(WalletReadModel.objects.create)(
            user_id=user_id, balance=Decimal("10.00"), currency="USD", status=WalletStatus.ACTIVE.name
        )
        await sync_to_async(WalletReadModel.objects.create)(
            user_id=user_id, balance=Decimal("20.00"), currency="USD", status=WalletStatus.ACTIVE.name
        )
        with pytest.raises(RuntimeError, match="multiple wallets exist for user"):
            await repo.by_user_id(user_id)

    @pytest.mark.asyncio
    async def test_get_balance_success(self, repo, wallet):
        balance = await repo.get_balance(wallet.id)
        assert balance == Decimal("150.75")  # Consistent Decimal assertion

    @pytest.mark.asyncio
    async def test_get_balance_not_found(self, repo):
        invalid_id = uuid4()
        with pytest.raises(WalletNotFoundError):
            await repo.get_balance(invalid_id)

    @pytest.mark.asyncio
    async def test_exists_true(self, repo, wallet):
        exists = await repo.exists(wallet.id)
        assert exists is True

    @pytest.mark.asyncio
    async def test_exists_false(self, repo):
        invalid_id = uuid4()
        exists = await repo.exists(invalid_id)
        assert exists is False