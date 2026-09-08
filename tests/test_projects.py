from fastapi.testclient import TestClient

from app.main import app

INVISIBLE_UNICODE = "\u200b"

# El 409 al borrar un proyecto con tareas se ejercita en
# tests/test_tasks.py::test_delete_proyecto_con_tareas_responde_409
# (necesita crear una tarea).


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


def test_post_projects_esquema_exacto():
    client = TestClient(app)

    cuerpo = client.post(
        "/projects", json={"name": "Casa", "description": "principal"}
    ).json()

    assert set(cuerpo.keys()) == {"id", "name", "description"}


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


def test_get_project_por_id_ok():
    client = TestClient(app)
    creado = _crear(client, "Casa", "principal")

    response = client.get(f"/projects/{creado['id']}")

    assert response.status_code == 200
    assert response.json() == creado


def test_get_project_inexistente_404():
    client = TestClient(app)

    response = client.get("/projects/999")

    assert response.status_code == 404
    assert "detail" in response.json()


def test_patch_project_cambia_description():
    client = TestClient(app)
    creado = _crear(client, "Casa")

    response = client.patch(
        f"/projects/{creado['id']}", json={"description": "con jardín"}
    )

    assert response.status_code == 200
    assert response.json()["description"] == "con jardín"


def test_patch_project_description_a_null():
    client = TestClient(app)
    creado = _crear(client, "Casa", "principal")

    response = client.patch(
        f"/projects/{creado['id']}", json={"description": None}
    )

    assert response.status_code == 200
    assert response.json()["description"] is None


def test_patch_project_omitir_campo_no_lo_cambia():
    client = TestClient(app)
    creado = _crear(client, "Casa", "principal")

    response = client.patch(f"/projects/{creado['id']}", json={"name": "Otra"})

    assert response.status_code == 200
    cuerpo = response.json()
    assert cuerpo["name"] == "Otra"
    assert cuerpo["description"] == "principal"


def test_patch_project_name_invisible_422():
    client = TestClient(app)
    creado = _crear(client, "Casa")

    response = client.patch(
        f"/projects/{creado['id']}", json={"name": INVISIBLE_UNICODE}
    )

    assert response.status_code == 422
    assert "detail" in response.json()


def test_patch_project_inexistente_404():
    client = TestClient(app)

    response = client.patch("/projects/999", json={"name": "Casa"})

    assert response.status_code == 404
    assert "detail" in response.json()


def test_patch_project_esquema_exacto():
    client = TestClient(app)
    creado = _crear(client, "Casa")

    cuerpo = client.patch(
        f"/projects/{creado['id']}", json={"description": "x"}
    ).json()

    assert set(cuerpo.keys()) == {"id", "name", "description"}


def test_delete_project_ok_204():
    client = TestClient(app)
    creado = _crear(client, "Casa")

    response = client.delete(f"/projects/{creado['id']}")

    assert response.status_code == 204
    assert response.content == b""
    assert client.get(f"/projects/{creado['id']}").status_code == 404


def test_delete_project_inexistente_404():
    client = TestClient(app)

    response = client.delete("/projects/999")

    assert response.status_code == 404
    assert "detail" in response.json()
