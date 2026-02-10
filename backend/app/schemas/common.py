from typing import Any

from pydantic import BaseModel


class ErrorDetail(BaseModel):
    field: str | None = None
    detail: str


class ApiResponse(BaseModel):
    data: Any = None
    message: str = "ok"
    errors: list[ErrorDetail] = []
