"""Configuración de la API: proveedor, modelo y lectura de la clave desde el entorno."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

from api.errors import STATUS_UNAVAILABLE, ApiError

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / "secrets" / ".env"

# Mismos proveedor, modelo, temperatura y variable que usa Chat.py.
API_KEY_VARIABLE = "OPENAI_API_KEY"
API_BASE_URL = "https://openrouter.ai/api/v1"
MODEL_NAME = "cohere/north-mini-code:free"
TEMPERATURE = 0.5

# Tiempo máximo (segundos) de cada llamada al proveedor.
REQUEST_TIMEOUT_SECONDS = 30.0

ALLOWED_ORIGINS = ["http://localhost:8000", "http://127.0.0.1:8000"]


@dataclass(frozen=True)
class Settings:
    # repr=False evita que la clave aparezca en trazas o registros accidentales.
    api_key: str = field(repr=False)
    api_base: str = API_BASE_URL
    model: str = MODEL_NAME
    temperature: float = TEMPERATURE
    timeout_seconds: float = REQUEST_TIMEOUT_SECONDS


def load_settings() -> Settings:
    """Lee la clave al usarla, para que /api/health funcione aunque falte."""
    load_dotenv(ENV_FILE)
    api_key = os.getenv(API_KEY_VARIABLE)
    if api_key is not None:
        api_key = api_key.strip()
    if not api_key:
        raise ApiError(
            STATUS_UNAVAILABLE,
            "missing_api_key",
            f"Falta configurar la variable {API_KEY_VARIABLE} en secrets/.env.",
        )
    return Settings(api_key=api_key)
