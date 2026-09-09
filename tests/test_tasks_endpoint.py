"""Smoke tests en vivo contra la API corriendo en http://127.0.0.1:8000.

No sustituyen a tests/test_tasks.py (matriz completa, in-process): solo
comprueban de un vistazo que los endpoints desplegados responden. Se saltan si
la API no está levantada.
"""
import httpx2 as httpx
import pytest

BASE_URL = "http://127.0.0.1:8000"
CAMPOS_TASK = {"id", "title", "description", "project_id", "state_id", "due_at"}


def _api_disponible() -> bool:
    try:
        httpx.get(f"{BASE_URL}/health", timeout=1.0)
        return True
    except httpx.HTTPError:
        return False


pytestmark = pytest.mark.skipif(
    not _api_disponible(),
    reason=f"la API no está corriendo en {BASE_URL}",
)


@pytest.fixture
def client():
    with httpx.Client(base_url=BASE_URL, timeout=5.0) as c:
        yield c


@pytest.fixture
def project_id(client):
    return client.post("/projects", json={"name": "Casa"}).json()["id"]


def test_recorrido_feliz_crear_leer_patch_borrar(client, project_id):
    creada = client.post(
        "/tasks",
        json={"title": "Regar", "project_id": project_id, "state_id": 1},
    )
    assert creada.status_code == 201
    tid = creada.json()["id"]
    assert set(creada.json().keys()) == CAMPOS_TASK
    assert creada.json()["due_at"] is None

    assert client.get(f"/tasks/{tid}").status_code == 200

    parcheada = client.patch(
        f"/tasks/{tid}", json={"due_at": "2026-03-01T09:00:00+01:00"}
    )
    assert parcheada.status_code == 200
    assert parcheada.json()["due_at"] == "2026-03-01T08:00:00Z"

    assert client.delete(f"/tasks/{tid}").status_code == 204
    assert client.get(f"/tasks/{tid}").status_code == 404


def test_get_tasks_filtrado_y_orden_estable(client, project_id):
    for titulo in ("A", "B", "C"):
        client.post(
            "/tasks",
            json={"title": titulo, "project_id": project_id, "state_id": 1},
        )

    primera = [t["id"] for t in client.get(f"/tasks?project_id={project_id}").json()]
    segunda = [t["id"] for t in client.get(f"/tasks?project_id={project_id}").json()]

    assert primera == segunda == sorted(primera)


def test_get_tasks_overdue(client, project_id):
    vencida = client.post(
        "/tasks",
        json={
            "title": "vencida",
            "project_id": project_id,
            "state_id": 1,
            "due_at": "2020-01-01T00:00:00+00:00",
        },
    ).json()
    client.post(
        "/tasks",
        json={
            "title": "futura",
            "project_id": project_id,
            "state_id": 1,
            "due_at": "2999-01-01T00:00:00+00:00",
        },
    )

    ids = [t["id"] for t in client.get("/tasks?overdue=true").json()]

    assert ids == [vencida["id"]]


def test_post_task_project_inexistente_404(client):
    response = client.post(
        "/tasks", json={"title": "X", "project_id": 999999, "state_id": 1}
    )

    assert response.status_code == 404
    assert "detail" in response.json()


def test_get_task_inexistente_404(client):
    response = client.get("/tasks/999999")

    assert response.status_code == 404
    assert "detail" in response.json()


def test_delete_proyecto_con_tareas_409(client, project_id):
    client.post(
        "/tasks",
        json={"title": "Regar", "project_id": project_id, "state_id": 1},
    )

    response = client.delete(f"/projects/{project_id}")

    assert response.status_code == 409
    assert "detail" in response.json()
