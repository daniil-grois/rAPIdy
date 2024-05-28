from http import HTTPStatus
from typing import Any

import pytest
from pytest_aiohttp.plugin import AiohttpClient
from typing_extensions import Annotated

from rapidy import web
from rapidy._annotation_container import RequestFieldAlreadyExistsError
from rapidy.request_params import JsonBody
from rapidy.web import Application


async def post_without_request(
        username: Annotated[str, JsonBody],
) -> web.Response:
    return web.Response()


async def post_with_request_fst(
        request: web.Request,
        username: Annotated[str, JsonBody],
) -> web.Response:
    return web.Response()


async def post_with_request_snd(
        username: Annotated[str, JsonBody],
        request: web.Request,
) -> web.Response:
    return web.Response()


async def post_with_request_different_name(
        any_req: web.Request,
        username: Annotated[str, JsonBody],
) -> web.Response:
    return web.Response()


@pytest.mark.parametrize(
    'post_handler', [
        post_without_request,
        post_with_request_fst,
        post_with_request_snd,
        post_with_request_different_name,
    ],
)
async def test_success(aiohttp_client: AiohttpClient, *, post_handler: Any) -> None:
    app = Application()
    app.add_routes([web.post('/', post_handler)])

    client = await aiohttp_client(app)
    resp = await client.post('/', json={'username': 'username'})

    assert resp.status == HTTPStatus.OK


async def test_request_defined_twice(aiohttp_client: AiohttpClient) -> None:
    async def post(
            r1: web.Request,
            r2: web.Request,
    ) -> web.Response:
        return web.Response()

    app = Application()

    with pytest.raises(RequestFieldAlreadyExistsError):
        app.add_routes([web.post('/', post)])
