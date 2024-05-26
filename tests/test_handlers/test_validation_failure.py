from http import HTTPStatus
from typing import Any, Dict, List

from pydantic import BaseModel, Field
from pytest_aiohttp.plugin import AiohttpClient
from typing_extensions import Annotated, Final

from rapidy import web
from rapidy.constants import PYDANTIC_V1, PYDANTIC_V2
from rapidy.request_params import Cookie, Header, JsonBody, Path, Query
from rapidy.typedefs import HandlerType

HANDLER_PATH: Final[str] = '/{attr1}/{attr2}/{attr3}'

REQUEST = {'attr1': '0', 'attr2': '0', 'attr3': '0'}
REQUEST_PATH: Final[str] = HANDLER_PATH.format(**REQUEST)


attr1_model_field_args = {
    'alias': 'attr1',
    'min_length': 2,

}
attr2_model_field_args = {
    'alias': 'attr2',
    'ge': 1,
}
attr3_model_field_args = {
    'alias': 'attr3',
    'min_items': 1,
}
attr4_model_field_args = {
    'alias': 'attr4',
}


class Schema(BaseModel):
    attr1: str = Field(**attr1_model_field_args)
    attr2: int = Field(**attr2_model_field_args)
    attr3: List[str] = Field(**attr3_model_field_args)
    attr4: str = Field(**attr4_model_field_args)


async def test_individual_params(aiohttp_client: AiohttpClient) -> None:
    async def handler(
            path_attr1: Annotated[str, Path(**attr1_model_field_args)],
            path_attr2: Annotated[int, Path(**attr2_model_field_args)],
            path_attr3: Annotated[List[int], Path(**attr3_model_field_args)],
            path_attr4: Annotated[str, Path(**attr4_model_field_args)],
            header_attr1: Annotated[str, Header(**attr1_model_field_args)],
            header_attr2: Annotated[int, Header(**attr2_model_field_args)],
            header_attr3: Annotated[List[int], Header(**attr3_model_field_args)],
            header_attr4: Annotated[str, Header(**attr4_model_field_args)],
            cookie_attr1: Annotated[str, Cookie(**attr1_model_field_args)],
            cookie_attr2: Annotated[int, Cookie(**attr2_model_field_args)],
            cookie_attr3: Annotated[List[int], Cookie(**attr3_model_field_args)],
            cookie_attr4: Annotated[str, Cookie(**attr4_model_field_args)],
            query_attr1: Annotated[str, Query(**attr1_model_field_args)],
            query_attr2: Annotated[int, Query(**attr2_model_field_args)],
            query_attr3: Annotated[List[int], Query(**attr3_model_field_args)],
            query_attr4: Annotated[str, Query(**attr4_model_field_args)],
            body_attr1: Annotated[str, JsonBody(**attr1_model_field_args)],
            body_attr2: Annotated[int, JsonBody(**attr2_model_field_args)],
            body_attr3: Annotated[List[int], JsonBody(**attr3_model_field_args)],
            body_attr4: Annotated[str, JsonBody(**attr4_model_field_args)],
    ) -> web.Response:
        return web.Response()

    await _test(aiohttp_client, handler)


async def test_single_schema(aiohttp_client: AiohttpClient) -> None:
    async def handler(
            path_data: Annotated[Schema, Path(extract_all=True)],
            header_data: Annotated[Schema, Header(extract_all=True)],
            cookie_data: Annotated[Schema, Cookie(extract_all=True)],
            query_data: Annotated[Schema, Query(extract_all=True)],
            body_data: Annotated[Schema, JsonBody(extract_all=True)],
    ) -> web.Response:
        return web.Response()

    await _test(aiohttp_client, handler)


async def _test(aiohttp_client: AiohttpClient, handler: HandlerType) -> None:
    app = web.Application()
    app.add_routes([web.post(HANDLER_PATH, handler)])
    client = await aiohttp_client(app)
    resp = await client.post(
        REQUEST_PATH,
        json=REQUEST,
        cookies=REQUEST,
        headers=REQUEST,
        params=REQUEST,
    )
    assert resp.status == HTTPStatus.UNPROCESSABLE_ENTITY
    resp_json = await resp.json()

    if PYDANTIC_V1:
        pydantic_v1_err_check(resp_json)
    elif PYDANTIC_V2:
        pydantic_v2_err_check(resp_json)
    else:
        raise


