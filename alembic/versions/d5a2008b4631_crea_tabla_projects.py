"""crea tabla projects

Revision ID: d5a2008b4631
Revises: a44fff1d0719
Create Date: 2026-09-07 18:58:15.544440

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'd5a2008b4631'
down_revision: str | Sequence[str] | None = 'a44fff1d0719'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "projects",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("projects")
