"""Errores de la API y su conversión al formato {"error": {"code", "message"}}."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

STATUS_VALIDATION = 422
STATUS_BAD_GATEWAY = 502
STATUS_UNAVAILABLE = 503
STATUS_TIMEOUT = 504


class ApiError(Exception):
    """Error controlado: lleva estado HTTP, código estable y causa legible.

    El mensaje es siempre texto propio de la API: nunca se copia el texto de
    excepciones externas, porque podrían contener fragmentos de secretos.
    """

    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


def error_body(code: str, message: str) -> dict:
    return {"error": {"code": code, "message": message}}


def describe_validation_errors(exc: RequestValidationError) -> str:
    """Resume los fallos con campo y regla, sin devolver los valores recibidos."""
    details = []
    for item in exc.errors():
        location = ".".join(str(part) for part in item["loc"] if part != "body")
        if location:
            details.append(f"{location}: {item['msg']}")
        else:
            details.append(str(item["msg"]))
    return "; ".join(details)


async def handle_api_error(request: Request, exc: ApiError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code, content=error_body(exc.code, exc.message)
    )


async def handle_validation_error(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=STATUS_VALIDATION,
        content=error_body("validation_error", describe_validation_errors(exc)),
    )


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(ApiError, handle_api_error)
    app.add_exception_handler(RequestValidationError, handle_validation_error)
