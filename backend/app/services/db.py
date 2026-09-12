"""
Postgres engine + session management.

Works identically against local Docker Postgres (dev) and Supabase
(production) — only the connection string in Settings changes.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """FastAPI dependency — yields a DB session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables defined in app.models on startup."""
    from app.models import base  # noqa: F401  (ensures models are registered)

    base.Base.metadata.create_all(bind=engine)
    print("[db] Tables ensured.")
