# Plan: Conexión de la API a PostgreSQL

Objetivo: conectar la API a PostgreSQL en incrementos pequeños, cada uno
confirmable por su cuenta.

Fuentes: `docs/contrato-api.md` (secciones Salud y Estados),
`docs/decisiones-ingenieria.md`, `CLAUDE.md`.

Fuera de alcance: proyectos, tareas, filtros, `due_at`, skills, hooks y CI.

## Incrementos

### 1. Driver y conexión a Postgres

- Agregar `sqlalchemy`, `psycopg[binary]` y `alembic` a `pyproject.toml`.
- Crear `app/db.py` con el engine/sesión, leyendo la URL de conexión desde
  variables de entorno (nombres de `.env.example`), sin leer `.env`.
- Test: conexión real contra el Postgres de `compose.yaml` (`SELECT 1`).
- Comprobación: `uv sync --locked`, `docker compose up -d`,
  `uv run pytest -q`, `uv run ruff check .`.

**Commit:** `887c91d` — Agrega conexión SQLAlchemy a PostgreSQL.

### 2. Esqueleto de Alembic

- `alembic init` apuntando al metadata de SQLAlchemy (`app/db.py: Base`).
- `env.py` toma la URL desde `app.db.get_database_url()` — una sola fuente
  de verdad para la conexión.
- Comprobación: `alembic upgrade head` y `alembic downgrade base` corren
  limpio sobre base vacía (sin migraciones propias todavía).

**Commit:** `b61bdf8` — Inicializa Alembic apuntando al metadata de la app.

### 3. Migración y modelo del catálogo `states`

- Modelo SQLAlchemy `State` (`id`, `code`, `sort_order`) según el esquema
  de respuesta del contrato.
- Migración que crea la tabla y siembra el catálogo fijo (`PENDIENTE`,
  `EN_CURSO`, `BLOQUEADA`, `HECHA`) de forma idempotente
  (`INSERT ... ON CONFLICT DO NOTHING`).
- Test (TDD, falla primero por ausencia de la tabla): tras `upgrade`, el
  catálogo existe con los 4 códigos; correr `upgrade` dos veces no
  duplica; `downgrade` revierte limpiamente.
- Comprobación: `uv run pytest -q` contra Postgres real, `alembic upgrade
  head` + `alembic downgrade base` + `alembic upgrade head` de nuevo,
  `uv run ruff check .`.

**Commit:** `1e6ee94` — Agrega modelo y migración del catálogo de estados.

### 4. Endpoint `GET /states`

- Devuelve la lista ordenada por `sort_order` y `id` como desempate, con
  el esquema exacto (`{"id": ..., "code": ...}`, sin campos de más).
- Test (TDD, falla primero por ausencia del endpoint): `200`, orden
  esperado, esquema exacto, orden estable entre llamadas idénticas.
- Comprobación: `uv run pytest -q`, `uv run ruff check .`, verificación
  manual con `curl http://127.0.0.1:8000/states`.

**Commit:** `2a6a38a` — Implementa GET /states.

### 5. `/health` refleja disponibilidad de la base (no incluido)

Quedó fuera del plan: el contrato actual no exige que `/health` verifique
la base. Se retoma solo si un ticket lo pide explícitamente.

## Estado

Los 4 incrementos están completados y confirmados en la rama
`feature/persistencia`, cada uno en un commit separado con su propia
comprobación en verde (`pytest` contra PostgreSQL real + `ruff`), sin
modificar `docs/contrato-api.md`, `docs/decisiones-ingenieria.md`,
`CLAUDE.md`, `.gitignore` ni `.env`, y sin debilitar ningún test existente.
