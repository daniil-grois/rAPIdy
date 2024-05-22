from dataclasses import dataclass
from http import HTTPStatus
from typing import Any, Optional, Type

import pytest
from pydantic import BaseModel
from pytest_aiohttp.plugin import AiohttpClient
from typing_extensions import Annotated, Final

from rapidy import web
from rapidy.request_params import (
    BodyBase,
    BytesBody,
    FormDataBody,
    FormDataBodyRaw,
    FormDataBodySchema,
    Header,
    HeaderBase,
    HeaderRaw,
    HeaderSchema,
    JsonBody,
    JsonBodyRaw,
    JsonBodySchema,
    MultipartBody,
    MultipartBodyRaw,
    MultipartBodySchema,
    TextBody,
)

simple_param_checklist = [Header, HeaderSchema, HeaderRaw]
body_checklist = [
    JsonBody,
    JsonBodySchema,
    JsonBodyRaw,
    FormDataBody,
    FormDataBodySchema,
    FormDataBodyRaw,
    MultipartBody,
    MultipartBodySchema,
    MultipartBodyRaw,
    BytesBody,
    TextBody,
]

ATTRIBUTE_DEFINITION_ERR_MSG: Final[str] = 'Error during attribute definition in the handler:'
EXTRACT_SCHEMA_TYPE_ERR_MSG: Final[str] = 'Schema annotated type must be a pydantic.BaseModel or dataclasses.dataclass'


class SchemaPydantic(BaseModel):
    attr: str


@dataclass
class SchemaDataclass:
    attr: str


def _create_annotated_def_handler(type_: Any, param: Any) -> Any:
    async def handler(attr: Annotated[type_, param]) -> Any: return web.Response()
    return handler


def _create_default_def_handler(type_: Any, param: Any) -> Any:
    async def handler(attr: type_ = param) -> Any: return web.Response()
    return handler


def _create_annotated_def_handler_two_params(param_1: Any, param_2: Any) -> Any:
    async def handler(attr1: Annotated[SchemaPydantic, param_1], attr2: Annotated[SchemaPydantic, param_2]) -> Any:
        return web.Response()
    return handler


def _create_default_def_handler_two_params(param_1: Any, param_2: Any) -> Any:
    async def handler(attr1: SchemaPydantic = param_1, attr2: SchemaPydantic = param_2) -> Any: return web.Response()
    return handler


@pytest.mark.parametrize('param_1', simple_param_checklist)
@pytest.mark.parametrize('param_2', simple_param_checklist)
@pytest.mark.parametrize(
    'create_handler_func', [
        pytest.param(_create_annotated_def_handler_two_params, id='annotated-def'),
        pytest.param(_create_default_def_handler_two_params, id='default-def'),
    ],
)
async def test_check_simple_param_incorrect_annotations(
        param_1: Type[HeaderBase],
        param_2: Type[HeaderBase],
        create_handler_func: Any,
) -> None:
    if param_1.validate_type.is_single_param() and param_2.validate_type.is_single_param():
        # skip success scenarios
        return

    handler = create_handler_func(param_1=param_1, param_2=param_2)

    app = web.Application()

    exc_message = ''
    with pytest.raises(Exception):
        try:
            app.add_routes([web.post('/', handler)])
        except Exception as exc:
            exc_message = exc.args[0]
            raise exc

    assert exc_message.startswith(ATTRIBUTE_DEFINITION_ERR_MSG)


@pytest.mark.parametrize('param_1', body_checklist)
@pytest.mark.parametrize('param_2', body_checklist)
@pytest.mark.parametrize(
    'create_handler_func', [
        pytest.param(_create_annotated_def_handler_two_params, id='annotated-def'),
        pytest.param(_create_default_def_handler_two_params, id='default-def'),
    ],
)
async def test_check_body_param_incorrect_annotations(
        param_1: Type[BodyBase],
        param_2: Type[BodyBase],
        create_handler_func: Any,
) -> None:
    params_is_single = param_1.validate_type.is_single_param() and param_2.validate_type.is_single_param()
    params_has_one_media_type = param_1.media_type == param_2.media_type

    if params_is_single and params_has_one_media_type:
        # skip success scenarios
        return

    handler = create_handler_func(param_1=param_1, param_2=param_2)

    app = web.Application()

    exc_message = ''
    with pytest.raises(Exception):
        try:
            app.add_routes([web.post('/', handler)])
        except Exception as exc:
            exc_message = exc.args[0]
            raise exc

    assert exc_message.startswith(ATTRIBUTE_DEFINITION_ERR_MSG)


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


@pytest.mark.parametrize(
    'type_', [
        SchemaPydantic,
        SchemaDataclass,
        Optional[SchemaPydantic],
        Optional[SchemaDataclass],
    ],
)
@pytest.mark.parametrize(
    'create_handler_func', [
        pytest.param(_create_annotated_def_handler, id='annotated-def'),
        pytest.param(_create_default_def_handler, id='default-def'),
    ],
)
async def test_success_schema_annotation(type_: Any, create_handler_func: Any) -> None:
    handler = create_handler_func(str, JsonBody)
    app = web.Application()
    app.add_routes([web.post('/', handler)])


@pytest.mark.parametrize(
    'param', [
        JsonBodySchema,
        FormDataBodySchema,
        MultipartBodySchema,
    ],
)
@pytest.mark.parametrize(
    'create_handler_func', [
        pytest.param(_create_annotated_def_handler, id='annotated-def'),
        pytest.param(_create_default_def_handler, id='default-def'),
    ],
)
async def test_failed_schema_annotation(param: Any, create_handler_func: Any) -> None:
    handler = create_handler_func(str, param)
    app = web.Application()
    exc_message = ''

    with pytest.raises(Exception):
        try:
            app.add_routes([web.post('/', handler)])
        except Exception as exc:
            exc_message = exc.args[0]
            raise exc

    assert exc_message.startswith(EXTRACT_SCHEMA_TYPE_ERR_MSG)


@pytest.mark.parametrize(
    'attr_type', [
        Annotated[str, str],
        Annotated[str, str, str],
    ],
)
async def test_incorrect_rapid_param(aiohttp_client: AiohttpClient, attr_type: Any) -> None:
    async def handler(any_param: attr_type, body: Annotated[str, str]) -> web.Response: pass

    app = web.Application()
    app.add_routes([web.post('/', handler)])

    client = await aiohttp_client(app)
    resp = await client.post('/', json={'attr': ''})

    assert resp.status == HTTPStatus.INTERNAL_SERVER_ERROR
