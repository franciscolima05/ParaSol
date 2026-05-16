"""
Repositorio de User.

Capa de acceso a datos para `users`. Cada función recibe una `Session` de
SQLAlchemy (la transacción la maneja el caller — típicamente vía
`session_scope()` de `database.py`).
"""
from __future__ import annotations

from typing import List, Optional

from sqlalchemy.orm import Session

from ParaSol.ParaSol.backend.src.models import User, UserRole


# === Create ===

def create_user(
    session: Session,
    *,
    email: str,
    full_name: Optional[str] = None,
    document_id: Optional[str] = None,
    country: Optional[str] = None,
    phone: Optional[str] = None,
    wallet_address: Optional[str] = None,
    role: UserRole = UserRole.PRODUCER,
) -> User:
    """Crea un nuevo usuario. No commitea — eso queda en manos del caller."""
    user = User(
        email=email,
        full_name=full_name,
        document_id=document_id,
        country=country,
        phone=phone,
        wallet_address=wallet_address,
        role=role.value if isinstance(role, UserRole) else role,
    )
    session.add(user)
    session.flush()  # asigna el id sin commitear
    return user


# === Read ===

def get_user_by_id(session: Session, user_id: int) -> Optional[User]:
    return session.get(User, user_id)


def get_user_by_email(session: Session, email: str) -> Optional[User]:
    return session.query(User).filter(User.email == email).one_or_none()


def get_user_by_wallet(session: Session, wallet_address: str) -> Optional[User]:
    return (
        session.query(User)
        .filter(User.wallet_address == wallet_address)
        .one_or_none()
    )


def get_user_by_document_id(
    session: Session, document_id: str
) -> Optional[User]:
    return (
        session.query(User)
        .filter(User.document_id == document_id)
        .one_or_none()
    )


def list_users(
    session: Session,
    *,
    role: Optional[UserRole] = None,
    country: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[User]:
    """Lista usuarios con filtros opcionales por rol y país."""
    q = session.query(User)
    if role is not None:
        q = q.filter(User.role == (role.value if isinstance(role, UserRole) else role))
    if country is not None:
        q = q.filter(User.country == country)
    return q.order_by(User.id).limit(limit).offset(offset).all()


# === Update ===

def update_user(session: Session, user: User, **fields) -> User:
    """Actualiza campos arbitrarios. Ignora claves desconocidas."""
    for key, value in fields.items():
        if hasattr(user, key) and value is not None:
            setattr(user, key, value)
    session.flush()
    return user


def attach_wallet(session: Session, user: User, wallet_address: str) -> User:
    """
    Asocia un smart account (ERC-4337) recién creado al usuario.
    Se llama una sola vez al onboarding.
    """
    user.wallet_address = wallet_address
    session.flush()
    return user


# === Delete ===

def delete_user(session: Session, user: User) -> None:
    session.delete(user)
    session.flush()