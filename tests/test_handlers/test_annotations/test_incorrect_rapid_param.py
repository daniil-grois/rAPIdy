from http import HTTPStatus
from typing import Any

from aiohttp.pytest_plugin import AiohttpClient
from rapidy import web
from typing_extensions import Annotated

import pytest


@pytest.mark.parametrize(
    'attr_type', [
        Annotated[str, str],
        Annotated[str, str, str],
    ],
)
async def test_incorrect_rapid_param(aiohttp_client: AiohttpClient, attr_type: Any) -> None:
    async def handler(any_param: attr_type) -> web.Response:
        return web.Response()

    app = web.Application()
    app.add_routes([web.post('/', handler)])

    client = await aiohttp_client(app)
    resp = await client.post('/', json={'attr': ''})

    assert resp.status == HTTPStatus.INTERNAL_SERVER_ERROR
