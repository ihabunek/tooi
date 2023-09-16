from httpx._client import UseClientDefault
from httpx._types import AuthTypes
from httpx._types import CookieTypes
from httpx._types import HeaderTypes
from httpx._types import QueryParamTypes
from httpx._types import RequestContent
from httpx._types import RequestData
from httpx._types import RequestExtensions
from httpx._types import RequestFiles
from httpx._types import TimeoutTypes
from typing import Optional, TypedDict, Union, Any


class RequestParams(TypedDict, total=False):
    """
    Types for optional params taken by httpx.request.
    """
    content: Optional[RequestContent]
    data: Optional[RequestData]
    files: Optional[RequestFiles]
    json: Optional[Any]
    params: Optional[QueryParamTypes]
    headers: Optional[HeaderTypes]
    cookies: Optional[CookieTypes]
    auth: Union[AuthTypes, UseClientDefault, None]
    follow_redirects: Union[bool, UseClientDefault]
    timeout: Union[TimeoutTypes, UseClientDefault]
    extensions: Optional[RequestExtensions]
