from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, Session
from sqlalchemy.pool import NullPool
from contextlib import contextmanager
import os

# Configuración de la base de datos
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://user:password@localhost:5432/parasol_db"
)

# Engine
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Cambiar a True para ver SQL
    pool_pre_ping=True,  # Verifica conexión antes de usar
    poolclass=NullPool,  # Sin pool para desarrollo
)

# Base para los modelos
Base = declarative_base()


def get_session() -> Session:
    """Obtiene una sesión de la base de datos."""
    return Session(engine)


@contextmanager
def session_scope():
    """Context manager para sesiones."""
    session = Session(engine)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db():
    """Crea todas las tablas."""
    Base.metadata.create_all(engine)


if __name__ == "__main__":
    init_db()
    print("✓ Base de datos inicializada")
