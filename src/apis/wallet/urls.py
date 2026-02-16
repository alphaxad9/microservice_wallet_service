# src/application/wallet/urls.py
from django.urls import path

from .command_views import (
    create_wallet,
    deposit,
    withdraw,
    pay_with_wallet,
    refund,
    adjustment,
    suspend_wallet,
    activate_wallet,
    close_wallet,
)
from .query_views import (
    get_wallet_with_owner,
    get_wallet_by_user_with_owner,
    get_wallet_balance,
    check_wallet_exists,
)

app_name = "wallet"

urlpatterns = [
    # --- Command Endpoints (Write) ---
    path("wallets/", create_wallet, name="create-wallet"),  # POST

    path("wallets/deposit/", deposit, name="deposit"),
    path("wallets/withdraw/", withdraw, name="withdraw"),
    path("wallets/pay/", pay_with_wallet, name="pay-with-wallet"),
    path("wallets/refund/", refund, name="refund"),
    path("wallets/adjustment/", adjustment, name="adjustment"),

    path("wallets/<uuid:wallet_id>/suspend/", suspend_wallet, name="suspend-wallet"),
    path("wallets/<uuid:wallet_id>/activate/", activate_wallet, name="activate-wallet"),
    path("wallets/<uuid:wallet_id>/close/", close_wallet, name="close-wallet"),

    # --- Query Endpoints (Read) ---
    path("wallets/<uuid:wallet_id>/", get_wallet_with_owner, name="get-wallet-with-owner"),
    path("wallets/by-user/<uuid:user_id>/", get_wallet_by_user_with_owner, name="get-wallet-by-user"),
    path("wallets/<uuid:wallet_id>/balance/", get_wallet_balance, name="get-wallet-balance"),
    path("wallets/<uuid:wallet_id>/exists/", check_wallet_exists, name="check-wallet-exists"),
]