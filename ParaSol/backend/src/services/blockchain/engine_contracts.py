"""
Wrappers de ParaSolPolicy.sol y ParaSolEngine.sol.

Los dos contratos viven acá porque forman una unidad funcional:
    - ParaSolPolicy  → mintPolicy()       (el NFT que representa la póliza)
    - ParaSolEngine  → processParametricEvent()  (el pago paramétrico)

No sabe nada de SQLAlchemy ni de modelos de dominio.

Para reemplazar los ABI inline con los artifacts de Foundry:
    import json, pathlib
    _POLICY_ABI = json.loads(
        pathlib.Path("contracts/out/ParaSolPolicy.sol/ParaSolPolicy.json").read_text()
    )["abi"]
    _ENGINE_ABI = json.loads(
        pathlib.Path("contracts/out/ParaSolEngine.sol/ParaSolEngine.json").read_text()
    )["abi"]
"""
import os
from decimal import Decimal

from .client import account, send_transaction, w3, wait_for_receipt

_USDC_DECIMALS = 10 ** 6

_POLICY_ADDRESS = os.getenv("POLICY_CONTRACT_ADDRESS", "")
_ENGINE_ADDRESS = os.getenv("ENGINE_CONTRACT_ADDRESS", "")

# ── ABIs ───────────────────────────────────────────────────────────────────────

_POLICY_ABI = [
    {
        "name": "mintPolicy",
        "type": "function",
        "inputs": [
            {"name": "to", "type": "address"},
            {"name": "_fieldHash", "type": "string"},
            {"name": "_poolId", "type": "uint256"},
            {"name": "_coverageUSDC", "type": "uint256"},
            {"name": "_premiumUSDC", "type": "uint256"},
            {"name": "_startDate", "type": "uint256"},
            {"name": "_endDate", "type": "uint256"},
            {"name": "_triggerSnapshotHash", "type": "string"},
        ],
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "nonpayable",
    },
    # Transfer es el evento ERC-721 estándar; _safeMint lo emite con from=0x0
    {
        "name": "Transfer",
        "type": "event",
        "inputs": [
            {"name": "from", "indexed": True, "type": "address"},
            {"name": "to", "indexed": True, "type": "address"},
            {"name": "tokenId", "indexed": True, "type": "uint256"},
        ],
        "anonymous": False,
    },
]

_ENGINE_ABI = [
    {
        "name": "processParametricEvent",
        "type": "function",
        "inputs": [
            {"name": "policyId", "type": "uint256"},
            {"name": "ndviDrop", "type": "uint256"},
        ],
        "outputs": [],
        "stateMutability": "nonpayable",
    },
    {
        "name": "PayoutTriggered",
        "type": "event",
        "inputs": [
            {"name": "policyId", "indexed": True, "type": "uint256"},
            {"name": "ndviDrop", "indexed": False, "type": "uint256"},
            {"name": "payoutPercent", "indexed": False, "type": "uint256"},
            {"name": "amountUSDC", "indexed": False, "type": "uint256"},
        ],
        "anonymous": False,
    },
]

_policy_contract = w3.eth.contract(address=_POLICY_ADDRESS, abi=_POLICY_ABI)
_engine_contract = w3.eth.contract(address=_ENGINE_ADDRESS, abi=_ENGINE_ABI)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _to_units(usdc: Decimal) -> int:
    return int(usdc * _USDC_DECIMALS)


def _to_usdc(units: int) -> Decimal:
    return Decimal(units) / Decimal(_USDC_DECIMALS)


# ── Funciones públicas ─────────────────────────────────────────────────────────

def mint_policy(
    holder_address: str,
    field_hash: str,
    pool_id: int,
    coverage_usdc: Decimal,
    premium_usdc: Decimal,
    start_timestamp: int,
    end_timestamp: int,
    trigger_snapshot_hash: str,
) -> tuple[str, int]:
    """
    Mintea el NFT ERC-721 que representa la póliza.
    Devuelve (tx_hash, token_id).

    El token_id sale del evento Transfer(from=0x0) que emite _safeMint.
    mintPolicy emite exactamente un Transfer, así que logs[0] es seguro.
    """
    tx = _policy_contract.functions.mintPolicy(
        holder_address,
        field_hash,
        pool_id,
        _to_units(coverage_usdc),
        _to_units(premium_usdc),
        start_timestamp,
        end_timestamp,
        trigger_snapshot_hash,
    ).build_transaction({"from": account.address})

    tx_hash = send_transaction(tx)
    receipt = wait_for_receipt(tx_hash)

    logs = _policy_contract.events.Transfer().process_receipt(receipt)
    token_id = int(logs[0]["args"]["tokenId"])
    return tx_hash, token_id


def process_event(policy_token_id: int, ndvi_drop_pct: int) -> tuple[str, Decimal]:
    """
    Reporta un evento paramétrico al Engine para gatillar el payout.
    Devuelve (tx_hash, amount_paid_usdc).

    ndvi_drop_pct: caída de NDVI como entero 0-100.
        Si tenés severity=0.35 (Decimal) del ParametricEvent, pasás int(0.35 * 100) = 35.

    El contrato aplica franquicia mínima de 20% y redondea a múltiplos de 5.
    Si el pago acumulado ya cubre ese tramo, el contrato revierte — verificar
    percentagePaidOut antes de llamar si querés evitar el revert.
    """
    tx = _engine_contract.functions.processParametricEvent(
        policy_token_id, ndvi_drop_pct
    ).build_transaction({"from": account.address})

    tx_hash = send_transaction(tx)
    receipt = wait_for_receipt(tx_hash)

    logs = _engine_contract.events.PayoutTriggered().process_receipt(receipt)
    amount_units = int(logs[0]["args"]["amountUSDC"])
    return tx_hash, _to_usdc(amount_units)
