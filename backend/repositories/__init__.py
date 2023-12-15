"""
Repository layer for Atlas backend.

Repositories centralize database access logic, keeping app.py focused on
HTTP concerns and schema serialization.
"""

from .user_repository import UserRepository
from .entry_repository import EntryRepository
from .report_repository import ReportRepository

__all__ = ["UserRepository", "EntryRepository", "ReportRepository"]
