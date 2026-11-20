"""Cliente asíncrono y reutilizable del modelo de chat (sin consola ni estado compartido)."""

from __future__ import annotations

import asyncio
import functools
import logging

import openai
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_openai import ChatOpenAI

from api.config import Settings
from api.errors import (
    STATUS_BAD_GATEWAY,
    STATUS_TIMEOUT,
    STATUS_UNAVAILABLE,
    ApiError,
)
from api.schemas import ChatTurn

logger = logging.getLogger("raglab.api")


def build_messages(question: str, history: list[ChatTurn]) -> list[BaseMessage]:
    """Ordena los mensajes: usuario/asistente de cada turno y la pregunta actual al final."""
    messages: list[BaseMessage] = []
    for turn in history:
        messages.append(HumanMessage(content=turn.user))
        messages.append(AIMessage(content=turn.assistant))
    messages.append(HumanMessage(content=question))
    return messages


def malformed_response_error() -> ApiError:
    return ApiError(
        STATUS_BAD_GATEWAY,
        "provider_malformed_response",
        "El proveedor devolvió una respuesta con formato inválido.",
    )


def error_for_status(exc: openai.APIStatusError) -> ApiError:
    """Traduce un rechazo HTTP del proveedor a una causa distinguible."""
    status = exc.status_code
    if status in (401, 403):
        return ApiError(
            STATUS_UNAVAILABLE,
            "provider_authentication_error",
            "El proveedor rechazó la clave de API (inválida, sin permisos o revocada).",
        )
    if status == 402 or getattr(exc, "code", None) == "insufficient_quota":
        return ApiError(
            STATUS_UNAVAILABLE,
            "provider_quota_exceeded",
            "Se agotó la cuota o el crédito de la cuenta del proveedor.",
        )
    if status == 429:
        return ApiError(
            STATUS_UNAVAILABLE,
            "provider_rate_limited",
            "El proveedor limitó temporalmente las peticiones; inténtalo más tarde.",
        )
    if status == 404:
        return ApiError(
            STATUS_UNAVAILABLE,
            "provider_model_not_found",
            "El proveedor no encontró el modelo configurado.",
        )
    if status >= 500:
        return ApiError(
            STATUS_UNAVAILABLE,
            "provider_unavailable",
            "El proveedor no está disponible en este momento.",
        )
    return ApiError(
        STATUS_BAD_GATEWAY,
        "provider_rejected_request",
        "El proveedor rechazó la petición.",
    )


def translate_provider_error(exc: Exception) -> ApiError:
    """Convierte cualquier fallo de la llamada al modelo en un ApiError con mensaje propio."""
    # APITimeoutError hereda de APIConnectionError: se comprueba primero.
    if isinstance(exc, (asyncio.TimeoutError, openai.APITimeoutError)):
        return ApiError(
            STATUS_TIMEOUT,
            "provider_timeout",
            "El proveedor no respondió dentro del tiempo límite.",
        )
    if isinstance(exc, openai.APIConnectionError):
        return ApiError(
            STATUS_BAD_GATEWAY,
            "provider_connection_error",
            "No se pudo establecer conexión con el proveedor.",
        )
    if isinstance(exc, openai.APIStatusError):
        return error_for_status(exc)
    # Cualquier otro fallo al interpretar la respuesta se trata como formato inválido.
    return malformed_response_error()


def extract_answer(response: object) -> str:
    """Obtiene el texto de la respuesta o falla si está vacía o malformada."""
    content = getattr(response, "content", None)
    if not isinstance(content, str):
        raise malformed_response_error()
    answer = content.strip()
    if not answer:
        raise ApiError(
            STATUS_BAD_GATEWAY,
            "provider_empty_response",
            "El proveedor devolvió una respuesta vacía.",
        )
    return answer


class ChatModelClient:
    """Envuelve el modelo de OpenRouter; sin reintentos y con tiempo límite finito."""

    def __init__(self, settings: Settings) -> None:
        self._timeout = settings.timeout_seconds
        self._model = ChatOpenAI(
            openai_api_base=settings.api_base,
            openai_api_key=settings.api_key,
            model_name=settings.model,
            temperature=settings.temperature,
            timeout=settings.timeout_seconds,
            max_retries=0,
        )

    async def answer(self, question: str, history: list[ChatTurn]) -> str:
        messages = build_messages(question, history)
        try:
            # wait_for acota el tiempo total; el timeout del cliente acota cada fase de red.
            response = await asyncio.wait_for(
                self._model.ainvoke(messages), timeout=self._timeout
            )
        except Exception as exc:
            error = translate_provider_error(exc)
            # Solo se registra el tipo de excepción: su texto podría incluir secretos.
            logger.warning("Fallo del proveedor (%s): %s", error.code, type(exc).__name__)
            raise error from None
        return extract_answer(response)


@functools.lru_cache(maxsize=4)
def get_chat_client(settings: Settings) -> ChatModelClient:
    """Reutiliza el cliente (y su pool de conexiones) mientras la configuración no cambie."""
    return ChatModelClient(settings)
