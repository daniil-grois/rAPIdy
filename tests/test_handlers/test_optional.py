from http import HTTPStatus
from typing import Any, Dict, Optional

import pytest
from aiohttp import MultipartWriter
from pydantic import BaseModel
from pytest_aiohttp.plugin import AiohttpClient
from typing_extensions import Annotated

from rapidy import web
from rapidy._annotation_extractor import ParameterCannotBeOptionalError
from rapidy.request_params import (
    BytesBody,
    Cookie,
    FormDataBody,
    Header,
    JsonBody,
    MultipartBody,
    Path,
    Query,
    StreamBody,
    TextBody,
)


class Schema(BaseModel):
    attr1: str


can_optional_param_instances = [
    pytest.param(Header(), id='header'),
    # NOTE: not check Header(extract_all=True) as it always contains data

    pytest.param(Cookie(), id='cookie'),
    pytest.param(Cookie(extract_all=True), id='cookie-all'),

    pytest.param(Query(), id='query'),
    pytest.param(Query(extract_all=True), id='query-all'),

    pytest.param(JsonBody(), id='json-body'),
    pytest.param(JsonBody(extract_all=True), id='json-body-all'),

    pytest.param(FormDataBody(), id='form-data-body'),
    pytest.param(FormDataBody(extract_all=True), id='form-data-body-all'),

    pytest.param(MultipartBody(), id='multipart-body'),
    pytest.param(MultipartBody(extract_all=True), id='multipart-body-all'),

    pytest.param(TextBody(), id='text-body'),
    pytest.param(BytesBody(), id='bytes-body'),
]

not_optional_param_instances = [
    pytest.param(Path(), id='path'),
    pytest.param(Path(extract_all=True), id='path-all'),
    pytest.param(StreamBody(), id='stream-body'),
]


@pytest.mark.parametrize('type_', can_optional_param_instances)
async def test_optional(aiohttp_client: AiohttpClient, type_: Any) -> None:
    async def handler_annotated_def(
            data: Annotated[Optional[Any], type_],
    ) -> web.Response:
        assert data is None
        return web.Response()

    async def handler_default_def(
            data: Optional[Any] = type_,
    ) -> web.Response:
        assert data is None
        return web.Response()

    await _test(aiohttp_client, handler_annotated_def, HTTPStatus.OK)
    await _test(aiohttp_client, handler_default_def, HTTPStatus.OK)


@pytest.mark.parametrize('type_', not_optional_param_instances)
async def test_not_optional(type_: Any) -> None:
    async def handler_annotated_def(
            data: Annotated[Optional[Any], type_],
    ) -> web.Response:
        assert data is None
        return web.Response()

    app = web.Application()

    async def handler_default_def(
            data: Optional[Any] = type_,
    ) -> web.Response:
        assert data is None
        return web.Response()

    with pytest.raises(ParameterCannotBeOptionalError):
        app.add_routes([web.post('/annotated_def', handler_annotated_def)])

    with pytest.raises(ParameterCannotBeOptionalError):
        app.add_routes([web.post('/default_def', handler_default_def)])


multipart_writer = MultipartWriter()

@pytest.mark.parametrize(
    'type_, request_kwargs', [
        pytest.param(Header(extract_all=True), {}, id='header-all'),
        pytest.param(Cookie(extract_all=True), {'cookies': {}}, id='cookie-all'),
        pytest.param(Query(extract_all=True), {'params': {}}, id='query-all'),
        pytest.param(JsonBody(extract_all=True), {'json': {}}, id='json-body-all'),
        pytest.param(FormDataBody(extract_all=True), {'data': ' '}, id='form-data-body-all'),
        pytest.param(MultipartBody(extract_all=True), {'data': multipart_writer}, id='multipart-body-all'),
    ],
)
async def test_optional_fields(
        aiohttp_client: AiohttpClient,
        type_: Any,
        request_kwargs: Dict[str, Any],
) -> None:
    class Schema(BaseModel):
        attr1: Optional[str] = None
        attr2: Optional[str] = None

    async def handler_annotated_def(
            data: Annotated[Schema, type_],
    ) -> web.Response:
        assert data == Schema(attr1=None, attr2=None)
        return web.Response()

    async def handler_default_def(
            data: Schema = type_,
    ) -> web.Response:
        assert data == Schema(attr1=None, attr2=None)
        return web.Response()

    await _test(aiohttp_client, handler_annotated_def, HTTPStatus.OK, **request_kwargs)
    await _test(aiohttp_client, handler_default_def, HTTPStatus.OK, **request_kwargs)


async def _test(
        aiohttp_client: AiohttpClient,
        handler: Any,
        resp_status: int,
        **request_kwargs: Any,
) -> None:
    app = web.Application()
    app.add_routes([web.post('/', handler)])
    client = await aiohttp_client(app)
    resp = await client.post('/', **request_kwargs)
    assert resp.status == resp_status
