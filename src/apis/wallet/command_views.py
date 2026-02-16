import json
import logging
from uuid import UUID
from decimal import Decimal
from typing import Optional

from dataclasses import asdict  # <-- Key import for serialization

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from src.application.wallet.factory import get_wallet_command_handler
from src.domain.apps.wallet.exceptions import (
    WalletDomainError,
    WalletNotFoundError,
)

logger = logging.getLogger(__name__)


# Helper to safely convert WalletView to dict
def _wallet_view_to_dict(wallet_view) -> dict:
    data = wallet_view.to_dict() if hasattr(wallet_view, "to_dict") else asdict(wallet_view)

    for k, v in data.items():
        if isinstance(v, Decimal):
            data[k] = format(v, "f")  # ✅ SAFE, NO normalize

    return data

# -------------------------
# Wallet Lifecycle
# -------------------------

@csrf_exempt
async def create_wallet(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    if not hasattr(request, "user_id") or not request.user_id:
        return JsonResponse({"error": "Authentication required"}, status=401)

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON body"}, status=400)

    currency = body.get("currency", "USD")
    wallet_id_str: Optional[str] = body.get("wallet_id")
    wallet_id: Optional[UUID] = UUID(wallet_id_str) if wallet_id_str else None

    try:
        wallet_view = await get_wallet_command_handler().create_wallet(
            user_id=UUID(request.user_id),
            currency=currency,
            wallet_id=wallet_id,
        )
    except WalletDomainError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except ValueError as ve:
        return JsonResponse({"error": f"Invalid UUID format: {str(ve)}"}, status=400)
    except Exception:
        logger.exception("Create wallet failed")
        return JsonResponse({"error": "Internal server error"}, status=500)

    return JsonResponse(_wallet_view_to_dict(wallet_view), status=201)


# -------------------------
# Balance Operations
# -------------------------

@csrf_exempt
async def deposit(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    if not hasattr(request, "user_id") or not request.user_id:
        return JsonResponse({"error": "Authentication required"}, status=401)

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON body"}, status=400)

    required = ["wallet_id", "amount"]
    if not all(field in body for field in required):
        return JsonResponse({"error": "Missing required fields"}, status=400)

    reference_id_str: Optional[str] = body.get("reference_id")
    reference_id: Optional[UUID] = UUID(reference_id_str) if reference_id_str else None

    try:
        wallet_view = await get_wallet_command_handler().deposit(
            wallet_id=UUID(body["wallet_id"]),
            amount=Decimal(str(body["amount"])),
            reference_id=reference_id,
        )
    except WalletDomainError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except WalletNotFoundError:
        return JsonResponse({"error": "Wallet not found"}, status=404)
    except ValueError as ve:
        return JsonResponse({"error": f"Invalid format: {str(ve)}"}, status=400)
    except Exception:
        logger.exception("Deposit failed")
        return JsonResponse({"error": "Internal server error"}, status=500)

    return JsonResponse(_wallet_view_to_dict(wallet_view), status=200)


@csrf_exempt
async def withdraw(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    if not hasattr(request, "user_id") or not request.user_id:
        return JsonResponse({"error": "Authentication required"}, status=401)

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON body"}, status=400)

    required = ["wallet_id", "amount"]
    if not all(field in body for field in required):
        return JsonResponse({"error": "Missing required fields"}, status=400)

    reference_id_str: Optional[str] = body.get("reference_id")
    reference_id: Optional[UUID] = UUID(reference_id_str) if reference_id_str else None

    try:
        wallet_view = await get_wallet_command_handler().withdraw(
            wallet_id=UUID(body["wallet_id"]),
            amount=Decimal(str(body["amount"])),
            reference_id=reference_id,
        )
    except WalletDomainError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except WalletNotFoundError:
        return JsonResponse({"error": "Wallet not found"}, status=404)
    except ValueError as ve:
        return JsonResponse({"error": f"Invalid format: {str(ve)}"}, status=400)
    except Exception:
        logger.exception("Withdraw failed")
        return JsonResponse({"error": "Internal server error"}, status=500)

    return JsonResponse(_wallet_view_to_dict(wallet_view), status=200)


@csrf_exempt
async def pay_with_wallet(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    if not hasattr(request, "user_id") or not request.user_id:
        return JsonResponse({"error": "Authentication required"}, status=401)

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON body"}, status=400)

    required = ["wallet_id", "amount", "booking_id"]
    if not all(field in body for field in required):
        return JsonResponse({"error": "Missing required fields"}, status=400)

    try:
        wallet_view = await get_wallet_command_handler().pay_with_wallet(
            wallet_id=UUID(body["wallet_id"]),
            amount=Decimal(str(body["amount"])),
            booking_id=UUID(body["booking_id"]),
        )
    except WalletDomainError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except WalletNotFoundError:
        return JsonResponse({"error": "Wallet not found"}, status=404)
    except ValueError as ve:
        return JsonResponse({"error": f"Invalid format: {str(ve)}"}, status=400)
    except Exception:
        logger.exception("Pay with wallet failed")
        return JsonResponse({"error": "Internal server error"}, status=500)

    return JsonResponse(_wallet_view_to_dict(wallet_view), status=200)


@csrf_exempt
async def refund(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    if not hasattr(request, "user_id") or not request.user_id:
        return JsonResponse({"error": "Authentication required"}, status=401)

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON body"}, status=400)

    required = ["wallet_id", "amount"]
    if not all(field in body for field in required):
        return JsonResponse({"error": "Missing required fields"}, status=400)

    booking_id_str: Optional[str] = body.get("booking_id")
    booking_id: Optional[UUID] = UUID(booking_id_str) if booking_id_str else None

    try:
        wallet_view = await get_wallet_command_handler().refund(
            wallet_id=UUID(body["wallet_id"]),
            amount=Decimal(str(body["amount"])),
            booking_id=booking_id,
        )
    except WalletDomainError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except WalletNotFoundError:
        return JsonResponse({"error": "Wallet not found"}, status=404)
    except ValueError as ve:
        return JsonResponse({"error": f"Invalid format: {str(ve)}"}, status=400)
    except Exception:
        logger.exception("Refund failed")
        return JsonResponse({"error": "Internal server error"}, status=500)

    return JsonResponse(_wallet_view_to_dict(wallet_view), status=200)


@csrf_exempt
async def adjustment(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    if not hasattr(request, "user_id") or not request.user_id:
        return JsonResponse({"error": "Authentication required"}, status=401)

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON body"}, status=400)

    required = ["wallet_id", "amount", "reason"]
    if not all(field in body for field in required):
        return JsonResponse({"error": "Missing required fields"}, status=400)

    admin_id_str: Optional[str] = body.get("admin_id")
    admin_id: Optional[UUID] = UUID(admin_id_str) if admin_id_str else None

    try:
        wallet_view = await get_wallet_command_handler().adjustment(
            wallet_id=UUID(body["wallet_id"]),
            amount=Decimal(str(body["amount"])),
            reason=body["reason"],
            admin_id=admin_id,
        )
    except WalletDomainError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except WalletNotFoundError:
        return JsonResponse({"error": "Wallet not found"}, status=404)
    except ValueError as ve:
        return JsonResponse({"error": f"Invalid format: {str(ve)}"}, status=400)
    except Exception:
        logger.exception("Adjustment failed")
        return JsonResponse({"error": "Internal server error"}, status=500)

    return JsonResponse(_wallet_view_to_dict(wallet_view), status=200)

# -------------------------
# Wallet State Management
# -------------------------

@csrf_exempt
async def suspend_wallet(request, wallet_id: UUID):  # ← Changed from wallet_id_str: str
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    if not hasattr(request, "user_id") or not request.user_id:
        return JsonResponse({"error": "Authentication required"}, status=401)

    try:
        wallet_view = await get_wallet_command_handler().suspend_wallet(wallet_id)
    except WalletDomainError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except WalletNotFoundError:
        return JsonResponse({"error": "Wallet not found"}, status=404)
    except Exception:
        logger.exception("Suspend wallet failed")
        return JsonResponse({"error": "Internal server error"}, status=500)

    return JsonResponse(_wallet_view_to_dict(wallet_view), status=200)


@csrf_exempt
async def activate_wallet(request, wallet_id: UUID):  # ← Changed
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    if not hasattr(request, "user_id") or not request.user_id:
        return JsonResponse({"error": "Authentication required"}, status=401)

    try:
        wallet_view = await get_wallet_command_handler().activate_wallet(wallet_id)
    except WalletDomainError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except WalletNotFoundError:
        return JsonResponse({"error": "Wallet not found"}, status=404)
    except Exception:
        logger.exception("Activate wallet failed")
        return JsonResponse({"error": "Internal server error"}, status=500)

    return JsonResponse(_wallet_view_to_dict(wallet_view), status=200)


@csrf_exempt
async def close_wallet(request, wallet_id: UUID):  # ← Changed
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    if not hasattr(request, "user_id") or not request.user_id:
        return JsonResponse({"error": "Authentication required"}, status=401)

    try:
        wallet_view = await get_wallet_command_handler().close_wallet(wallet_id)
    except WalletDomainError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except WalletNotFoundError:
        return JsonResponse({"error": "Wallet not found"}, status=404)
    except Exception:
        logger.exception("Close wallet failed")
        return JsonResponse({"error": "Internal server error"}, status=500)

    return JsonResponse(_wallet_view_to_dict(wallet_view), status=200)