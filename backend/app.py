"""
Fluid API — secure academic journey tracker.

Auth: JWT bearer tokens. User data is scoped to /me/* to prevent IDOR.
"""

from __future__ import annotations

import csv
import io
import logging
import time
import uuid
from datetime import date
from typing import List, Literal, Optional

from fastapi import Depends, FastAPI, HTTPException, Query, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

import schemas
from auth import (
    create_access_token,
    get_current_user,
    hash_password,
    maybe_upgrade_password_hash,
    verify_password,
)
from database import get_db, run_migrations
from models import Entry, User
from repositories import EntryRepository, ReportRepository, UserRepository

logger = logging.getLogger("fluid")
logging.basicConfig(level=logging.INFO)

run_migrations()

app = FastAPI(
    title="Meridian API",
    description="Academic journey tracker — accounts, entries, analytics, export",
    version="4.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:[0-9]+)?$",
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    started = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - started) * 1000
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time"] = f"{elapsed_ms:.1f}ms"
    if request.url.path not in {"/health", "/"}:
        logger.info("%s %s -> %s (%.1fms)", request.method, request.url.path, response.status_code, elapsed_ms)
    return response


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Validation failed", "errors": exc.errors()},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception):
    if isinstance(exc, HTTPException):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
    logger.exception("Unhandled error: %s", exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


def _entry_to_out(entry: Entry) -> schemas.EntryOut:
    return schemas.EntryOut(
        id=entry.id,
        user_id=entry.user_id,
        category=entry.category_rel.name if entry.category_rel else "",
        date=entry.date,
        details=entry.details,
        created_at=entry.created_at,
    )


@app.get("/", tags=["Health"])
def root():
    return {"message": "Meridian API", "docs": "/docs", "version": "4.0.0"}


@app.get("/health", response_model=schemas.HealthResponse, tags=["Health"])
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return schemas.HealthResponse(status="ok", database="ok")
    except Exception:
        return schemas.HealthResponse(status="degraded", database="error")


@app.post("/auth/register", response_model=schemas.TokenResponse, tags=["Auth"])
def register(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = UserRepository.get_by_username(db, user_in.username)
    if existing:
        raise HTTPException(status_code=400, detail="Username already taken")

    user = UserRepository.create(
        db,
        username=user_in.username,
        first_name=user_in.first_name,
        last_name=user_in.last_name,
        birthday=user_in.birthday,
        password_hash=hash_password(user_in.password),
    )
    token = create_access_token(subject=user.username, user_id=user.id)
    return schemas.TokenResponse(access_token=token, user=user)


@app.post("/auth/login", response_model=schemas.TokenResponse, tags=["Auth"])
def login(user_in: schemas.UserLogin, db: Session = Depends(get_db)):
    user = UserRepository.get_by_username(db, user_in.username)
    if not user or not verify_password(user_in.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    maybe_upgrade_password_hash(db, user, user_in.password)
    token = create_access_token(subject=user.username, user_id=user.id)
    return schemas.TokenResponse(access_token=token, user=user)


@app.get("/auth/me", response_model=schemas.UserOut, tags=["Auth"])
def me(current_user: User = Depends(get_current_user)):
    return current_user


@app.get("/me/categories", response_model=List[str], tags=["Entries"])
def get_categories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ReportRepository.get_categories(db)


@app.get("/me/entries", response_model=schemas.EntryListResponse, tags=["Entries"])
def list_entries(
    category: Optional[str] = None,
    search: Optional[str] = None,
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    sort: Literal["date", "category", "created_at"] = "date",
    order: Literal["asc", "desc"] = "asc",
    limit: Optional[int] = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if from_date and to_date and from_date > to_date:
        raise HTTPException(status_code=400, detail="`from` must be on or before `to`")

    entries, total_count = EntryRepository.list_entries(
        db,
        current_user.id,
        category=category,
        search=search,
        from_date=from_date,
        to_date=to_date,
        sort=sort,
        order=order,
        limit=limit,
        offset=offset,
    )
    return schemas.EntryListResponse(
        entries=[_entry_to_out(e) for e in entries],
        total_count=total_count,
    )


@app.get("/me/entries/{entry_id}", response_model=schemas.EntryOut, tags=["Entries"])
def get_entry(
    entry_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    entry = EntryRepository.get_by_id(db, current_user.id, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    return _entry_to_out(entry)


@app.post("/me/entries", response_model=schemas.EntryOut, status_code=status.HTTP_201_CREATED, tags=["Entries"])
def create_entry(
    entry_in: schemas.EntryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    category = ReportRepository.get_category_by_name(db, entry_in.category)
    if not category:
        raise HTTPException(status_code=400, detail=f"Invalid category: '{entry_in.category}'.")
    entry = EntryRepository.create(
        db,
        user_id=current_user.id,
        category_id=category.id,
        date_val=entry_in.date,
        details=entry_in.details,
    )
    return _entry_to_out(entry)


@app.patch("/me/entries/{entry_id}", response_model=schemas.EntryOut, tags=["Entries"])
def update_entry(
    entry_id: int,
    entry_in: schemas.EntryUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    entry = EntryRepository.get_by_id(db, current_user.id, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    category_id = None
    if entry_in.category is not None:
        category = ReportRepository.get_category_by_name(db, entry_in.category)
        if not category:
            raise HTTPException(status_code=400, detail=f"Invalid category: '{entry_in.category}'.")
        category_id = category.id

    entry = EntryRepository.update(
        db,
        entry,
        category_id=category_id,
        date_val=entry_in.date,
        details=entry_in.details,
    )
    return _entry_to_out(entry)


@app.delete("/me/entries/{entry_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Entries"])
def delete_entry(
    entry_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    entry = EntryRepository.get_by_id(db, current_user.id, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    EntryRepository.delete(db, entry)
    return None


@app.get("/me/analytics/summary", response_model=schemas.AnalyticsSummary, tags=["Analytics"])
def analytics_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = ReportRepository.analytics_summary(db, current_user.id)
    return schemas.AnalyticsSummary(username=current_user.username, **data)


@app.get("/me/reports/timeline", response_model=schemas.TimelineReport, tags=["Reports"])
def report_timeline(
    group_by: Literal["month", "quarter"] = "month",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = ReportRepository.timeline_report(db, current_user.id, group_by=group_by)
    groups = [schemas.TimelineGroup(period=p, count=c) for p, c in rows]
    return schemas.TimelineReport(username=current_user.username, group_by=group_by, groups=groups)


@app.get("/me/reports/by-category", response_model=schemas.ByCategoryReport, tags=["Reports"])
def report_by_category(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    by_category = ReportRepository.by_category_report(db, current_user.id)
    return schemas.ByCategoryReport(username=current_user.username, by_category=by_category)


@app.get("/me/reports/activity-summary", response_model=schemas.ActivitySummaryReport, tags=["Reports"])
def report_activity_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = ReportRepository.activity_summary_report(db, current_user.id)
    timeline = [schemas.TimelineGroup(period=t["period"], count=t["count"]) for t in data["timeline_by_month"]]
    return schemas.ActivitySummaryReport(
        username=current_user.username,
        total_entries=data["total_entries"],
        first_entry_date=data["first_entry_date"],
        last_entry_date=data["last_entry_date"],
        entries_per_category=data["entries_per_category"],
        timeline_by_month=timeline,
    )


@app.get("/me/export", tags=["Export"])
def export_user_data(
    format: Literal["csv", "json"] = Query("json", alias="format"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = EntryRepository.export_entries(db, current_user.id)
    username = current_user.username

    if format == "json":
        data = [
            {
                "id": e.id,
                "category": cat_name,
                "date": e.date.isoformat(),
                "details": e.details,
                "created_at": e.created_at.isoformat(),
            }
            for e, cat_name in rows
        ]
        return JSONResponse(content={"username": username, "entries": data})

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["category", "date", "details", "created_at"])
    for e, cat_name in rows:
        writer.writerow(
            [
                cat_name,
                e.date.isoformat() if e.date else "",
                e.details or "",
                e.created_at.isoformat() if e.created_at else "",
            ]
        )
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=meridian_export_{username}.csv"},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
