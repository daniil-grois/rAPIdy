from http import HTTPStatus
from typing import Any, Dict

from pydantic import BaseModel
from pytest_aiohttp.plugin import AiohttpClient
from typing_extensions import Annotated, Final

from rapidy import web
from rapidy.request_params import (
    Cookie,
    CookieRaw,
    CookieSchema,
    Header,
    HeaderRaw,
    HeaderSchema,
    JsonBody,
    JsonBodyRaw,
    JsonBodySchema,
    Path,
    PathRaw,
    PathSchema,
    Query,
    QueryRaw,
    QuerySchema,
)
from rapidy.typedefs import HandlerType

HANDLER_PATH: Final[str] = '/{attr1}/{attr2}'

REQUEST = {'attr1': 'attr1', 'attr2': 'attr2'}
REQUEST_PATH: Final[str] = HANDLER_PATH.format(**REQUEST)


class Schema(BaseModel):
    attr1: str
    attr2: str


async def test_raw_data(aiohttp_client: AiohttpClient) -> None:
    async def handler(
            path_data: Annotated[Dict[str, Any], PathRaw()],
            header_data: Annotated[Dict[str, Any], HeaderRaw()],
            cookie_data: Annotated[Dict[str, Any], CookieRaw()],
            query_data: Annotated[Dict[str, Any], QueryRaw()],
            body_data: Annotated[Dict[str, Any], JsonBodyRaw()],
    ) -> web.Response:
        return web.Response()

    await _test(aiohttp_client, handler)


async def test_individual_params(aiohttp_client: AiohttpClient) -> None:
    async def handler(
            path_attr1: Annotated[str, Path(alias='attr1')],
            path_attr2: Annotated[str, Path(alias='attr2')],
            header_attr1: Annotated[str, Header(alias='attr1')],
            header_attr2: Annotated[str, Header(alias='attr2')],
            cookie_attr1: Annotated[str, Cookie(alias='attr1')],
            cookie_attr2: Annotated[str, Cookie(alias='attr2')],
            query_attr1: Annotated[str, Query(alias='attr1')],
            query_attr2: Annotated[str, Query(alias='attr2')],
            body_attr1: Annotated[str, JsonBody(alias='attr1')],
            body_attr2: Annotated[str, JsonBody(alias='attr2')],
    ) -> web.Response:
        return web.Response()

    await _test(aiohttp_client, handler)


async def test_single_schema(aiohttp_client: AiohttpClient) -> None:
    async def handler(
            path_data: Annotated[Schema, PathSchema()],
            header_data: Annotated[Schema, HeaderSchema()],
            cookie_data: Annotated[Schema, CookieSchema()],
            query_data: Annotated[Schema, QuerySchema()],
            body_data: Annotated[Schema, JsonBodySchema()],
    ) -> web.Response:
        return web.Response()

    await _test(aiohttp_client, handler)


async def _test(aiohttp_client: AiohttpClient, handler: HandlerType) -> None:
    app = web.Application()
    app.add_routes([web.post(HANDLER_PATH, handler)])
    client = await aiohttp_client(app)
    resp = await client.post(
        REQUEST_PATH,
        json=REQUEST,
        cookies=REQUEST,
        headers=REQUEST,
        params=REQUEST,
    )
    assert resp.status == HTTPStatus.OK
