"""Create candidates table.

Revision ID: 0001
Revises: -
Create Date: 2026-05-28
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the ``candidates`` table with all columns."""
    op.create_table(
        "candidates",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("first_name", sa.String(255), nullable=False),
        sa.Column("last_name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(320), nullable=False, unique=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("linkedin_url", sa.String(2048), nullable=True),
        sa.Column("github_url", sa.String(2048), nullable=True),
        sa.Column("experience_summary", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    """Drop the ``candidates`` table."""
    op.drop_table("candidates")
