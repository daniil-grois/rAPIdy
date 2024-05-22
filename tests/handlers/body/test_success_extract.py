from http import HTTPStatus
from typing import Any, Dict

import pytest
from aiohttp import MultipartWriter, StreamReader
from pydantic import BaseModel
from pytest_aiohttp.plugin import AiohttpClient
from typing_extensions import Annotated

from rapidy import web
from rapidy.request_params import (
    BytesBody,
    FormDataBody,
    FormDataBodyRaw,
    FormDataBodySchema,
    JsonBody,
    JsonBodyRaw,
    JsonBodySchema,
    MultipartBody,
    MultipartBodyRaw,
    MultipartBodySchema,
    StreamBody,
    TextBody,
)
from rapidy.typedefs import HandlerType
from tests.helpers import create_multipart_headers


async def test_json_param(aiohttp_client: AiohttpClient) -> None:
    async def handler(
            attr1: Annotated[int, JsonBody()],
    ) -> web.Response:
        assert attr1 == 1
        return web.Response()

    await _success_json(aiohttp_client, handler)


async def test_json_schema(aiohttp_client: AiohttpClient) -> None:
    class Schema(BaseModel):
        attr1: int

    async def handler(
            body_data: Annotated[Schema, JsonBodySchema()],
    ) -> web.Response:
        assert body_data.attr1 == 1
        return web.Response()

    await _success_json(aiohttp_client, handler)


async def test_json_raw(aiohttp_client: AiohttpClient) -> None:
    async def handler(
            body_data: Annotated[Dict[str, Any], JsonBodyRaw()],
    ) -> web.Response:
        assert body_data == {"attr1": 1}
        return web.Response()

    await _success_json(aiohttp_client, handler)


async def _success_json(aiohttp_client: AiohttpClient, handler: HandlerType) -> None:
    app = web.Application()
    app.add_routes([web.post('/', handler)])
    client = await aiohttp_client(app)
    resp = await client.post('/', json={"attr1": 1})
    assert resp.status == HTTPStatus.OK


async def test_form_data_param(aiohttp_client: AiohttpClient) -> None:
    async def handler(
            attr1: Annotated[int, FormDataBody()],
    ) -> web.Response:
        assert attr1 == 1
        return web.Response()

    await _success_form_data(aiohttp_client, handler)


async def test_form_data_schema(aiohttp_client: AiohttpClient) -> None:
    class Schema(BaseModel):
        attr1: int

    async def handler(
            body_data: Annotated[Schema, FormDataBodySchema()],
    ) -> web.Response:
        assert body_data.attr1 == 1
        return web.Response()

    await _success_form_data(aiohttp_client, handler)


async def test_form_data_raw(aiohttp_client: AiohttpClient) -> None:
    async def handler(
            body_data: Annotated[Dict[str, str], FormDataBodyRaw()],
    ) -> web.Response:
        assert body_data == {"attr1": "1"}
        return web.Response()

    await _success_form_data(aiohttp_client, handler)


async def _success_form_data(aiohttp_client: AiohttpClient, handler: HandlerType) -> None:
    app = web.Application()
    app.add_routes([web.post('/', handler)])
    client = await aiohttp_client(app)
    resp = await client.post('/', data={"attr1": 1})
    assert resp.status == HTTPStatus.OK


@pytest.mark.parametrize(
    'param_name_1, param_name_2, attrs_case_sensitive, duplicated_attrs_parse_as_array, expected_body_data',
    [
        ['Attr1', 'Attr1', True, True, {"Attr1": ["1", "1"]}],
        ['attr1', 'Attr1', True, True, {"attr1": ["1"], "Attr1": ["1"]}],
        ['attr1', 'Attr1', False, True, {"attr1": ["1", "1"]}],
        ['attr1', 'Attr1', True, False, {"Attr1": "1", "attr1": "1"}],
        ['Attr1', 'Attr1', False, False, {"attr1": "1"}],
    ],
)
async def test_form_data_attributes(
        aiohttp_client: AiohttpClient,
        *,
        param_name_1: str,
        param_name_2: str,
        attrs_case_sensitive: bool,
        duplicated_attrs_parse_as_array: bool,
        expected_body_data: Dict[str, Any],
) -> None:
    body_param = FormDataBodyRaw(
        duplicated_attrs_parse_as_array=duplicated_attrs_parse_as_array,
        attrs_case_sensitive=attrs_case_sensitive,
    )

    body_type = Dict[str, list[str]] if duplicated_attrs_parse_as_array else Dict[str, str]

    async def handler(
            body_data: Annotated[body_type, body_param],
    ) -> web.Response:
        assert body_data == expected_body_data
        return web.Response()

    app = web.Application()
    app.add_routes([web.post('/', handler)])
    client = await aiohttp_client(app)

    resp = await client.post('/', data=f'{param_name_1}=1&{param_name_2}=1')
    assert resp.status == HTTPStatus.OK


