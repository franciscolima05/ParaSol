"""
Repositorio de Policy.

La póliza es la entidad central: vincula User (holder) + Field + Pool, y se
materializa como un NFT (ERC-721) en Avalanche.

Las funciones de transición de estado (`mark_minted`, `mark_active`, …)
reflejan el ciclo de vida descrito en el modelo:

    QUOTED → PENDING_PAYMENT → ACTIVE → (UNDER_REVIEW)? → SETTLED / EXPIRED
"""
from __future__ import annotations

import hashlib
import json
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union

from sqlalchemy import and_
from sqlalchemy.orm import Session

from ParaSol.ParaSol.backend.src.models import (
    Peril,
    Policy,
    PolicyStatus,
    PremiumProvider,
    PremiumStatus,
)

Amount = Union[Decimal, int, float, str]


def _to_decimal(x: Optional[Amount]) -> Decimal:
    if x is None:
        return Decimal(0)
    return x if isinstance(x, Decimal) else Decimal(str(x))


def _hash_terms(snapshot: Dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(snapshot, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


# === Create ===

def create_policy(
    session: Session,
    *,
    policy_number: str,
    holder_id: int,
    field_id: int,
    pool_id: int,
    peril: Peril,
    coverage_amount_usdc: Amount,
    premium_local_amount: Amount,
    premium_local_currency: str,
    premium_usdc_amount: Amount,
    coverage_start: date,
    coverage_end: date,
    trigger_snapshot: Dict[str, Any],
    polygon_hash: str,
    geometry_snapshot: Optional[Dict[str, Any]] = None,
    field_area_ha_at_emission: Optional[Amount] = None,
    fx_rate_at_purchase: Optional[Amount] = None,
    premium_provider: Optional[PremiumProvider] = None,
    chain_id: int = 43113,
    nft_contract_address: Optional[str] = None,
) -> Policy:
    """
    Crea una póliza en estado QUOTED. La emisión real (mint del NFT y lock
    de capital) se hace después con `mark_minted` + lock en el pool.
    """
    policy = Policy(
        policy_number=policy_number,
        holder_id=holder_id,
        field_id=field_id,
        pool_id=pool_id,
        chain_id=chain_id,
        nft_contract_address=nft_contract_address,
        peril=peril.value if isinstance(peril, Peril) else peril,
        coverage_amount_usdc=_to_decimal(coverage_amount_usdc),
        premium_local_amount=_to_decimal(premium_local_amount),
        premium_local_currency=premium_local_currency,
        premium_usdc_amount=_to_decimal(premium_usdc_amount),
        fx_rate_at_purchase=_to_decimal(fx_rate_at_purchase) if fx_rate_at_purchase is not None else None,
        premium_provider=(
            premium_provider.value
            if isinstance(premium_provider, PremiumProvider)
            else premium_provider
        ),
        premium_status=PremiumStatus.PENDING.value,
        coverage_start=coverage_start,
        coverage_end=coverage_end,
        trigger_snapshot=trigger_snapshot,
        polygon_hash=polygon_hash,
        geometry_snapshot=geometry_snapshot,
        field_area_ha_at_emission=(
            _to_decimal(field_area_ha_at_emission)
            if field_area_ha_at_emission is not None
            else None
        ),
        terms_hash=_hash_terms(trigger_snapshot),
        status=PolicyStatus.QUOTED.value,
        total_paid_pct=Decimal(0),
        total_paid_amount=Decimal(0),
        holdback_remaining=Decimal(0),
    )
    session.add(policy)
    session.flush()
    return policy


# === Read ===

def get_policy_by_id(session: Session, policy_id: int) -> Optional[Policy]:
    return session.get(Policy, policy_id)


def get_policy_by_number(
    session: Session, policy_number: str
) -> Optional[Policy]:
    return (
        session.query(Policy)
        .filter(Policy.policy_number == policy_number)
        .one_or_none()
    )


def get_policy_by_token_id(
    session: Session,
    *,
    nft_contract_address: str,
    nft_token_id: str,
) -> Optional[Policy]:
    return (
        session.query(Policy)
        .filter(
            and_(
                Policy.nft_contract_address == nft_contract_address,
                Policy.nft_token_id == nft_token_id,
            )
        )
        .one_or_none()
    )


def list_policies_by_holder(
    session: Session, holder_id: int
) -> List[Policy]:
    return (
        session.query(Policy)
        .filter(Policy.holder_id == holder_id)
        .order_by(Policy.created_at.desc())
        .all()
    )


def list_policies_by_field(session: Session, field_id: int) -> List[Policy]:
    return (
        session.query(Policy)
        .filter(Policy.field_id == field_id)
        .order_by(Policy.created_at.desc())
        .all()
    )


def list_policies_by_pool(session: Session, pool_id: int) -> List[Policy]:
    return (
        session.query(Policy)
        .filter(Policy.pool_id == pool_id)
        .order_by(Policy.created_at.desc())
        .all()
    )


def list_active_policies(
    session: Session,
    *,
    peril: Optional[Peril] = None,
    on_date: Optional[date] = None,
) -> List[Policy]:
    """
    Pólizas que cubren `on_date` (default: hoy) y están en un estado donde
    todavía pueden gatillar payouts.
    """
    on_date = on_date or date.today()
    live_states = (
        PolicyStatus.ACTIVE.value,
        PolicyStatus.PARTIAL_PAID.value,
        PolicyStatus.UNDER_REVIEW.value,
    )
    q = (
        session.query(Policy)
        .filter(Policy.status.in_(live_states))
        .filter(Policy.coverage_start <= on_date)
        .filter(Policy.coverage_end >= on_date)
    )
    if peril is not None:
        q = q.filter(Policy.peril == (peril.value if isinstance(peril, Peril) else peril))
    return q.order_by(Policy.id).all()


def list_policies_covering_field_on(
    session: Session,
    *,
    field_id: int,
    on_date: date,
    peril: Optional[Peril] = None,
) -> List[Policy]:
    """Pólizas vigentes para un campo en una fecha dada. Útil al detectar un evento."""
    live_states = (
        PolicyStatus.ACTIVE.value,
        PolicyStatus.PARTIAL_PAID.value,
        PolicyStatus.UNDER_REVIEW.value,
    )
    q = (
        session.query(Policy)
        .filter(Policy.field_id == field_id)
        .filter(Policy.status.in_(live_states))
        .filter(Policy.coverage_start <= on_date)
        .filter(Policy.coverage_end >= on_date)
    )
    if peril is not None:
        q = q.filter(Policy.peril == (peril.value if isinstance(peril, Peril) else peril))
    return q.all()


# === Transiciones de estado ===

def mark_premium_paid(
    session: Session,
    policy: Policy,
    *,
    provider_ref: Optional[str] = None,
) -> Policy:
    policy.premium_status = PremiumStatus.PAID.value
    policy.premium_paid_at = datetime.utcnow()
    if provider_ref is not None:
        policy.premium_provider_ref = provider_ref
    if policy.status == PolicyStatus.QUOTED.value:
        policy.status = PolicyStatus.PENDING_PAYMENT.value
    session.flush()
    return policy


def mark_minted(
    session: Session,
    policy: Policy,
    *,
    nft_token_id: str,
    nft_metadata_uri: str,
    mint_tx_hash: str,
) -> Policy:
    """
    La póliza fue minteada como NFT on-chain. Se considera ACTIVE a partir
    de acá (asumiendo que la prima ya está pagada).
    """
    policy.nft_token_id = nft_token_id
    policy.nft_metadata_uri = nft_metadata_uri
    policy.mint_tx_hash = mint_tx_hash
    policy.minted_at = datetime.utcnow()
    policy.activated_at = datetime.utcnow()
    policy.status = PolicyStatus.ACTIVE.value
    session.flush()
    return policy


def mark_under_review(session: Session, policy: Policy) -> Policy:
    """Severo: esperando verificación humana del 25% holdback."""
    policy.status = PolicyStatus.UNDER_REVIEW.value
    session.flush()
    return policy


def mark_settled(session: Session, policy: Policy) -> Policy:
    """Ya se pagó todo lo correspondiente; póliza cerrada."""
    policy.status = PolicyStatus.SETTLED.value
    session.flush()
    return policy


def mark_cancelled(session: Session, policy: Policy) -> Policy:
    policy.status = PolicyStatus.CANCELLED.value
    session.flush()
    return policy


def mark_expired(session: Session, policy: Policy) -> Policy:
    policy.status = PolicyStatus.EXPIRED.value
    policy.expired_at = datetime.utcnow()
    session.flush()
    return policy


def expire_outdated_policies(session: Session, on_date: Optional[date] = None) -> int:
    """
    Marca como EXPIRED todas las pólizas activas cuya `coverage_end` ya pasó
    y nunca llegaron a SETTLED. Devuelve cuántas se actualizaron.
    """
    on_date = on_date or date.today()
    live_states = (
        PolicyStatus.ACTIVE.value,
        PolicyStatus.PARTIAL_PAID.value,
    )
    policies = (
        session.query(Policy)
        .filter(Policy.status.in_(live_states))
        .filter(Policy.coverage_end < on_date)
        .all()
    )
    for p in policies:
        p.status = PolicyStatus.EXPIRED.value
        p.expired_at = datetime.utcnow()
    session.flush()
    return len(policies)


# === Progreso de pagos (sincronizado por PolicyPayout repo) ===

def apply_payout_progress(
    session: Session,
    policy: Policy,
    *,
    paid_pct_delta: Amount,
    paid_amount_delta: Amount,
    tier: Optional[str] = None,
    holdback_delta: Amount = 0,
) -> Policy:
    """
    Actualiza los acumuladores de progreso al confirmar un PolicyPayout.
    Lo llama `policyPayoutRepository.confirm_payout`.
    """
    policy.total_paid_pct = _to_decimal(policy.total_paid_pct) + _to_decimal(paid_pct_delta)
    policy.total_paid_amount = _to_decimal(policy.total_paid_amount) + _to_decimal(paid_amount_delta)
    policy.holdback_remaining = max(
        Decimal(0), _to_decimal(policy.holdback_remaining) + _to_decimal(holdback_delta)
    )
    if tier is not None:
        policy.current_tier = tier

    # Si ya se pagó algo pero no todo, pasamos a PARTIAL_PAID
    if (
        policy.status == PolicyStatus.ACTIVE.value
        and _to_decimal(policy.total_paid_pct) > 0
    ):
        policy.status = PolicyStatus.PARTIAL_PAID.value

    # Si llegamos al 100% efectivo y no hay holdback, cerramos
    if (
        _to_decimal(policy.total_paid_pct) >= Decimal(100)
        and _to_decimal(policy.holdback_remaining) <= 0
    ):
        policy.status = PolicyStatus.SETTLED.value

    session.flush()
    return policy


# === Delete ===

def delete_policy(session: Session, policy: Policy) -> None:
    """
    Borrado físico. En producción casi nunca se usa — preferir
    `mark_cancelled`. Existe para tests/seeding.
    """
    session.delete(policy)
    session.flush()
