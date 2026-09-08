from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import Project, State, Task
from app.schemas import (
    ProjectIn,
    ProjectOut,
    ProjectUpdate,
    TaskIn,
    TaskOut,
    TaskUpdate,
)

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
        tiene_tareas = session.scalar(
            select(Task.id).where(Task.project_id == project_id).limit(1)
        )
        if tiene_tareas is not None:
            raise HTTPException(
                status_code=409,
                detail="el proyecto tiene tareas y no se puede borrar",
            )
        session.delete(proyecto)
        session.commit()


def _a_task_out(tarea: Task) -> TaskOut:
    return TaskOut(
        id=tarea.id,
        title=tarea.title,
        description=tarea.description,
        project_id=tarea.project_id,
        state_id=tarea.state_id,
        due_at=tarea.due_at,
    )


def _validar_referencias(session: Session, project_id: int, state_id: int) -> None:
    if session.get(Project, project_id) is None:
        raise HTTPException(status_code=404, detail="proyecto no encontrado")
    if session.get(State, state_id) is None:
        raise HTTPException(status_code=404, detail="estado no encontrado")


def _get_task_or_404(session: Session, task_id: int) -> Task:
    tarea = session.get(Task, task_id)
    if tarea is None:
        raise HTTPException(status_code=404, detail="tarea no encontrada")
    return tarea


@app.post("/tasks", status_code=201)
def create_task(payload: TaskIn) -> TaskOut:
    with SessionLocal() as session:
        _validar_referencias(session, payload.project_id, payload.state_id)
        tarea = Task(
            title=payload.title,
            description=payload.description,
            project_id=payload.project_id,
            state_id=payload.state_id,
            due_at=payload.due_at,
        )
        session.add(tarea)
        session.commit()
        session.refresh(tarea)
        return _a_task_out(tarea)


@app.get("/tasks")
def list_tasks(
    project_id: int | None = None, state_id: int | None = None
) -> list[TaskOut]:
    with SessionLocal() as session:
        consulta = select(Task)
        if project_id is not None:
            consulta = consulta.where(Task.project_id == project_id)
        if state_id is not None:
            consulta = consulta.where(Task.state_id == state_id)
        tareas = session.scalars(consulta.order_by(Task.id)).all()
        return [_a_task_out(tarea) for tarea in tareas]


@app.get("/tasks/{task_id}")
def get_task(task_id: int) -> TaskOut:
    with SessionLocal() as session:
        return _a_task_out(_get_task_or_404(session, task_id))


@app.patch("/tasks/{task_id}")
def update_task(task_id: int, payload: TaskUpdate) -> TaskOut:
    with SessionLocal() as session:
        tarea = _get_task_or_404(session, task_id)
        datos = payload.model_dump(exclude_unset=True)
        nuevo_project_id = datos.get("project_id", tarea.project_id)
        nuevo_state_id = datos.get("state_id", tarea.state_id)
        if "project_id" in datos or "state_id" in datos:
            _validar_referencias(session, nuevo_project_id, nuevo_state_id)
        for campo in ("title", "description", "project_id", "state_id", "due_at"):
            if campo in datos:
                setattr(tarea, campo, datos[campo])
        session.commit()
        session.refresh(tarea)
        return _a_task_out(tarea)


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int) -> None:
    with SessionLocal() as session:
        tarea = _get_task_or_404(session, task_id)
        session.delete(tarea)
        session.commit()
