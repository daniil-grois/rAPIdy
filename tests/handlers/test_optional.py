from http import HTTPStatus
from typing import Any, Dict, Optional

import pytest
from pydantic import BaseModel
from pytest_aiohttp.plugin import AiohttpClient
from typing_extensions import Annotated

from rapidy import web
from rapidy._annotation_extractor import (
    IncorrectDefineDefaultValueError,
    ParameterCannotUseDefaultError,
    ParameterCannotUseDefaultFactoryError,
    SpecifyBothDefaultAndDefaultFactoryError,
)
from rapidy.request_params import (
    BytesBody,
    Cookie,
    CookieRaw,
    CookieSchema,
    FormDataBody,
    FormDataBodyRaw,
    FormDataBodySchema,
    Header,
    HeaderSchema,
    JsonBody,
    JsonBodyRaw,
    JsonBodySchema,
    MultipartBody,
    MultipartBodyRaw,
    MultipartBodySchema,
    Path,
    PathRaw,
    PathSchema,
    Query,
    QueryRaw,
    QuerySchema,
    TextBody,
)
from rapidy.typedefs import HandlerType

class Schema(BaseModel):
    attr1: str


params = [
    pytest.param(str, Header, id='header-param'),
    pytest.param(str, Cookie, id='cookie-param'),
    pytest.param(str, Query, id='query-param'),
    pytest.param(str, JsonBody, id='body-json-param'),
    pytest.param(str, FormDataBody, id='body-form-data-param'),
    pytest.param(str, MultipartBody, id='body-multipart-param'),
    pytest.param(Schema, CookieSchema, id='cookie-schema'),
    pytest.param(Schema, QuerySchema, id='query-schema'),
    pytest.param(Schema, JsonBodySchema, id='body-json-schema'),
    pytest.param(Schema, FormDataBodySchema, id='body-form-data-schema'),
    pytest.param(Schema, MultipartBodySchema, id='body-multipart-schema'),
    pytest.param(Dict[str, Any], CookieRaw, id='cookie-raw'),
    pytest.param(Dict[str, Any], QueryRaw, id='query-raw'),
    pytest.param(Dict[str, Any], JsonBodyRaw, id='body-json-raw'),
    pytest.param(Dict[str, Any], FormDataBodyRaw, id='body-form-data-raw'),
    pytest.param(Dict[str, Any], MultipartBodyRaw, id='body-multipart-raw'),
]


@pytest.mark.parametrize('type_, param', params)
async def test_success_optional(
        aiohttp_client: AiohttpClient,
        type_: Any,
        param: Any,
) -> None:
    async def handler_1(
            data: Annotated[Optional[type_], param],
    ) -> web.Response:
        assert data is None
        return web.Response()

    async def handler_2(
            data: Annotated[Optional[type_], param()],
    ) -> web.Response:
        assert data is None
        return web.Response()

    async def handler_3(
            data: Optional[type_] = param(),
    ) -> web.Response:
        assert data is None
        return web.Response()

    for handler in (handler_1, handler_2, handler_3):
        await _test(aiohttp_client, handler, {}, HTTPStatus.OK)


async def _test(
        aiohttp_client: AiohttpClient,
        handler: Any,
        request_kw: Dict[str, Any],
        resp_status: int,
) -> None:
    app = web.Application()
    app.add_routes([web.post('/', handler)])
    client = await aiohttp_client(app)
    resp = await client.post('/', **request_kw)
    assert resp.status == resp_status
