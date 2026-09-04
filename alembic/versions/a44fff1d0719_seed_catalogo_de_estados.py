"""seed catalogo de estados

Revision ID: a44fff1d0719
Revises:
Create Date: 2026-09-04 16:05:11.138307

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a44fff1d0719'
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

CATALOGO = [
    ("PENDIENTE", 1),
    ("EN_CURSO", 2),
    ("BLOQUEADA", 3),
    ("HECHA", 4),
]

def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "states",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.UniqueConstraint("code", name="uq_states_code"),
    )
    conn = op.get_bind()
    for code, sort_order in CATALOGO:
        conn.execute(
            sa.text(
                "INSERT INTO states (code, sort_order) VALUES (:code, :sort_order) "
                "ON CONFLICT (code) DO NOTHING"
            ),
            {"code": code, "sort_order": sort_order},
        )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("states")
