from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from backend.config import FILTERS_BY_KEY


SearchMode = Literal["filters", "business_name", "nit", "batch_nits"]

MODE_LABELS: dict[str, str] = {
    "filters": "Segmentación por filtros",
    "business_name": "Búsqueda por razón social",
    "nit": "Búsqueda por NIT",
    "batch_nits": "Búsqueda masiva por NIT",
}


def _clean_filters(selections: dict[str, list[str]]) -> dict[str, list[str]]:
    if len(selections) > len(FILTERS_BY_KEY):
        raise ValueError("Demasiados filtros.")
    unknown = sorted(set(selections) - set(FILTERS_BY_KEY))
    if unknown:
        raise ValueError(f"Filtros no permitidos: {', '.join(unknown)}.")
    cleaned: dict[str, list[str]] = {}
    for key, values in selections.items():
        if len(values) > 250:
            raise ValueError(f"Demasiados valores para {key}.")
        unique: list[str] = []
        seen: set[str] = set()
        for value in values:
            item = str(value).strip()[:300]
            if item and item not in seen:
                seen.add(item)
                unique.append(item)
        if unique:
            cleaned[key] = unique
    return cleaned


def clean_nit(value: object) -> str:
    return "".join(character for character in str(value) if character.isdigit())


class FilterOptionsRequest(BaseModel):
    selections: dict[str, list[str]] = Field(default_factory=dict)

    @field_validator("selections")
    @classmethod
    def limit_selections(cls, selections: dict[str, list[str]]) -> dict[str, list[str]]:
        return _clean_filters(selections)


class SearchRequest(BaseModel):
    mode: SearchMode = "filters"
    filters: dict[str, list[str]] = Field(default_factory=dict)
    term: str = ""
    nits: list[str] = Field(default_factory=list)
    page: int = Field(default=1, ge=1, le=400)
    page_size: int = Field(default=25, ge=10, le=100)

    @field_validator("filters")
    @classmethod
    def clean_filters(cls, selections: dict[str, list[str]]) -> dict[str, list[str]]:
        return _clean_filters(selections)

    @field_validator("term")
    @classmethod
    def clean_term(cls, value: str) -> str:
        return value.strip()[:180]

    @field_validator("nits")
    @classmethod
    def clean_nits(cls, values: list[str]) -> list[str]:
        unique: list[str] = []
        seen: set[str] = set()
        for value in values:
            nit = clean_nit(value)
            if 2 <= len(nit) <= 12 and nit not in seen:
                seen.add(nit)
                unique.append(nit)
            if len(unique) >= 5000:
                break
        return unique

    @model_validator(mode="after")
    def validate_mode_payload(self) -> "SearchRequest":
        if self.mode in {"business_name", "nit"} and not self.term:
            raise ValueError("Escribe un criterio de búsqueda.")
        if self.mode == "business_name" and len(self.term) < 2:
            raise ValueError("Escribe al menos dos caracteres de la razón social.")
        if self.mode == "nit" and not any(character.isdigit() for character in self.term):
            raise ValueError("El NIT debe contener números.")
        if self.mode == "batch_nits" and not self.nits:
            raise ValueError("Carga al menos un NIT válido.")
        return self

    def summary(self) -> str:
        """Descripción corta de la consulta, para trazabilidad y nombres de archivo."""
        if self.mode == "business_name":
            return f"razón social contiene «{self.term}»"
        if self.mode == "nit":
            return f"NIT contiene «{clean_nit(self.term)}»"
        if self.mode == "batch_nits":
            return f"lote de {len(self.nits)} NIT"
        active = sum(len(values) for values in self.filters.values())
        return f"{active} criterio(s) de filtro" if active else "toda la base empresarial"
