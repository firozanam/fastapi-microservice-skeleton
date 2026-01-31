"""
Logging middleware for request/response logging.
"""
import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import get_logger

logger = get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests and responses."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        """
        Process request and log details.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware or route handler

        Returns:
            HTTP response
        """
        # Start timer
        start_time = time.time()

        # Get request details
        method = request.method
        url = str(request.url)
        client_host = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")

        # Log request
        logger.info(
            "Incoming request",
            method=method,
            path=url,
            client_host=client_host,
            user_agent=user_agent,
        )

        # Process request
        try:
            response = await call_next(request)

            # Calculate processing time
            process_time = time.time() - start_time

            # Add custom header
            response.headers["X-Process-Time"] = str(process_time)

            # Log response
            logger.info(
                "Request completed",
                method=method,
                path=url,
                status_code=response.status_code,
                process_time=round(process_time, 4),
            )

            return response

        except Exception as e:
            # Calculate processing time
            process_time = time.time() - start_time

            # Log error
            logger.error(
                "Request failed",
                method=method,
                path=url,
                error=str(e),
                process_time=round(process_time, 4),
            )
            raise
