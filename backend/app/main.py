"""FastAPI application factory."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.core.errors import register_error_handlers
from app.core.logging import configure_logging
from app.middleware.request_logging import RequestLoggingMiddleware
from app.realtime import broadcaster


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    broadcaster.start(get_settings().database_url)  # LISTEN for real-time events
    yield
    await broadcaster.stop()


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(title="Dataset Request Desk API", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    # Added last so it is the outermost layer and times the whole request.
    app.add_middleware(RequestLoggingMiddleware)
    register_error_handlers(app)
    app.include_router(api_router)
    return app


app = create_app()
