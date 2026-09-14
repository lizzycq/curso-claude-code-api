# TaskFlow API

API de TaskFlow construida con FastAPI, administrada con [uv](https://docs.astral.sh/uv/)
sobre Python 3.12, con persistencia en PostgreSQL vía SQLAlchemy y migraciones
de Alembic. El comportamiento observable completo está documentado en
[`docs/contrato-api.md`](docs/contrato-api.md).

## Requisitos

- Python 3.12
- [uv](https://docs.astral.sh/uv/)
- Docker y Docker Compose
- Para probar peticiones con [`api.http`](api.http): un editor con soporte
  para archivos `.http` (por ejemplo, VS Code con la extensión
  [REST Client](https://marketplace.visualstudio.com/items?itemName=humao.rest-client)),
  o `curl` como alternativa manual.

## Recorrido

Instalar, levantar la base, migrar y arrancar la API, en este orden:

```bash
# 1. Instalar dependencias exactas del lockfile
uv sync --locked

# 2. Levantar la base de datos (PostgreSQL)
docker compose up -d

# 3. Comprobar que la base quedó lista (STATUS debe decir "healthy")
docker compose ps

# 4. Aplicar las migraciones
uv run alembic upgrade head

# 5. Ejecutar la API en modo desarrollo
uv run uvicorn app.main:app --reload
```

La API queda disponible en `http://127.0.0.1:8000`. Verifica el estado con:

```bash
curl http://127.0.0.1:8000/health
```

## Probar un endpoint

Con la API arriba, abre [`api.http`](api.http) en un cliente que entienda el
formato (VS Code + REST Client, por ejemplo) y ejecuta el primer bloque
(`GET /health`). Cada petición del archivo deja su resultado disponible para
las siguientes, así que conviene ejecutarlas en el orden en que aparecen. El
contrato completo —métodos, rutas y comportamiento esperado de cada uno— está
en [`docs/contrato-api.md`](docs/contrato-api.md).

## Otros comandos

```bash
# Correr la batería de tests (requiere la base levantada y migrada)
uv run pytest -q

# Ejecutar el linter
uv run ruff check .

# Detener la base de datos
docker compose down
```

## Configuración

`compose.yaml` funciona con valores locales por defecto sin necesidad de crear
un archivo `.env`. Para personalizar las credenciales de PostgreSQL, copia
`.env.example` a `.env` y ajusta los valores:

```bash
cp .env.example .env
```
