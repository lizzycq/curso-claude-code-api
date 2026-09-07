from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import Project, State
from app.schemas import ProjectIn, ProjectOut, ProjectUpdate

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


def _get_project_or_404(session: Session, project_id: int) -> Project:
    proyecto = session.get(Project, project_id)
    if proyecto is None:
        raise HTTPException(status_code=404, detail="proyecto no encontrado")
    return proyecto


@app.get("/projects/{project_id}")
def get_project(project_id: int) -> ProjectOut:
    with SessionLocal() as session:
        return _a_project_out(_get_project_or_404(session, project_id))


@app.patch("/projects/{project_id}")
def update_project(project_id: int, payload: ProjectUpdate) -> ProjectOut:
    with SessionLocal() as session:
        proyecto = _get_project_or_404(session, project_id)
        datos = payload.model_dump(exclude_unset=True)
        if "name" in datos:
            proyecto.name = datos["name"]
        if "description" in datos:
            proyecto.description = datos["description"]
        session.commit()
        session.refresh(proyecto)
        return _a_project_out(proyecto)


@app.delete("/projects/{project_id}", status_code=204)
def delete_project(project_id: int) -> None:
    with SessionLocal() as session:
        proyecto = _get_project_or_404(session, project_id)
        session.delete(proyecto)
        session.commit()
