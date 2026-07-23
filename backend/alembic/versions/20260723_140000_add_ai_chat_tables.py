"""add ai chat tables

Revision ID: 20260723_140000
Revises: 20260723_100000
Create Date: 2026-07-23 14:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260723_140000"
down_revision: str | None = "20260723_100000"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ai_chat_messages",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("family_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("message_kind", sa.String(length=30), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["family_id"], ["families.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_ai_chat_messages_family_user_id",
        "ai_chat_messages",
        ["family_id", "user_id", "id"],
        unique=False,
    )

    op.create_table(
        "fridge_image_analyses",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("family_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("image_url", sa.String(length=500), nullable=False),
        sa.Column("recognized_ingredients_json", sa.JSON(), nullable=False),
        sa.Column("raw_model_output", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["family_id"], ["families.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_fridge_image_analyses_family_user_id",
        "fridge_image_analyses",
        ["family_id", "user_id", "id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_fridge_image_analyses_family_user_id",
        table_name="fridge_image_analyses",
    )
    op.drop_table("fridge_image_analyses")
    op.drop_index("ix_ai_chat_messages_family_user_id", table_name="ai_chat_messages")
    op.drop_table("ai_chat_messages")
