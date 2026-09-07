from sqlalchemy import text

from app.db import engine


def test_puede_conectar_a_postgres():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        assert result.scalar() == 1
