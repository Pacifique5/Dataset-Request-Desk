"""Aggregates all route modules. New feature routers are registered here."""

from fastapi import APIRouter

from app.api.routes import health

api_router = APIRouter()
api_router.include_router(health.router)
