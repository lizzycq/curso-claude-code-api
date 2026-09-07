---
name: planificar-incremento
description: >-
  Redacta el plan de un incremento de trabajo de este repositorio: lo planifica
  contra el contrato y las decisiones de ingeniería, lo escribe en docs/ con un
  nombre que diga de qué es, lo parte en incrementos numerados con una
  comprobación ejecutable por incremento, no aplaza ninguna decisión (pregunta
  en vez de proponer en condicional) y declara qué queda fuera de alcance.
  Planifica; no implementa.
---

# planificar-incremento

Produce un documento de plan para un incremento de TaskFlow. El entregable es
un archivo Markdown en `docs/`. Esta skill **no escribe código ni tests, no
instala dependencias y no toca la base de datos** (ver "Límites").

## Fuentes contra las que se planifica

Se leen antes de redactar nada. Son la única base admitida para justificar
decisiones:

- `docs/contrato-api.md` — comportamiento observable de la API. El plan no lo
  modifica; se ciñe a las secciones que el incremento toca y las cita.
- `docs/decisiones-ingenieria.md` — decisiones del equipo que no se deducen del
  código (persistencia en PostgreSQL, migraciones con `upgrade`/`downgrade`
  probadas en ambos sentidos, TDD empezando por un test que falla, no debilitar
  tests existentes).
- `README.md` — comandos canónicos del repositorio (`uv sync --locked`,
  `uv run pytest -q`, `uv run ruff check .`, `docker compose up -d`).
- `CLAUDE.md` — reglas no negociables del repositorio.
- Los `docs/plan-*.md` que ya existan, como referencia de formato y de lo ya
  planificado.

Si el usuario nombró un ticket o una consigna, esa fija el alcance; el plan no
lo amplía por su cuenta.

## Procedimiento

1. **Leer las fuentes de arriba** y el estado actual del repositorio relevante
   al incremento (módulos, tests y migraciones que ya existen). Solo lectura.
2. **Fijar el alcance** en una o dos frases: qué capacidad observable añade
   este incremento, anclada a una sección concreta de `docs/contrato-api.md`.
3. **Detectar las decisiones que el incremento exige** (driver, forma de una
   tabla, formato de una respuesta, criterio de orden, códigos de error…).
   Para cada una:
   - Si el repositorio (código, contrato, decisiones de ingeniería, plan
     previo) permite decidirla, se decide y se escribe en afirmativo, citando
     de dónde sale.
   - Si **no** se puede decidir con lo que hay, **se pregunta al usuario** con
     una pregunta concreta. No se escribe en condicional ("se podría…", "quizá
     convenga…"), no se deja "a criterio de la implementación" ni se aplaza a
     una sesión posterior. El plan no avanza hasta que esa decisión está
     cerrada.
4. **Partir el trabajo en incrementos numerados** (`### 1.`, `### 2.`, …),
   cada uno confirmable por su cuenta en un commit. Cada incremento declara:
   - Qué cambia, en términos de comportamiento o de estructura.
   - **Su propia comprobación ejecutable**: los comandos exactos que otra
     persona correría para verificar ese incremento (de los comandos canónicos
     de `README.md` más lo específico del incremento — p. ej.
     `uv run alembic upgrade head && uv run alembic downgrade base`,
     `curl -s -w '\n%{http_code}\n' http://127.0.0.1:8000/<ruta>`), y el
     resultado esperado.
   - El commit previsto, con un asunto de una línea.
5. **Escribir "Fuera de alcance"**: una lista explícita de lo que este plan
   NO cubre (capacidades vecinas, endpoints relacionados, CI, hooks, skills,
   rendimiento…), para que nadie lo dé por incluido.
6. **Guardar el plan en `docs/`** con un nombre que diga de qué es:
   `docs/plan-<tema>.md` (p. ej. `docs/plan-projects.md`,
   `docs/plan-tareas-due-at.md`). Si ya existe uno con ese nombre, se acuerda
   con el usuario si se reemplaza o se versiona.
7. **Enseñar el plan al usuario** antes de darlo por cerrado.

## Estructura del archivo de plan

```
# Plan: <tema>

Objetivo: <una o dos frases; capacidad observable + sección del contrato>.

Fuentes: docs/contrato-api.md (<secciones>), docs/decisiones-ingenieria.md,
README.md, CLAUDE.md.

Fuera de alcance: <lista explícita>.

## Decisiones tomadas

- <decisión> — <de dónde sale en el repositorio>.

## Incrementos

### 1. <título>
- Qué cambia: <...>
- Comprobación: <comandos exactos> → <resultado esperado>.
- Commit: <asunto de una línea>.

### 2. <título>
...
```

## Límites

- **Planifica; no implementa.** No crea ni modifica código, tests, migraciones
  ni archivos de configuración fuera del propio `docs/plan-<tema>.md`.
- **No instala dependencias** (`uv sync`, `uv add`, editar `pyproject.toml`).
- **No toca la base de datos** ni ejecuta `alembic upgrade/downgrade`; los
  comandos de migración se escriben en el plan como comprobación, no se corren
  aquí.
- No abre PRs ni hace commits del plan salvo que el usuario lo pida por
  separado.
- No modifica `docs/contrato-api.md` ni `docs/decisiones-ingenieria.md`.
