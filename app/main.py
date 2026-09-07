from fastapi import FastAPI
from pydantic import BaseModel
from sqlalchemy import select

from app.db import SessionLocal
from app.models import State

app = FastAPI(title="TaskFlow API")


class StateOut(BaseModel):
    id: int
    code: str


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/states")
def list_states() -> list[StateOut]:
    with SessionLocal() as session:
        estados = session.scalars(
            select(State).order_by(State.sort_order, State.id)
        ).all()
        return [StateOut(id=estado.id, code=estado.code) for estado in estados]
