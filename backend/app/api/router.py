"""Aggregates all route modules. New feature routers are registered here."""

from fastapi import APIRouter

from app.api.routes import auth, episodes, health

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(episodes.router)
