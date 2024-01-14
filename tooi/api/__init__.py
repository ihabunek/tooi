import logging
import time

from httpx import Response, RequestError
from tooi.context import get_context
from tooi.api.types import RequestParams
from typing import Optional, Tuple, Unpack

logger = logging.getLogger(__name__)


class APIError(Exception):
    """
    Represents an error response from the API.
    """

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
    start = time.time()
    logger.info(f"--> {method} {url}")

    try:
        response = await ctx.auth.client.request(method, url, **kwargs)
    except RequestError as exc:
        raise (APIError(cause=exc))

    duration_ms = int(1000 * (time.time() - start))

    if response.is_success:
        logger.info(f"<-- {method} {url} HTTP {response.status_code} {duration_ms}ms")
        return response

    error, description = await get_error(response)
    raise ResponseError(response.status_code, error, description)


async def get_error(response: Response) -> Tuple[Optional[str], Optional[str]]:
    """Attempt to extract the error and error description from response body.

    See: https://docs.joinmastodon.org/entities/error/
    """
    try:
        data = response.json()
        return data.get("error"), data.get("error_description")
    except Exception:
        return None, None
