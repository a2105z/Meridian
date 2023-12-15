"""Normalize categories table, add updated_at, improve constraints.

Revision ID: 002_normalize
Revises: 001_initial
Create Date: 2025-02-03

- Creates categories table with default seed data
- Adds category_id FK to entries, migrates from category string
- Drops category column
- Adds updated_at to users and entries
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002_normalize"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Default categories: (name, slug, sort_order)
DEFAULT_CATEGORIES = [
    ("Awards & Honors", "awards-honors", 1),
    ("Professional Experiences", "professional-experiences", 2),
    ("Summer Programs", "summer-programs", 3),
    ("SAT/ACT/SATII/ACTII Scores", "sat-act-scores", 4),
    ("AP Scores", "ap-scores", 5),
    ("GPA", "gpa", 6),
    ("Future Plans & Competitions", "future-plans", 7),
    ("Personal Goals", "personal-goals", 8),
    ("Reflection Journal", "reflection-journal", 9),
]


def upgrade() -> None:
    # 1. Create categories table
    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_categories_name"),
        sa.UniqueConstraint("slug", name="uq_categories_slug"),
    )
    op.create_index(op.f("ix_categories_id"), "categories", ["id"], unique=False)
    op.create_index(op.f("ix_categories_slug"), "categories", ["slug"], unique=True)

    # 2. Seed default categories
    categories_table = sa.table(
        "categories",
        sa.column("id", sa.Integer),
        sa.column("name", sa.String),
        sa.column("slug", sa.String),
        sa.column("sort_order", sa.Integer),
    )
    op.bulk_insert(
        categories_table,
        [
            {"id": i, "name": name, "slug": slug, "sort_order": sort_order}
            for i, (name, slug, sort_order) in enumerate(DEFAULT_CATEGORIES, start=1)
        ],
    )

    # 3. Add category_id and updated_at to entries (nullable for migration)
    op.add_column("entries", sa.Column("category_id", sa.Integer(), nullable=True))
    op.add_column("entries", sa.Column("updated_at", sa.DateTime(), nullable=True))
    op.add_column("users", sa.Column("updated_at", sa.DateTime(), nullable=True))

    # 4. Data migration: set category_id from category string
    conn = op.get_bind()
    result = conn.execute(sa.text("SELECT id, category FROM entries"))
    rows = result.fetchall()
    for entry_id, category_name in rows:
        cat_result = conn.execute(
            sa.text("SELECT id FROM categories WHERE name = :name"),
            {"name": category_name},
        )
        cat_row = cat_result.fetchone()
        if cat_row:
            conn.execute(
                sa.text("UPDATE entries SET category_id = :cid WHERE id = :eid"),
                {"cid": cat_row[0], "eid": entry_id},
            )
        else:
            # Unknown category: create it
            slug = category_name.lower().replace(" ", "-").replace("/", "-")
            conn.execute(
                sa.text(
                    "INSERT INTO categories (name, slug, sort_order) VALUES (:name, :slug, 99)"
                ),
                {"name": category_name, "slug": slug},
            )
            new_id = conn.execute(sa.text("SELECT last_insert_rowid()")).scalar()
            conn.execute(
                sa.text("UPDATE entries SET category_id = :cid WHERE id = :eid"),
                {"cid": new_id, "eid": entry_id},
            )

    # 5. Backfill updated_at = created_at
    conn.execute(sa.text("UPDATE entries SET updated_at = created_at WHERE updated_at IS NULL"))
    conn.execute(sa.text("UPDATE users SET updated_at = created_at WHERE updated_at IS NULL"))

    # 6. Use batch_alter_table for SQLite compatibility (drop column, alter nullable)
    with op.batch_alter_table("entries", schema=None) as batch_op:
        batch_op.drop_index("ix_entries_category")
        batch_op.drop_column("category")
        batch_op.alter_column(
            "category_id",
            existing_type=sa.Integer(),
            nullable=False,
        )
        batch_op.alter_column(
            "updated_at",
            existing_type=sa.DateTime(),
            nullable=False,
        )
        batch_op.create_foreign_key(
            "fk_entries_category_id_categories",
            "categories",
            ["category_id"],
            ["id"],
            ondelete="RESTRICT",
        )
        batch_op.create_index("ix_entries_category_id", ["category_id"], unique=False)

    # 7. Make users.updated_at NOT NULL (SQLite: use batch)
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.alter_column(
            "updated_at",
            existing_type=sa.DateTime(),
            nullable=False,
        )


def downgrade() -> None:
    # Reverse the migration - complex, simplified for development
    op.drop_constraint("fk_entries_category_id_categories", "entries", type_="foreignkey")
    op.drop_index(op.f("ix_entries_category_id"), table_name="entries")

    op.add_column("entries", sa.Column("category", sa.String(), nullable=True))

    # Migrate category_id back to category string
    conn = op.get_bind()
    result = conn.execute(sa.text("SELECT e.id, c.name FROM entries e JOIN categories c ON e.category_id = c.id"))
    for entry_id, cat_name in result.fetchall():
        conn.execute(sa.text("UPDATE entries SET category = :name WHERE id = :eid"), {"name": cat_name, "eid": entry_id})

    op.alter_column("entries", "category", nullable=False)
    op.create_index(op.f("ix_entries_category"), "entries", ["category"], unique=False)

    op.drop_column("entries", "category_id")
    op.drop_column("entries", "updated_at")
    op.drop_column("users", "updated_at")

    op.drop_index(op.f("ix_categories_slug"), table_name="categories")
    op.drop_index(op.f("ix_categories_id"), table_name="categories")
    op.drop_table("categories")
