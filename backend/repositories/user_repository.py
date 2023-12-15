"""
User repository: database operations for User entities.
"""

from typing import Optional

from sqlalchemy.orm import Session

from models import User


class UserRepository:
    """Centralizes User-related database queries."""

    @staticmethod
    def get_by_username(db: Session, username: str) -> Optional[User]:
        """Fetch a user by username, or None if not found."""
        return db.query(User).filter(User.username == username).first()

    @staticmethod
    def create(
        db: Session,
        username: str,
        first_name: str,
        last_name: str,
        birthday,
        password_hash: str,
    ) -> User:
        """Create a new user. Caller must handle uniqueness check."""
        user = User(
            username=username,
            first_name=first_name,
            last_name=last_name,
            birthday=birthday,
            password_hash=password_hash,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
