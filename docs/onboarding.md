# Mapa de Onboarding — TaskFlow API

Este documento resume, con evidencia citada (archivo y línea), lo necesario
para incorporarse al proyecto. Separa hechos verificables, inferencias
razonables y decisiones aún no establecidas.

## 1. Fuente de verdad del comportamiento

`docs/contrato-api.md` es la fuente de verdad explícita: "Este documento fija
comportamiento observable" (`docs/contrato-api.md:1-2`), y los códigos de las
tablas "son parte del contrato: son lo que afirman los tests"
(`docs/contrato-api.md:11-13`).

El código actual solo implementa una fracción mínima de ese contrato:
`GET /health` (`app/main.py:6-8`). El README lo confirma: "Esta primera
entrega expone únicamente `GET /health`; el resto del contrato [...] se
implementa en sesiones posteriores" (`README.md:3-4`).

## 2. Comandos exactos

Verificados en `README.md:15-35` y coherentes con `pyproject.toml`:

| Acción | Comando |
|---|---|
| Instalar (lockfile exacto) | `uv sync --locked` (`README.md:17`) |
| Probar | `uv run pytest -q` (`README.md:20`) |
| Revisar estilo (lint) | `uv run ruff check .` (`README.md:23`) |
| Levantar DB | `docker compose up -d` (`README.md:26`) |
| Ejecutar API (dev) | `uv run uvicorn app.main:app --reload` (`README.md:29`) |
| Detener DB | `docker compose down` (`README.md:32`) |

- `testpaths = ["tests"]` y `pythonpath = ["."]` en `pyproject.toml:22-23`.
- Config de Ruff: `target-version = "py312"`, `line-length = 100`
  (`pyproject.toml:26-27`) — no hay reglas (`select`/`ignore`) configuradas
  explícitamente, solo target y longitud.
- No hay comando de "detener la API" documentado más allá de interrumpir el
  proceso de `uvicorn --reload`.

## 3. Motor para futuros tests de persistencia

**Desconocido / no establecido con evidencia.** El contrato exige
migraciones para el seed de estados (`docs/contrato-api.md:71-78`: "El curso
adopta la migración") y menciona PostgreSQL vía `compose.yaml` (imagen
`postgres:18-alpine`, `compose.yaml:3`), pero:

- No hay ninguna dependencia de driver o ORM en `pyproject.toml` (sin
  `sqlalchemy`, `asyncpg`, `psycopg`, `alembic`).
- No existe carpeta de migraciones ni módulo de acceso a datos en el repo.
- El commit `41d751b` menciona en su mensaje un "servicio db de PostgreSQL
  18-alpine [...] con valores locales por defecto", pero eso es
  infraestructura Docker, no el motor/driver Python que usará la app.

Esta es una decisión pendiente que ninguna sesión posterior ha fijado
todavía en este repositorio.

## 4. Límites sobre archivos con secretos

- `.env` está en `.gitignore:1` — nunca se versiona.
- `.env.example` sí está versionado y contiene solo valores de desarrollo
  (`.env.example:1-4`: `taskflow_dev` / `taskflow_dev_password`), que
  coinciden exactamente con los defaults embebidos en `compose.yaml:5-7` vía
  sintaxis `${VAR:-default}`.
- README es explícito: "`compose.yaml` funciona con valores locales por
  defecto sin necesidad de crear un archivo `.env`" (`README.md:37-38`);
  `.env` es solo para personalizar credenciales.
- El `.env` presente en el working directory local es idéntico al
  `.env.example` — no contiene secretos reales, son credenciales de
  desarrollo local.
- El contrato exige explícitamente que `/health` "no expone credenciales ni
  detalles internos" (`docs/contrato-api.md:33`).

## 5. Decisiones sin evidencia (desconocidos)

- **Motor/driver de persistencia** (SQLAlchemy vs. otro, sync vs. async) —
  no fijado (ver sección 3).
- **Herramienta de migraciones** (Alembic u otra) — el contrato exige
  migraciones pero no nombra herramienta.
- **`docs/glosario.md`** — referenciado en `docs/contrato-api.md:79` (enlace
  a `#idempotente`) pero el archivo no existe en el repo; enlace roto,
  contenido pendiente.
- **Estructura interna del código** (capas, módulos) — el propio contrato
  dice "La estructura interna queda abierta salvo las restricciones de
  seguridad, migración y verificación" (`docs/contrato-api.md:2-3`), así que
  es intencionalmente indefinida, no un olvido.
- **Reglas de lint específicas de Ruff** (más allá de target/line-length) —
  no configuradas.
- **`evidencias/`** — carpeta vacía, propósito no documentado en ningún
  archivo del repo.
- **Comando para "detener" la API** en sí (no la DB) — no documentado
  explícitamente.

## Nota sobre inferencias

- Que `evidencias/` probablemente se usa en sesiones futuras del curso para
  guardar capturas o salidas es una inferencia por el nombre de la carpeta,
  sin confirmación textual en el repo.
- Que el stack de persistencia probablemente será SQLAlchemy + Alembic es
  una inferencia por ser el estándar en proyectos FastAPI + PostgreSQL, pero
  **no está confirmado** en ningún archivo del repositorio.
