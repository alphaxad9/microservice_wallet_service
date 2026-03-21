# src/application/booking/views/booking_query_views.py

import json
import logging
from uuid import UUID
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from src.application.booking.factory import get_booking_query_handler
from src.domain.apps.booking.exceptions import BookingNotFoundError
from src.domain.apps.booking.models import BookingStatus

logger = logging.getLogger(__name__)

from decimal import Decimal

def _serialize_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, UUID):
        return str(value)
    elif isinstance(value, datetime):
        dt = value.astimezone(timezone.utc) if value.tzinfo else value.replace(tzinfo=timezone.utc)
        return dt.isoformat().replace("+00:00", "Z")
    elif isinstance(value, Decimal):
        return str(value)  # or float(value) if you prefer, but str preserves precision
    elif hasattr(value, "__dict__"):
        # Recursively serialize object attributes (e.g., BookingView, UserView)
        return _serialize_value(value.__dict__)
    elif isinstance(value, dict):
        return {k: _serialize_value(v) for k, v in value.items()}
    elif isinstance(value, (list, tuple)):
        return [_serialize_value(v) for v in value]
    else:
        return value
    
    
def _dto_to_dict(dto) -> Dict[str, Any]:
    """
    Convert BookingResponseDTO or similar dataclass-like object to dict.
    Assumes it has __dict__ or can be handled generically.
    """
    if hasattr(dto, "__dict__"):
        raw = dto.__dict__
    else:
        from dataclasses import asdict
        raw = asdict(dto)
    return _serialize_value(raw)


def _parse_uuid_from_str(param: str) -> UUID:
    """Parse UUID only when input is a string (e.g., from query params)."""
    try:
        return UUID(param)
    except ValueError as e:
        raise ValueError(f"Invalid UUID format: {param}") from e


def _parse_datetime_param(dt_str: Optional[str]) -> Optional[datetime]:
    if not dt_str:
        return None
    try:
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except ValueError as e:
        raise ValueError(f"Invalid datetime format: {dt_str}") from e


def _parse_status_list(statuses_str: Optional[str]) -> Optional[List[BookingStatus]]:
    if not statuses_str:
        return None
    try:
        status_names = statuses_str.split(",")
        return [BookingStatus[name.strip()] for name in status_names]
    except KeyError as e:
        raise ValueError(f"Invalid booking status: {e}") from e


# -------------------------
# Query Endpoints
# -------------------------

@csrf_exempt
@require_http_methods(["GET"])
async def get_booking(request, booking_id: UUID):
    """booking_id is already a UUID thanks to <uuid:booking_id> in URL."""
    try:
        booking_view = await get_booking_query_handler().get_booking(booking_id)
    except BookingNotFoundError:
        return JsonResponse({"error": "Booking not found"}, status=404)
    except Exception:
        logger.exception("Failed to fetch booking")
        return JsonResponse({"error": "Internal server error"}, status=500)

    return JsonResponse(_serialize_value(booking_view.__dict__), status=200)


@csrf_exempt
@require_http_methods(["GET"])
async def get_booking_with_guest(request, booking_id: UUID):
    try:
        dto = await get_booking_query_handler().get_booking_with_guest(booking_id)
    except BookingNotFoundError:
        return JsonResponse({"error": "Booking not found"}, status=404)
    except Exception:
        logger.exception("Failed to fetch booking with guest")
        return JsonResponse({"error": "Internal server error"}, status=500)

    return JsonResponse(_serialize_value(dto), status=200)  # ✅ Works!

@csrf_exempt
@require_http_methods(["GET"])
async def get_bookings_by_guest(request, guest_id: UUID):
    statuses = _parse_status_list(request.GET.get("statuses"))
    limit = int(request.GET.get("limit", 100))
    offset = int(request.GET.get("offset", 0))

    try:
        bookings = await get_booking_query_handler().get_bookings_by_guest(
            guest_id=guest_id,
            statuses=statuses,
            limit=limit,
            offset=offset,
        )
    except BookingNotFoundError:
        return JsonResponse({"error": "No bookings found for guest"}, status=404)
    except Exception:
        logger.exception("Failed to fetch bookings by guest")
        return JsonResponse({"error": "Internal server error"}, status=500)

    serialized = [_serialize_value(b.__dict__) for b in bookings]
    return JsonResponse(serialized, safe=False, status=200)


@csrf_exempt
@require_http_methods(["GET"])
async def get_bookings_by_guest_with_guest(request, guest_id: UUID):
    statuses = _parse_status_list(request.GET.get("statuses"))
    limit = int(request.GET.get("limit", 100))
    offset = int(request.GET.get("offset", 0))

    try:
        dtos = await get_booking_query_handler().get_bookings_by_guest_with_guest(
            guest_id=guest_id,
            statuses=statuses,
            limit=limit,
            offset=offset,
        )
    except BookingNotFoundError:
        return JsonResponse({"error": "No bookings found for guest"}, status=404)
    except Exception:
        logger.exception("Failed to fetch enriched bookings by guest")
        return JsonResponse({"error": "Internal server error"}, status=500)

    serialized = [_dto_to_dict(dto) for dto in dtos]
    return JsonResponse(serialized, safe=False, status=200)


