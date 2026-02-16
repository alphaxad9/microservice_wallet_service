from typing import Dict, Any
from uuid import UUID as UUIDType
from decimal import Decimal as DecimalType

from src.application.ant_corruption_layer.booking.commands.room_acl_commands import (
    RequestRefundACLCommand,
    RequestPaymentACLCommand,
)


def translate_booking_command(
    booking_command_name: str,
    payload: Dict[str, Any],
):
    """
    Translates booking_service commands into wallet-compatible ACL commands.
    Validates and converts raw payload into strongly-typed domain commands.
    """
    try:
        if booking_command_name == "RequestRefundCommand":
            return RequestRefundACLCommand(
                booking_id=UUIDType(payload["booking_id"]),
                amount=DecimalType(str(payload["amount"])),
                client_id=UUIDType(payload["client_id"]),
            )
        elif booking_command_name == "RequestPaymentCommand":
            return RequestPaymentACLCommand(
                booking_id=UUIDType(payload["booking_id"]),
                amount=DecimalType(str(payload["amount"])),
                client_id=UUIDType(payload["client_id"]),
            )
        else:
            raise RuntimeError(f"Unsupported booking command: {booking_command_name}")
    except KeyError as e:
        raise ValueError(f"Missing required field in payload for {booking_command_name}: {e}")
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid data in payload for {booking_command_name}: {e}")