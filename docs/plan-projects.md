# Plan: proyectos (CRUD)

Objetivo: implementar el recurso Proyectos de la API —crear, listar, obtener,
actualizar parcialmente y borrar— según la sección "Proyectos" de
`docs/contrato-api.md`, con persistencia en PostgreSQL vía una migración de
Alembic.

Fuentes: docs/contrato-api.md (Proyectos; Convenciones; Orden de las listas;
Esquemas de Respuesta), docs/decisiones-ingenieria.md, README.md, CLAUDE.md.
Referencia de formato y estilo ya aplicado: docs/plan-persistencia.md.

## Fuera de alcance

- **La respuesta `409` de `DELETE /projects/{id}` cuando el proyecto tiene
  tareas.** En este incremento `DELETE` siempre borra y responde `204`. El
  `409` se añade en el incremento de Tareas, cuando existan la tabla `tasks`
  y su clave foránea a `projects`. Hasta entonces, no hay forma de que un
  proyecto tenga tareas.
- Tareas (tabla, endpoints, filtros), `due_at` y `overdue`.
- `GET /tasks`, `GET /states` ya existente (no se toca).
- Paginación, ordenación configurable, búsqueda por `name`.
- Borrado en cascada (el contrato lo prohíbe explícitamente).
- CI, hooks, skills nuevas y pruebas de carga.
- Autenticación y autorización.

## Decisiones tomadas

- **Rama y archivo**: se trabaja en `feature/projects`; este plan es
  `docs/plan-projects.md`. — consigna del usuario.
- **Tabla `projects`**: columnas `id` (entero, PK, autogenerado), `name`
  (texto, `NOT NULL`), `description` (texto, `NULL`). — "Campos mínimos: `id`,
  `name`, `description` opcional" y "IDs enteros positivos generados por la
  base" (contrato, Proyectos y Convenciones).
- **Esquema de respuesta**: exactamente `{"id", "name", "description"}`, sin
  campos de más; `description` ausente se devuelve como `null`, no se omite. —
  contrato, "Esquemas de Respuesta".
- **`POST /projects`**: `201` con el recurso creado. `name` se normaliza antes
  de validar y guardar —se recorta el espacio de los extremos y se rechaza con
  `422` si no queda ningún carácter visible (comprobación por categoría
  Unicode: `Cc`, `Cf`, `Zl`, `Zp`, `Zs`)—, igual que el `title` de tarea. —
  contrato, "Normalización de texto" (se aplica a `title` de tarea; se adopta
  la misma regla para `name` de proyecto por coherencia, al ser el otro campo
  de texto libre obligatorio). `description` es opcional; si se omite, queda
  `null`.
- **`GET /projects`**: `200` con lista JSON en la raíz (sin envoltorio),
  ordenada por `id` ascendente. — contrato, "Orden de las listas" y "Esquemas
  de Respuesta".
- **`GET /projects/{id}`**: `200` con el recurso, o `404` si no existe. —
  contrato, Proyectos.
- **`PATCH /projects/{id}`**: `200` con actualización parcial. Omitir un campo
  lo deja igual; enviar `description: null` la vuelve a `null`; un `name` que
  quede sin carácter visible tras normalizar se rechaza con `422`. `404` si el
  id no existe. — contrato, Proyectos ("actualización parcial") + regla de
  normalización aplicada también aquí; el manejo explícito de `null` en
  `description` es decisión de este plan para que `PATCH` pueda limpiar el
  campo.
- **`DELETE /projects/{id}`**: `204` sin cuerpo si el proyecto existe; `404`
  si no. (El `409` queda fuera de alcance, ver arriba.) — contrato, Proyectos
  + Convenciones (`404` para recurso inexistente).
- **Errores**: forma `{"detail": "<mensaje>"}`; para el `422` de validación se
  admite además la forma que genere FastAPI, con `detail` como clave de primer
  nivel. — contrato, Convenciones.
- **Persistencia**: modelo SQLAlchemy `Project` en `app/models.py` y migración
  de Alembic encadenada a `a44fff1d0719`, con `upgrade` que crea la tabla y
  `downgrade` que la elimina. Tests de persistencia contra PostgreSQL, nunca
  SQLite. — docs/decisiones-ingenieria.md.
- **TDD**: cada incremento empieza por un test que falla por la ausencia de la
  capacidad. No se debilita ningún test existente. — docs/decisiones-
  ingenieria.md.

## Incrementos

### 1. Modelo y migración de la tabla `projects`
- Qué cambia: se añade el modelo `Project` (`id`, `name`, `description`) en
  `app/models.py`, se registra en `alembic/env.py`, y una migración nueva
  (down_revision = `a44fff1d0719`) crea la tabla `projects` en `upgrade` y la
  elimina en `downgrade`. Sin endpoints todavía.
