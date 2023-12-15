"""
Database setup for Atlas.
"""

from __future__ import annotations

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = (
    os.getenv("MERIDIAN_DATABASE_URL")
    or os.getenv("FLUID_DATABASE_URL")
    or os.getenv("ATLAS_DATABASE_URL", "sqlite:///./meridian.db")
)

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _seed_categories() -> None:
    from models import Category
    from seed_categories import DEFAULT_CATEGORIES

    db = SessionLocal()
    try:
        if db.query(Category).count() == 0:
            for i, (name, slug, sort_order) in enumerate(DEFAULT_CATEGORIES, 1):
                db.add(Category(id=i, name=name, slug=slug, sort_order=sort_order))
            db.commit()
    finally:
        db.close()


def run_migrations() -> None:
    """Run Alembic migrations; fall back to create_all on failure."""
    import subprocess
    import sys

    try:
        backend_dir = os.path.dirname(os.path.abspath(__file__))
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            cwd=backend_dir,
            env={**os.environ, "PYTHONPATH": backend_dir},
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            _seed_categories()
            return
    except FileNotFoundError:
        pass

    Base.metadata.create_all(bind=engine)
    _seed_categories()
