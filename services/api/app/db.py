"""DB engine: Postgres when DATABASE_URL/POSTGRES_URL set, else local SQLite."""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

def database_url() -> str:
    url = os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_URL") or ""
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg://", 1)
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    if url:
        return url
    base = os.path.dirname(os.path.abspath(__file__))
    return f"sqlite:///{os.path.join(base, 'dev.db')}"

engine = create_engine(database_url(), pool_pre_ping=True)

class Base(DeclarativeBase):
    pass

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
