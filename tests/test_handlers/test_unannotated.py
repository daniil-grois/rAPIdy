from http import HTTPStatus

import pytest
from aiohttp.pytest_plugin import AiohttpClient

from rapidy import web
from rapidy._annotation_container import RequestFieldAlreadyExistError


async def test_success(aiohttp_client: AiohttpClient) -> None:
    async def handler(request):
        return web.Response()

    app = web.Application()
    app.add_routes([web.post('/', handler)])

    client = await aiohttp_client(app)
    resp = await client.post('/')

    assert resp.status == HTTPStatus.OK


async def test_twice_request_def(aiohttp_client: AiohttpClient) -> None:
    async def handler(req, request: web.Request):  # type: ignore[no-untyped-def]
        return web.Response()

    app = web.Application()
    with pytest.raises(RequestFieldAlreadyExistError):
        app.add_routes([web.post('/', handler)])
