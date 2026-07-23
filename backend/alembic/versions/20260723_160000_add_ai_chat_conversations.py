"""add ai chat conversations

Revision ID: 20260723_160000
Revises: 20260723_140000
Create Date: 2026-07-23 16:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260723_160000"
down_revision: str | None = "20260723_140000"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ai_chat_conversations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("family_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column(
            "title",
            sa.String(length=100),
            nullable=False,
            server_default=sa.text("'新对话'"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["family_id"], ["families.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_ai_chat_conversations_family_user_updated_at",
        "ai_chat_conversations",
        ["family_id", "user_id", "updated_at"],
        unique=False,
    )

    op.add_column("ai_chat_messages", sa.Column("conversation_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_ai_chat_messages_conversation_id",
        "ai_chat_messages",
        "ai_chat_conversations",
        ["conversation_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.execute(
        sa.text(
            """
            INSERT INTO ai_chat_conversations (family_id, user_id, title, created_at, updated_at)
            SELECT
                family_id,
                user_id,
                '历史对话',
                MIN(created_at),
                MAX(created_at)
            FROM ai_chat_messages
            GROUP BY family_id, user_id
            """
        )
    )
    op.execute(
        sa.text(
            """
            UPDATE ai_chat_messages AS message
            SET conversation_id = conversation.id
            FROM ai_chat_conversations AS conversation
            WHERE message.family_id = conversation.family_id
              AND message.user_id = conversation.user_id
              AND message.conversation_id IS NULL
            """
        )
    )

    op.alter_column("ai_chat_messages", "conversation_id", nullable=False)
    op.drop_index("ix_ai_chat_messages_family_user_id", table_name="ai_chat_messages")
    op.create_index(
        "ix_ai_chat_messages_family_user_conversation_id",
        "ai_chat_messages",
        ["family_id", "user_id", "conversation_id", "id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_ai_chat_messages_family_user_conversation_id", table_name="ai_chat_messages")
    op.create_index(
        "ix_ai_chat_messages_family_user_id",
        "ai_chat_messages",
        ["family_id", "user_id", "id"],
        unique=False,
    )
    op.drop_constraint("fk_ai_chat_messages_conversation_id", "ai_chat_messages", type_="foreignkey")
    op.drop_column("ai_chat_messages", "conversation_id")
    op.drop_index(
        "ix_ai_chat_conversations_family_user_updated_at",
        table_name="ai_chat_conversations",
    )
    op.drop_table("ai_chat_conversations")
