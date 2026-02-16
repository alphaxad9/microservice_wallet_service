from src.application.external.user_view import UserView
from src.domain.apps.wallet.models import WalletView
from dataclasses import dataclass


@dataclass(frozen=True)
class WalletResponseDTO:
    wallet: WalletView
    ownr: UserView | None = None