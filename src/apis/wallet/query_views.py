# src/application/wallet/query_views.py
from __future__ import annotations
from src.application.wallet.handlers.dtos import WalletResponseDTO
import json
import logging
from uuid import UUID
from decimal import Decimal
from dataclasses import asdict
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from src.application.wallet.factory import get_wallet_query_handler
from src.domain.apps.wallet.exceptions import WalletNotFoundError


logger = logging.getLogger(__name__)
# Helper to safely convert WalletView to dict
def _wallet_view_to_dict(wallet_view) -> dict:
    data = wallet_view.to_dict() if hasattr(wallet_view, "to_dict") else asdict(wallet_view)

    for k, v in data.items():
        if isinstance(v, Decimal):
            data[k] = format(v, "f")  # ✅ SAFE, NO normalize

    return data


@csrf_exempt
async def get_wallet_with_owner(request, wallet_id: UUID):
    if request.method != "GET":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        dto = await get_wallet_query_handler().get_wallet_with_owner(wallet_id)
    except WalletNotFoundError:
        return JsonResponse({"error": "Wallet not found"}, status=404)
    except Exception:
        logger.exception("Failed to fetch wallet with owner")
        return JsonResponse({"error": "Internal server error"}, status=500)

    return JsonResponse({
        "wallet": _wallet_view_to_dict(dto.wallet),
        "owner": dto.ownr.to_dict() if dto.ownr else None,
    })



@csrf_exempt
async def get_wallet_by_user_with_owner(request, user_id: UUID):
    if request.method != "GET":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    try:
        dto = await get_wallet_query_handler().get_wallet_by_user_with_owner(user_id)
    except WalletNotFoundError:
        return JsonResponse({"error": "Wallet not found for user"}, status=404)
    except Exception:
        logger.exception("Failed to fetch wallet by user")
        return JsonResponse({"error": "Internal server error"}, status=500)

    return JsonResponse({
        "wallet": _wallet_view_to_dict(dto.wallet),
        "owner": dto.ownr.to_dict() if dto.ownr else None,
    })

@csrf_exempt
async def get_wallet_balance(request, wallet_id: UUID):
    if request.method != "GET":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        balance: Decimal = await get_wallet_query_handler().get_wallet_balance(wallet_id)
    except WalletNotFoundError:
        return JsonResponse({"error": "Wallet not found"}, status=404)
    except Exception:
        logger.exception("Failed to fetch wallet balance")
        return JsonResponse({"error": "Internal server error"}, status=500)

    return JsonResponse({"balance": str(balance)})


@csrf_exempt
async def check_wallet_exists(request, wallet_id: UUID):
    if request.method != "GET":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        exists: bool = await get_wallet_query_handler().wallet_exists(wallet_id)
    except Exception:
        logger.exception("Failed to check wallet existence")
        return JsonResponse({"error": "Internal server error"}, status=500)

    return JsonResponse({"exists": exists})