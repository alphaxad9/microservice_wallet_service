# src/application/booking/views.py

import json
import logging
from uuid import UUID
from decimal import Decimal
from datetime import datetime, timezone
from typing import Any, Dict

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from src.application.booking.factory import get_booking_command_handler
from src.domain.apps.booking.exceptions import (
    BookingDomainError,
    BookingNotFoundError,
)

logger = logging.getLogger(__name__)


def _serialize_value(value: Any) -> Any:
    """Recursively serialize common non-JSON-safe types."""
    if isinstance(value, UUID):
        return str(value)
    elif isinstance(value, Decimal):
        return str(value)  # or float(value) if preferred, but str preserves precision
    elif isinstance(value, datetime):
        # Ensure UTC and ISO 8601 format with timezone
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        else:
            value = value.astimezone(timezone.utc)
        return value.isoformat().replace("+00:00", "Z")
    elif isinstance(value, dict):
        return {k: _serialize_value(v) for k, v in value.items()}
    elif isinstance(value, (list, tuple)):
        return [_serialize_value(v) for v in value]
    else:
        return value


def _booking_view_to_dict(booking_view) -> Dict[str, Any]:
    """
    Safely convert BookingView (a dataclass) to a JSON-serializable dictionary.
    Handles UUID, Decimal, and datetime fields explicitly.
    """
    from dataclasses import asdict
    raw_dict = asdict(booking_view)
    return _serialize_value(raw_dict)


# -------------------------
# Booking Lifecycle
# -------------------------


