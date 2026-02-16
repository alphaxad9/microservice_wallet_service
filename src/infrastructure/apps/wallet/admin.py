# src/infrastructure/apps/wallet/admin.py

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import WalletReadModel


@admin.register(WalletReadModel)
class WalletReadModelAdmin(admin.ModelAdmin):
    """
    Admin interface for the WalletReadModel.
    Provides read-only access (as this is a read model updated via projections).
    """

    list_display = (
        'id',
        'user_id',
        'balance',
        'currency',
        'status',
        'created_at',
        'updated_at'
    )
    list_filter = (
        'status',
        'currency',
        'created_at',
        'updated_at'
    )
    search_fields = (
        'id',
        'user_id'
    )
    ordering = ('-created_at',)

    # Make all fields read-only to reinforce that this model is projection-based
    readonly_fields = (
        'id',
        'user_id',
        'balance',
        'currency',
        'status',
        'created_at',
        'updated_at'
    )

    # Disable add/delete to prevent manual manipulation of projection data
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        # Allow viewing but not editing
        return False  # or return True if you want to allow manual fixes in emergencies

    fieldsets = (
        (None, {
            'fields': ('id', 'user_id')
        }),
        (_('Financial'), {
            'fields': ('balance', 'currency'),
            'classes': ('extrapretty',)
        }),
        (_('Status & Timestamps'), {
            'fields': ('status', 'created_at', 'updated_at')
        }),
    )