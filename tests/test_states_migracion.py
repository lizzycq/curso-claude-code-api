import subprocess
import sys

from sqlalchemy import text

from app.db import engine

CODIGOS_ESPERADOS = {"PENDIENTE", "EN_CURSO", "BLOQUEADA", "HECHA"}


def _alembic(*args: str) -> None:
    subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        check=True,
        capture_output=True,
        text=True,
    )


def test_migracion_siembra_catalogo_de_estados_de_forma_idempotente():
    _alembic("downgrade", "base")

    _alembic("upgrade", "head")
    with engine.connect() as conn:
        filas = conn.execute(text("SELECT code FROM states")).scalars().all()
    assert set(filas) == CODIGOS_ESPERADOS
    assert len(filas) == len(CODIGOS_ESPERADOS)

    _alembic("upgrade", "head")
    with engine.connect() as conn:
        filas = conn.execute(text("SELECT code FROM states")).scalars().all()
    assert set(filas) == CODIGOS_ESPERADOS
    assert len(filas) == len(CODIGOS_ESPERADOS)


def test_downgrade_elimina_tabla_states():
    _alembic("upgrade", "head")
    _alembic("downgrade", "base")
    with engine.connect() as conn:
        existe = conn.execute(
            text(
                "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
                "WHERE table_name = 'states')"
            )
        ).scalar()
    assert existe is False

    _alembic("upgrade", "head")
