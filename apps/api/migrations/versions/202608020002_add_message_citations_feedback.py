from __future__ import annotations

"""add message citations and feedback

Revision ID: 202608020002
Revises: 202608020001
Create Date: 2026-08-02 00:02:00
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "202608020002"
down_revision: str | None = "202608020001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "message_citations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("message_id", sa.UUID(), nullable=False),
        sa.Column("chunk_id", sa.UUID(), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("similarity_score", sa.Float(), nullable=False),
        sa.Column("quoted_text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["chunk_id"], ["document_chunks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["message_id"], ["messages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_message_citations_chunk_id", "message_citations", ["chunk_id"])
    op.create_index("ix_message_citations_message_id", "message_citations", ["message_id"])

    op.create_table(
        "message_feedback",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("message_id", sa.UUID(), nullable=False),
        sa.Column("rating", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("rating IN ('positive', 'negative')", name="ck_message_feedback_rating"),
        sa.ForeignKeyConstraint(["message_id"], ["messages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("message_id", name="uq_message_feedback_message_id"),
    )
    op.create_index("ix_message_feedback_message_id", "message_feedback", ["message_id"])


def downgrade() -> None:
    op.drop_index("ix_message_feedback_message_id", table_name="message_feedback")
    op.drop_table("message_feedback")
    op.drop_index("ix_message_citations_message_id", table_name="message_citations")
    op.drop_index("ix_message_citations_chunk_id", table_name="message_citations")
    op.drop_table("message_citations")
