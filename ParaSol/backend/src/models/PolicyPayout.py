from enum import Enum

from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ParaSol.ParaSol.backend.src.database import Base


# === Enums propios de PolicyPayout ===
# `PayoutTier` se define acá porque PolicyPayout es el modelo cuya esencia
# ES un tramo de pago. Otros modelos lo importan desde acá.

class PayoutTier(str, Enum):
    LEVE = "leve"                # 25%
    MODERADO = "moderado"        # 50%
    SEVERO = "severo"            # 75%
    FINAL = "final"              # 25% restante post-verificación


class PayoutStatus(str, Enum):
    PENDING = "pending"
    SUBMITTED = "submitted"
    CONFIRMED = "confirmed"
    REVERTED = "reverted"


class PolicyPayout(Base):
    """
    Cada tramo de payout que se libera bajo una póliza.

    Una misma póliza puede tener varios payouts en su vida:
        leve (25%)  ->  moderado (+25%)  ->  severo (+25%)  ->  final (25%)

    Tabla separada (en vez de un array dentro de Policy) para:
      - reconciliar contra `tx_hash` on-chain
      - indexar por estado / fecha para queries operativos
      - vincular cada pago al `ParametricEvent` que lo justificó
    """
    __tablename__ = "policy_payouts"

    id = Column(Integer, primary_key=True)
    policy_id = Column(Integer, ForeignKey("policies.id"), nullable=False, index=True)
    parametric_event_id = Column(Integer, ForeignKey("parametric_events.id"))

    tier = Column(String(20), nullable=False)              # ver PayoutTier
    percentage = Column(Numeric(5, 2), nullable=False)     # 25, 50, 75, 25 (final)
    amount_usdc = Column(Numeric(20, 6), nullable=False)

    # On-chain
    tx_hash = Column(String(66))
    block_number = Column(Integer)

    status = Column(String(20), default=PayoutStatus.PENDING.value)

    submitted_at = Column(DateTime)
    paid_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())

    policy = relationship("Policy", back_populates="payouts")
    parametric_event = relationship("ParametricEvent", back_populates="payouts")

    def __repr__(self):
        return (
            f"<PolicyPayout(policy_id={self.policy_id}, tier='{self.tier}', "
            f"pct={self.percentage}, status='{self.status}')>"
        )
