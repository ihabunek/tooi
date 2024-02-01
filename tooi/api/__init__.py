import httpx
import logging
import time

from httpx import Response
from tooi.api.types import RequestParams
from tooi.context import get_context
from typing import Optional, Tuple, Unpack

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Represents an error response from the API."""
    def __init__(self, message: str | None = None, cause: Exception | None = None):
        assert (message or cause)
        self.message = message or str(cause)
        self.cause = cause
        super().__init__(self.message)


class ResponseError(APIError):
    """Raised when the API returns a response with status code >= 400."""
    def __init__(self, status_code: int, error: str | None, description: str | None):
        self.status_code = status_code
        self.error = error
        self.description = description

        msg = f"HTTP {status_code}"
        msg += f". Error: {error}" if error else ""
        msg += f". Description: {description}" if description else ""
        super().__init__(msg)


async def request(method: str, url: str, **kwargs: Unpack[RequestParams]) -> Response:
    ctx = get_context()
    started_at = time.time()
    log_request(method, url, **kwargs)

    try:
        response = await ctx.auth.client.request(method, url, **kwargs)
        log_response(response, started_at)
        response.raise_for_status()
        return response
    except httpx.HTTPStatusError as ex:
        error, description = await get_error(ex.response)
        raise ResponseError(ex.response.status_code, error, description)
    except httpx.TimeoutException:
        logger.error(f"<-- {method} {url} Request timed out")
        raise APIError(message="Request timed out")
    except httpx.RequestError as exc:
        logger.error(f"<-- {method} {url} Exception: {str(exc)}")
        logger.exception(exc)
        raise APIError(cause=exc)


def log_request(method: str, url: str, **kwargs: Unpack[RequestParams]):
    ctx = get_context()
    merged_url = ctx.auth.client._merge_url(url)
    logger.info(f"--> {method} {merged_url}")

    for key in ["params", "data", "json", "files"]:
        if key in kwargs:
            logger.debug(f"--> {key}={kwargs[key]}")


def log_response(response: Response, started_at: float):
    request = response.request
    duration_ms = int(1000 * (time.time() - started_at))
    logger.info(f"<-- {request.method} {request.url} HTTP {response.status_code} {duration_ms}ms")


async def get_error(response: Response) -> Tuple[Optional[str], Optional[str]]:
    """Attempt to extract the error and error description from response body.

    See: https://docs.joinmastodon.org/entities/error/
    """
    try:
        data = response.json()
        return data.get("error"), data.get("error_description")
    except Exception:
        return None, None
