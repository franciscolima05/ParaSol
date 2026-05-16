"""
Repositorios — capa de acceso a datos.

Cada módulo expone funciones puras que reciben una `Session` y operan
sobre un único modelo. La gestión de transacciones queda en manos del
caller (típicamente con `session_scope()` de `database.py`).
"""
from . import (
    parametricEventRepository as parametricEventRepository,
    userRepository,
    fieldRepository,
    liquidityPoolRepository,
    policyRepository,
    policyPayoutRepository,
)

__all__ = [
    "userRepository",
    "fieldRepository",
    "liquidityPoolRepository",
    "policyRepository",
    "parametricEventRepository",
    "policyPayoutRepository",
]