@csrf_exempt
@require_http_methods(["GET"])
async def get_bookings_by_room(request, room_id: UUID):
    statuses = _parse_status_list(request.GET.get("statuses"))
    limit = int(request.GET.get("limit", 100))
    offset = int(request.GET.get("offset", 0))

    try:
        bookings = await get_booking_query_handler().get_bookings_by_room(
            room_id=room_id,
            statuses=statuses,
            limit=limit,
            offset=offset,
        )
    except BookingNotFoundError as e:
        return JsonResponse({"error": str(e)}, status=404)
    except Exception:
        logger.exception("Failed to fetch bookings by room")
        return JsonResponse({"error": "Internal server error"}, status=500)

    serialized = [_serialize_value(b.__dict__) for b in bookings]
    return JsonResponse(serialized, safe=False, status=200)


@csrf_exempt
@require_http_methods(["GET"])
async def get_active_bookings(request):
    check_in_after = _parse_datetime_param(request.GET.get("check_in_after"))
    check_out_before = _parse_datetime_param(request.GET.get("check_out_before"))
    limit = int(request.GET.get("limit", 100))
    offset = int(request.GET.get("offset", 0))

    try:
        bookings = await get_booking_query_handler().get_active_bookings(
            check_in_after=check_in_after,
            check_out_before=check_out_before,
            limit=limit,
            offset=offset,
        )
    except BookingNotFoundError as e:
        return JsonResponse({"error": str(e)}, status=404)
    except Exception:
        logger.exception("Failed to fetch active bookings")
        return JsonResponse({"error": "Internal server error"}, status=500)

    serialized = [_serialize_value(b.__dict__) for b in bookings]
    return JsonResponse(serialized, safe=False, status=200)


@csrf_exempt
@require_http_methods(["GET"])
async def get_bookings_by_status(request, status_name: str):
    try:
        status = BookingStatus[status_name]
    except KeyError:
        return JsonResponse({"error": f"Invalid status: {status_name}"}, status=400)

    limit = int(request.GET.get("limit", 100))
    offset = int(request.GET.get("offset", 0))

    try:
        bookings = await get_booking_query_handler().get_bookings_by_status(
            status=status,
            limit=limit,
            offset=offset,
        )
    except BookingNotFoundError as e:
        return JsonResponse({"error": str(e)}, status=404)
    except Exception:
        logger.exception("Failed to fetch bookings by status")
        return JsonResponse({"error": "Internal server error"}, status=500)

    serialized = [_serialize_value(b.__dict__) for b in bookings]
    return JsonResponse(serialized, safe=False, status=200)


@csrf_exempt
@require_http_methods(["GET"])
async def count_bookings_by_status_view(request, status_name: str):
    try:
        status = BookingStatus[status_name]
    except KeyError:
        return JsonResponse({"error": f"Invalid status: {status_name}"}, status=400)

    try:
        count = await get_booking_query_handler().count_bookings_by_status(status)
    except Exception:
        logger.exception("Failed to count bookings by status")
        return JsonResponse({"error": "Internal server error"}, status=500)

    return JsonResponse({"count": count}, status=200)


@csrf_exempt
@require_http_methods(["GET"])
async def booking_exists_view(request, booking_id: UUID):
    try:
        exists = await get_booking_query_handler().booking_exists(booking_id)
    except Exception:
        logger.exception("Failed to check booking existence")
        return JsonResponse({"error": "Internal server error"}, status=500)

    return JsonResponse({"exists": exists}, status=200)


@csrf_exempt
@require_http_methods(["GET"])
async def is_room_available_view(request):
    room_id_str = request.GET.get("room_id")
    check_in_str = request.GET.get("check_in")
    check_out_str = request.GET.get("check_out")

    if not all([room_id_str, check_in_str, check_out_str]):
        return JsonResponse(
            {"error": "Missing query parameters: room_id, check_in, check_out"},
            status=400
        )

    try:
        room_id = _parse_uuid_from_str(room_id_str)  # From query param → must parse string
        check_in = _parse_datetime_param(check_in_str)
        check_out = _parse_datetime_param(check_out_str)
        if not check_in or not check_out:
            raise ValueError("Invalid datetime")
    except ValueError as e:
        return JsonResponse({"error": f"Invalid input: {str(e)}"}, status=400)

    try:
        available = await get_booking_query_handler().is_room_available_for_dates(
            room_id=room_id,
            check_in=check_in,
            check_out=check_out,
        )
    except Exception:
        logger.exception("Failed to check room availability")
        return JsonResponse({"error": "Internal server error"}, status=500)

    return JsonResponse({"available": available}, status=200)