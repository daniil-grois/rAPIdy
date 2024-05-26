from http import HTTPStatus

from aiohttp.pytest_plugin import AiohttpClient

from rapidy import web


async def test_func_handler_404(aiohttp_client: AiohttpClient) -> None:
    async def handler(request: web.Request) -> web.Response:
        return web.Response()

    app = web.Application()
    app.add_routes([web.get('/', handler)])

    client = await aiohttp_client(app)
    resp = await client.post('/wrong')

    assert resp.status == HTTPStatus.NOT_FOUND


async def test_class_handler_404(aiohttp_client: AiohttpClient) -> None:
    class ViewHandler(web.View):
        def get(self) -> web.Response:
            return web.Response()

    app = web.Application()
    app.add_routes([web.post('/', ViewHandler)])

    client = await aiohttp_client(app)
    resp = await client.post('/wrong')

    assert resp.status == HTTPStatus.NOT_FOUND
