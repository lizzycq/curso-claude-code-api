import pytest
from sqlalchemy import text

from app.db import engine

# Los tests de projects y tasks escriben en la base. Se asume que las
# migraciones ya están aplicadas, igual que hoy se asume la de states para
# tests/test_states.py.
#
# Los tests de migración (test_*_migracion.py) hacen downgrade/upgrade y
# pueden dejar la base sin `tasks` momentáneamente entre casos; por eso el
# fixture trunca solo las tablas que existen en ese momento.

_TABLAS_ESCRIBIBLES = ("tasks", "projects")


@pytest.fixture(autouse=True)
def _limpia_tablas_escribibles():
    with engine.begin() as conn:
        existentes = [
            tabla
            for tabla in _TABLAS_ESCRIBIBLES
            if conn.execute(
                text(
                    "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
                    "WHERE table_name = :nombre)"
                ),
                {"nombre": tabla},
            ).scalar()
        ]
        if existentes:
            conn.execute(
                text(
                    f"TRUNCATE {', '.join(existentes)} RESTART IDENTITY CASCADE"
                )
            )
    yield
