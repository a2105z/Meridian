"""
API tests for Atlas auth and me-scoped routes.
"""

from __future__ import annotations

import os
from datetime import date

import pytest
from fastapi.testclient import TestClient

# Isolate test DB before importing the app
os.environ["FLUID_DATABASE_URL"] = "sqlite:///./test_fluid.db"
os.environ["FLUID_SECRET_KEY"] = "test-secret-key"
os.environ.pop("ATLAS_DATABASE_URL", None)
os.environ.pop("ATLAS_SECRET_KEY", None)

from app import app  # noqa: E402
from database import Base, engine  # noqa: E402


@pytest.fixture(autouse=True)
def fresh_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    # seed categories expected by create entry
    from sqlalchemy.orm import Session
    from models import Category
    from seed_categories import DEFAULT_CATEGORIES

    with Session(engine) as db:
        for name, slug, sort_order in DEFAULT_CATEGORIES:
            if not db.query(Category).filter(Category.name == name).first():
                db.add(Category(name=name, slug=slug, sort_order=sort_order))
        db.commit()
    yield


@pytest.fixture
def client():
    return TestClient(app)


def register(client, username="alice", password="password123"):
    return client.post(
        "/auth/register",
        json={
            "username": username,
            "first_name": "Alice",
            "last_name": "Test",
            "birthday": "2005-01-15",
            "password": password,
        },
    )


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] in {"ok", "degraded"}


def test_register_login_and_me(client):
    r = register(client)
    assert r.status_code == 200
    body = r.json()
    assert "access_token" in body
    assert body["user"]["username"] == "alice"

    me = client.get("/auth/me", headers=auth_header(body["access_token"]))
    assert me.status_code == 200
    assert me.json()["username"] == "alice"

    login = client.post("/auth/login", json={"username": "alice", "password": "password123"})
    assert login.status_code == 200
    assert "access_token" in login.json()


def test_unauthenticated_me_routes_rejected(client):
    assert client.get("/me/entries").status_code == 401
    assert client.get("/me/reports/activity-summary").status_code == 401
    assert client.get("/me/export").status_code == 401


def test_entry_crud_scoped_to_user(client):
    a = register(client, "alice", "password123").json()
    b = register(client, "bob", "password123").json()

    created = client.post(
        "/me/entries",
        headers=auth_header(a["access_token"]),
        json={
            "category": "GPA",
            "date": str(date.today()),
            "details": "3.9 unweighted",
        },
    )
    assert created.status_code == 201
    entry_id = created.json()["id"]

    # Bob cannot see Alice's entry
    bob_list = client.get("/me/entries", headers=auth_header(b["access_token"]))
    assert bob_list.status_code == 200
    assert bob_list.json()["total_count"] == 0

    alice_get = client.get(f"/me/entries/{entry_id}", headers=auth_header(a["access_token"]))
    assert alice_get.status_code == 200

    bob_get = client.get(f"/me/entries/{entry_id}", headers=auth_header(b["access_token"]))
    assert bob_get.status_code == 404


def test_export_requires_auth(client):
    token = register(client).json()["access_token"]
    client.post(
        "/me/entries",
        headers=auth_header(token),
        json={"category": "GPA", "date": "2024-01-01", "details": "4.0"},
    )
    r = client.get("/me/export?format=json", headers=auth_header(token))
    assert r.status_code == 200
    assert "entries" in r.json()
