# Plan: tareas (CRUD v1 + fechas límite v2)

Objetivo: implementar el recurso Tareas completo —crear, listar con filtros,
obtener, actualizar parcialmente y borrar— según las secciones "Tareas v1" y
"Tareas v2: Fechas Límite" de `docs/contrato-api.md`, con persistencia en
PostgreSQL, y cerrar de paso el `409` de `DELETE /projects/{id}` con tareas que
`docs/plan-projects.md` había dejado fuera de alcance.

Fuentes: docs/contrato-api.md (Tareas v1; Tareas v2; Convenciones;
Normalización de texto; Orden de las listas; Esquemas de Respuesta; Proyectos),
docs/decisiones-ingenieria.md, README.md, CLAUDE.md. Referencia de estilo:
docs/plan-projects.md, app/schemas.py, app/main.py.

## Fuera de alcance

- Recordatorios, scheduler, zona horaria preferida del usuario y cambio
  automático de estado (el contrato lo excluye explícitamente en "Tareas v2").
- Borrado en cascada de tareas al borrar un proyecto: no se implementa; el
  proyecto con tareas se bloquea con `409` (contrato, "Proyectos").
- Endpoint propio para tareas vencidas: `overdue` es un filtro de `GET /tasks`,
  no una ruta aparte.
- Paginación, ordenación configurable, búsqueda por texto.
- Autenticación y autorización.
- CI, hooks, skills nuevas y pruebas de carga.
- Modificar el catálogo de estados o el recurso Proyectos más allá del `409`
  de borrado.

## Decisiones tomadas

- **Rama y archivo**: se trabaja en `feature/tasks`; este plan es
  `docs/plan-tasks.md`. — consigna del usuario.
- **Tabla `tasks`**: columnas `id` (entero, PK, autogenerado), `title` (texto,
  `NOT NULL`), `description` (texto, `NULL`), `project_id` (entero, `NOT NULL`,
  FK a `projects.id`), `state_id` (entero, `NOT NULL`, FK a `states.id`),
  `due_at` (`TIMESTAMP WITH TIME ZONE`, `NULL`). — "Campos: `id`, `title`,
  `description` opcional, `project_id`, `state_id`" (v1) + "Se añade `due_at`,
  opcional" (v2) + "IDs enteros positivos generados por la base"
  (Convenciones).
- **FK sin cascada**: `project_id` y `state_id` son `NOT NULL`; las FK **no**
  llevan `ON DELETE CASCADE`. Borrar un proyecto con tareas se bloquea en la
  capa de la app con `409` antes de tocar la base. — contrato, "Proyectos"
  ("no hay borrado en cascada implícito") + decisión del usuario.
