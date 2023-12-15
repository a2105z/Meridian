"""
ORM models for Atlas.

Defines User, Category, and Entry tables with relationships and constraints.
"""

from datetime import datetime, date

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Date,
    ForeignKey,
    Text,
)
from sqlalchemy.orm import relationship

from database import Base


class User(Base):
    """User account with profile and credentials."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(80), unique=True, index=True, nullable=False)
    first_name = Column(String(80), nullable=False)
    last_name = Column(String(80), nullable=False)
    birthday = Column(Date, nullable=False)
    password_hash = Column(String(256), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    entries = relationship(
        "Entry",
        back_populates="user",
        cascade="all, delete-orphan",
    )


class Category(Base):
    """
    Normalized category lookup table.
    Entries reference categories via category_id (FK).
    """

    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    sort_order = Column(Integer, nullable=False, default=0)

    entries = relationship("Entry", back_populates="category_rel")


class Entry(Base):
    """Academic achievement or activity entry, linked to a user and category."""

    __tablename__ = "entries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category_id = Column(
        Integer,
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    date = Column(Date, nullable=False)
    details = Column(Text, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="entries")
    category_rel = relationship("Category", back_populates="entries")
