"""crea tabla tasks

Revision ID: 2a9e2f058eef
Revises: d5a2008b4631
Create Date: 2026-09-07 19:40:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '2a9e2f058eef'
down_revision: str | Sequence[str] | None = 'd5a2008b4631'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "tasks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("state_id", sa.Integer(), nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["project_id"], ["projects.id"], name="fk_tasks_project_id"
        ),
        sa.ForeignKeyConstraint(
            ["state_id"], ["states.id"], name="fk_tasks_state_id"
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("tasks")
