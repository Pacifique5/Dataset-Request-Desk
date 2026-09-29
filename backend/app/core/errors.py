"""Domain errors and their HTTP mapping.

Services raise these (they know nothing about HTTP); one handler turns them into a
consistent JSON body: {"detail": "...", "code": "..."}.
"""

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger("app.errors")


class DomainError(Exception):
    status_code = 400
    code = "bad_request"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(DomainError):
    status_code = 404
    code = "not_found"


class PermissionDeniedError(DomainError):
    status_code = 403
    code = "forbidden"


class ConflictError(DomainError):
    status_code = 409
    code = "conflict"


class InvalidTransitionError(ConflictError):
    code = "invalid_transition"


class BusinessRuleError(DomainError):
    status_code = 422
    code = "business_rule_violation"


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def _domain(_: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse({"detail": exc.message, "code": exc.code}, exc.status_code)

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception) -> JSONResponse:
        # Never leak internals to the client; the request_id links the log line.
        request_id = request.scope.get("state", {}).get("request_id")
        logger.exception("unhandled_error", extra={"request_id": request_id})
        return JSONResponse(
            {"detail": "Internal server error", "code": "internal_error", "request_id": request_id},
            status_code=500,
        )
