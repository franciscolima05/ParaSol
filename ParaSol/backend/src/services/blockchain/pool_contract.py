"""
Wrapper de ParaSolPool.sol.

Única responsabilidad: hablar con el contrato on-chain.
No sabe nada de SQLAlchemy ni de modelos de dominio.

ABI inline con solo las funciones que el backend llama.
Cuando corras `forge build`, podés reemplazarlo así:
    import json, pathlib
    _ABI = json.loads(
        (pathlib.Path("contracts/out/ParaSolPool.sol/ParaSolPool.json")).read_text()
    )["abi"]
"""
import os
from decimal import Decimal

from .client import account, send_transaction, w3, wait_for_receipt

_USDC_DECIMALS = 10 ** 6

_ADDRESS = os.getenv("POOL_CONTRACT_ADDRESS", "")

_ABI = [
    {
        "name": "createPool",
        "type": "function",
        "inputs": [{"name": "_name", "type": "string"}],
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "nonpayable",
    },
    {
        "name": "fundPool",
        "type": "function",
        "inputs": [
            {"name": "poolId", "type": "uint256"},
            {"name": "amount", "type": "uint256"},
        ],
        "outputs": [],
        "stateMutability": "nonpayable",
    },
    {
        "name": "lockCapital",
        "type": "function",
        "inputs": [
            {"name": "poolId", "type": "uint256"},
            {"name": "amount", "type": "uint256"},
        ],
        "outputs": [],
        "stateMutability": "nonpayable",
    },
    {
        "name": "getAvailableCapital",
        "type": "function",
        "inputs": [{"name": "poolId", "type": "uint256"}],
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
    },
    {
        "name": "PoolCreated",
        "type": "event",
        "inputs": [
            {"name": "poolId", "indexed": True, "type": "uint256"},
            {"name": "name", "indexed": False, "type": "string"},
        ],
        "anonymous": False,
    },
    {
        "name": "CapitalLocked",
        "type": "event",
        "inputs": [
            {"name": "poolId", "indexed": True, "type": "uint256"},
            {"name": "amount", "indexed": False, "type": "uint256"},
        ],
        "anonymous": False,
    },
]

_contract = w3.eth.contract(address=_ADDRESS, abi=_ABI)


# ── Conversión USDC ────────────────────────────────────────────────────────────

def _to_units(usdc: Decimal) -> int:
    return int(usdc * _USDC_DECIMALS)


def _to_usdc(units: int) -> Decimal:
    return Decimal(units) / Decimal(_USDC_DECIMALS)


# ── Funciones públicas ─────────────────────────────────────────────────────────

def create_pool(name: str) -> tuple[str, int]:
    """
    Llama a createPool on-chain. Devuelve (tx_hash, pool_id).
    El pool_id sale del evento PoolCreated del receipt.
    """
    tx = _contract.functions.createPool(name).build_transaction(
        {"from": account.address}
    )
    tx_hash = send_transaction(tx)
    receipt = wait_for_receipt(tx_hash)

    logs = _contract.events.PoolCreated().process_receipt(receipt)
    pool_id = int(logs[0]["args"]["poolId"])
    return tx_hash, pool_id


def lock_capital(pool_id: int, amount_usdc: Decimal) -> str:
    """
    Bloquea capital en el pool para respaldar una póliza activa.
    Devuelve tx_hash. Falla si no hay capital disponible (revert del contrato).
    """
    tx = _contract.functions.lockCapital(
        pool_id, _to_units(amount_usdc)
    ).build_transaction({"from": account.address})
    tx_hash = send_transaction(tx)
    wait_for_receipt(tx_hash)
    return tx_hash


def get_available_capital(pool_id: int) -> Decimal:
    """View call sin tx. Consulta el capital disponible en USDC."""
    raw = _contract.functions.getAvailableCapital(pool_id).call()
    return _to_usdc(raw)
