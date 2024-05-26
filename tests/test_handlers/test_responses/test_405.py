from http import HTTPStatus

from aiohttp.pytest_plugin import AiohttpClient

from rapidy import web


async def test_func_handler_405(aiohttp_client: AiohttpClient) -> None:
    async def handler(request: web.Request) -> web.Response:
        return web.Response()

    app = web.Application()
    app.add_routes([web.get('/', handler)])

    client = await aiohttp_client(app)
    resp = await client.post('/')

    assert resp.status == HTTPStatus.METHOD_NOT_ALLOWED


async def test_class_handler_405(aiohttp_client: AiohttpClient) -> None:
    class ViewHandler(web.View):
        def get(self) -> web.Response:
            return web.Response()

    app = web.Application()
    app.add_routes([web.post('/', ViewHandler)])

    client = await aiohttp_client(app)
    resp = await client.post('/')

    assert resp.status == HTTPStatus.METHOD_NOT_ALLOWED
