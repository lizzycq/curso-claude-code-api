# TaskFlow API

API de TaskFlow construida con FastAPI, administrada con [uv](https://docs.astral.sh/uv/)
sobre Python 3.12. Esta primera entrega expone únicamente `GET /health`; el resto
del contrato (`docs/contrato-api.md`) se implementa en sesiones posteriores.

## Requisitos

- Python 3.12
- [uv](https://docs.astral.sh/uv/)
- Docker y Docker Compose

## Recorrido

```bash
# 1. Instalar dependencias exactas del lockfile
uv sync --locked

# 2. Ejecutar la batería de tests
uv run pytest -q

# 3. Ejecutar el linter
uv run ruff check .

# 4. Levantar la base de datos (PostgreSQL)
docker compose up -d

# 5. Ejecutar la API en modo desarrollo
uv run uvicorn app.main:app --reload

# 6. Detener la base de datos
docker compose down
```

La API queda disponible en `http://127.0.0.1:8000`. Verifica el estado con:

```bash
curl http://127.0.0.1:8000/health
```

## Configuración

`compose.yaml` funciona con valores locales por defecto sin necesidad de crear
un archivo `.env`. Para personalizar las credenciales de PostgreSQL, copia
`.env.example` a `.env` y ajusta los valores:

```bash
cp .env.example .env
```
