from fastapi import FastAPI
from pydantic import BaseModel
from sqlalchemy import select

from app.db import SessionLocal
from app.models import Project, State
from app.schemas import ProjectIn, ProjectOut

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


def _a_project_out(proyecto: Project) -> ProjectOut:
    return ProjectOut(
        id=proyecto.id,
        name=proyecto.name,
        description=proyecto.description,
    )


@app.post("/projects", status_code=201)
def create_project(payload: ProjectIn) -> ProjectOut:
    with SessionLocal() as session:
        proyecto = Project(name=payload.name, description=payload.description)
        session.add(proyecto)
        session.commit()
        session.refresh(proyecto)
        return _a_project_out(proyecto)


@app.get("/projects")
def list_projects() -> list[ProjectOut]:
    with SessionLocal() as session:
        proyectos = session.scalars(
            select(Project).order_by(Project.id)
        ).all()
        return [_a_project_out(proyecto) for proyecto in proyectos]
