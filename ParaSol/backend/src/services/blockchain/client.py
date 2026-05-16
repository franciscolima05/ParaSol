import os
from web3 import Web3

# ── Configuración desde entorno ────────────────────────────────────────────────
_RPC_URL = os.getenv(
    "AVALANCHE_FUJI_RPC",
    "https://api.avax-test.network/ext/bc/C/rpc",
)
_PRIVATE_KEY: str = os.getenv("PRIVATE_KEY", "")

chain_id: int = int(os.getenv("CHAIN_ID", "43113"))

if not _PRIVATE_KEY:
    raise EnvironmentError("PRIVATE_KEY env var is not set")

# ── Singleton Web3 ─────────────────────────────────────────────────────────────
w3 = Web3(Web3.HTTPProvider(_RPC_URL, request_kwargs={"timeout": 30}))
account = w3.eth.account.from_key(_PRIVATE_KEY)


# ── Helpers que usan los contract-wrappers ────────────────────────────────────

def send_transaction(tx_params: dict) -> str:
    """
    Firma y difunde una transacción. Devuelve el tx_hash como string hex.

    El caller solo tiene que pasar los parámetros propios del contrato
    (to, data, value). El nonce, gas y gasPrice se completan acá si faltan.
    """
    tx_params.setdefault("chainId", chain_id)
    tx_params.setdefault("from", account.address)

    if "nonce" not in tx_params:
        tx_params["nonce"] = w3.eth.get_transaction_count(account.address, "pending")

    if "gas" not in tx_params:
        tx_params["gas"] = w3.eth.estimate_gas(tx_params)

    if "gasPrice" not in tx_params:
        tx_params["gasPrice"] = w3.eth.gas_price

    signed = w3.eth.account.sign_transaction(tx_params, private_key=_PRIVATE_KEY)
    raw_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    return raw_hash.hex()


def wait_for_receipt(tx_hash: str, timeout: int = 30):
    """
    Bloquea hasta que la tx se confirma on-chain. Levanta TimeExhausted si
    supera el timeout. En Fuji la confirmación tarda ~2-3 s; 30 s es holgado.
    """
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=timeout)
    if receipt.status == 0:
        raise RuntimeError(f"Transaction reverted: {tx_hash}")
    return receipt
