from __future__ import annotations

import logging
from typing import Optional
from decimal import Decimal
from uuid import UUID

from src.messaging.rabbitMQ.command_handlers.base_handler import BaseCommandHandler, BaseCommandHandlerContext
from src.application.ant_corruption_layer.booking.commands.room_acl_commands import (
    RequestPaymentACLCommand,
    RequestRefundACLCommand,
)
from src.domain.shared.commands import DomainCommand
from src.domain.apps.wallet.exceptions import WalletNotFoundError, WalletDomainError
from src.application.wallet.factory import get_wallet_command_handler, get_wallet_query_handler

logger = logging.getLogger(__name__)


class RequestPaymentHandler(BaseCommandHandler):
    """
    Handles RequestPaymentACLCommand by:
      1. Fetching the client's wallet using client_id via injected wallet_query_service,
      2. Delegating payment to the injected wallet_command_handler via pay_with_wallet.
    """

    async def handle(self, command: DomainCommand) -> None:
        if not isinstance(command, RequestPaymentACLCommand):
            logger.warning(
                "Handler received unexpected command type: %s",
                type(command).__name__,
            )
            return

        cmd: RequestPaymentACLCommand = command
        booking_id = cmd.booking_id
        amount = cmd.amount
        client_id = cmd.client_id

        logger.info(
            "[📬 Wallet Command Handler 📬] "
            "Received RequestPaymentCommand: booking_id=%s, amount=%s, client_id=%s",
            booking_id,
            amount,
            client_id,
        )

        try:
            # Step 1: Get wallet by user (client_id) using injected query service
            wallet_dto = await self.ctx.wallet_query_service.get_wallet_by_user_with_owner(user_id=client_id)
            wallet_id: UUID = wallet_dto.wallet.wallet_id

            logger.debug(
                "✅[[Wallet Service] Payment Handler]✅ Found wallet for client: client_id=%s, wallet_id=%s",
                client_id,
                wallet_id,
            )

            # Step 2: Process payment using injected command handler
            wallet_view = await self.ctx.wallet_command_handler.pay_with_wallet(
                wallet_id=wallet_id,
                amount=Decimal(str(amount)),
                booking_id=booking_id,
            )

            logger.info(
                "✅[[Wallet Service] Payment Handler]✅ Payment processed successfully: "
                "booking_id=%s, amount=%s, client_id=%s, wallet_id=%s, new_balance=%s",
                booking_id,
                amount,
                client_id,
                wallet_id,
                wallet_view.balance,
            )

        except WalletNotFoundError:
            logger.error(
                "❌[[Wallet Service] Payment Handler]❌ Wallet not found for client during payment request: "
                "booking_id=%s, client_id=%s",
                booking_id,
                client_id,
            )

        except WalletDomainError as e:
            logger.warning(
                "⚠️[[Wallet Service] Payment Handler]⚠️ Payment failed due to domain rule: "
                "booking_id=%s, client_id=%s, amount=%s, reason='%s'",
                booking_id,
                client_id,
                amount,
                str(e),
            )

        except (ValueError, TypeError) as e:
            logger.error(
                "❌[[Wallet Service] Payment Handler]❌ Invalid amount or data format: "
                "booking_id=%s, client_id=%s, amount=%s, error='%s'",
                booking_id,
                client_id,
                amount,
                str(e),
            )

        except Exception:
            logger.exception(
                "💥💥[[Wallet Service] Payment Handler]💥💥 Unexpected error during payment processing: "
                "booking_id=%s, client_id=%s, amount=%s",
                booking_id,
                client_id,
                amount,
            )


class RequestRefundHandler(BaseCommandHandler):
    """
    Handles RequestRefundACLCommand by:
      1. Fetching the client's wallet using client_id via injected wallet_query_service,
      2. Delegating refund to the injected wallet_command_handler via refund().
    """

    async def handle(self, command: DomainCommand) -> None:
        if not isinstance(command, RequestRefundACLCommand):
            logger.warning(
                "Handler received unexpected command type: %s",
                type(command).__name__,
            )
            return

        cmd: RequestRefundACLCommand = command
        booking_id = cmd.booking_id
        amount = cmd.amount
        client_id = cmd.client_id

        logger.info(
            "[📬 Wallet Command Handler 📬] "
            "Received RequestRefundCommand: booking_id=%s, amount=%s, client_id=%s",
            booking_id,
            amount,
            client_id,
        )

        try:
            # Step 1: Get wallet by user (client_id)
            wallet_dto = await self.ctx.wallet_query_service.get_wallet_by_user_with_owner(user_id=client_id)
            wallet_id: UUID = wallet_dto.wallet.wallet_id

            logger.debug(
                "✅[[Wallet Service] Refund Handler]✅ Found wallet for refund: client_id=%s, wallet_id=%s",
                client_id,
                wallet_id,
            )

            # Step 2: Process refund
            wallet_view = await self.ctx.wallet_command_handler.refund(
                wallet_id=wallet_id,
                amount=Decimal(str(amount)),
                booking_id=booking_id,
            )

            logger.info(
                "✅[[Wallet Service] Refund Handler]✅ Refund processed successfully: "
                "booking_id=%s, amount=%s, client_id=%s, wallet_id=%s, new_balance=%s",
                booking_id,
                amount,
                client_id,
                wallet_id,
                wallet_view.balance,
            )

        except WalletNotFoundError:
            logger.error(
                "❌[[Wallet Service] Refund Handler]❌ Wallet not found for client during refund request: "
                "booking_id=%s, client_id=%s",
                booking_id,
                client_id,
            )

        except WalletDomainError as e:
            logger.warning(
                "⚠️[[Wallet Service] Refund Handler]⚠️ Refund failed due to domain rule: "
                "booking_id=%s, client_id=%s, amount=%s, reason='%s'",
                booking_id,
                client_id,
                amount,
                str(e),
            )

        except (ValueError, TypeError) as e:
            logger.error(
                "❌[[Wallet Service] Refund Handler]❌ Invalid amount or data format: "
                "booking_id=%s, client_id=%s, amount=%s, error='%s'",
                booking_id,
                client_id,
                amount,
                str(e),
            )

        except Exception:
            logger.exception(
                "💥💥[[Wallet Service] Refund Handler]💥💥 Unexpected error during refund processing: "
                "booking_id=%s, client_id=%s, amount=%s",
                booking_id,
                client_id,
                amount,
            )


# Context with pre-injected services
_default_ctx = BaseCommandHandlerContext(
    wallet_command_handler=get_wallet_command_handler(),
    wallet_query_service=get_wallet_query_handler(),
)

# Map command types to handler instances
WALLET_COMMAND_HANDLERS: dict[type[DomainCommand], BaseCommandHandler] = {
    RequestPaymentACLCommand: RequestPaymentHandler(_default_ctx),
    RequestRefundACLCommand: RequestRefundHandler(_default_ctx),
}