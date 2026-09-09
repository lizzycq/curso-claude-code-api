"""Smoke tests en vivo contra la API corriendo en http://127.0.0.1:8000.

No sustituyen a tests/test_projects.py (matriz completa, in-process): solo
comprueban de un vistazo que los endpoints desplegados responden. Se saltan si
la API no está levantada.
"""
import httpx2 as httpx
import pytest

BASE_URL = "http://127.0.0.1:8000"


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


def test_health_responde_ok(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_recorrido_feliz_crear_leer_borrar(client):
    creado = client.post("/projects", json={"name": "Casa"})
    assert creado.status_code == 201
    pid = creado.json()["id"]
    assert creado.json() == {"id": pid, "name": "Casa", "description": None}

    leido = client.get(f"/projects/{pid}")
    assert leido.status_code == 200
    assert leido.json() == creado.json()

    assert client.get("/projects").status_code == 200

    borrado = client.delete(f"/projects/{pid}")
    assert borrado.status_code == 204
    assert client.get(f"/projects/{pid}").status_code == 404


def test_get_project_inexistente_404(client):
    response = client.get("/projects/999999")

    assert response.status_code == 404
    assert "detail" in response.json()


def test_post_project_name_vacio_422(client):
    response = client.post("/projects", json={"name": "   "})

    assert response.status_code == 422
    assert "detail" in response.json()
