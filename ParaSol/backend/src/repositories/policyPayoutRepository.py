
"""
Repositorio de ParametricEvent.

Fusiona los conceptos de detección off-chain y reporte firmado on-chain.

Flujo de status:
    DETECTED → SIGNED → SUBMITTED → CONFIRMED   (o FAILED)
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union

from sqlalchemy.orm import Session

from ParaSol.ParaSol.backend.src.models import (
    ParametricEvent,
    ParametricEventStatus,
    PayoutTier,
    Peril,
)

Amount = Union[Decimal, int, float, str]


def _to_decimal(x: Optional[Amount]) -> Optional[Decimal]:
    if x is None:
        return None
    return x if isinstance(x, Decimal) else Decimal(str(x))


def compute_payload_hash(payload: Dict[str, Any]) -> str:
    """
    Hash determinístico del payload (query + fórmula + datos). El smart
    contract puede recomputarlo para verificar reproducibilidad: mismo
    polígono + período + dataset ⇒ mismo hash.
    """
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


# === Create ===

def create_event(
    session: Session,
    *,
    field_id: int,
    peril: Peril,
    period_start: datetime,
    period_end: datetime,
    payload: Dict[str, Any],
    policy_id: Optional[int] = None,
    severity: Optional[Amount] = None,
    severity_tier: Optional[PayoutTier] = None,
    confidence: Optional[Amount] = None,
    measured_value: Optional[Amount] = None,
    trigger_met: bool = False,
    expected_payout_usdc: Optional[Amount] = None,
    sources_used: Optional[List[str]] = None,
    measurements: Optional[Dict[str, Any]] = None,
    basis_risk_flag: bool = False,
) -> ParametricEvent:
    """
    Registra un evento detectado por el motor paramétrico (estado DETECTED).
    """
    event = ParametricEvent(
        policy_id=policy_id,
        field_id=field_id,
        peril=peril.value if isinstance(peril, Peril) else peril,
        period_start=period_start,
        period_end=period_end,
        severity=_to_decimal(severity),
        severity_tier=(
            severity_tier.value if isinstance(severity_tier, PayoutTier) else severity_tier
        ),
        confidence=_to_decimal(confidence),
        measured_value=_to_decimal(measured_value),
        trigger_met=trigger_met,
        expected_payout_usdc=_to_decimal(expected_payout_usdc),
        sources_used=sources_used,
        measurements=measurements,
        basis_risk_flag=basis_risk_flag,
        payload=payload,
        payload_hash=compute_payload_hash(payload),
        status=ParametricEventStatus.DETECTED.value,
    )
    session.add(event)
    session.flush()
    return event


# === Read ===

def get_event_by_id(session: Session, event_id: int) -> Optional[ParametricEvent]:
    return session.get(ParametricEvent, event_id)


def get_event_by_payload_hash(
    session: Session, payload_hash: str
) -> Optional[ParametricEvent]:
    """Útil para evitar reprocesar el mismo cálculo on-chain."""
    return (
        session.query(ParametricEvent)
        .filter(ParametricEvent.payload_hash == payload_hash)
        .one_or_none()
    )


def list_events_by_policy(
    session: Session, policy_id: int
) -> List[ParametricEvent]:
    return (
        session.query(ParametricEvent)
        .filter(ParametricEvent.policy_id == policy_id)
        .order_by(ParametricEvent.detected_at.desc())
        .all()
    )


def list_events_by_field(
    session: Session, field_id: int
) -> List[ParametricEvent]:
    return (
        session.query(ParametricEvent)
        .filter(ParametricEvent.field_id == field_id)
        .order_by(ParametricEvent.detected_at.desc())
        .all()
    )


def list_events_by_status(
    session: Session,
    status: ParametricEventStatus,
    *,
    limit: int = 100,
) -> List[ParametricEvent]:
    val = status.value if isinstance(status, ParametricEventStatus) else status
    return (
        session.query(ParametricEvent)
        .filter(ParametricEvent.status == val)
        .order_by(ParametricEvent.id.desc())
        .limit(limit)
        .all()
    )


def list_pending_for_oracle(session: Session) -> List[ParametricEvent]:
    """Eventos que dispararon trigger pero todavía no firmaron."""
    return (
        session.query(ParametricEvent)
        .filter(ParametricEvent.status == ParametricEventStatus.DETECTED.value)
        .filter(ParametricEvent.trigger_met.is_(True))
        .filter(ParametricEvent.basis_risk_flag.is_(False))
        .order_by(ParametricEvent.detected_at)
        .all()
    )


def list_under_basis_risk_review(session: Session) -> List[ParametricEvent]:
    """Eventos en revisión manual por disenso entre fuentes satelitales."""
    return (
        session.query(ParametricEvent)
        .filter(ParametricEvent.basis_risk_flag.is_(True))
        .filter(ParametricEvent.status == ParametricEventStatus.DETECTED.value)
        .order_by(ParametricEvent.detected_at)
        .all()
    )


# === Transiciones ===

def mark_signed(
    session: Session,
    event: ParametricEvent,
    *,
    signature: str,
) -> ParametricEvent:
    """El oráculo firma el reporte con ECDSA."""
    event.signature = signature
    event.signed_at = datetime.utcnow()
    event.status = ParametricEventStatus.SIGNED.value
    session.flush()
    return event


def mark_submitted(
    session: Session,
    event: ParametricEvent,
    *,
    tx_hash: str,
) -> ParametricEvent:
    """Tx enviada al smart contract (todavía sin minar)."""
    event.tx_hash = tx_hash
    event.submitted_at = datetime.utcnow()
    event.status = ParametricEventStatus.SUBMITTED.value
    session.flush()
    return event


def mark_confirmed(
    session: Session,
    event: ParametricEvent,
    *,
    block_number: int,
) -> ParametricEvent:
    """Tx confirmada on-chain."""
    event.block_number = block_number
    event.confirmed_at = datetime.utcnow()
    event.status = ParametricEventStatus.CONFIRMED.value
    session.flush()
    return event


def mark_failed(
    session: Session, event: ParametricEvent
) -> ParametricEvent:
    event.status = ParametricEventStatus.FAILED.value
    session.flush()
    return event


def flag_basis_risk(
    session: Session, event: ParametricEvent
) -> ParametricEvent:
    """
    Marca el evento como sospechoso por disenso entre fuentes. No bloquea,
    pero indica que necesita revisión manual antes de gatillar payout.
    """
    event.basis_risk_flag = True
    session.flush()
    return event


# === Delete ===

def delete_event(session: Session, event: ParametricEvent) -> None:
    session.delete(event)
    session.flush()