- **Referencia inexistente al crear/actualizar una tarea**: `project_id` o
  `state_id` que no existan devuelven `404` con clave `detail`. — Convenciones
  ("`404` para recurso inexistente"; "una referencia a proyecto o estado
  inexistente no se crea implícitamente") + decisión del usuario.
- **Normalización de `title`**: se recorta y se rechaza con `422` por categoría
  Unicode (`Cc`, `Cf`, `Zl`, `Zp`, `Zs`), reutilizando
  `normalizar_texto_visible` de `app/schemas.py`. — contrato, "Normalización
  de texto" (se aplica a `title` de tarea).
- **`due_at` de entrada**: se acepta solo con zona horaria explícita; una fecha
  **sin** zona se rechaza con `422`. Se normaliza a UTC antes de guardar. —
  contrato, "Tareas v2".
- **`due_at` de salida**: se serializa siempre en UTC con sufijo `Z`, sin
  desplazamiento `+00:00` y sin microsegundos (`2026-03-01T09:00:00Z`).
  Ausente se devuelve como `null`, no se omite. — contrato, "Esquemas de
  Respuesta".
- **Esquema de respuesta de tarea**: exactamente `{"id", "title",
  "description", "project_id", "state_id", "due_at"}`, ni un campo más. —
  contrato, "Esquemas de Respuesta".
- **`GET /tasks`**: `200` con lista JSON en la raíz, ordenada por `id`
  ascendente **también con filtros aplicados**. Filtros `project_id`,
  `state_id` y `overdue`, solos o combinados. — contrato, "Tareas v1", "Orden
  de las listas", "Tareas v2".
- **`GET /tasks?overdue=true`**: devuelve las tareas con `due_at` anterior al
  instante de evaluación (ahora, en UTC) **y** `state_id` distinto del de
  `HECHA`. Una tarea sin `due_at` nunca está vencida. `overdue=false` (u
  omitido) no filtra por vencimiento. — contrato, "Tareas v2".
- **`PATCH /tasks/{id}`**: actualización parcial consistente. Omitir un campo
  lo deja igual; enviar `description: null` o `due_at: null` los limpia;
  `title` sin carácter visible → `422`; `due_at` sin zona → `422`;
  `project_id`/`state_id` inexistente → `404`; id de la tarea inexistente →
  `404`. — contrato, "Tareas v1" + decisiones anteriores.
- **`DELETE /tasks/{id}`**: `204` sin cuerpo si existe; `404` si no. — contrato,
  "Tareas v1" + Convenciones.
- **`DELETE /projects/{id}` con tareas**: pasa a devolver `409` con clave
  `detail` si el proyecto tiene al menos una tarea; sigue devolviendo `204` si
  no tiene y `404` si el proyecto no existe. — contrato, "Proyectos" + decisión
  del usuario (se cierra en este plan).
- **Aislamiento de tests**: `tests/conftest.py` amplía el fixture `autouse`
  para truncar `tasks` además de `projects` (`TRUNCATE tasks, projects RESTART
  IDENTITY CASCADE`), dejando `states` intacto. — patrón ya establecido en el
  repo.
- **Persistencia**: modelo SQLAlchemy `Task` en `app/models.py` y migración de
  Alembic encadenada a `d5a2008b4631`, escrita a mano al estilo de las
  existentes, con `upgrade`/`downgrade` probados en ambos sentidos. Tests
  contra PostgreSQL, nunca SQLite. — docs/decisiones-ingenieria.md.
- **TDD**: cada incremento empieza por un test que falla por la ausencia de la
  capacidad. No se debilita ningún test existente. — docs/decisiones-
  ingenieria.md.

## Incrementos

### 1. Modelo y migración de la tabla `tasks`
- Qué cambia: modelo `Task` (`id`, `title`, `description`, `project_id`,
  `state_id`, `due_at`) en `app/models.py`, registrado en `alembic/env.py`;
  migración nueva (down_revision = `d5a2008b4631`) que crea `tasks` con las dos
  FK (`projects.id`, `states.id`, ambas `NOT NULL`, sin cascada) y la columna
  `due_at` con zona, y la elimina en `downgrade`. Sin endpoints.
- Comprobación:
  ```
  docker compose up -d
  uv run alembic upgrade head
  uv run alembic downgrade -1
  uv run alembic upgrade head
  uv run pytest -q tests/test_tasks_migracion.py
  uv run ruff check .
  ```
  Esperado: `upgrade` crea `tasks` con las 6 columnas, `due_at` de tipo
  `timestamp with time zone`, y las FK a `projects` y `states`; `downgrade -1`
  la elimina y deja `alembic_version` en `d5a2008b4631` con `projects` y
  `states` intactos; el segundo `upgrade` la recrea; los tests de migración
  pasan; `ruff` sin hallazgos.
- Commit: `feat: agrega modelo y migración de la tabla tasks`

### 2. `POST /tasks` y `GET /tasks` (v1, sin filtros de vencimiento)
- Qué cambia: schemas `TaskIn` / `TaskOut` en `app/schemas.py` (`title`
  normalizado; `description`, `due_at` opcionales; `due_at` sin zona → `422`;
  salida con `due_at` en UTC + `Z` sin microsegundos). `POST /tasks` → `201`
  validando que `project_id` y `state_id` existen (`404` si no) y el título
  (`422`). `GET /tasks` → `200`, lista JSON en la raíz ordenada por `id`, con
  filtros `project_id` y `state_id` solos o combinados. Esquema de respuesta
  exacto.
- Comprobación:
  ```
  uv run pytest -q tests/test_tasks.py
  uv run ruff check .
  uv run uvicorn app.main:app --port 8000 &
  # (crear antes un proyecto id=1 y usar state_id=1)
  curl -s -w '\n%{http_code}\n' -X POST http://127.0.0.1:8000/tasks \
    -H 'content-type: application/json' \
    -d '{"title":"Regar","project_id":1,"state_id":1}'
  curl -s -w '\n%{http_code}\n' -X POST http://127.0.0.1:8000/tasks \
    -H 'content-type: application/json' \
    -d '{"title":"X","project_id":999,"state_id":1}'
  curl -s -w '\n%{http_code}\n' 'http://127.0.0.1:8000/tasks?project_id=1&state_id=1'
  ```
  Esperado: primer `POST` → `201` con `{"id":1,"title":"Regar",
  "description":null,"project_id":1,"state_id":1,"due_at":null}`; segundo →
  `404` con `detail`; `GET` con filtros → `200` lista ordenada por `id`, solo
  con los seis campos declarados; dos `GET` idénticos → mismos ids por
  posición; `test_health`, `test_states*`, `test_projects*` siguen pasando;
  `ruff` limpio.
- Commit: `feat: implementa POST /tasks y GET /tasks con filtros de proyecto y estado`

### 3. `GET /tasks/{id}`, `PATCH /tasks/{id}`, `DELETE /tasks/{id}`
- Qué cambia: `TaskUpdate` en `app/schemas.py` (`extra="forbid"`; todos los
  campos opcionales; `title` normalizado si viene; `due_at` sin zona → `422`).
  `GET /tasks/{id}` → `200`/`404`. `PATCH /tasks/{id}` → `200` parcial: omitir
  campo lo deja igual, `description: null` / `due_at: null` limpian,
  `project_id`/`state_id` inexistente → `404`, `title` inválido → `422`, id
  inexistente → `404`. `DELETE /tasks/{id}` → `204` sin cuerpo / `404`.
- Comprobación:
  ```
  uv run pytest -q tests/test_tasks.py
  uv run ruff check .
  uv run uvicorn app.main:app --port 8000 &
  curl -s -w '\n%{http_code}\n' http://127.0.0.1:8000/tasks/1
  curl -s -w '\n%{http_code}\n' http://127.0.0.1:8000/tasks/999
  curl -s -w '\n%{http_code}\n' -X PATCH http://127.0.0.1:8000/tasks/1 \
    -H 'content-type: application/json' -d '{"due_at":"2026-03-01T09:00:00+01:00"}'
  curl -s -w '\n%{http_code}\n' -X PATCH http://127.0.0.1:8000/tasks/1 \
    -H 'content-type: application/json' -d '{"due_at":"2026-03-01T09:00:00"}'
  curl -s -w '\n%{http_code}\n' -X DELETE http://127.0.0.1:8000/tasks/1
  curl -s -w '\n%{http_code}\n' -X DELETE http://127.0.0.1:8000/tasks/999
  ```
  Esperado: `GET /1` → `200`; `GET /999` → `404` con `detail`; primer `PATCH`
  → `200` con `due_at` serializado como `"2026-03-01T08:00:00Z"` (UTC, `Z`,
  sin microsegundos); segundo `PATCH` (sin zona) → `422` con `detail`;
  `DELETE /1` → `204` sin cuerpo; `DELETE /999` → `404`; tests nuevos y
  previos pasan; `ruff` limpio.
- Commit: `feat: implementa GET, PATCH y DELETE de /tasks/{id}`

### 4. `GET /tasks?overdue=true` (v2)
- Qué cambia: se añade el filtro `overdue` a `GET /tasks`. `overdue=true`
  devuelve tareas con `due_at` no nulo y anterior a "ahora" en UTC y con
  `state_id` distinto del de `HECHA`; combinable con `project_id` y
  `state_id`; orden por `id`. `overdue` omitido o `false` no filtra por
  vencimiento. Sin cambios de esquema.
- Comprobación:
  ```
  uv run pytest -q tests/test_tasks.py
  uv run ruff check .
  uv run uvicorn app.main:app --port 8000 &
  curl -s -w '\n%{http_code}\n' 'http://127.0.0.1:8000/tasks?overdue=true'
  ```
  Esperado: con datos sembrados por el test (una vencida no HECHA, una vencida
  HECHA, una futura, una sin fecha) `overdue=true` devuelve solo la vencida no
  HECHA; `overdue=true&project_id=X` cruza ambos filtros; orden por `id`
  estable entre llamadas; tests nuevos y previos pasan; `ruff` limpio.
- Commit: `feat: implementa el filtro GET /tasks?overdue=true`

### 5. `DELETE /projects/{id}` devuelve 409 si el proyecto tiene tareas
- Qué cambia: `delete_project` en `app/main.py` comprueba si el proyecto tiene
  al menos una tarea antes de borrar; si la tiene, `409` con clave `detail` y
  no borra nada; si no, sigue devolviendo `204`; proyecto inexistente sigue
  dando `404`. Se actualiza el comentario de `tests/test_projects.py` que
  remitía a la deuda y se añaden los tests del `409`.
- Comprobación:
  ```
  uv run pytest -q tests/test_projects.py tests/test_tasks.py
  uv run ruff check .
  uv run uvicorn app.main:app --port 8000 &
  # proyecto 1 con una tarea:
  curl -s -w '\n%{http_code}\n' -X DELETE http://127.0.0.1:8000/projects/1
  # proyecto 2 sin tareas:
  curl -s -w '\n%{http_code}\n' -X DELETE http://127.0.0.1:8000/projects/2
  ```
  Esperado: `DELETE` del proyecto con tareas → `409` con `detail`, el proyecto
  y sus tareas siguen existiendo; `DELETE` del proyecto sin tareas → `204`;
  proyecto inexistente → `404`; ningún test de projects se debilita; `ruff`
  limpio.
- Commit: `feat: DELETE /projects/{id} responde 409 si el proyecto tiene tareas`

### 6. Matriz mínima de tests del recurso
- Qué cambia: revisar `tests/test_tasks.py` contra la "Matriz Mínima de Tests"
  del contrato y completar lo que falte tras los incrementos 2–5: CRUD feliz
  de tareas; ids inexistentes en `GET`/`PATCH`/`DELETE`; título vacío y
  espacios ASCII; proyecto o estado inexistente al crear una tarea; borrado de
  proyecto con tareas (`409`); filtros solos y combinados (`project_id`,
  `state_id`, `overdue`); orden estable con y sin filtros; esquema de
  respuesta exacto en `POST`, `GET`, `GET /{id}`, `PATCH`; `due_at` omitido,
  válido, sin zona, vencido, futuro y tarea hecha. Sin cambios de
  comportamiento.
- Comprobación:
  ```
  uv run pytest -q
  uv run ruff check .
  ```
  Esperado: toda la suite pasa (previos + migración de tasks + tasks), sin
  debilitar ninguno; `ruff` sin hallazgos.
- Commit: `test: cubre la matriz mínima del recurso tasks`

### 7. Rollback de v2 verificado
- Qué cambia: nada de producción. Un test de migración
  (`tests/test_tasks_migracion.py`) que verifica el rollback completo de v2:
  `upgrade head` → `downgrade` hasta antes de `tasks` → comprobar que `tasks`
  no existe y que `projects`/`states` quedan intactos → `upgrade head` para
  restaurar. Cubre la invariante "Migración desde base vacía y rollback de v2"
  de la Matriz Mínima.
- Comprobación:
  ```
  uv run pytest -q tests/test_tasks_migracion.py
  uv run alembic downgrade base
  uv run alembic upgrade head
  uv run pytest -q
  uv run ruff check .
  ```
  Esperado: el rollback de v2 deja el esquema sin `tasks` y con `states` +
  `projects` correctos; `downgrade base` + `upgrade head` reconstruye todo;
  suite completa verde; `ruff` limpio.
- Commit: `test: verifica el rollback de la migración de tasks (v2)`
