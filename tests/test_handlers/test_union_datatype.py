from http import HTTPStatus
from typing import Union, Dict, Any, Type

import pytest
from aiohttp.pytest_plugin import AiohttpClient

from rapidy import web
from rapidy.request_params import JsonBody


@pytest.mark.parametrize('json, expected_type', (
    ({'p': 1}, int),
    ({'p': '1'}, str),
    ({'p': '1s'}, str),
))
async def test_union_datatype(
        aiohttp_client: AiohttpClient,
        json: Dict[str, Any],
        expected_type: Type[Any],
) -> None:
    async def handler(p: Union[int, str] = JsonBody()):
        assert isinstance(p, expected_type)
        return web.Response()

    app = web.Application()
    app.add_routes([web.post('/', handler)])

    client = await aiohttp_client(app)
    resp = await client.post('/', json=json)

    assert resp.status == HTTPStatus.OK
