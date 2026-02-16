# src/infrastructure/apps/wallet/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
import uuid
from decimal import Decimal

from src.domain.apps.wallet.models import WalletStatus


class WalletReadModel(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text=_('Unique wallet identifier')
    )

    user_id = models.UUIDField(
        _('user ID'),
        help_text=_('UUID of the user owning the wallet')
    )

    balance = models.DecimalField(
        max_digits=24,
        decimal_places=4,
        default=Decimal("0.0000"),
    )


    currency = models.CharField(
        _('currency'),
        max_length=3,
        default='USD',
        help_text=_('ISO 4217 currency code (e.g., USD, EUR) in uppercase')
    )

    status = models.CharField(
        _('status'),
        max_length=20,
        choices=[(status.value, status.value) for status in WalletStatus],  # ← CHANGED
        default=WalletStatus.ACTIVE.value  # ← CHANGED
    )

    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        db_table = 'wallet_read_model'
        verbose_name = _('wallet read model')
        verbose_name_plural = _('wallet read models')
        constraints = [
            models.CheckConstraint(
                condition=models.Q(balance__gte=Decimal('0')),
                name='check_wallet_balance_non_negative'
            ),
        ]
        indexes = [
            models.Index(fields=['user_id'], name='idx_wallet_read_user'),
            models.Index(fields=['status'], name='idx_wallet_read_status'),
            models.Index(fields=['currency'], name='idx_wallet_read_currency'),
            models.Index(fields=['created_at'], name='idx_wallet_read_created'),
        ]

    def __str__(self) -> str:
        return f"Wallet {self.id} (user: {self.user_id}) - {self.balance} {self.currency} ({self.status})"