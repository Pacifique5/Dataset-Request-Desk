"""Aggregates all route modules. New feature routers are registered here."""

from fastapi import APIRouter

from app.api.routes import assignments, auth, episodes, health, requests

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(episodes.router)
api_router.include_router(requests.router)
api_router.include_router(assignments.router)
