# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Fuentes de verdad

- `docs/contrato-api.md` fija el comportamiento observable de la API. Solo se
  modifica cuando el ticket dice explícitamente que cambia el contrato.
- `docs/decisiones-ingenieria.md` fija las decisiones de equipo que no se
  deducen del código.
- `README.md` contiene los comandos canónicos del repositorio.

## Comandos canónicos

```bash
uv sync --locked      # instalar dependencias exactas del lockfile
uv run pytest -q      # correr los tests
uv run ruff check .   # lint
```

## Reglas no negociables

- Los tests que ejercitan persistencia corren contra **PostgreSQL**, nunca
  contra SQLite.
- `.env` puede contener secretos: no lo abras, muestres, edites ni lo
  confirmes (commit).
- No se debilita ni elimina un test existente para conseguir verde. Si el
  comportamiento acordado cambió, primero se actualiza el contrato
  (`docs/contrato-api.md`) y después el test, en un commit separado.
