"""
Entry repository: database operations for Entry entities.

Handles listing, fetching, creating, updating, and deleting entries,
plus export queries.
"""

from datetime import date
from typing import List, Optional, Tuple, Literal, Dict, Any

from sqlalchemy import func, desc, asc
from sqlalchemy.orm import Session, joinedload

from models import User, Entry, Category


class EntryRepository:
    """Centralizes Entry-related database queries."""

    @staticmethod
    def list_entries(
        db: Session,
        user_id: int,
        *,
        category: Optional[str] = None,
        search: Optional[str] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        sort: str = "date",
        order: str = "asc",
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> Tuple[List[Entry], int]:
        """
        List entries for a user with optional filters, sorting, and pagination.
        Returns (entries, total_count).
        """
        query = (
            db.query(Entry)
            .options(joinedload(Entry.category_rel))
            .filter(Entry.user_id == user_id)
        )

        need_category_join = category is not None or sort == "category"
        if need_category_join:
            query = query.join(Entry.category_rel)
        if category:
            query = query.filter(Category.name == category)
        if search:
            query = query.filter(Entry.details.ilike(f"%{search}%"))
        if from_date:
            query = query.filter(Entry.date >= from_date)
        if to_date:
            query = query.filter(Entry.date <= to_date)

        total_count = query.count()

        sort_col = {
            "date": Entry.date,
            "category": Category.name,
            "created_at": Entry.created_at,
        }.get(sort, Entry.date)
        if order == "desc":
            query = query.order_by(desc(sort_col), desc(Entry.id))
        else:
            query = query.order_by(asc(sort_col), asc(Entry.id))

        if limit is not None:
            query = query.limit(limit)
        if offset > 0:
            query = query.offset(offset)

        entries = query.all()
        return entries, total_count

    @staticmethod
    def get_by_id(db: Session, user_id: int, entry_id: int) -> Optional[Entry]:
        """Fetch a single entry by ID for a user, or None if not found."""
        return (
            db.query(Entry)
            .options(joinedload(Entry.category_rel))
            .filter(Entry.user_id == user_id, Entry.id == entry_id)
            .first()
        )

    @staticmethod
    def create(
        db: Session,
        user_id: int,
        category_id: int,
        date_val: date,
        details: str,
    ) -> Entry:
        """Create a new entry. Returns the created entry with category_rel loaded."""
        entry = Entry(
            user_id=user_id,
            category_id=category_id,
            date=date_val,
            details=details,
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        entry = (
            db.query(Entry)
            .options(joinedload(Entry.category_rel))
            .filter(Entry.id == entry.id)
            .first()
        )
        return entry

    @staticmethod
    def update(
        db: Session,
        entry: Entry,
        *,
        category_id: Optional[int] = None,
        date_val: Optional[date] = None,
        details: Optional[str] = None,
    ) -> Entry:
        """Update an entry in-place. Returns refreshed entry with category_rel."""
        if category_id is not None:
            entry.category_id = category_id
        if date_val is not None:
            entry.date = date_val
        if details is not None:
            entry.details = details
        db.commit()
        db.refresh(entry)
        return (
            db.query(Entry)
            .options(joinedload(Entry.category_rel))
            .filter(Entry.id == entry.id)
            .first()
        )

    @staticmethod
    def delete(db: Session, entry: Entry) -> None:
        """Delete an entry."""
        db.delete(entry)
        db.commit()

    @staticmethod
    def export_entries(
        db: Session, user_id: int
    ) -> List[Tuple[Entry, str]]:
        """
        Fetch all entries for a user with category names, ordered by date.
        Returns list of (Entry, category_name) tuples.
        """
        return (
            db.query(Entry, Category.name)
            .join(Category, Entry.category_id == Category.id)
            .filter(Entry.user_id == user_id)
            .order_by(Entry.date.asc())
            .all()
        )