def pydantic_v1_err_check(resp_json: Dict[str, Any]) -> None:
    assert resp_json == {
        'errors': [
            {
                'ctx': {'limit_value': 2},
                'loc': ['path', 'attr1'],
                'msg': 'ensure this value has at least 2 characters',
                'type': 'value_error.any_str.min_length',
            },
            {
                'ctx': {'limit_value': 1},
                'loc': ['path', 'attr2'],
                'msg': 'ensure this value is greater than or equal to 1',
                'type': 'value_error.number.not_ge',
            },
            {
                'loc': ['path', 'attr3'],
                'msg': 'value is not a valid list',
                'type': 'type_error.list',
            },
            {
                'loc': ['path', 'attr4'],
                'msg': 'field required',
                'type': 'value_error.missing',
            },
            {
                'ctx': {'limit_value': 2},
                'loc': ['header', 'attr1'],
                'msg': 'ensure this value has at least 2 characters',
                'type': 'value_error.any_str.min_length',
            },
            {
                'ctx': {'limit_value': 1},
                'loc': ['header', 'attr2'],
                'msg': 'ensure this value is greater than or equal to 1',
                'type': 'value_error.number.not_ge',
            },
            {
                'loc': ['header', 'attr3'],
                'msg': 'value is not a valid list',
                'type': 'type_error.list',
            },
            {
                'loc': ['header', 'attr4'],
                'msg': 'field required',
                'type': 'value_error.missing',
            },
            {
                'ctx': {'limit_value': 2},
                'loc': ['cookie', 'attr1'],
                'msg': 'ensure this value has at least 2 characters',
                'type': 'value_error.any_str.min_length',
            },
            {
                'ctx': {'limit_value': 1},
                'loc': ['cookie', 'attr2'],
                'msg': 'ensure this value is greater than or equal to 1',
                'type': 'value_error.number.not_ge',
            },
            {
                'loc': ['cookie', 'attr3'],
                'msg': 'value is not a valid list',
                'type': 'type_error.list',
            },
            {
                'loc': ['cookie', 'attr4'],
                'msg': 'field required',
                'type': 'value_error.missing',
            },
            {
                'ctx': {'limit_value': 2},
                'loc': ['query', 'attr1'],
                'msg': 'ensure this value has at least 2 characters',
                'type': 'value_error.any_str.min_length',
            },
            {
                'ctx': {'limit_value': 1},
                'loc': ['query', 'attr2'],
                'msg': 'ensure this value is greater than or equal to 1',
                'type': 'value_error.number.not_ge',
            },
            {
                'loc': ['query', 'attr3'],
                'msg': 'value is not a valid list',
                'type': 'type_error.list',
            },
            {
                'loc': ['query', 'attr4'],
                'msg': 'field required',
                'type': 'value_error.missing',
            },
            {
                'ctx': {'limit_value': 2},
                'loc': ['body', 'attr1'],
                'msg': 'ensure this value has at least 2 characters',
                'type': 'value_error.any_str.min_length',
            },
            {
                'ctx': {'limit_value': 1},
                'loc': ['body', 'attr2'],
                'msg': 'ensure this value is greater than or equal to 1',
                'type': 'value_error.number.not_ge',
            },
            {
                'loc': ['body', 'attr3'],
                'msg': 'value is not a valid list',
                'type': 'type_error.list',
            },
            {
                'loc': ['body', 'attr4'],
                'msg': 'field required',
                'type': 'value_error.missing',
            },
        ],
    }


def pydantic_v2_err_check(resp_json: Dict[str, Any]) -> None:
    assert resp_json == {
        'errors': [
            {
                'ctx': {'min_length': 2},
                'loc': ['path', 'attr1'],
                'msg': 'String should have at least 2 characters',
                'type': 'string_too_short',
            },
            {
                'ctx': {'ge': 1},
                'loc': ['path', 'attr2'],
                'msg': 'Input should be greater than or equal to 1',
                'type': 'greater_than_equal',
            },
            {
                'loc': ['path', 'attr3'],
                'msg': 'Input should be a valid list',
                'type': 'list_type',
            },
            {
                'loc': ['path', 'attr4'],
                'msg': 'Field required',
                'type': 'missing',
            },
            {
                'ctx': {'min_length': 2},
                'loc': ['header', 'attr1'],
                'msg': 'String should have at least 2 characters',
                'type': 'string_too_short',
            },
            {
                'ctx': {'ge': 1},
                'loc': ['header', 'attr2'],
                'msg': 'Input should be greater than or equal to 1',
                'type': 'greater_than_equal',
            },
            {
                'loc': ['header', 'attr3'],
                'msg': 'Input should be a valid list',
                'type': 'list_type',
            },
            {
                'loc': ['header', 'attr4'],
                'msg': 'Field required',
                'type': 'missing',
            },
            {
                'ctx': {'min_length': 2},
                'loc': ['cookie', 'attr1'],
                'msg': 'String should have at least 2 characters',
                'type': 'string_too_short',
            },
            {
                'ctx': {'ge': 1},
                'loc': ['cookie', 'attr2'],
                'msg': 'Input should be greater than or equal to 1',
                'type': 'greater_than_equal',
            },
            {
                'loc': ['cookie', 'attr3'],
                'msg': 'Input should be a valid list',
                'type': 'list_type',
            },
            {
                'loc': ['cookie', 'attr4'],
                'msg': 'Field required',
                'type': 'missing',
            },
            {
                'ctx': {'min_length': 2},
                'loc': ['query', 'attr1'],
                'msg': 'String should have at least 2 characters',
                'type': 'string_too_short',
            },
            {
                'ctx': {'ge': 1},
                'loc': ['query', 'attr2'],
                'msg': 'Input should be greater than or equal to 1',
                'type': 'greater_than_equal',
            },
            {
                'loc': ['query', 'attr3'],
                'msg': 'Input should be a valid list',
                'type': 'list_type',
            },
            {
                'loc': ['query', 'attr4'],
                'msg': 'Field required',
                'type': 'missing',
            },
            {
                'ctx': {'min_length': 2},
                'loc': ['body', 'attr1'],
                'msg': 'String should have at least 2 characters',
                'type': 'string_too_short',
            },
            {
                'ctx': {'ge': 1},
                'loc': ['body', 'attr2'],
                'msg': 'Input should be greater than or equal to 1',
                'type': 'greater_than_equal',
            },
            {
                'loc': ['body', 'attr3'],
                'msg': 'Input should be a valid list',
                'type': 'list_type',
            },
            {
                'loc': ['body', 'attr4'],
                'msg': 'Field required',
                'type': 'missing',
            },
        ],
    }
