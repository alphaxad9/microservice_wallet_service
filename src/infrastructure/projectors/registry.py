# src/infrastructure/projections/registry.py
from typing import Dict
from src.infrastructure.projectors.wallet.projector import WalletProjectionRunner

PROJECTION_RUNNERS: Dict[str, WalletProjectionRunner] = {}

def register_projection(name: str, runner: WalletProjectionRunner) -> None:
    PROJECTION_RUNNERS[name] = runner
