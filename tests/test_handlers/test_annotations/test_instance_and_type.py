from http import HTTPStatus
from typing import Annotated, Any

import pytest
from aiohttp.pytest_plugin import AiohttpClient

from rapidy import web
from rapidy.request_params import JsonBody


def _create_annotated_def_handler(type_: Any, param: Any) -> Any:
    async def handler(attr: Annotated[type_, param]) -> Any: return web.Response()
    return handler


def _create_default_def_handler(type_: Any, param: Any) -> Any:
    async def handler(attr: type_ = param) -> Any: return web.Response()
    return handler


@pytest.mark.parametrize(
    'param', [
        pytest.param(JsonBody(), id='define-as-instance'),
        pytest.param(JsonBody, id='define-as-class'),
    ],
)
@pytest.mark.parametrize(
    'create_handler_func', [
        pytest.param(_create_annotated_def_handler, id='annotated-def'),
        pytest.param(_create_default_def_handler, id='default-def'),
    ],
)
async def test_check_annotation(
        aiohttp_client: AiohttpClient,
        param: Any,
        create_handler_func: Any,
) -> None:
    handler = create_handler_func(str, JsonBody)

    app = web.Application()
    app.add_routes([web.post('/', handler)])
    client = await aiohttp_client(app)
    resp = await client.post('/', json={'attr': ''})

    assert resp.status == HTTPStatus.OK
