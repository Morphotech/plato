import json
import logging
from http import HTTPStatus
from time import time
from typing import Any, Callable, Coroutine

from fastapi import HTTPException, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.routing import APIRoute
from pydantic import BaseModel

logger = logging.getLogger(__name__)

BODYLESS_CONTENT_TYPES = ("multipart/form-data", "application/x-www-form-urlencoded")


class RequestLoggerRoute(APIRoute):
    """
    Custom route that logs every request it handles: method, path, query, content-type, status, request body and
    execution time. Logs at INFO for successful responses, WARNING for client-caused outcomes (raised HTTPExceptions,
    FastAPI request validation errors, or manually returned 4xx/5xx responses), and ERROR with a traceback
    for genuinely unhandled exceptions.
    """

    class LoggerContext(BaseModel):
        http_method: str
        url: str
        query: str
        content_type: str
        status: int | None = None
        execution_time: float | None = None
        body: dict[str, Any] | None = None

    def get_route_handler(self) -> Callable[[Request], Coroutine[Any, Any, Response]]:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            content_type = request.headers.get("content-type", "").split(";")[0]
            logger_context = self.LoggerContext(
                http_method=request.method,
                url=request.url.path,
                query=request.url.query,
                content_type=content_type,
            )
            start_time = time()

            if content_type not in BODYLESS_CONTENT_TYPES:
                raw_body = await request.body()
                if raw_body:
                    try:
                        logger_context.body = json.loads(raw_body)
                    except ValueError:
                        logger_context.body = None

            try:
                response = await original_route_handler(request)
            except HTTPException as exc:
                logger_context.status = exc.status_code
                logger_context.execution_time = time() - start_time
                logger.warning(f"Client warning in request - {logger_context.model_dump_json(exclude_none=True)}")
                raise
            except RequestValidationError:
                # Not an HTTPException, but still a normal client-caused failure (FastAPI
                # converts it to a 422 response one layer up) — log as a warning, not an
                # unhandled server error.
                logger_context.status = status.HTTP_422_UNPROCESSABLE_ENTITY
                logger_context.execution_time = time() - start_time
                logger.warning(f"Client warning in request - {logger_context.model_dump_json(exclude_none=True)}")
                raise
            except Exception:
                logger_context.execution_time = time() - start_time
                logger.exception(f"Server error in request - {logger_context.model_dump_json(exclude_none=True)}")
                raise

            logger_context.status = response.status_code
            logger_context.execution_time = time() - start_time
            if response.status_code >= HTTPStatus.BAD_REQUEST:
                logger.warning(f"Client warning in request - {logger_context.model_dump_json(exclude_none=True)}")
            else:
                logger.info(f"Successful request - {logger_context.model_dump_json(exclude_none=True)}")

            return response

        return custom_route_handler
