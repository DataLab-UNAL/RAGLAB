"""Rutas HTTP: solo reciben la petición y delegan en configuración y modelo."""

from __future__ import annotations

from fastapi import APIRouter

from api.config import load_settings
from api.llm import get_chat_client
from api.schemas import ChatRequest, ChatResponse, HealthResponse

router = APIRouter(prefix="/api")


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    # No toca configuración ni modelo: responde aunque falte la clave.
    return HealthResponse(status="ok", service="RAGLAB")


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    # FastAPI ya validó el cuerpo; la clave solo se exige si la petición es válida.
    client = get_chat_client(load_settings())
    answer = await client.answer(request.question, request.history)
    return ChatResponse(answer=answer, sources=[])
