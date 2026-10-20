"""Định dạng lỗi chung theo SRS 7.4: {"error": {"code", "message", "retryable", "fields"?}}.

Lỗi Music Engine giữ handler riêng (422, có `details`) vì đã là hợp đồng của CP1.
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class AppError(Exception):
    def __init__(
        self,
        status: int,
        code: str,
        message: str,
        *,
        retryable: bool = False,
        fields: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message
        self.retryable = retryable
        self.fields = fields
        self.headers = headers


def error_response(status: int, code: str, message: str, *, retryable: bool = False,
                   fields: dict[str, str] | None = None, headers: dict[str, str] | None = None) -> JSONResponse:
    body: dict[str, Any] = {"code": code, "message": message, "retryable": retryable}
    if fields:
        body["fields"] = fields
    return JSONResponse(status_code=status, content={"error": body}, headers=headers)


def _field_name(loc: tuple[Any, ...]) -> str:
    # ("body", "password") → "password"; ("query", "k") → "k"
    parts = [str(p) for p in loc if p not in ("body", "query", "path", "header", "cookie")]
    return ".".join(parts) or "request"


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError):
        return error_response(exc.status, exc.code, exc.message, retryable=exc.retryable,
                              fields=exc.fields, headers=exc.headers)

    @app.exception_handler(RequestValidationError)
    async def _validation_error(_: Request, exc: RequestValidationError):
        fields: dict[str, str] = {}
        for err in exc.errors():
            fields.setdefault(_field_name(tuple(err.get("loc", ()))), str(err.get("msg", "Không hợp lệ")))
        return error_response(400, "VALIDATION_ERROR", "Dữ liệu gửi lên chưa hợp lệ.", fields=fields)

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(_: Request, exc: StarletteHTTPException):
        # Router cũ ném HTTPException(detail={"code": ...}); đổi sang cùng một định dạng.
        detail = exc.detail
        if isinstance(detail, dict):
            code = str(detail.get("code", f"HTTP_{exc.status_code}"))
            message = str(detail.get("message", code))
        else:
            code = {404: "NOT_FOUND", 405: "METHOD_NOT_ALLOWED"}.get(exc.status_code, f"HTTP_{exc.status_code}")
            message = str(detail)
        return error_response(exc.status_code, code, message, retryable=exc.status_code >= 500,
                              headers=getattr(exc, "headers", None))
