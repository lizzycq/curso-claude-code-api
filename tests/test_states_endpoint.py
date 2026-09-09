"""Smoke tests en vivo contra la API corriendo en http://127.0.0.1:8000.

No sustituyen a tests/test_states.py (matriz completa, in-process): solo
comprueban de un vistazo que el endpoint desplegado responde. Se saltan si la
API no está levantada.
"""
import httpx2 as httpx
import pytest

BASE_URL = "http://127.0.0.1:8000"
CODIGOS_ESTADOS = {"PENDIENTE", "EN_CURSO", "BLOQUEADA", "HECHA"}


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


def test_get_states_responde_200_con_el_catalogo(client):
    response = client.get("/states")

    assert response.status_code == 200
    cuerpo = response.json()
    assert {estado["code"] for estado in cuerpo} == CODIGOS_ESTADOS


def test_get_states_esquema_exacto(client):
    for estado in client.get("/states").json():
        assert set(estado.keys()) == {"id", "code"}


def test_get_states_orden_estable_entre_llamadas(client):
    primera = [e["id"] for e in client.get("/states").json()]
    segunda = [e["id"] for e in client.get("/states").json()]

    assert primera == segunda
