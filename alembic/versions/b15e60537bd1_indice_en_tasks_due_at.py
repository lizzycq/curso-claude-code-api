"""indice en tasks.due_at

Revision ID: b15e60537bd1
Revises: 2a9e2f058eef
Create Date: 2026-09-09 00:00:00.000000

"""
from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'b15e60537bd1'
down_revision: str | Sequence[str] | None = '2a9e2f058eef'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_index("ix_tasks_due_at", "tasks", ["due_at"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_tasks_due_at", table_name="tasks")
