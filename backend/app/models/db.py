"""SQLAlchemy base and session helpers."""

from __future__ import annotations

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

_default_db = "sqlite:////tmp/space_mission.db" if os.getenv("VERCEL") else "sqlite:///./space_mission.db"
DB_URL = os.getenv("DATABASE_URL", _default_db)
engine = create_engine(DB_URL, connect_args={"check_same_thread": False} if DB_URL.startswith("sqlite") else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()