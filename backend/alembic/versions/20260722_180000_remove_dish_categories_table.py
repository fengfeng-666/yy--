"""remove dish categories table

Revision ID: 20260722_180000
Revises: 20260722_170000
Create Date: 2026-07-22 18:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "20260722_180000"
down_revision: str | None = "20260722_170000"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint("dishes_category_id_fkey", "dishes", type_="foreignkey")
    op.drop_column("dishes", "category_id")
    op.drop_table("dish_categories")


def downgrade() -> None:
    op.create_table(
        "dish_categories",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("family_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["family_id"], ["families.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("family_id", "name", name="uq_dish_categories_family_name"),
    )
    op.add_column("dishes", sa.Column("category_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "dishes_category_id_fkey",
        "dishes",
        "dish_categories",
        ["category_id"],
        ["id"],
        ondelete="RESTRICT",
    )
