import subprocess
import sys

from sqlalchemy import text

from app.db import engine

REVISION_PROJECTS = "d5a2008b4631"
REVISION_PREVIA = "a44fff1d0719"
CODIGOS_ESTADOS = {"PENDIENTE", "EN_CURSO", "BLOQUEADA", "HECHA"}


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


def test_migracion_crea_tabla_projects():
    _alembic("upgrade", "head")

    assert _tabla_existe("projects") is True

    with engine.connect() as conn:
        columnas = {
            fila[0]: fila[1]
            for fila in conn.execute(
                text(
                    "SELECT column_name, is_nullable FROM information_schema.columns "
                    "WHERE table_name = 'projects'"
                )
            ).all()
        }
    assert set(columnas) == {"id", "name", "description"}
    assert columnas["name"] == "NO"
    assert columnas["description"] == "YES"


def test_downgrade_projects_deja_states_intacto():
    _alembic("upgrade", "head")
    # Revertir hasta la revisión previa a projects. No se usa "-1" porque
    # tasks se encadena por encima de projects; "-1" ya no la elimina.
    _alembic("downgrade", REVISION_PREVIA)

    assert _tabla_existe("projects") is False
    assert _tabla_existe("states") is True

    with engine.connect() as conn:
        codigos = conn.execute(text("SELECT code FROM states")).scalars().all()
        revision = conn.execute(
            text("SELECT version_num FROM alembic_version")
        ).scalar()
    assert set(codigos) == CODIGOS_ESTADOS
    assert revision == REVISION_PREVIA

    _alembic("upgrade", "head")
