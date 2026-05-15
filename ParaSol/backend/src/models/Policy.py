from enum import Enum

from sqlalchemy import (
    Column, Integer, String, ForeignKey, DateTime, Date, Numeric
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ParaSol.ParaSol.backend.src.database import Base
from .PolicyPayout import PayoutTier  # noqa: F401 — re-exportado para conveniencia


# === Enums propios de Policy ===
# `Peril` se define acá porque la póliza es la entidad que "compra" la
# cobertura contra un peril determinado. LiquidityPool y ParametricEvent
# importan Peril desde Policy.

class Peril(str, Enum):
    HAIL = "hail"                # granizo — MVP del hackathon
    DROUGHT = "drought"
    EXCESS_RAIN = "excess_rain"
    FROST = "frost"
    HEAT = "heat"
    FLOOD = "flood"
    NDVI_ANOMALY = "ndvi_anomaly"


class PolicyStatus(str, Enum):
    QUOTED = "quoted"
    PENDING_PAYMENT = "pending_payment"
    ACTIVE = "active"
    PARTIAL_PAID = "partial_paid"
    UNDER_REVIEW = "under_review"     # severo: esperando verificación del 25%
    SETTLED = "settled"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class PremiumStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    REFUNDED = "refunded"
    FAILED = "failed"


class PremiumProvider(str, Enum):
    MERCADO_PAGO = "mercado_pago"
    BITSO = "bitso"
    RIPIO = "ripio"
    BANK_TRANSFER = "bank_transfer"


class Policy(Base):
    """
    Póliza paramétrica. La póliza ES un NFT (ERC-721) que vive en Avalanche.

    Sistema de pago escalonado (sección 14 del PDF):
        leve     20-40%  -> 25% inmediato
        moderado 40-60%  -> 50% inmediato
        severo   60%+    -> 75% inmediato + 25% post-verificación

    El capital sale del `LiquidityPool` referenciado en `pool_id`.

    INMUTABILIDAD CONTRACTUAL:
        `trigger_snapshot` (JSONB) congela TODA la regla al emitir: peril,
        fuentes, ventana, escala de severidad, fórmula. Cambios futuros al
        catálogo de productos NO afectan pólizas vigentes.

    ANTI-FRAUDE:
        `polygon_hash` + `geometry_snapshot` + `terms_hash` permiten
        verificar on-chain que las condiciones siguen siendo las que se
        firmaron al emitir.
    """
    __tablename__ = "policies"

    id = Column(Integer, primary_key=True)
    policy_number = Column(String(40), unique=True, nullable=False)
    # ejemplo: "PSL-AR-2026-000123"

    # === Partes ===
    holder_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    field_id = Column(Integer, ForeignKey("fields.id"), nullable=False, index=True)
    pool_id = Column(Integer, ForeignKey("liquidity_pools.id"), nullable=False, index=True)

    # === On-chain (NFT) ===
    chain_id = Column(Integer, nullable=False, default=43113)
    nft_contract_address = Column(String(42))
    nft_token_id = Column(String(80))                      # uint256 como string
    nft_metadata_uri = Column(String(255))                 # ipfs:// o ar://
    mint_tx_hash = Column(String(66))

    # === Cobertura (siempre en USDC) ===
    peril = Column(String(40), nullable=False, index=True)   # ver Peril
    coverage_amount_usdc = Column(Numeric(20, 6), nullable=False)

    # === Prima ===
    # El agricultor paga en moneda local; se convierte a USDC para el pool.
    premium_local_amount = Column(Numeric(20, 2), nullable=False)
    premium_local_currency = Column(String(3), nullable=False)  # "ARS", "MXN", "BRL"
    premium_usdc_amount = Column(Numeric(20, 6), nullable=False)
    fx_rate_at_purchase = Column(Numeric(20, 8))
    premium_provider = Column(String(30))                  # ver PremiumProvider
    premium_provider_ref = Column(String(120))             # id de tx externa
    premium_status = Column(String(20), default=PremiumStatus.PENDING.value)
    premium_paid_at = Column(DateTime)

    # === Período ===
    coverage_start = Column(Date, nullable=False)
    coverage_end = Column(Date, nullable=False)

    # === Regla paramétrica (snapshot inmutable) ===
    trigger_snapshot = Column(JSONB, nullable=False)
    # ejemplo:
    # {
    #   "peril": "hail",
    #   "data_sources": ["Sentinel-1", "NASA_POWER"],
    #   "consensus": "majority",
    #   "window_days": 15,
    #   "index": "ndvi_drop_pct",
    #   "severity_schema": [
    #     {"tier":"leve",     "range_pct":[20,40], "payout_pct":25, "immediate":true},
    #     {"tier":"moderado", "range_pct":[40,60], "payout_pct":50, "immediate":true},
    #     {"tier":"severo",   "range_pct":[60,100],"payout_pct":75, "immediate":true,
    #                         "holdback_pct":25, "requires_final_verification":true}
    #   ]
    # }

    # === Progreso de pagos ===
    total_paid_pct = Column(Numeric(5, 2), default=0)
    total_paid_amount = Column(Numeric(20, 6), default=0)
    holdback_remaining = Column(Numeric(20, 6), default=0)
    current_tier = Column(String(20))                      # ver PolicyPayout.PayoutTier

    # === Estado ===
    status = Column(
        String(30),
        default=PolicyStatus.QUOTED.value,
        nullable=False,
        index=True,
    )

    # === Anti-fraude (snapshot al emitir) ===
    polygon_hash = Column(String(64), nullable=False)      # SHA-256 del polígono
    geometry_snapshot = Column(JSONB)                      # GeoJSON congelado
    field_area_ha_at_emission = Column(Numeric(12, 4))
    terms_hash = Column(String(64))                        # SHA-256 del PDF de condiciones

    # === Timestamps del ciclo de vida ===
    minted_at = Column(DateTime)
    activated_at = Column(DateTime)
    expired_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # === Relaciones ===
    holder = relationship("User", back_populates="policies", foreign_keys=[holder_id])
    field = relationship("Field", back_populates="policies")
    pool = relationship("LiquidityPool", back_populates="policies")

    payouts = relationship(
        "PolicyPayout",
        back_populates="policy",
        cascade="all, delete-orphan",
    )
    parametric_events = relationship("ParametricEvent", back_populates="policy")

    def __repr__(self):
        return (
            f"<Policy(number='{self.policy_number}', peril='{self.peril}', "
            f"status='{self.status}')>"
        )
