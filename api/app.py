"""Aplicación FastAPI de RAGLAB.

Arranque:  python -m uvicorn api.app:app --port 8010
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import ALLOWED_ORIGINS
from api.errors import register_error_handlers
from api.routes import router


def create_app() -> FastAPI:
    app = FastAPI(title="RAGLAB API")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )
    register_error_handlers(app)
    app.include_router(router)
    return app


app = create_app()
