import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    pass


def get_database_url() -> str:
    user = os.environ.get("POSTGRES_USER", "taskflow_dev")
    password = os.environ.get("POSTGRES_PASSWORD", "taskflow_dev_password")
    db = os.environ.get("POSTGRES_DB", "taskflow_dev")
    port = os.environ.get("POSTGRES_PORT", "5432")
    host = os.environ.get("POSTGRES_HOST", "localhost")
    return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{db}"


engine = create_engine(get_database_url())
SessionLocal = sessionmaker(bind=engine)
