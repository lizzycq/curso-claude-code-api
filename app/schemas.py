import unicodedata
from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, field_serializer, field_validator

# Categorías Unicode sin ningún carácter visible: controles, formato y
# separadores. strip() no basta: hay invisibles como U+200B que lo atraviesan.
_CATEGORIAS_INVISIBLES = {"Cc", "Cf", "Zl", "Zp", "Zs"}


def normalizar_texto_visible(valor: str) -> str:
    """Recorta los extremos y exige al menos un carácter visible.

    Se aplica antes de validar y guardar. Rechaza con ValueError el valor que
    tras el recorte no deja ningún carácter fuera de _CATEGORIAS_INVISIBLES.
    """
    recortado = valor.strip()
    if not recortado or all(
        unicodedata.category(caracter) in _CATEGORIAS_INVISIBLES
        for caracter in recortado
    ):
        raise ValueError("el texto no tiene ningún carácter visible")
    return recortado


class ProjectIn(BaseModel):
    name: str
    description: str | None = None

    @field_validator("name")
    @classmethod
    def _name_visible(cls, valor: str) -> str:
        return normalizar_texto_visible(valor)


class ProjectUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    description: str | None = None

    @field_validator("name")
    @classmethod
    def _name_visible(cls, valor: str | None) -> str | None:
        if valor is None:
            return None
        return normalizar_texto_visible(valor)


class ProjectOut(BaseModel):
    id: int
    name: str
    description: str | None


def _due_at_a_utc(valor: datetime | None) -> datetime | None:
    """Exige zona horaria explícita y normaliza a UTC.

    Una fecha sin zona es ambigua: se rechaza con ValueError (el contrato no
    supone ninguna por su cuenta).
    """
    if valor is None:
        return None
    if valor.tzinfo is None or valor.tzinfo.utcoffset(valor) is None:
        raise ValueError("due_at debe incluir zona horaria")
    return valor.astimezone(UTC)


class TaskIn(BaseModel):
    title: str
    description: str | None = None
    project_id: int
    state_id: int
    due_at: datetime | None = None

    @field_validator("title")
    @classmethod
    def _title_visible(cls, valor: str) -> str:
        return normalizar_texto_visible(valor)

    @field_validator("due_at")
    @classmethod
    def _due_at_con_zona(cls, valor: datetime | None) -> datetime | None:
        return _due_at_a_utc(valor)


class TaskUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = None
    description: str | None = None
    project_id: int | None = None
    state_id: int | None = None
    due_at: datetime | None = None

    @field_validator("title")
    @classmethod
    def _title_visible(cls, valor: str | None) -> str | None:
        if valor is None:
            return None
        return normalizar_texto_visible(valor)

    @field_validator("due_at")
    @classmethod
    def _due_at_con_zona(cls, valor: datetime | None) -> datetime | None:
        return _due_at_a_utc(valor)


class TaskOut(BaseModel):
    id: int
    title: str
    description: str | None
    project_id: int
    state_id: int
    due_at: datetime | None

    @field_serializer("due_at", when_used="json")
    def _serializa_due_at(self, valor: datetime | None) -> str | None:
        if valor is None:
            return None
        return (
            valor.astimezone(UTC)
            .replace(microsecond=0)
            .strftime("%Y-%m-%dT%H:%M:%SZ")
        )
