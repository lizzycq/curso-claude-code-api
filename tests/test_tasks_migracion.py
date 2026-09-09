import subprocess
import sys

from sqlalchemy import text

from app.db import engine

REVISION_TASKS = "2a9e2f058eef"
REVISION_PREVIA = "d5a2008b4631"


def _alembic(*args: str) -> None:
    subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        check=True,
        capture_output=True,
        text=True,
    )


def _tabla_existe(nombre: str) -> bool:
    with engine.connect() as conn:
        return conn.execute(
            text(
                "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
                "WHERE table_name = :nombre)"
            ),
            {"nombre": nombre},
        ).scalar()


def test_migracion_crea_tabla_tasks():
    _alembic("upgrade", "head")

    assert _tabla_existe("tasks") is True

    with engine.connect() as conn:
        columnas = {
            fila[0]: fila[1]
            for fila in conn.execute(
                text(
                    "SELECT column_name, data_type FROM information_schema.columns "
                    "WHERE table_name = 'tasks'"
                )
            ).all()
        }
        fks = conn.execute(
            text(
                "SELECT constraint_name FROM information_schema.table_constraints "
                "WHERE table_name = 'tasks' AND constraint_type = 'FOREIGN KEY'"
            )
        ).scalars().all()
    assert set(columnas) == {
        "id",
        "title",
        "description",
        "project_id",
        "state_id",
        "due_at",
    }
    assert columnas["due_at"] == "timestamp with time zone"
    assert set(fks) == {"fk_tasks_project_id", "fk_tasks_state_id"}


def test_downgrade_tasks_deja_projects_y_states_intactos():
    _alembic("upgrade", "head")
    _alembic("downgrade", "-1")

    assert _tabla_existe("tasks") is False
    assert _tabla_existe("projects") is True
    assert _tabla_existe("states") is True

    with engine.connect() as conn:
        revision = conn.execute(
            text("SELECT version_num FROM alembic_version")
        ).scalar()
    assert revision == REVISION_PREVIA

    _alembic("upgrade", "head")
