import unicodedata

from pydantic import BaseModel, ConfigDict, field_validator

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
