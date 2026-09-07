from fastapi.testclient import TestClient

from app.main import app

INVISIBLE_UNICODE = "\u200b"


def _crear(client: TestClient, name: str, description: str | None = None) -> dict:
    cuerpo: dict[str, object] = {"name": name}
    if description is not None:
        cuerpo["description"] = description
    response = client.post("/projects", json=cuerpo)
    assert response.status_code == 201
    return response.json()


def test_post_projects_crea_y_devuelve_201():
    client = TestClient(app)

    response = client.post("/projects", json={"name": "Casa"})

    assert response.status_code == 201
    assert response.json() == {"id": 1, "name": "Casa", "description": None}


def test_post_projects_descripcion_opcional_es_null():
    client = TestClient(app)

    response = client.post("/projects", json={"name": "Casa"})

    assert response.json()["description"] is None


def test_post_projects_name_solo_espacios_es_422():
    client = TestClient(app)

    response = client.post("/projects", json={"name": "   "})

    assert response.status_code == 422
    assert "detail" in response.json()


def test_post_projects_name_vacio_es_422():
    client = TestClient(app)

    response = client.post("/projects", json={"name": ""})

    assert response.status_code == 422
    assert "detail" in response.json()


def test_post_projects_name_invisible_unicode_es_422():
    client = TestClient(app)

    response = client.post("/projects", json={"name": INVISIBLE_UNICODE})

    assert response.status_code == 422
    assert "detail" in response.json()


def test_post_projects_recorta_espacios_de_name():
    client = TestClient(app)

    response = client.post("/projects", json={"name": "  Casa  "})

    assert response.json()["name"] == "Casa"


def test_get_projects_lista_vacia():
    client = TestClient(app)

    response = client.get("/projects")

    assert response.status_code == 200
    assert response.json() == []


def test_get_projects_ordena_por_id():
    client = TestClient(app)
    _crear(client, "B")
    _crear(client, "A")
    _crear(client, "C")

    ids = [p["id"] for p in client.get("/projects").json()]

    assert ids == sorted(ids)


def test_get_projects_esquema_exacto():
    client = TestClient(app)
    _crear(client, "Casa", "principal")

    for proyecto in client.get("/projects").json():
        assert set(proyecto.keys()) == {"id", "name", "description"}


def test_get_projects_orden_estable_entre_llamadas():
    client = TestClient(app)
    _crear(client, "B")
    _crear(client, "A")
    _crear(client, "C")

    primera = client.get("/projects").json()
    segunda = client.get("/projects").json()

    assert [p["id"] for p in primera] == [p["id"] for p in segunda]
