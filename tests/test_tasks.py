from fastapi.testclient import TestClient

from app.main import app

INVISIBLE_UNICODE = "\u200b"
CAMPOS_TASK = {"id", "title", "description", "project_id", "state_id", "due_at"}


def _crear_proyecto(client: TestClient, name: str = "Casa") -> int:
    return client.post("/projects", json={"name": name}).json()["id"]


def _crear_tarea(
    client: TestClient,
    project_id: int,
    state_id: int = 1,
    title: str = "Regar",
    **extra: object,
) -> dict:
    cuerpo: dict[str, object] = {
        "title": title,
        "project_id": project_id,
        "state_id": state_id,
    }
    cuerpo.update(extra)
    response = client.post("/tasks", json=cuerpo)
    assert response.status_code == 201, response.text
    return response.json()


def test_post_tasks_crea_y_devuelve_201():
    client = TestClient(app)
    pid = _crear_proyecto(client)

    response = client.post(
        "/tasks", json={"title": "Regar", "project_id": pid, "state_id": 1}
    )

    assert response.status_code == 201
    assert response.json() == {
        "id": 1,
        "title": "Regar",
        "description": None,
        "project_id": pid,
        "state_id": 1,
        "due_at": None,
    }


def test_post_tasks_esquema_exacto():
    client = TestClient(app)
    pid = _crear_proyecto(client)

    cuerpo = _crear_tarea(client, pid, description="con manguera")

    assert set(cuerpo.keys()) == CAMPOS_TASK


def test_post_tasks_project_id_inexistente_es_404():
    client = TestClient(app)

    response = client.post(
        "/tasks", json={"title": "X", "project_id": 999, "state_id": 1}
    )

    assert response.status_code == 404
    assert "detail" in response.json()


def test_post_tasks_state_id_inexistente_es_404():
    client = TestClient(app)
    pid = _crear_proyecto(client)

    response = client.post(
        "/tasks", json={"title": "X", "project_id": pid, "state_id": 999}
    )

    assert response.status_code == 404
    assert "detail" in response.json()


def test_post_tasks_title_solo_espacios_es_422():
    client = TestClient(app)
    pid = _crear_proyecto(client)

    response = client.post(
        "/tasks", json={"title": "   ", "project_id": pid, "state_id": 1}
    )

    assert response.status_code == 422
    assert "detail" in response.json()


def test_post_tasks_title_vacio_es_422():
    client = TestClient(app)
    pid = _crear_proyecto(client)

    response = client.post(
        "/tasks", json={"title": "", "project_id": pid, "state_id": 1}
    )

    assert response.status_code == 422


def test_post_tasks_title_invisible_unicode_es_422():
    client = TestClient(app)
    pid = _crear_proyecto(client)

    response = client.post(
        "/tasks",
        json={"title": INVISIBLE_UNICODE, "project_id": pid, "state_id": 1},
    )

    assert response.status_code == 422


def test_post_tasks_recorta_title():
    client = TestClient(app)
    pid = _crear_proyecto(client)

    cuerpo = _crear_tarea(client, pid, title="  Regar  ")

    assert cuerpo["title"] == "Regar"


def test_post_tasks_due_at_con_zona_se_serializa_en_utc_con_z():
    client = TestClient(app)
    pid = _crear_proyecto(client)

    cuerpo = _crear_tarea(client, pid, due_at="2026-03-01T09:00:00+01:00")

    assert cuerpo["due_at"] == "2026-03-01T08:00:00Z"


def test_post_tasks_due_at_sin_zona_es_422():
    client = TestClient(app)
    pid = _crear_proyecto(client)

    response = client.post(
        "/tasks",
        json={
            "title": "Regar",
            "project_id": pid,
            "state_id": 1,
            "due_at": "2026-03-01T09:00:00",
        },
    )

    assert response.status_code == 422
    assert "detail" in response.json()


def test_get_tasks_lista_vacia():
    client = TestClient(app)

    response = client.get("/tasks")

    assert response.status_code == 200
    assert response.json() == []


def test_get_tasks_ordena_por_id():
    client = TestClient(app)
    pid = _crear_proyecto(client)
    _crear_tarea(client, pid, title="B")
    _crear_tarea(client, pid, title="A")
    _crear_tarea(client, pid, title="C")

    ids = [t["id"] for t in client.get("/tasks").json()]

    assert ids == sorted(ids)


def test_get_tasks_filtra_por_project_id():
    client = TestClient(app)
    p1 = _crear_proyecto(client, "P1")
    p2 = _crear_proyecto(client, "P2")
    _crear_tarea(client, p1)
    _crear_tarea(client, p2)

    tareas = client.get(f"/tasks?project_id={p1}").json()

    assert [t["project_id"] for t in tareas] == [p1]


def test_get_tasks_filtra_por_state_id():
    client = TestClient(app)
    pid = _crear_proyecto(client)
    _crear_tarea(client, pid, state_id=1)
    _crear_tarea(client, pid, state_id=2)

    tareas = client.get("/tasks?state_id=2").json()

    assert [t["state_id"] for t in tareas] == [2]


def test_get_tasks_filtros_combinados():
    client = TestClient(app)
    p1 = _crear_proyecto(client, "P1")
    p2 = _crear_proyecto(client, "P2")
    _crear_tarea(client, p1, state_id=1)
    _crear_tarea(client, p1, state_id=2)
    _crear_tarea(client, p2, state_id=2)

    tareas = client.get(f"/tasks?project_id={p1}&state_id=2").json()

    assert len(tareas) == 1
    assert tareas[0]["project_id"] == p1
    assert tareas[0]["state_id"] == 2


