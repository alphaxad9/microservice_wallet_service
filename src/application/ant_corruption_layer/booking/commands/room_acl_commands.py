# src/application/anti_corruption_layer/booking/commands.py

from __future__ import annotations
from uuid import UUID
from decimal import Decimal

from src.domain.shared.commands import DomainCommand

class RequestPaymentACLCommand(DomainCommand):
    booking_id: UUID
    amount: Decimal
    client_id: UUID


class RequestRefundACLCommand(DomainCommand):
    booking_id: UUID
    amount: Decimal
    client_id: UUID