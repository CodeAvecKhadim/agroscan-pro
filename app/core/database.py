"""
Connexion à la base de données et fabrique de sessions SQLAlchemy.
Compatible SQLite (démarrage) et PostgreSQL (production) sans changement de code.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

# SQLite a besoin d'un argument spécifique pour fonctionner avec FastAPI (multithread).
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(settings.DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dépendance FastAPI : ouvre une session par requête et la referme proprement."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
