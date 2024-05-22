from http import HTTPStatus
from typing import Any, Dict, Optional

import pytest
from pydantic import BaseModel
from pytest_aiohttp.plugin import AiohttpClient
from typing_extensions import Annotated

from rapidy import web
from rapidy._annotation_extractor import (
    IncorrectDefineDefaultValueError,
    ParameterCannotUseDefaultError,
    ParameterCannotUseDefaultFactoryError,
    SpecifyBothDefaultAndDefaultFactoryError,
)
from rapidy.request_params import (
    BytesBody,
    Cookie,
    CookieRaw,
    CookieSchema,
    FormDataBody,
    FormDataBodyRaw,
    FormDataBodySchema,
    Header,
    HeaderSchema,
    JsonBody,
    JsonBodyRaw,
    JsonBodySchema,
    MultipartBody,
    MultipartBodyRaw,
    MultipartBodySchema,
    Path,
    PathRaw,
    PathSchema,
    Query,
    QueryRaw,
    QuerySchema,
    TextBody,
)
from rapidy.typedefs import HandlerType


class Schema(BaseModel):
    attr1: str


class SchemaWithOneDefaultParam(BaseModel):
    attr1: str = ''
    attr2: str


# NOTE: We do not check the default value type, as this may affect the performance of the whole application at startup.
# Perhaps in a future patch this feature will be added as a toggleable feature.
default_values = [
    pytest.param(1, id='int'),
    pytest.param(1.0, id='float'),
    pytest.param('1', id='str'),
    pytest.param((1,), id='tuple'),
    pytest.param(Schema(attr1='1'), id='base-model-instance'),
    pytest.param(None, id='none'),
]

cant_default_params = [
    pytest.param(Dict[str, Any], Path, id='path-param'),
    pytest.param(Dict[str, Any], PathSchema, id='path-schema'),
    pytest.param(Dict[str, Any], PathRaw, id='path-raw'),

    # TODO: перенести в др колонку
    # pytest.param(Dict[str, Any], CookieRaw, id='cookie-raw'),
    # pytest.param(Dict[str, Any], QueryRaw, id='query-raw'),
    # pytest.param(Dict[str, Any], JsonBodyRaw, id='body-json-raw'),
    # pytest.param(Dict[str, Any], FormDataBodyRaw, id='body-form-data-raw'),
    # pytest.param(Dict[str, Any], MultipartBodyRaw, id='body-multipart-raw'),
    pytest.param(str, TextBody, id='body-text'),
    pytest.param(bytes, BytesBody, id='body-bytes'),
]

# NOTE: HeaderSchema cannot be checked because the http-client always send headers
default_params = [
    pytest.param(str, Header, id='header-param'),
    pytest.param(str, Cookie, id='cookie-param'),
    pytest.param(str, Query, id='query-param'),
    pytest.param(str, JsonBody, id='body-json-param'),
    pytest.param(str, FormDataBody, id='body-form-data-param'),
    pytest.param(str, MultipartBody, id='body-multipart-param'),
    pytest.param(Schema, CookieSchema, id='cookie-schema'),
    pytest.param(Schema, QuerySchema, id='query-schema'),
    pytest.param(Schema, JsonBodySchema, id='body-json-schema'),
    pytest.param(Schema, FormDataBodySchema, id='body-form-data-schema'),
    pytest.param(Schema, MultipartBodySchema, id='body-multipart-schema'),
]

