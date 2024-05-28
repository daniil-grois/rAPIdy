from http import HTTPStatus
from typing import Any, Dict

import pytest
from aiohttp import MultipartWriter
from pydantic import BaseModel
from pytest_aiohttp.plugin import AiohttpClient
from typing_extensions import Final

from rapidy import web
from rapidy._fields import ParamFieldInfo
from rapidy.request_params import Cookie, FormDataBody, Header, JsonBody, MultipartBody, Path, Query
from rapidy.typedefs import HandlerType
from tests.helpers import create_multipart_headers

HANDLER_PATH: Final[str] = '/{attr1}/{attr2}'

REQUEST = {'attr1': '1', 'attr2': '2'}
REQUEST_PATH: Final[str] = HANDLER_PATH.format(**REQUEST)

multipart_writer = MultipartWriter()
multipart_writer.append('1', create_multipart_headers(part_name='attr1'))
multipart_writer.append('2', create_multipart_headers(part_name='attr2'))

test_params = [
    (Path, {}),
    (Header, {'headers': REQUEST}),
    (Cookie, {'cookies': REQUEST}),
    (Query, {'params': REQUEST}),
    (JsonBody, {'json': REQUEST}),
    (FormDataBody, {'data': REQUEST}),
    (MultipartBody, {'data': multipart_writer}),
]


@pytest.mark.parametrize('type_, request_', test_params)
async def test_individual(aiohttp_client: AiohttpClient, type_: ParamFieldInfo, request_: Dict[str, Any]) -> None:
    async def handler(attr1: int = type_(), attr2: int = type_(validate=False)) -> web.Response:
        _check_data_type(attr1, expected_type=int)
        _check_data_type(attr2, expected_type=str)
        return web.Response()

    await _test(aiohttp_client=aiohttp_client, handler=handler, request=request_)


class Schema(BaseModel):
    attr1: int
    attr2: int


@pytest.mark.parametrize('type_, request_', test_params)
@pytest.mark.parametrize('validation_type', [Schema, dict[str, Any]])
async def test_complex(
        aiohttp_client: AiohttpClient, type_: ParamFieldInfo, request_: Dict[str, Any], validation_type: Any,
) -> None:
    async def handler(attr: validation_type = type_(extract_all=True, validate=False)) -> web.Response:
        _check_data_type(attr, expected_type=dict)
        return web.Response()

    await _test(aiohttp_client=aiohttp_client, handler=handler, request=request_)


def _check_data_type(*params: Any, expected_type: Any) -> None:
    for data in params:
        assert type(data) == expected_type


async def _test(aiohttp_client: AiohttpClient, handler: HandlerType, request: Dict[str, Any]) -> None:
    app = web.Application()
    app.add_routes([web.post(HANDLER_PATH, handler)])
    client = await aiohttp_client(app)
    resp = await client.post(REQUEST_PATH, **request)
    assert resp.status == HTTPStatus.OK