- Comprobación:
  ```
  docker compose up -d
  uv run alembic upgrade head
  uv run alembic downgrade -1
  uv run alembic upgrade head
  uv run pytest -q tests/test_projects_migracion.py
  uv run ruff check .
  ```
  Esperado: `upgrade` crea la tabla `projects` con las tres columnas y `id`
  autogenerado; `downgrade -1` la elimina y deja `alembic_version` en
  `a44fff1d0719`; el segundo `upgrade` la vuelve a crear; el test de migración
  pasa (tabla presente tras `upgrade`, ausente tras `downgrade`); `states` y su
  contenido quedan intactos; `ruff` sin hallazgos.
- Commit: `feat: agrega modelo y migración de la tabla projects`

### 2. `POST /projects` y `GET /projects`
- Qué cambia: se añaden la ruta de creación (`201`, normaliza y valida `name`,
  `422` si `name` no deja carácter visible, `description` opcional →`null`) y
  la de listado (`200`, lista JSON en la raíz, orden por `id` ascendente,
  esquema exacto `{"id","name","description"}`).
- Comprobación:
  ```
  uv run pytest -q tests/test_projects.py
  uv run ruff check .
  uv run uvicorn app.main:app --port 8000 &
  curl -s -w '\n%{http_code}\n' -X POST http://127.0.0.1:8000/projects \
    -H 'content-type: application/json' -d '{"name":"Casa"}'
  curl -s -w '\n%{http_code}\n' -X POST http://127.0.0.1:8000/projects \
    -H 'content-type: application/json' -d '{"name":"   "}'
  curl -s -w '\n%{http_code}\n' http://127.0.0.1:8000/projects
  ```
  Esperado: el primer `POST` → `201` con `{"id":1,"name":"Casa",
  "description":null}`; el segundo → `422` con clave `detail`; `GET` → `200`
  con una lista JSON cuyos elementos tienen solo `id`, `name`, `description`,
  ordenada por `id` ascendente; dos `GET` idénticos devuelven los ids en la
  misma posición; los tests nuevos pasan y los de salud y `states` siguen
  pasando; `ruff` sin hallazgos.
- Commit: `feat: implementa POST /projects y GET /projects`

### 3. `GET /projects/{id}`, `PATCH /projects/{id}` y `DELETE /projects/{id}`
- Qué cambia: se añaden obtención por id (`200`/`404`), actualización parcial
  (`200`; omitir campo lo deja igual; `description: null` la limpia; `name`
  sin carácter visible →`422`; id inexistente →`404`) y borrado (`204` sin
  cuerpo si existe; `404` si no).
- Comprobación:
  ```
  uv run pytest -q tests/test_projects.py
  uv run ruff check .
  uv run uvicorn app.main:app --port 8000 &
  curl -s -w '\n%{http_code}\n' http://127.0.0.1:8000/projects/1
  curl -s -w '\n%{http_code}\n' http://127.0.0.1:8000/projects/999
  curl -s -w '\n%{http_code}\n' -X PATCH http://127.0.0.1:8000/projects/1 \
    -H 'content-type: application/json' -d '{"description":"con jardín"}'
  curl -s -w '\n%{http_code}\n' -X PATCH http://127.0.0.1:8000/projects/1 \
    -H 'content-type: application/json' -d '{"description":null}'
  curl -s -w '\n%{http_code}\n' -X DELETE http://127.0.0.1:8000/projects/1
  curl -s -w '\n%{http_code}\n' -X DELETE http://127.0.0.1:8000/projects/999
  ```
  Esperado: `GET /projects/1` → `200` con el recurso; `GET /projects/999` →
  `404` con clave `detail`; primer `PATCH` → `200` con `description` cambiada;
  segundo `PATCH` → `200` con `description` de nuevo `null`; `DELETE
  /projects/1` → `204` sin cuerpo; `DELETE /projects/999` → `404`; los tests
  nuevos pasan, los previos siguen pasando; `ruff` sin hallazgos.
- Commit: `feat: implementa GET, PATCH y DELETE de /projects/{id}`

### 4. Matriz mínima de tests del recurso
- Qué cambia: se completa `tests/test_projects.py` con los casos de la "Matriz
  Mínima de Tests" del contrato aplicables a Proyectos: CRUD feliz, id
  inexistente en `GET`/`PATCH`/`DELETE`, `name` vacío y con espacios ASCII,
  esquema de respuesta exacto (ni un campo de más), y orden estable en dos
  llamadas idénticas. Sin cambios de comportamiento.
- Comprobación:
  ```
  uv run pytest -q
  uv run ruff check .
  ```
  Esperado: toda la suite pasa (los tests previos más los nuevos de
  proyectos), sin debilitar ninguno; `ruff` sin hallazgos.
- Commit: `test: cubre la matriz mínima del recurso projects`
