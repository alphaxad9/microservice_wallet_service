# src/infrastructure/apps/wallet/mappers.py

from src.domain.apps.wallet.models import Wallet, WalletStatus
from src.infrastructure.apps.wallet.models import WalletReadModel


class WalletReadModelMapper:
    @staticmethod
    def to_view(read_model: WalletReadModel) -> Wallet:
        status_enum = WalletStatus(read_model.status)  # e.g., "active" → WalletStatus.ACTIVE
        return Wallet(
            wallet_id=read_model.id,
            user_id=read_model.user_id,
            currency=read_model.currency,
            status=status_enum,
            created_at=read_model.created_at,
            updated_at=read_model.updated_at,
        )