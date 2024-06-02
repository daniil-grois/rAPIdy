from http import HTTPStatus
from typing import Any, Dict, Type, Union

import pytest
from aiohttp.pytest_plugin import AiohttpClient
from pydantic import BaseModel

from rapidy import web
from rapidy.constants import PYDANTIC_V1, PYDANTIC_V2
from rapidy.request_params import JsonBody


class SchemaA(BaseModel):
    a: int


class SchemaB(BaseModel):
    b: int


@pytest.mark.parametrize(
    'validated_union_type, extract_all, json, expected_type_pydantic_v1, expected_type_pydantic_v2', (
        (Union[int, str], False, {'p': 1}, int, int),
        (Union[int, str], False, {'p': '1'}, int, str),
        (Union[int, str], False, {'p': '1s'}, str, str),
        (Union[SchemaA, SchemaB], True, {'a': 1}, SchemaA, SchemaA),
        (Union[SchemaA, SchemaB], True, {'b': 1}, SchemaB, SchemaB),
    ),
)
async def test_union_datatype(
        validated_union_type: Any,
        extract_all: bool,
        aiohttp_client: AiohttpClient,
        json: Dict[str, Any],
        expected_type_pydantic_v1: Type[Any],
        expected_type_pydantic_v2: Type[Any],
) -> None:
    async def handler(p: validated_union_type  = JsonBody(extract_all=extract_all)) -> web.Response:
        if PYDANTIC_V1:
            assert isinstance(p, expected_type_pydantic_v1)
        elif PYDANTIC_V2:
            assert isinstance(p, expected_type_pydantic_v2)
        else:
            raise
        return web.Response()

    app = web.Application()
    app.add_routes([web.post('/', handler)])

    client = await aiohttp_client(app)
    resp = await client.post('/', json=json)

    assert resp.status == HTTPStatus.OK