def test_get_tasks_esquema_exacto():
    client = TestClient(app)
    pid = _crear_proyecto(client)
    _crear_tarea(client, pid)

    for tarea in client.get("/tasks").json():
        assert set(tarea.keys()) == CAMPOS_TASK


def test_get_tasks_orden_estable_entre_llamadas():
    client = TestClient(app)
    pid = _crear_proyecto(client)
    _crear_tarea(client, pid, title="B")
    _crear_tarea(client, pid, title="A")
    _crear_tarea(client, pid, title="C")

    primera = client.get(f"/tasks?project_id={pid}").json()
    segunda = client.get(f"/tasks?project_id={pid}").json()

    assert [t["id"] for t in primera] == [t["id"] for t in segunda]


def test_get_task_por_id_ok():
    client = TestClient(app)
    pid = _crear_proyecto(client)
    creada = _crear_tarea(client, pid)

    response = client.get(f"/tasks/{creada['id']}")

    assert response.status_code == 200
    assert response.json() == creada


def test_get_task_inexistente_404():
    client = TestClient(app)

    response = client.get("/tasks/999")

    assert response.status_code == 404
    assert "detail" in response.json()


def test_patch_task_cambia_description():
    client = TestClient(app)
    pid = _crear_proyecto(client)
    creada = _crear_tarea(client, pid)

    response = client.patch(
        f"/tasks/{creada['id']}", json={"description": "con manguera"}
    )

    assert response.status_code == 200
    assert response.json()["description"] == "con manguera"


def test_patch_task_description_a_null():
    client = TestClient(app)
    pid = _crear_proyecto(client)
    creada = _crear_tarea(client, pid, description="algo")

    response = client.patch(f"/tasks/{creada['id']}", json={"description": None})

    assert response.status_code == 200
    assert response.json()["description"] is None


def test_patch_task_due_at_a_null():
    client = TestClient(app)
    pid = _crear_proyecto(client)
    creada = _crear_tarea(client, pid, due_at="2026-03-01T09:00:00+00:00")

    response = client.patch(f"/tasks/{creada['id']}", json={"due_at": None})

    assert response.status_code == 200
    assert response.json()["due_at"] is None


def test_patch_task_omitir_campo_no_lo_cambia():
    client = TestClient(app)
    pid = _crear_proyecto(client)
    creada = _crear_tarea(client, pid, description="original")

    response = client.patch(f"/tasks/{creada['id']}", json={"title": "Otra"})

    assert response.status_code == 200
    cuerpo = response.json()
    assert cuerpo["title"] == "Otra"
    assert cuerpo["description"] == "original"


def test_patch_task_title_invisible_422():
    client = TestClient(app)
    pid = _crear_proyecto(client)
    creada = _crear_tarea(client, pid)

    response = client.patch(
        f"/tasks/{creada['id']}", json={"title": INVISIBLE_UNICODE}
    )

    assert response.status_code == 422
    assert "detail" in response.json()


def test_patch_task_due_at_sin_zona_422():
    client = TestClient(app)
    pid = _crear_proyecto(client)
    creada = _crear_tarea(client, pid)

    response = client.patch(
        f"/tasks/{creada['id']}", json={"due_at": "2026-03-01T09:00:00"}
    )

    assert response.status_code == 422
    assert "detail" in response.json()


def test_patch_task_project_id_inexistente_404():
    client = TestClient(app)
    pid = _crear_proyecto(client)
    creada = _crear_tarea(client, pid)

    response = client.patch(
        f"/tasks/{creada['id']}", json={"project_id": 999}
    )

    assert response.status_code == 404
    assert "detail" in response.json()


def test_patch_task_state_id_inexistente_404():
    client = TestClient(app)
    pid = _crear_proyecto(client)
    creada = _crear_tarea(client, pid)

    response = client.patch(f"/tasks/{creada['id']}", json={"state_id": 999})

    assert response.status_code == 404
    assert "detail" in response.json()


def test_patch_task_inexistente_404():
    client = TestClient(app)

    response = client.patch("/tasks/999", json={"title": "X"})

    assert response.status_code == 404
    assert "detail" in response.json()


def test_patch_task_esquema_exacto():
    client = TestClient(app)
    pid = _crear_proyecto(client)
    creada = _crear_tarea(client, pid)

    cuerpo = client.patch(
        f"/tasks/{creada['id']}", json={"description": "x"}
    ).json()

    assert set(cuerpo.keys()) == CAMPOS_TASK


def test_delete_task_ok_204():
    client = TestClient(app)
    pid = _crear_proyecto(client)
    creada = _crear_tarea(client, pid)

    response = client.delete(f"/tasks/{creada['id']}")

    assert response.status_code == 204
    assert response.content == b""
    assert client.get(f"/tasks/{creada['id']}").status_code == 404


def test_delete_task_inexistente_404():
    client = TestClient(app)

    response = client.delete("/tasks/999")

    assert response.status_code == 404
    assert "detail" in response.json()



def test_delete_proyecto_con_tareas_responde_409():
    client = TestClient(app)
    pid = _crear_proyecto(client)
    _crear_tarea(client, pid)

    response = client.delete(f"/projects/{pid}")

    assert response.status_code == 409
    assert "detail" in response.json()
    # el proyecto y su tarea siguen existiendo
    assert client.get(f"/projects/{pid}").status_code == 200
    assert len(client.get(f"/tasks?project_id={pid}").json()) == 1


def test_delete_proyecto_sin_tareas_responde_204():
    client = TestClient(app)
    pid = _crear_proyecto(client)

    response = client.delete(f"/projects/{pid}")

    assert response.status_code == 204
    assert client.get(f"/projects/{pid}").status_code == 404
