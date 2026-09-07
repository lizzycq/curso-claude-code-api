from fastapi.testclient import TestClient

from app.main import app

ORDEN_ESPERADO = ["PENDIENTE", "EN_CURSO", "BLOQUEADA", "HECHA"]


def test_get_states_devuelve_catalogo_completo_y_ordenado():
    client = TestClient(app)

    response = client.get("/states")

    assert response.status_code == 200
    cuerpo = response.json()
    assert [estado["code"] for estado in cuerpo] == ORDEN_ESPERADO


def test_get_states_esquema_exacto():
    client = TestClient(app)

    response = client.get("/states")

    for estado in response.json():
        assert set(estado.keys()) == {"id", "code"}
        assert isinstance(estado["id"], int)
        assert isinstance(estado["code"], str)


def test_get_states_orden_estable_entre_llamadas():
    client = TestClient(app)

    primera = client.get("/states").json()
    segunda = client.get("/states").json()

    assert [e["id"] for e in primera] == [e["id"] for e in segunda]
