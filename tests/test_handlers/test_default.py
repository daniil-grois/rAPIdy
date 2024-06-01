from functools import partial
from http import HTTPStatus
from typing import Any, Type, Tuple

import pytest
from pydantic import BaseModel
from pytest_aiohttp.plugin import AiohttpClient
from typing_extensions import Annotated, Final

from rapidy import web
from rapidy._annotation_extractor import ParameterCannotUseDefaultError, ParameterCannotUseDefaultFactoryError, \
    IncorrectDefineDefaultValueError, SpecifyBothDefaultAndDefaultFactoryError
from rapidy._base_exceptions import RapidyException
from rapidy._fields import ParamFieldInfo
from rapidy.request_params import (
    BytesBody,
    Cookie,
    FormDataBody,
    Header,
    JsonBody,
    MultipartBody,
    Path,
    Query,
    TextBody, StreamBody,
)
from rapidy.typedefs import Handler, DictStrAny

DEFAULT_VALUE: Final[str] = 'DEFAULT'


can_default_params = [
    pytest.param(Header, id='header'),
    # NOTE: not check Header(extract_all=True) as it always contains data

    pytest.param(Cookie, id='cookie'),
    pytest.param(partial(Cookie, extract_all=True), id='cookie-all'),

    pytest.param(Query, id='query'),
    pytest.param(partial(Query, extract_all=True), id='query-all'),

    pytest.param(JsonBody, id='json-body'),
    pytest.param(partial(JsonBody, extract_all=True), id='json-body-all'),

    pytest.param(FormDataBody, id='form-data-body'),
    pytest.param(partial(FormDataBody, extract_all=True), id='form-data-body-all'),

    pytest.param(MultipartBody, id='multipart-body'),
    pytest.param(partial(MultipartBody, extract_all=True), id='multipart-body-all'),

    pytest.param(TextBody, id='text-body'),
    pytest.param(BytesBody, id='bytes-body'),
]

not_default_params = [
    pytest.param(Path, id='path'),
    pytest.param(partial(Path, extract_all=True), id='path-all'),
    pytest.param(StreamBody, id='stream-body'),
]


def _create_all_default_handlers_type(
        type_: Type[ParamFieldInfo],
        default: Any = DEFAULT_VALUE,
) -> Tuple[Tuple[Handler, Type[RapidyException]], ...]:
    async def handler_1(p: Annotated[Any, type_()] = default) -> web.Response:
        assert p == default
        return web.Response()

    async def handler_2(p: Annotated[Any, type_(default)]) -> web.Response:
        assert p == default
        return web.Response()

    async def handler_3(p: Annotated[Any, type_(default_factory=lambda: default)]) -> web.Response:
        assert p == default
        return web.Response()

    async def handler_4(p: Any = type_(default)) -> web.Response:
        assert p == default
        return web.Response()

    async def handler_5(p: Any = type_(default_factory=lambda: default)) -> web.Response:
        assert p == default
        return web.Response()

    return (
        (handler_1, ParameterCannotUseDefaultError),
        (handler_2, ParameterCannotUseDefaultError),
        (handler_3, ParameterCannotUseDefaultFactoryError),
        (handler_4, ParameterCannotUseDefaultError),
        (handler_5, ParameterCannotUseDefaultFactoryError),
    )


@pytest.mark.parametrize('type_', can_default_params)
async def test_can_default(type_: Type[ParamFieldInfo], *, aiohttp_client: AiohttpClient) -> None:
    app = web.Application()
    counter, paths = 0, []

    for handler, _ in _create_all_default_handlers_type(type_):
        path = f'/{counter}'
        app.add_routes([web.post(path, handler)])
        paths.append(path)
        counter += 1

    for path in paths:
        await _test(app=app, path=path, aiohttp_client=aiohttp_client)



@pytest.mark.parametrize('type_', not_default_params)
async def test_cant_default_params(type_: Type[ParamFieldInfo]) -> None:
    app = web.Application()
    for handler, exc in _create_all_default_handlers_type(type_):
        with pytest.raises(exc):
            app.add_routes([web.post('/', handler)])


@pytest.mark.parametrize('type_', can_default_params)
async def test_incorrect_define_default_annotated_def(type_: Type[ParamFieldInfo]) -> None:
    async def handler(p: Annotated[str, type_('default')] = 'default') -> web.Response:
        pass

    app = web.Application()
    with pytest.raises(IncorrectDefineDefaultValueError):
        app.add_routes([web.post('/', handler)])

    with pytest.raises((TypeError, ValueError)):
        type_('default', default_factory=lambda: 'default')  # NOTE: this exc raise pydantic


@pytest.mark.parametrize('type_', can_default_params)
async def test_specify_both_default_and_default_factory(type_: Type[ParamFieldInfo]) -> None:
    async def handler(p: Annotated[str, type_(default_factory=lambda: 'default')] = 'default') -> web.Response:
        pass

    app = web.Application()
    with pytest.raises(SpecifyBothDefaultAndDefaultFactoryError):
        app.add_routes([web.post('/', handler)])


# NOTE: Let's not stop the `dev-user` if he wants to set default = None to an optional parameter
@pytest.mark.parametrize('type_', can_default_params)
async def test_optional_default(
        aiohttp_client: AiohttpClient,
        type_: Any,
) -> None:
    counter, paths = 0, []

    app = web.Application()

    for handler, _ in _create_all_default_handlers_type(type_=type_, default=None):
        path = f'/{counter}'
        app.add_routes([web.post(path, handler)])
        paths.append(path)
        counter += 1

    for path in paths:
        await _test(app=app, path=path, aiohttp_client=aiohttp_client)


@pytest.mark.parametrize('type_, request_kw', (
    (Header, {'headers': {'attr2': 'attr2'}}),
    (Cookie, {'cookies': {'attr2': 'attr2'}}),
    (Query, {'params': {'attr2': 'attr2'}}),
    (JsonBody, {'json': {'attr2': 'attr2'}}),
    (FormDataBody, {'data': {'attr2': 'attr2'}}),
))
async def test_attrs_schema_one_param_exist_second_param_is_default(
        aiohttp_client: AiohttpClient,
        type_: Type[ParamFieldInfo],
        request_kw: DictStrAny,
) -> None:
    class SchemaWithOneDefaultParam(BaseModel):
        attr1: str = 'attr1'
        attr2: str

    async def handler(
            schema: Annotated[SchemaWithOneDefaultParam, type_(extract_all=True)],
    ) -> web.Response:
        assert schema == SchemaWithOneDefaultParam(attr2='attr2')
        return web.Response()

    app = web.Application()
    app.add_routes([web.post('/', handler)])

    await _test(app=app, aiohttp_client=aiohttp_client, **request_kw)


async def _test(
        app: web.Application,
        aiohttp_client: AiohttpClient,
        path: str = '/',
        **request_kwargs: Any,
) -> None:
    client = await aiohttp_client(app)
    resp = await client.post(path, **request_kwargs)
    assert resp.status == HTTPStatus.OK
