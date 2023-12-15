"""
Atlas authentication: bcrypt password hashing + JWT bearer tokens.
"""

from __future__ import annotations

import hashlib
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from database import get_db
from models import User
from repositories import UserRepository

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)

SECRET_KEY = (
    os.getenv("MERIDIAN_SECRET_KEY")
    or os.getenv("FLUID_SECRET_KEY")
    or os.getenv("ATLAS_SECRET_KEY", "meridian-dev-secret-change-me")
)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("MERIDIAN_TOKEN_EXPIRE_MINUTES")
    or os.getenv("FLUID_TOKEN_EXPIRE_MINUTES")
    or os.getenv("ATLAS_TOKEN_EXPIRE_MINUTES", "10080")
)


def hash_password(raw: str) -> str:
    return pwd_context.hash(raw)


def _is_legacy_sha256(stored: str) -> bool:
    return len(stored) == 64 and all(c in "0123456789abcdef" for c in stored.lower())


def verify_password(raw: str, stored_hash: str) -> bool:
    if _is_legacy_sha256(stored_hash):
        return hashlib.sha256(raw.encode("utf-8")).hexdigest() == stored_hash
    return pwd_context.verify(raw, stored_hash)


def maybe_upgrade_password_hash(db: Session, user: User, raw_password: str) -> None:
    """Re-hash legacy SHA-256 passwords to bcrypt on successful login."""
    if _is_legacy_sha256(user.password_hash):
        user.password_hash = hash_password(raw_password)
        db.add(user)
        db.commit()
        db.refresh(user)


def create_access_token(*, subject: str, user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": subject, "uid": user_id, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: Optional[str] = payload.get("sub")
        user_id: Optional[int] = payload.get("uid")
        if not username or user_id is None:
            raise JWTError("missing claims")
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = UserRepository.get_by_username(db, username)
    if not user or user.id != user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user
