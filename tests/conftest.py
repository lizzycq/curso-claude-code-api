import pytest
from sqlalchemy import text

from app.db import engine

# Los tests de projects escriben en la base. Se asume que la migración de
# projects (d5a2008b4631) ya está aplicada, igual que hoy se asume la de
# states para tests/test_states.py. Si se corre pytest sin `alembic upgrade
# head` previo, este fixture falla en el TRUNCATE.


@pytest.fixture(autouse=True)
def _limpia_projects():
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE projects RESTART IDENTITY CASCADE"))
    yield