no_values_no_default_params = [
    pytest.param(str, Cookie, None, HTTPStatus.UNPROCESSABLE_ENTITY, id='cookie-param'),
    pytest.param(str, Query, None, HTTPStatus.UNPROCESSABLE_ENTITY, id='query-param'),
    pytest.param(str, JsonBody, None, HTTPStatus.UNPROCESSABLE_ENTITY, id='body-json-param'),
    pytest.param(str, FormDataBody, None, HTTPStatus.UNPROCESSABLE_ENTITY, id='body-form-data-param'),
    pytest.param(str, MultipartBody, None, HTTPStatus.UNPROCESSABLE_ENTITY, id='body-multipart-param'),
    pytest.param(Schema, CookieSchema, None, HTTPStatus.UNPROCESSABLE_ENTITY, id='header-schema'),
    pytest.param(Schema, QuerySchema, None, HTTPStatus.UNPROCESSABLE_ENTITY, id='query-schema'),
    pytest.param(Schema, JsonBodySchema, None, HTTPStatus.UNPROCESSABLE_ENTITY, id='body-json-schema'),
    pytest.param(Schema, FormDataBodySchema, None, HTTPStatus.UNPROCESSABLE_ENTITY, id='body-form-data-schema'),
    pytest.param(Schema, MultipartBodySchema, None, HTTPStatus.UNPROCESSABLE_ENTITY, id='body-multipart-schema'),
    pytest.param(Dict[str, Any], CookieRaw, None, HTTPStatus.UNPROCESSABLE_ENTITY, id='cookie-raw'),
    pytest.param(Dict[str, Any], QueryRaw, None, HTTPStatus.UNPROCESSABLE_ENTITY, id='query-raw'),
    pytest.param(Dict[str, Any], JsonBodyRaw, None, HTTPStatus.UNPROCESSABLE_ENTITY, id='body-json-raw'),
    pytest.param(Dict[str, Any], FormDataBodyRaw, None, HTTPStatus.UNPROCESSABLE_ENTITY, id='body-form-data-raw'),
    pytest.param(Dict[str, Any], MultipartBodyRaw, None, HTTPStatus.UNPROCESSABLE_ENTITY, id='body-multipart-raw'),
    pytest.param(str, TextBody, None, HTTPStatus.UNPROCESSABLE_ENTITY, id='body-text'),
    pytest.param(bytes, BytesBody, None, HTTPStatus.UNPROCESSABLE_ENTITY, id='body-bytes'),
]

schema_one_param_exist_second_param_is_default_params = [
    [HeaderSchema, {'headers': {'attr2': 'attr2'}}],
    [CookieSchema, {'cookies': {'attr2': 'attr2'}}],
    [QuerySchema, {'params': {'attr2': 'attr2'}}],
    [JsonBodySchema, {'json': {'attr2': 'attr2'}}],
    [FormDataBodySchema, {'data': {'attr2': 'attr2'}}],
]


@pytest.mark.parametrize('type_, param', cant_default_params)
async def test_cant_default(
        aiohttp_client: AiohttpClient,
        *,
        type_: Any,
        param: Any,
) -> None:
    app = web.Application()

    async def handler_1(path: Annotated[type_, param] = 'default') -> web.Response: pass
    async def handler_2(path: Annotated[type_, param('default')]) -> web.Response: pass
    async def handler_3(path: Annotated[type_, param(default_factory=lambda: 'default')]) -> web.Response: pass
    async def handler_4(path: type_ = param('default')) -> web.Response: pass
    async def handler_5(path: type_ = param(default_factory=lambda: 'default')) -> web.Response: pass

    handlers_and_exc = [
        (handler_1, ParameterCannotUseDefaultError),
        (handler_2, ParameterCannotUseDefaultError),
        (handler_3, ParameterCannotUseDefaultFactoryError),
        (handler_4, ParameterCannotUseDefaultError),
        (handler_5, ParameterCannotUseDefaultFactoryError),
    ]
    for handler, exc in handlers_and_exc:
        with pytest.raises(exc):
            app.add_routes([web.post('/', handler)])  # type: ignore[arg-type]


async def test_incorrect_define_default_annotated_def(aiohttp_client: AiohttpClient) -> None:
    async def handler(
            query: Annotated[str, Query('default')] = 'default',
    ) -> web.Response:
        pass

    app = web.Application()
    with pytest.raises(IncorrectDefineDefaultValueError):
        app.add_routes([web.post('/', handler)])

    with pytest.raises((TypeError, ValueError)):
        Query('default', default_factory=lambda: 'default')  # NOTE: this exc raise pydantic


async def test_specify_both_default_and_default_factory() -> None:
    async def handler(
            query: Annotated[str, Query(default_factory=lambda: 'default')] = 'default',
    ) -> web.Response:
        pass

    app = web.Application()
    with pytest.raises(SpecifyBothDefaultAndDefaultFactoryError):
        app.add_routes([web.post('/', handler)])


@pytest.mark.parametrize('type_, param', default_params)
@pytest.mark.parametrize('default_value', default_values)
async def test_success_default(
        aiohttp_client: AiohttpClient,
        *,
        type_: Any,
        param: Any,
        default_value: Any,
) -> None:
    async def handler_1(
            data: Annotated[type_, param] = default_value,
    ) -> web.Response:
        assert data == default_value
        return web.Response()

    async def handler_2(
            data: Annotated[type_, param(default=default_value)],
    ) -> web.Response:
        assert data == default_value
        return web.Response()

    async def handler_3(
            data: type_ = param(default=default_value),
    ) -> web.Response:
        assert data == default_value
        return web.Response()

    for handler in (handler_1, handler_2, handler_3):
        await _test(aiohttp_client, handler, {}, HTTPStatus.OK)


