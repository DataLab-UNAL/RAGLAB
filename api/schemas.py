"""Modelos de entrada y salida de la API (toda la validación vive aquí)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

MAX_TEXT_LENGTH = 8000
MAX_HISTORY_TURNS = 10


class StrictModel(BaseModel):
    """Rechaza campos extra y tipos distintos de los declarados; recorta espacios."""

    model_config = ConfigDict(extra="forbid", strict=True, str_strip_whitespace=True)


class ChatTurn(StrictModel):
    """Un turno completo: pregunta del usuario y respuesta del asistente."""

    user: str = Field(min_length=1, max_length=MAX_TEXT_LENGTH)
    assistant: str = Field(min_length=1, max_length=MAX_TEXT_LENGTH)


class ChatRequest(StrictModel):
    question: str = Field(min_length=1, max_length=MAX_TEXT_LENGTH)
    history: list[ChatTurn] = Field(default_factory=list, max_length=MAX_HISTORY_TURNS)


class ChatResponse(StrictModel):
    answer: str
    # Esta fase no usa documentos: siempre vacío.
    sources: list[str] = Field(default_factory=list)


class HealthResponse(StrictModel):
    status: str
    service: str
