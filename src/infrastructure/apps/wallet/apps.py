# src/infrastructure/apps/wallet/apps.py

from django.apps import AppConfig


class WalletConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "src.infrastructure.apps.wallet"

    def ready(self) -> None:
        # Register projection runner
        from src.infrastructure.projectors.wallet.projector import WalletProjectionRunner
        from src.infrastructure.projectors.registry import register_projection

        register_projection("wallet", WalletProjectionRunner())

        # Configure wallet event handlers on the global event bus
        from src.messaging.wallet.config import configure_wallet_event_bus

        configure_wallet_event_bus()