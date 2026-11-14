"""Exception handlers that render every error as an RFC 9457 problem document.

Uniform error shape is part of the contract: the UI, the mock clients, and the API tests
all switch on ``code``/``status``, never on message text.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.discovery.cocoindex import CocoIndexError
from app.discovery.code_index import CrossBaselineError, SnapshotError
from app.domain.api import ProblemDetails
from app.domain.errors import DomainError, FeatureNotImplemented

logger = logging.getLogger(__name__)

PROBLEM_TYPE_PREFIX = "urn:cta:error:"

_HTTP_TITLES = {
    404: "Not found",
    405: "Method not allowed",
    422: "Unprocessable request",
}


def problem_response(
    *,
    status: int,
    code: str,
    title: str,
    detail: str,
    instance: str,
    story: str | None = None,
    milestone: str | None = None,
) -> JSONResponse:
    body = ProblemDetails(
        type=f"{PROBLEM_TYPE_PREFIX}{code}",
        title=title,
        status=status,
        detail=detail,
        instance=instance,
        code=code,
        story=story,
        milestone=milestone,
    )
    return JSONResponse(status_code=status, content=body.model_dump(exclude_none=True))


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def _domain_error(request: Request, exc: DomainError) -> JSONResponse:
        if isinstance(exc, FeatureNotImplemented):
            logger.info("contract-only endpoint called: %s", request.url.path)
            return problem_response(
                status=exc.status,
                code=exc.code,
                title=exc.title,
                detail=exc.detail,
                instance=request.url.path,
                story=exc.story,
                milestone=exc.milestone,
            )
        return problem_response(
            status=exc.status,
            code=exc.code,
            title=exc.title,
            detail=exc.detail,
            instance=request.url.path,
        )

    @app.exception_handler(CocoIndexError)
    async def _cocoindex_error(request: Request, exc: CocoIndexError) -> JSONResponse:
        return problem_response(
            status=503,
            code=exc.code,
            title="CocoIndex retrieval unavailable",
            detail=str(exc),
            instance=request.url.path,
        )

    @app.exception_handler(CrossBaselineError)
    async def _cross_baseline_error(request: Request, exc: CrossBaselineError) -> JSONResponse:
        return problem_response(
            status=409,
            code="cross-baseline",
            title="Cross-baseline retrieval refused",
            detail=str(exc),
            instance=request.url.path,
        )

    @app.exception_handler(SnapshotError)
    async def _snapshot_error(request: Request, exc: SnapshotError) -> JSONResponse:
        return problem_response(
            status=422,
            code="snapshot-invalid",
            title="Retrieval snapshot invalid",
            detail=str(exc),
            instance=request.url.path,
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        problems = [
            f"{'.'.join(str(part) for part in error['loc'][1:]) or 'body'}: {error['msg']}"
            for error in exc.errors()
        ]
        return problem_response(
            status=422,
            code="request-validation",
            title="Request validation failed",
            detail="; ".join(problems),
            instance=request.url.path,
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        status = exc.status_code
        return problem_response(
            status=status,
            code=f"http-{status}",
            title=_HTTP_TITLES.get(status, "HTTP error"),
            detail=str(exc.detail),
            instance=request.url.path,
        )

    @app.exception_handler(Exception)
    async def _unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled error while serving %s", request.url.path)
        return problem_response(
            status=500,
            code="internal-error",
            title="Internal error",
            detail=f"{type(exc).__name__}: {exc}",
            instance=request.url.path,
        )
