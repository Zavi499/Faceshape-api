"""Request origin security helpers."""

from __future__ import annotations

from urllib.parse import urlparse

from fastapi import Request
from fastapi.responses import JSONResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware

from config import ALLOWED_ORIGINS

PUBLIC_PATHS = {
    "/docs",
    "/openapi.json",
    "/redoc",
    "/favicon.ico",
}


def _normalize_origin(value: str | None) -> str | None:
    """Normalize an Origin or Referer header into a scheme and hostname origin."""

    if not value:
        return None
    parsed = urlparse(value)
    if not parsed.scheme or not parsed.netloc:
        return None
    return f"{parsed.scheme}://{parsed.netloc}".rstrip("/")


def _is_allowed_origin(origin: str | None) -> bool:
    """Return whether an origin is explicitly allowed."""

    return origin in ALLOWED_ORIGINS


def _cors_headers(origin: str | None) -> dict[str, str]:
    """Build CORS headers for an allowed request origin."""

    if not _is_allowed_origin(origin):
        return {}
    return {
        "Access-Control-Allow-Origin": origin or "",
        "Access-Control-Allow-Methods": "GET,POST,DELETE,OPTIONS",
        "Access-Control-Allow-Headers": "Accept,Authorization,Content-Type,X-Requested-With",
        "Access-Control-Max-Age": "600",
        "Vary": "Origin",
    }


class OriginGuardMiddleware(BaseHTTPMiddleware):
    """Restrict API access to requests originating from configured frontend domains."""

    async def dispatch(self, request: Request, call_next):
        """Validate request origin and attach CORS response headers."""

        raw_origin = request.headers.get("origin")
        raw_referer = request.headers.get("referer")
        origin = _normalize_origin(raw_origin)
        referer_origin = _normalize_origin(raw_referer)
        candidate_origin = origin or referer_origin

        if request.method == "OPTIONS":
            if _is_allowed_origin(origin):
                return Response(status_code=204, headers=_cors_headers(origin))
            return JSONResponse(
                status_code=403,
                content={
                    "success": False,
                    "message": "Origin not allowed.",
                    "detail": "Requests are only accepted from facesanalyzer.com.",
                },
            )

        if request.url.path not in PUBLIC_PATHS and not _is_allowed_origin(candidate_origin):
            return JSONResponse(
                status_code=403,
                content={
                    "success": False,
                    "message": "Origin not allowed.",
                    "detail": "Requests are only accepted from facesanalyzer.com.",
                },
            )

        response = await call_next(request)
        for header, value in _cors_headers(origin).items():
            response.headers[header] = value
        return response