@csrf_exempt
async def create_booking(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    if not hasattr(request, "user_id") or not request.user_id:
        return JsonResponse({"error": "Authentication required"}, status=401)

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON body"}, status=400)

    # guest_id is NOT accepted from the client — it's derived from auth
    required = ["room_id", "check_in_date", "check_out_date"]
    if not all(field in body for field in required):
        return JsonResponse({"error": "Missing required fields"}, status=400)

    try:
        check_in = datetime.fromisoformat(body["check_in_date"].replace("Z", "+00:00"))
        check_out = datetime.fromisoformat(body["check_out_date"].replace("Z", "+00:00"))
        total_price = Decimal(str(body.get("total_price", "0.00")))
    except (ValueError, TypeError) as ve:
        return JsonResponse({"error": f"Invalid date or price format: {str(ve)}"}, status=400)

    try:
        booking_view = await get_booking_command_handler().create_booking(
            room_id=UUID(body["room_id"]),
            guest_id=UUID(request.user_id),  # Enforced from authenticated context
            check_in_date=check_in,
            check_out_date=check_out,
            total_price=total_price,
        )
    except BookingDomainError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except ValueError as ve:
        return JsonResponse({"error": f"Invalid UUID format: {str(ve)}"}, status=400)
    except Exception:
        logger.exception("Create booking failed")
        return JsonResponse({"error": "Internal server error"}, status=500)

    return JsonResponse(_booking_view_to_dict(booking_view), status=201)


@csrf_exempt
async def confirm_booking(request, booking_id: UUID):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    if not hasattr(request, "user_id") or not request.user_id:
        return JsonResponse({"error": "Authentication required"}, status=401)

    try:
        booking_view = await get_booking_command_handler().confirm_booking(booking_id)
    except BookingDomainError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except BookingNotFoundError:
        return JsonResponse({"error": "Booking not found"}, status=404)
    except Exception:
        logger.exception("Confirm booking failed")
        return JsonResponse({"error": "Internal server error"}, status=500)

    return JsonResponse(_booking_view_to_dict(booking_view), status=200)


@csrf_exempt
async def cancel_booking(request, booking_id: UUID):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    if not hasattr(request, "user_id") or not request.user_id:
        return JsonResponse({"error": "Authentication required"}, status=401)

    try:
        booking_view = await get_booking_command_handler().cancel_booking(booking_id)
    except BookingDomainError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except BookingNotFoundError:
        return JsonResponse({"error": "Booking not found"}, status=404)
    except Exception:
        logger.exception("Cancel booking failed")
        return JsonResponse({"error": "Internal server error"}, status=500)

    return JsonResponse(_booking_view_to_dict(booking_view), status=200)


@csrf_exempt
async def expire_booking(request, booking_id: UUID):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    if not hasattr(request, "user_id") or not request.user_id:
        return JsonResponse({"error": "Authentication required"}, status=401)

    try:
        booking_view = await get_booking_command_handler().expire_booking(booking_id)
    except BookingDomainError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except BookingNotFoundError:
        return JsonResponse({"error": "Booking not found"}, status=404)
    except Exception:
        logger.exception("Expire booking failed")
        return JsonResponse({"error": "Internal server error"}, status=500)

    return JsonResponse(_booking_view_to_dict(booking_view), status=200)


@csrf_exempt
async def check_in_booking(request, booking_id: UUID):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    if not hasattr(request, "user_id") or not request.user_id:
        return JsonResponse({"error": "Authentication required"}, status=401)

    try:
        booking_view = await get_booking_command_handler().check_in_booking(booking_id)
    except BookingDomainError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except BookingNotFoundError:
        return JsonResponse({"error": "Booking not found"}, status=404)
    except Exception:
        logger.exception("Check-in booking failed")
        return JsonResponse({"error": "Internal server error"}, status=500)

    return JsonResponse(_booking_view_to_dict(booking_view), status=200)


@csrf_exempt
async def check_out_booking(request, booking_id: UUID):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    if not hasattr(request, "user_id") or not request.user_id:
        return JsonResponse({"error": "Authentication required"}, status=401)

    try:
        booking_view = await get_booking_command_handler().check_out_booking(booking_id)
    except BookingDomainError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except BookingNotFoundError:
        return JsonResponse({"error": "Booking not found"}, status=404)
    except Exception:
        logger.exception("Check-out booking failed")
        return JsonResponse({"error": "Internal server error"}, status=500)

    return JsonResponse(_booking_view_to_dict(booking_view), status=200)


# -------------------------
# Booking Modifications
# -------------------------

@csrf_exempt
async def update_booking_dates(request, booking_id: UUID):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    if not hasattr(request, "user_id") or not request.user_id:
        return JsonResponse({"error": "Authentication required"}, status=401)

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON body"}, status=400)

    required = ["new_check_in", "new_check_out"]
    if not all(field in body for field in required):
        return JsonResponse({"error": "Missing required fields: new_check_in, new_check_out"}, status=400)

    try:
        new_check_in = datetime.fromisoformat(body["new_check_in"].replace("Z", "+00:00"))
        new_check_out = datetime.fromisoformat(body["new_check_out"].replace("Z", "+00:00"))
    except ValueError as ve:
        return JsonResponse({"error": f"Invalid date format: {str(ve)}"}, status=400)

    try:
        booking_view = await get_booking_command_handler().update_booking_dates(
            booking_id=booking_id,
            new_check_in=new_check_in,
            new_check_out=new_check_out,
        )
    except BookingDomainError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except BookingNotFoundError:
        return JsonResponse({"error": "Booking not found"}, status=404)
    except Exception:
        logger.exception("Update booking dates failed")
        return JsonResponse({"error": "Internal server error"}, status=500)

    return JsonResponse(_booking_view_to_dict(booking_view), status=200)


@csrf_exempt
async def change_booking_room(request, booking_id: UUID):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    if not hasattr(request, "user_id") or not request.user_id:
        return JsonResponse({"error": "Authentication required"}, status=401)

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON body"}, status=400)

    new_room_id_str = body.get("new_room_id")
    if not new_room_id_str:
        return JsonResponse({"error": "Missing 'new_room_id'"}, status=400)

    try:
        new_room_id = UUID(new_room_id_str)
    except ValueError as ve:
        return JsonResponse({"error": f"Invalid UUID format: {str(ve)}"}, status=400)

    try:
        booking_view = await get_booking_command_handler().change_booking_room(
            booking_id=booking_id,
            new_room_id=new_room_id,
        )
    except BookingDomainError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except BookingNotFoundError:
        return JsonResponse({"error": "Booking not found"}, status=404)
    except Exception:
        logger.exception("Change booking room failed")
        return JsonResponse({"error": "Internal server error"}, status=500)

    return JsonResponse(_booking_view_to_dict(booking_view), status=200)


@csrf_exempt
async def update_booking_price(request, booking_id: UUID):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    if not hasattr(request, "user_id") or not request.user_id:
        return JsonResponse({"error": "Authentication required"}, status=401)

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON body"}, status=400)

    new_price = body.get("new_total_price")
    if new_price is None:
        return JsonResponse({"error": "Missing 'new_total_price'"}, status=400)

    try:
        price_decimal = Decimal(str(new_price))
    except Exception as ve:
        return JsonResponse({"error": f"Invalid price format: {str(ve)}"}, status=400)

    try:
        booking_view = await get_booking_command_handler().update_booking_price(
            booking_id=booking_id,
            new_total_price=price_decimal,
        )
    except BookingDomainError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except BookingNotFoundError:
        return JsonResponse({"error": "Booking not found"}, status=404)
    except Exception:
        logger.exception("Update booking price failed")
        return JsonResponse({"error": "Internal server error"}, status=500)

    return JsonResponse(_booking_view_to_dict(booking_view), status=200)


@csrf_exempt
async def delete_booking(request, booking_id: UUID):
    if request.method != "DELETE":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    if not hasattr(request, "user_id") or not request.user_id:
        return JsonResponse({"error": "Authentication required"}, status=401)

    try:
        await get_booking_command_handler().delete_booking(booking_id)
    except BookingDomainError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except BookingNotFoundError:
        return JsonResponse({"error": "Booking not found"}, status=404)
    except Exception:
        logger.exception("Delete booking failed")
        return JsonResponse({"error": "Internal server error"}, status=500)

    return JsonResponse({"message": "Booking deleted successfully"}, status=200)