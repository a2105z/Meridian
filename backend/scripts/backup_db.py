"""
Backup the Atlas SQLite database.

Creates a timestamped copy of atlas.db in backend/backups/ (or a custom path).

Usage:
  python scripts/backup_db.py                    # backend/backups/atlas_backup_YYYYMMDD_HHMMSS.db
  python scripts/backup_db.py /path/to/backup.db # custom output path

Run from the backend/ directory.
"""
import os
import shutil
import sys
from datetime import datetime

# Ensure we can import database
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import DATABASE_URL


def get_db_path() -> str:
    """Get the path to the SQLite database file."""
    # DATABASE_URL is like "sqlite:///./atlas.db"
    if not DATABASE_URL.startswith("sqlite"):
        print("[ERROR] Backup only supports SQLite databases.")
        sys.exit(1)
    path = DATABASE_URL.replace("sqlite:///", "").lstrip("/")
    # Resolve relative to backend/
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if not os.path.isabs(path):
        path = os.path.join(backend_dir, path)
    return os.path.normpath(path)


def backup_database(output_path: str | None = None) -> str:
    """Copy the database file to a backup location. Returns the backup path."""
    db_path = get_db_path()
    if not os.path.exists(db_path):
        print(f"[ERROR] Database not found at {db_path}")
        sys.exit(1)

    if output_path is None:
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        backups_dir = os.path.join(backend_dir, "backups")
        os.makedirs(backups_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(backups_dir, f"atlas_backup_{timestamp}.db")

    shutil.copy2(db_path, output_path)
    print(f"[DONE] Backed up database to: {output_path}")
    return output_path


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else None
    backup_database(out)