@pytest.mark.parametrize('type_, param', default_params)
async def test_success_optional_default(
        aiohttp_client: AiohttpClient,
        type_: Any,
        param: Any,
) -> None:
    async def handler_1(
            data: Annotated[Optional[type_], param] = None,
    ) -> web.Response:
        assert data is None
        return web.Response()

    async def handler_2(
            data: Annotated[Optional[type_], param(None)],
    ) -> web.Response:
        assert data is None
        return web.Response()

    async def handler_3(
            data: Optional[type_] = param(None),
    ) -> web.Response:
        assert data is None
        return web.Response()

    for handler in (handler_1, handler_2, handler_3):
        await _test(aiohttp_client, handler, {}, HTTPStatus.OK)


@pytest.mark.parametrize('type_, param', default_params)
@pytest.mark.parametrize('default_value', default_values)
async def test_success_default_factory(
        aiohttp_client: AiohttpClient,
        *,
        type_: Any,
        param: Any,
        default_value: Any,
) -> None:
    async def handler_1(
            data: Annotated[type_, param(default_factory=lambda: default_value)],
    ) -> web.Response:
        assert data == default_value
        return web.Response()

    async def handler_2(
            data: type_ = param(default_factory=lambda: default_value),
    ) -> web.Response:
        assert data == default_value
        return web.Response()

    for handler in (handler_1, handler_2):
        await _test(aiohttp_client, handler, {}, HTTPStatus.OK)


# TODO: переписать на неуспешный
# @pytest.mark.parametrize('type_, param', default_params)
# async def test_success_optional_default_factory(
#         aiohttp_client: AiohttpClient,
#         *,
#         type_: Any,
#         param: Any,
# ) -> None:
#     async def handler_1(
#             data: Annotated[Optional[type_], param(default_factory=lambda: None)],
#     ) -> web.Response:
#         assert data is None
#         return web.Response()
#
#     async def handler_2(
#             data: Optional[type_] = param(default_factory=lambda: None),
#     ) -> web.Response:
#         assert data is None
#         return web.Response()
#
#     for handler in (handler_1, handler_2):
#         await _test(aiohttp_client, handler, {}, HTTPStatus.OK)


@pytest.mark.parametrize('type_, param, expected_data, resp_code', no_values_no_default_params)
async def test_attrs_no_values_no_default_annotated_definition(
        aiohttp_client: AiohttpClient,
        type_: Any,
        param: Any,
        resp_code: HTTPStatus,
        expected_data: Any,
) -> None:
    async def handler(
            data: Annotated[type_, param],
    ) -> web.Response:
        assert data == expected_data
        return web.Response()

    await _test(aiohttp_client, handler, {}, resp_code)

    async def handler(
            data: type_ = param,
    ) -> web.Response:
        assert data == expected_data
        return web.Response()

    await _test(aiohttp_client, handler, {}, resp_code)


@pytest.mark.parametrize('param, request_kw', schema_one_param_exist_second_param_is_default_params)
async def test_attrs_schema_one_param_exist_second_param_is_default(
        aiohttp_client: AiohttpClient,
        param: Any,
        request_kw: Dict[str, Any],
) -> None:
    async def handler(
            schema: Annotated[SchemaWithOneDefaultParam, param],
    ) -> web.Response:
        assert schema == SchemaWithOneDefaultParam(attr2='attr2')
        return web.Response()

    await _test(aiohttp_client, handler, request_kw, HTTPStatus.OK)

    async def handler(
            schema: SchemaWithOneDefaultParam = param,
    ) -> web.Response:
        assert schema == SchemaWithOneDefaultParam(attr2='attr2')
        return web.Response()

    await _test(aiohttp_client, handler, request_kw, HTTPStatus.OK)


async def _test(
        aiohttp_client: AiohttpClient,
        handler: Any,
        request_kw: Dict[str, Any],
        resp_status: int,
) -> None:
    app = web.Application()
    app.add_routes([web.post('/', handler)])
    client = await aiohttp_client(app)
    resp = await client.post('/', **request_kw)
    assert resp.status == resp_status
