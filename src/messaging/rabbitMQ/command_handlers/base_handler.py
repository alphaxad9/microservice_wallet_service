
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass

# Generic domain command base
from src.domain.shared.commands import DomainCommand
from src.application.wallet.handlers.wallet_command_handler import WalletCommandHandler
from src.application.wallet.handlers.wallet_query_handler import WalletQueryHandler
logger = logging.getLogger(__name__)


@dataclass
class BaseCommandHandlerContext:
    wallet_command_handler: WalletCommandHandler
    wallet_query_service: WalletQueryHandler


class BaseCommandHandler(ABC):
    """
    Abstract base for all booking command handlers.
    Accepts DomainCommand to comply with global command bus contract.
    Concrete handlers filter by type using isinstance().
    """
    def __init__(self, ctx: BaseCommandHandlerContext) -> None:
        self.ctx = ctx

    @abstractmethod
    async def handle(self, command: DomainCommand) -> None:
        """
        Handle a domain command.
        Implementations must first check if the command is of the expected type.
        """
        raise NotImplementedError()