async def test_multipart_param(
        aiohttp_client: AiohttpClient,
        multipart_writer: MultipartWriter,
) -> None:
    async def handler(
            attr1: Annotated[int, MultipartBody()],
    ) -> web.Response:
        assert attr1 == 1
        return web.Response()

    await _success_multipart(aiohttp_client, handler, multipart_writer)


async def test_multipart_schema(
        aiohttp_client: AiohttpClient,
        multipart_writer: MultipartWriter,
) -> None:
    class Schema(BaseModel):
        attr1: int

    async def handler(
            body_data: Annotated[Schema, MultipartBodySchema()],
    ) -> web.Response:
        assert body_data.attr1 == 1
        return web.Response()

    await _success_multipart(aiohttp_client, handler, multipart_writer)


async def test_multipart_raw(
        aiohttp_client: AiohttpClient,
        multipart_writer: MultipartWriter,
) -> None:
    async def handler(
            body_data: Annotated[Dict[str, str], MultipartBodyRaw()],
    ) -> web.Response:
        assert body_data == {"attr1": "1"}
        return web.Response()

    await _success_multipart(aiohttp_client, handler, multipart_writer)


async def _success_multipart(
        aiohttp_client: AiohttpClient,
        handler: HandlerType,
        multipart_writer: MultipartWriter,
) -> None:
    app = web.Application()
    app.add_routes([web.post('/', handler)])
    client = await aiohttp_client(app)

    multipart_writer.append("1", create_multipart_headers(part_name='attr1'))

    resp = await client.post('/', data=multipart_writer)
    assert resp.status == HTTPStatus.OK


@pytest.mark.parametrize(
    'param_name_1, param_name_2, attrs_case_sensitive, duplicated_attrs_parse_as_array, expected_body_data',
    [
        ['Attr1', 'Attr1', True, True, {"Attr1": ["1", "1"]}],
        ['attr1', 'Attr1', True, True, {"attr1": ["1"], "Attr1": ["1"]}],
        ['attr1', 'Attr1', False, True, {"attr1": ["1", "1"]}],
        ['attr1', 'Attr1', True, False, {"Attr1": "1", "attr1": "1"}],
        ['Attr1', 'Attr1', False, False, {"attr1": "1"}],
    ],
)
async def test_multipart_attributes(
        aiohttp_client: AiohttpClient,
        multipart_writer: MultipartWriter,
        *,
        param_name_1: str,
        param_name_2: str,
        attrs_case_sensitive: bool,
        duplicated_attrs_parse_as_array: bool,
        expected_body_data: Dict[str, Any],
) -> None:
    body_param = MultipartBodyRaw(
        duplicated_attrs_parse_as_array=duplicated_attrs_parse_as_array,
        attrs_case_sensitive=attrs_case_sensitive,
    )

    body_type = Dict[str, list[str]] if duplicated_attrs_parse_as_array else Dict[str, str]

    async def handler(
            body_data: Annotated[body_type, body_param],
    ) -> web.Response:
        assert body_data == expected_body_data
        return web.Response()

    app = web.Application()
    app.add_routes([web.post('/', handler)])
    client = await aiohttp_client(app)

    multipart_writer.append('1', create_multipart_headers(part_name=param_name_1))
    multipart_writer.append('1', create_multipart_headers(part_name=param_name_2))

    resp = await client.post('/', data=multipart_writer)
    assert resp.status == HTTPStatus.OK

async def test_body_text(aiohttp_client: AiohttpClient) -> None:
    async def handler(
            attr1: Annotated[str, TextBody()],
    ) -> web.Response:
        assert attr1 == '{"attr1": 1}'
        return web.Response()

    app = web.Application()
    app.add_routes([web.post('/', handler)])
    client = await aiohttp_client(app)
    resp = await client.post('/', data='{"attr1": 1}')
    assert resp.status == HTTPStatus.OK


async def test_body_bytes(aiohttp_client: AiohttpClient) -> None:
    async def handler(
            attr1: Annotated[bytes, BytesBody()],
    ) -> web.Response:
        assert attr1 == b'{"attr1": 1}'
        return web.Response()

    app = web.Application()
    app.add_routes([web.post('/', handler)])
    client = await aiohttp_client(app)
    resp = await client.post('/', data='{"attr1": 1}')
    assert resp.status == HTTPStatus.OK


async def test_body_stream(aiohttp_client: AiohttpClient) -> None:
    async def handler(
            attr1: Annotated[StreamReader, StreamBody()],
    ) -> web.Response:
        assert isinstance(attr1, StreamReader)
        return web.Response()

    app = web.Application()
    app.add_routes([web.post('/', handler)])
    client = await aiohttp_client(app)
    resp = await client.post('/', data='1')
    assert resp.status == HTTPStatus.OK
