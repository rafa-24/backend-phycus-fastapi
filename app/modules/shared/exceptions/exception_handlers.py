import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.modules.shared.exceptions.app_exceptions import AppException

logger = logging.getLogger(__name__)


def _format_validation_error(errors: list) -> str:
    if not errors:
        return "Error de validación en los datos enviados."

    first = errors[0]
    location = first.get("loc", ())
    field_parts = [
        str(part) for part in location if part not in ("body", "query", "path")
    ]
    field = ".".join(field_parts)
    message = first.get("msg", "Valor inválido.")

    if field:
        return f"{field}: {message}"

    return message


async def app_exception_handler(_: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.message},
    )


async def validation_exception_handler(
    _: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"message": _format_validation_error(exc.errors())},
    )


async def http_exception_handler(
    _: Request, exc: StarletteHTTPException
) -> JSONResponse:
    detail = exc.detail

    if isinstance(detail, str):
        message = detail
    elif isinstance(detail, list):
        message = _format_validation_error(detail)
    else:
        message = "Ha ocurrido un error."

    return JSONResponse(
        status_code=exc.status_code,
        content={"message": message},
    )


async def generic_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("Error no controlado: %s", exc)

    return JSONResponse(
        status_code=500,
        content={"message": "Ha ocurrido un error interno del servidor."},
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
