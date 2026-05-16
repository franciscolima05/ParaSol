"""
Repositorio de LiquidityPool.

Identidad contable:
    available = total_capital - locked_capital - paid_out_capital

La verdad última del capital vive on-chain. Estas columnas son un snapshot
sincronizado para queries rápidas. Las funciones `lock_capital`,
`unlock_capital` y `register_payout` mueven los snapshots respetando esa
identidad.
"""
from __future__ import annotations

from decimal import Decimal
from typing import List, Optional, Union

from sqlalchemy.orm import Session

from ParaSol.ParaSol.backend.src.models import (
    LiquidityPool,
    Peril,
    PoolStatus,
)

Amount = Union[Decimal, int, float, str]


def _to_decimal(x: Amount) -> Decimal:
    return x if isinstance(x, Decimal) else Decimal(str(x))


# === Create ===

def create_pool(
    session: Session,
    *,
    name: str,
    chain_id: int = 43113,
    escrow_contract_address: Optional[str] = None,
    total_capital_usdc: Amount = 0,
    peril_focus: Optional[Peril] = None,
    region_focus: Optional[str] = None,
    funded_by_user_id: Optional[int] = None,
) -> LiquidityPool:
    pool = LiquidityPool(
        name=name,
        chain_id=chain_id,
        escrow_contract_address=escrow_contract_address,
        total_capital_usdc=_to_decimal(total_capital_usdc),
        locked_capital_usdc=Decimal(0),
        paid_out_usdc=Decimal(0),
        peril_focus=peril_focus.value if isinstance(peril_focus, Peril) else peril_focus,
        region_focus=region_focus,
        funded_by_user_id=funded_by_user_id,
        status=PoolStatus.ACTIVE.value,
    )
    session.add(pool)
    session.flush()
    return pool


# === Read ===

def get_pool_by_id(session: Session, pool_id: int) -> Optional[LiquidityPool]:
    return session.get(LiquidityPool, pool_id)


def list_pools(
    session: Session,
    *,
    peril: Optional[Peril] = None,
    region: Optional[str] = None,
    only_active: bool = True,
) -> List[LiquidityPool]:
    q = session.query(LiquidityPool)
    if peril is not None:
        peril_val = peril.value if isinstance(peril, Peril) else peril
        # Acepta pools generales (peril_focus IS NULL) o específicos
        q = q.filter(
            (LiquidityPool.peril_focus == peril_val)
            | (LiquidityPool.peril_focus.is_(None))
        )
    if region is not None:
        q = q.filter(
            (LiquidityPool.region_focus == region)
            | (LiquidityPool.region_focus.is_(None))
        )
    if only_active:
        q = q.filter(LiquidityPool.status == PoolStatus.ACTIVE.value)
    return q.order_by(LiquidityPool.id).all()


def available_capital(pool: LiquidityPool) -> Decimal:
    """Capital realmente disponible para respaldar nuevas pólizas."""
    total = _to_decimal(pool.total_capital_usdc or 0)
    locked = _to_decimal(pool.locked_capital_usdc or 0)
    paid = _to_decimal(pool.paid_out_usdc or 0)
    return total - locked - paid


def find_pool_for_coverage(
    session: Session,
    *,
    peril: Peril,
    region: Optional[str],
    coverage_amount_usdc: Amount,
) -> Optional[LiquidityPool]:
    """
    Encuentra el pool más específico con capital suficiente para una nueva
    póliza. Prioriza pool específico por (peril, region), luego peril, luego
    general.
    """
    needed = _to_decimal(coverage_amount_usdc)
    candidates = list_pools(session, peril=peril, region=region, only_active=True)
    # Prioridad: más específico primero
    def specificity(p: LiquidityPool) -> int:
        score = 0
        if p.peril_focus is not None:
            score += 2
        if p.region_focus is not None:
            score += 1
        return -score  # invertido para sort ascendente
    candidates.sort(key=specificity)
    for p in candidates:
        if available_capital(p) >= needed:
            return p
    return None


# === Capital — movimientos de snapshot ===

def add_capital(
    session: Session, pool: LiquidityPool, amount: Amount
) -> LiquidityPool:
    """Aseguradora/backer aporta capital al pool (o se suma una prima)."""
    pool.total_capital_usdc = _to_decimal(pool.total_capital_usdc or 0) + _to_decimal(amount)
    if pool.status == PoolStatus.DEPLETED.value and available_capital(pool) > 0:
        pool.status = PoolStatus.ACTIVE.value
    session.flush()
    return pool


def lock_capital(
    session: Session, pool: LiquidityPool, amount: Amount
) -> LiquidityPool:
    """
    Reserva capital para respaldar una póliza recién emitida.
    Lanza ValueError si no hay suficiente disponible.
    """
    amt = _to_decimal(amount)
    if available_capital(pool) < amt:
        raise ValueError(
            f"Capital insuficiente en pool {pool.id}: "
            f"disponible={available_capital(pool)}, requerido={amt}"
        )
    pool.locked_capital_usdc = _to_decimal(pool.locked_capital_usdc or 0) + amt
    session.flush()
    return pool


def unlock_capital(
    session: Session, pool: LiquidityPool, amount: Amount
) -> LiquidityPool:
    """Libera capital reservado (póliza expirada sin payout, cancelada, etc.)."""
    amt = _to_decimal(amount)
    pool.locked_capital_usdc = max(
        Decimal(0), _to_decimal(pool.locked_capital_usdc or 0) - amt
    )
    session.flush()
    return pool


def register_payout(
    session: Session, pool: LiquidityPool, amount: Amount
) -> LiquidityPool:
    """
    Registra que se pagó `amount` desde este pool. Mueve del bucket
    `locked` al bucket `paid_out`.
    """
    amt = _to_decimal(amount)
    pool.locked_capital_usdc = max(
        Decimal(0), _to_decimal(pool.locked_capital_usdc or 0) - amt
    )
    pool.paid_out_usdc = _to_decimal(pool.paid_out_usdc or 0) + amt
    if available_capital(pool) <= 0:
        pool.status = PoolStatus.DEPLETED.value
    session.flush()
    return pool


# === Update ===

def set_status(
    session: Session, pool: LiquidityPool, status: PoolStatus
) -> LiquidityPool:
    pool.status = status.value if isinstance(status, PoolStatus) else status
    session.flush()
    return pool


# === Delete ===

def delete_pool(session: Session, pool: LiquidityPool) -> None:
    session.delete(pool)
    session.flush()
