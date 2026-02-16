# src/domain/apps/wallet/exceptions.py

from __future__ import annotations
from decimal import Decimal
from typing import Optional
from uuid import UUID


class WalletDomainError(Exception):
    """Base exception for all wallet-related domain errors."""
    pass


class InvalidWalletStateError(WalletDomainError):
    """
    Raised when an operation is attempted on a wallet in an invalid state
    (e.g., trying to pay with a suspended or closed wallet).
    """
    def __init__(
        self,
        wallet_id: UUID | str,
        current_state: str,
        attempted_operation: str,
        message: Optional[str] = None
    ):
        if message is None:
            message = (
                f"Cannot perform '{attempted_operation}' on wallet {wallet_id} "
                f"because it is in state '{current_state}'. "
                f"Operation allowed only on active wallets."
            )
        self.wallet_id = wallet_id
        self.current_state = current_state
        self.attempted_operation = attempted_operation
        super().__init__(message)


class InsufficientFundsError(WalletDomainError):
    """
    Raised when a withdrawal, payment, or transfer exceeds available balance.
    Note: In an event-sourced system, this is typically validated in the application
    service using a read model before invoking the aggregate.
    """
    def __init__(
        self,
        wallet_id: UUID | str,
        available_balance: Decimal | str,
        requested_amount: Decimal | str,
        currency: str,
        message: Optional[str] = None
    ):
        if message is None:
            message = (
                f"Insufficient funds in wallet {wallet_id}. "
                f"Available: {available_balance} {currency}, "
                f"Requested: {requested_amount} {currency}."
            )
        self.wallet_id = wallet_id
        self.available_balance = available_balance
        self.requested_amount = requested_amount
        self.currency = currency
        super().__init__(message)

# src/domain/apps/wallet/exceptions.py

class WalletNotFoundError(WalletDomainError, LookupError):
    def __init__(
        self,
        wallet_id: UUID | str | None = None,
        user_id: UUID | str | None = None,
        message: Optional[str] = None
    ):
        # Convert UUIDs to strings immediately
        if isinstance(wallet_id, UUID):
            wallet_id = str(wallet_id)
        if isinstance(user_id, UUID):
            user_id = str(user_id)

        if message is None:
            if wallet_id:
                message = f"Wallet not found (ID: {wallet_id})"
            elif user_id:
                message = f"No wallet found for user (ID: {user_id})"
            else:
                message = "Wallet not found"
        self.wallet_id = wallet_id
        self.user_id = user_id
        super().__init__(message)

class WalletAlreadyExistsError(WalletDomainError):
    """Raised when attempting to create a wallet for a user who already has one."""
    def __init__(
        self,
        user_id: UUID | str,
        existing_wallet_id: UUID | str | None = None,
        message: Optional[str] = None
    ):
        if message is None:
            base = f"Wallet already exists for user {user_id}"
            if existing_wallet_id:
                base += f" (wallet ID: {existing_wallet_id})"
            message = base
        self.user_id = user_id
        self.existing_wallet_id = existing_wallet_id
        super().__init__(message)


class InvalidWalletCurrencyError(WalletDomainError, ValueError):
    """Raised when a wallet operation uses a currency different from its native currency."""
    def __init__(
        self,
        wallet_id: UUID | str,
        wallet_currency: str,
        operation_currency: str,
        message: Optional[str] = None
    ):
        if message is None:
            message = (
                f"Currency mismatch for wallet {wallet_id}: "
                f"wallet currency is '{wallet_currency}', "
                f"but operation requested '{operation_currency}'."
            )
        self.wallet_id = wallet_id
        self.wallet_currency = wallet_currency
        self.operation_currency = operation_currency
        super().__init__(message)


class WalletClosedError(WalletDomainError):
    """Raised when an operation is attempted on a permanently closed wallet."""
    def __init__(
        self,
        wallet_id: UUID | str,
        attempted_operation: str,
        message: Optional[str] = None
    ):
        if message is None:
            message = (
                f"Cannot perform '{attempted_operation}' on wallet {wallet_id} "
                f"because it has been permanently closed."
            )
        self.wallet_id = wallet_id
        self.attempted_operation = attempted_operation
        super().__init__(message)


class WalletSuspendedError(WalletDomainError):
    """Raised when an operation is attempted on a suspended wallet."""
    def __init__(
        self,
        wallet_id: UUID | str,
        attempted_operation: str,
        message: Optional[str] = None
    ):
        if message is None:
            message = (
                f"Cannot perform '{attempted_operation}' on wallet {wallet_id} "
                f"because it is currently suspended."
            )
        self.wallet_id = wallet_id
        self.attempted_operation = attempted_operation
        super().__init__(message)