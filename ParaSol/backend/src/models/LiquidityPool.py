from enum import Enum

from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ParaSol.ParaSol.backend.src.database import Base
from .Policy import Peril  # noqa: F401 — reusado para `peril_focus`


# === Enums propios de LiquidityPool ===

class PoolStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    DEPLETED = "depleted"        # sin capital disponible
    CLOSED = "closed"


class LiquidityPool(Base):
    """
    Pool de liquidez on-chain que respalda las pólizas.

    Responde la pregunta clave del jurado: "¿de dónde sale la plata del
    payout?". La aseguradora (o un backer) pre-fondea un pool en USDC, las
    primas se acumulan en el pool, y cada `PolicyPayout` se descuenta de
    ahí.

    Identidad contable:
        available = total_capital - locked_capital - paid_out_capital

    Un pool puede ser:
        - general: cubre cualquier peril / cualquier región
        - específico: peril y/o región acotados (p.ej. "granizo BA 2026")

    NOTA: la verdad última del capital vive en el smart contract on-chain.
    Estas columnas son un *snapshot* sincronizado para queries rápidas y
    para el dashboard.
    """
    __tablename__ = "liquidity_pools"

    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)             # "Pool Granizo BA 2026"

    # On-chain
    chain_id = Column(Integer, default=43113)              # Fuji por defecto
    escrow_contract_address = Column(String(42))           # contrato que custodia

    # Capital (USDC) — snapshot del estado on-chain
    total_capital_usdc = Column(Numeric(20, 6), default=0)
    locked_capital_usdc = Column(Numeric(20, 6), default=0)    # respaldando pólizas activas
    paid_out_usdc = Column(Numeric(20, 6), default=0)          # ya pagado

    # Foco del pool (null = sin restricción)
    peril_focus = Column(String(40))                       # ver Policy.Peril; null = general
    region_focus = Column(String(100))                     # "AR-BA" o null

    # Backer principal (aseguradora o productor que aporta capital)
    funded_by_user_id = Column(Integer, ForeignKey("users.id"))

    status = Column(String(20), default=PoolStatus.ACTIVE.value)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    policies = relationship("Policy", back_populates="pool")
    funded_by = relationship("User")

    def __repr__(self):
        return (
            f"<LiquidityPool(id={self.id}, name='{self.name}', "
            f"status='{self.status}')>"
        )
