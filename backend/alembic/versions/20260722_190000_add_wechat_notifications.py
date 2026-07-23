"""add WeChat login and subscription notifications

Revision ID: 20260722_190000
Revises: 20260722_180000
Create Date: 2026-07-22 19:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "20260722_190000"
down_revision: str | None = "20260722_180000"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("wechat_openid", sa.String(length=128), nullable=True))
    op.add_column("users", sa.Column("wechat_unionid", sa.String(length=128), nullable=True))
    op.create_index("ix_users_wechat_openid", "users", ["wechat_openid"], unique=True)
    op.create_index("ix_users_wechat_unionid", "users", ["wechat_unionid"], unique=False)

    op.create_table(
        "wechat_subscriptions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=40), nullable=False),
        sa.Column("available_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id", "event_type", name="uq_wechat_subscriptions_user_event"
        ),
    )
    op.create_index(
        "ix_wechat_subscriptions_user_id", "wechat_subscriptions", ["user_id"], unique=False
    )

    op.create_table(
        "wechat_notifications",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("recipient_id", sa.Integer(), nullable=False),
        sa.Column("meal_order_id", sa.Integer(), nullable=True),
        sa.Column("event_type", sa.String(length=40), nullable=False),
        sa.Column("template_id", sa.String(length=128), nullable=False),
        sa.Column("page", sa.String(length=255), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("attempt_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("error_message", sa.String(length=500), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["meal_order_id"], ["meal_orders.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["recipient_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_wechat_notifications_meal_order_id",
        "wechat_notifications",
        ["meal_order_id"],
        unique=False,
    )
    op.create_index(
        "ix_wechat_notifications_recipient_id",
        "wechat_notifications",
        ["recipient_id"],
        unique=False,
    )
    op.create_index(
        "ix_wechat_notifications_status", "wechat_notifications", ["status"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_wechat_notifications_status", table_name="wechat_notifications")
    op.drop_index("ix_wechat_notifications_recipient_id", table_name="wechat_notifications")
    op.drop_index("ix_wechat_notifications_meal_order_id", table_name="wechat_notifications")
    op.drop_table("wechat_notifications")
    op.drop_index("ix_wechat_subscriptions_user_id", table_name="wechat_subscriptions")
    op.drop_table("wechat_subscriptions")
    op.drop_index("ix_users_wechat_unionid", table_name="users")
    op.drop_index("ix_users_wechat_openid", table_name="users")
    op.drop_column("users", "wechat_unionid")
    op.drop_column("users", "wechat_openid")
