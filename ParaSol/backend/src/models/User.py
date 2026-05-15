from enum import Enum

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ParaSol.ParaSol.backend.src.database import Base


# === Statuses propios de User ===

class UserRole(str, Enum):
    PRODUCER = "producer"        # dueño de campo / agricultor
    ADMIN = "admin"              # admin de la plataforma
    ORACLE = "oracle"            # cuenta firmante del oráculo


class KYCStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class KYCLevel(str, Enum):
    NONE = "none"
    BASIC = "basic"              # DNI + selfie + geo
    ENHANCED = "enhanced"


class User(Base):
    """
    Usuario del sistema.

    El agricultor nunca ve crypto: `wallet_address` es un smart account
    (ERC-4337) creado automáticamente al registrarse — desde la perspectiva
    del agricultor, simplemente se registra como en cualquier app.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(120), unique=True, nullable=False)
    full_name = Column(String(100))

    # Identidad
    document_id = Column(String(20), unique=True, nullable=True)   # DNI / RFC
    country = Column(String(2))                                    # "AR", "MX"
    phone = Column(String(20))

    # Wallet (smart account ERC-4337)
    wallet_address = Column(String(42), unique=True, nullable=True)

    # KYC
    kyc_status = Column(String(20), default=KYCStatus.PENDING.value)
    kyc_level = Column(String(20), default=KYCLevel.NONE.value)
    kyc_approved_at = Column(DateTime)

    # Rol (producer | admin | oracle)
    role = Column(String(20), default=UserRole.PRODUCER.value)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    fields = relationship("Field", back_populates="owner")
    policies = relationship(
        "Policy",
        back_populates="holder",
        foreign_keys="Policy.holder_id",
    )

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"
