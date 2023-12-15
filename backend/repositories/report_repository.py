"""
Report repository: SQL-based aggregations and reporting queries.

Provides timeline, by-category, and activity-summary reports.
"""

from datetime import date
from typing import Dict, List, Optional, Literal

from sqlalchemy import func, cast, Integer
from sqlalchemy.orm import Session, joinedload

from models import User, Entry, Category


class ReportRepository:
    """Centralizes report and analytics queries."""

    @staticmethod
    def get_categories(db: Session) -> List[str]:
        """Return all category names ordered by sort_order."""
        rows = (
            db.query(Category.name)
            .order_by(Category.sort_order.asc(), Category.id.asc())
            .all()
        )
        return [r[0] for r in rows]

    @staticmethod
    def get_category_by_name(db: Session, name: str) -> Optional[Category]:
        """Fetch category by name, or None if not found."""
        return db.query(Category).filter(Category.name == name).first()

    @staticmethod
    def timeline_report(
        db: Session,
        user_id: int,
        group_by: Literal["month", "quarter"] = "month",
    ) -> List[tuple]:
        """
        Entries grouped by month or quarter.
        Returns list of (period_str, count) tuples.
        """
        if group_by == "month":
            period_expr = func.strftime("%Y-%m", Entry.date)
        else:
            month_num = cast(func.strftime("%m", Entry.date), Integer)
            quarter = cast((month_num + 2) / 3, Integer)
            year = func.strftime("%Y", Entry.date)
            period_expr = func.printf("%s-Q%d", year, quarter)

        rows = (
            db.query(period_expr.label("period"), func.count(Entry.id).label("count"))
            .filter(Entry.user_id == user_id)
            .group_by(period_expr)
            .order_by(period_expr)
            .all()
        )
        return [(str(r.period), r.count) for r in rows]

    @staticmethod
    def by_category_report(db: Session, user_id: int) -> Dict[str, int]:
        """Entry counts per category for a user."""
        rows = (
            db.query(Category.name, func.count(Entry.id).label("count"))
            .join(Entry, Entry.category_id == Category.id)
            .filter(Entry.user_id == user_id)
            .group_by(Category.name)
            .order_by(Category.sort_order)
            .all()
        )
        return {r.name: r.count for r in rows}

    @staticmethod
    def activity_summary_report(
        db: Session, user_id: int
    ) -> Dict:
        """
        Rich activity summary: total, first/last dates, per-category counts,
        and timeline by month. Returns dict with keys:
        total_entries, first_entry_date, last_entry_date,
        entries_per_category, timeline_by_month.
        """
        entries = (
            db.query(Entry)
            .options(joinedload(Entry.category_rel))
            .filter(Entry.user_id == user_id)
            .order_by(Entry.date.asc())
            .all()
        )

        total = len(entries)
        per_category: Dict[str, int] = {}
        first_date: Optional[date] = None
        last_date: Optional[date] = None
        month_counts: Dict[str, int] = {}

        for e in entries:
            cat_name = e.category_rel.name if e.category_rel else "Unknown"
            per_category[cat_name] = per_category.get(cat_name, 0) + 1
            if first_date is None or e.date < first_date:
                first_date = e.date
            if last_date is None or e.date > last_date:
                last_date = e.date
            if e.date:
                period = e.date.strftime("%Y-%m")
                month_counts[period] = month_counts.get(period, 0) + 1

        timeline = [
            {"period": k, "count": v}
            for k, v in sorted(month_counts.items())
        ]

        return {
            "total_entries": total,
            "first_entry_date": first_date,
            "last_entry_date": last_date,
            "entries_per_category": per_category,
            "timeline_by_month": timeline,
        }

    @staticmethod
    def analytics_summary(db: Session, user_id: int) -> Dict:
        """
        Simple analytics summary (used by /analytics/{username}/summary).
        Returns dict with total_entries, entries_per_category,
        first_entry_date, last_entry_date.
        """
        entries = (
            db.query(Entry)
            .options(joinedload(Entry.category_rel))
            .filter(Entry.user_id == user_id)
            .order_by(Entry.date.asc())
            .all()
        )

        total = len(entries)
        per_category: Dict[str, int] = {}
        first_date: Optional[date] = None
        last_date: Optional[date] = None

        for e in entries:
            cat_name = e.category_rel.name if e.category_rel else "Unknown"
            per_category[cat_name] = per_category.get(cat_name, 0) + 1
            if first_date is None or e.date < first_date:
                first_date = e.date
            if last_date is None or e.date > last_date:
                last_date = e.date

        return {
            "total_entries": total,
            "entries_per_category": per_category,
            "first_entry_date": first_date,
            "last_entry_date": last_date,
        }
