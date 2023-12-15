"""
Export all Atlas entries to a CSV file (admin/CLI).

Exports all users' entries with username, category, date, details, created_at.
Use the API endpoint GET /users/{username}/export for per-user export.

Usage:
  python scripts/export_data.py              # writes to backend/exports/entries_export.csv
  python scripts/export_data.py /path/to.csv # writes to specified path

Run from the backend/ directory.
"""
import os
import sys
import csv

from sqlalchemy.orm import Session

from database import SessionLocal, run_migrations
from models import User, Entry, Category


def get_default_export_path() -> str:
    """ Default export path: backend/exports/entries_export.csv """
    current_dir = os.path.dirname(__file__)      # backend/scripts
    backend_dir = os.path.dirname(current_dir)   # backend
    exports_dir = os.path.join(backend_dir, "exports")

    if not os.path.exists(exports_dir):
        os.makedirs(exports_dir, exist_ok=True)

    return os.path.join(exports_dir, "entries_export.csv")


def export_data(output_path: str | None = None) -> str:
    """ Export all entries (joined with usernames and category names) to a CSV file """
    # Ensure DB schema is up to date
    run_migrations()

    if output_path is None:
        output_path = get_default_export_path()

    db: Session = SessionLocal()

    try:
        # Query all entries with user and category
        rows = (
            db.query(User.username, Category.name, Entry.date, Entry.details, Entry.created_at)
            .join(Entry, Entry.user_id == User.id)
            .join(Category, Entry.category_id == Category.id)
            .order_by(User.username.asc(), Entry.date.asc())
            .all()
        )

        # Write CSV
        with open(output_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            # Header
            writer.writerow(["username", "category", "date", "details", "created_at"])

            # Rows
            for username, category, date_obj, details, created_at in rows:
                writer.writerow(
                    [username, category, date_obj.isoformat() if date_obj else "",
                        details or "", created_at.isoformat() if created_at else "",
                    ]
                )

        print(f"[DONE] Exported {len(rows)} entries to: {output_path}")
    finally:
        db.close()

    return output_path


if __name__ == "__main__":
    if len(sys.argv) > 1:
        out_path = sys.argv[1]
    else:
        out_path = None

    export_data(out_path)
