"""
Import legacy ScholarPath data from tracker_data.json into the Atlas database.

Reads legacy/tracker_data.json (format: {username: {category: [entry_strings]}})
and creates users and entries. Legacy users get default profile fields and
can log in with the password 'changeme'.

Usage:
  python scripts/import_legacy_data.py

Run from the backend/ directory or project root (with PYTHONPATH set).
"""
import os
import json
import hashlib
from datetime import datetime, date

from sqlalchemy.orm import Session

# Make sure Python can find database.py and models.py when run from backend/
from database import SessionLocal, run_migrations
from models import User, Entry, Category

# Default password for legacy-imported users (they must use this to log in)
LEGACY_DEFAULT_PASSWORD = "changeme"


def get_legacy_file_path() -> str:
    """ Build the path to ../legacy/tracker_data.json relative to this file """
    current_dir = os.path.dirname(__file__)         # backend/scripts
    backend_dir = os.path.dirname(current_dir)      # backend
    project_root = os.path.dirname(backend_dir)     # Atlas project root
    legacy_file = os.path.join(project_root, "legacy", "tracker_data.json")
    return legacy_file


def hash_password(raw: str) -> str:
    """ Simple SHA-256 hash for demo (matches app.py) """
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def get_or_create_user(db: Session, username: str) -> User:
    """
    Find an existing user by username, or create a new one.

    Legacy users from JSON don't have first_name, last_name, birthday, or password.
    We use defaults so they can log in with LEGACY_DEFAULT_PASSWORD.
    """
    user = db.query(User).filter(User.username == username).first()
    if user:
        return user

    # Create user with required fields - use defaults for legacy import
    user = User(
        username=username,
        first_name=username,  # Use username as first name for legacy
        last_name="User",
        birthday=date(2000, 1, 1),  # Default placeholder
        password_hash=hash_password(LEGACY_DEFAULT_PASSWORD),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def parse_legacy_entry(entry_str: str):
    """ Parse a legacy entry string of the form "MM/DD/YYYY: details" """

    if ": " in entry_str:
        date_part, details = entry_str.split(": ", 1)
    else:
        # Fallback: split on first colon only
        parts = entry_str.split(":", 1)
        if len(parts) == 2:
            date_part, details = parts
        else:
            return None, None

    date_part = date_part.strip()
    details = details.strip()

    try:
        date_obj = datetime.strptime(date_part, "%m/%d/%Y").date()
    except ValueError:
        print(f"[WARN] Skipping entry with invalid date format: {entry_str!r}")
        return None, None

    if not details:
        print(f"[WARN] Skipping entry with empty details: {entry_str!r}")
        return None, None

    return date_obj, details


def get_or_create_category(db: Session, category_name: str) -> Category:
    """Find category by name, or create it if unknown (e.g. from legacy data)."""
    cat = db.query(Category).filter(Category.name == category_name).first()
    if cat:
        return cat
    slug = category_name.lower().replace(" ", "-").replace("/", "-")
    cat = Category(name=category_name, slug=slug, sort_order=99)
    db.add(cat)
    db.flush()  # Get ID without committing
    return cat


def import_legacy_data():
    """ Main import function """
    # Ensure DB schema is up to date
    run_migrations()

    legacy_path = get_legacy_file_path()
    if not os.path.exists(legacy_path):
        print(f"[ERROR] Legacy file not found at: {legacy_path}")
        print("Make sure legacy/tracker_data.json exists.")
        return

    print(f"[INFO] Loading legacy data from: {legacy_path}")

    with open(legacy_path, "r", encoding="utf-8") as f:
        try:
            legacy_data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"[ERROR] Failed to parse JSON: {e}")
            return

    if not isinstance(legacy_data, dict):
        print("[ERROR] Legacy JSON root is not an object; aborting.")
        return

    db: Session = SessionLocal()
    imported_users = 0
    imported_entries = 0

    try:
        for username, categories in legacy_data.items():
            if not isinstance(categories, dict):
                print(f"[WARN] Skipping user {username!r}: categories is not a dict")
                continue

            user = get_or_create_user(db, username)
            imported_users += 1

            for category, entries in categories.items():
                if not isinstance(entries, list):
                    print(
                        f"[WARN] Skipping category {category!r} for user {username!r}: entries is not a list"
                    )
                    continue

                # We allow unknown categories, but you could enforce DEFAULT_CATEGORIES here
                for entry_str in entries:
                    if not isinstance(entry_str, str):
                        print(
                            f"[WARN] Skipping non-string entry for user {username!r}, category {category!r}: {entry_str!r}"
                        )
                        continue

                    date_obj, details = parse_legacy_entry(entry_str)
                    if date_obj is None or details is None:
                        continue

                    cat = get_or_create_category(db, category)
                    entry = Entry(
                        user_id=user.id,
                        category_id=cat.id,
                        date=date_obj,
                        details=details,
                    )
                    db.add(entry)
                    imported_entries += 1

        db.commit()
    finally:
        db.close()

    print(f"[DONE] Imported {imported_users} users and {imported_entries} entries.")
    print("You can now query this data via the Atlas API.")
    if imported_users > 0:
        print(f"\n[IMPORTANT] Legacy users can log in with password: '{LEGACY_DEFAULT_PASSWORD}'")
        print("            They should change it after first login (change-password not yet implemented).")
    

if __name__ == "__main__":
    import_legacy_data()
