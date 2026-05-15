from enum import Enum

from sqlalchemy import (
    Column, Integer, String, Numeric, Boolean, DateTime, ForeignKey
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ParaSol.ParaSol.backend.src.database import Base
from .Policy import Peril  # noqa: F401 — reusado para `peril`
from .PolicyPayout import PayoutTier  # noqa: F401 — reusado para `severity_tier`


# === Enums propios de ParametricEvent ===

class ParametricEventStatus(str, Enum):
    DETECTED = "detected"        # motor paramétrico detectó el evento
    SIGNED = "signed"            # oráculo firmó el reporte
    SUBMITTED = "submitted"      # tx enviada al smart contract
    CONFIRMED = "confirmed"      # tx confirmada on-chain
    FAILED = "failed"


class ParametricEvent(Base):
    """
    Evento climático detectado sobre un Field, opcionalmente firmado por el
    oráculo y enviado al smart contract.

    Esta tabla fusiona dos conceptos que en una versión más madura serían
    tablas distintas:
        - detección (motor paramétrico off-chain)
        - reporte firmado (oráculo on-chain)

    Flujo de status:
        detected -> signed -> submitted -> confirmed   (o failed)

    `payload_hash` es el hash determinístico de la consulta a Earth Engine
    (mismo polígono + período + dataset ⇒ mismo hash). El smart contract
    puede recomputarlo para verificar la reproducibilidad del cálculo.

    `basis_risk_flag` se prende cuando las fuentes satelitales disienten,
    para que el evento pase a revisión manual antes de gatillar payout.
    """
    __tablename__ = "parametric_events"

    id = Column(Integer, primary_key=True)
    policy_id = Column(Integer, ForeignKey("policies.id"), index=True)
    field_id = Column(Integer, ForeignKey("fields.id"), index=True)

    peril = Column(String(40), nullable=False)             # ver Policy.Peril

    # Período observado
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    detected_at = Column(DateTime, server_default=func.now())

    # Resultado del análisis
    severity = Column(Numeric(5, 4))                       # 0.0 .. 1.0
    severity_tier = Column(String(20))                     # ver PolicyPayout.PayoutTier
    confidence = Column(Numeric(5, 4))                     # 0.0 .. 1.0
    measured_value = Column(Numeric(20, 6))                # valor del índice
    trigger_met = Column(Boolean, default=False)
    expected_payout_usdc = Column(Numeric(20, 6))

    # Trazabilidad multi-fuente
    sources_used = Column(JSONB)                           # ["Sentinel-1", "NASA_POWER"]
    measurements = Column(JSONB)                           # valor crudo por fuente
    basis_risk_flag = Column(Boolean, default=False)

    # Reproducibilidad y firma
    payload = Column(JSONB, nullable=False)                # query + fórmula + datos
    payload_hash = Column(String(64), nullable=False)      # SHA-256 determinístico
    signature = Column(String(132))                        # firma ECDSA del oráculo

    # On-chain
    tx_hash = Column(String(66))
    block_number = Column(Integer)

    # Estado y timestamps
    status = Column(
        String(20),
        default=ParametricEventStatus.DETECTED.value,
        nullable=False,
        index=True,
    )
    signed_at = Column(DateTime)
    submitted_at = Column(DateTime)
    confirmed_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())

    # Relaciones
    policy = relationship("Policy", back_populates="parametric_events")
    field = relationship("Field", back_populates="parametric_events")
    payouts = relationship("PolicyPayout", back_populates="parametric_event")

    def __repr__(self):
        return (
            f"<ParametricEvent(peril='{self.peril}', "
            f"tier='{self.severity_tier}', status='{self.status}')>"
        )
