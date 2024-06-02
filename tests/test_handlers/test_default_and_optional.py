from functools import partial
from typing import Any, Optional, Tuple, Type

import pytest
from typing_extensions import Annotated, Final

from rapidy import web
from rapidy._annotation_extractor import (
    ParameterCannotBeOptionalError,
    SpecifyBothDefaultAndOptionalError,
    SpecifyBothDefaultFactoryAndOptionalError,
)
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
    StreamBody,
    TextBody,
)
from rapidy.typedefs import Handler

DEFAULT_VALUE: Final[str] = 'DEFAULT'


can_default_params = [
    pytest.param(Header, id='header?'),
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

def _create_all_handlers_type(
        validation_type: Any,
        type_: Type[ParamFieldInfo],
) -> Tuple[Tuple[Handler, Type[RapidyException]], ...]:
    async def handler_1(p: Annotated[Optional[validation_type], type_()] = DEFAULT_VALUE) -> web.Response:
        pass

    async def handler_2(p: Annotated[Optional[validation_type], type_(DEFAULT_VALUE)]) -> web.Response:
        pass

    async def handler_3(p: Annotated[Optional[validation_type], type_(default_factory=lambda: DEFAULT_VALUE)]) -> web.Response:
        pass

    async def handler_4(p: Optional[validation_type] = type_(DEFAULT_VALUE)) -> web.Response:
        pass

    async def handler_5(p: Optional[validation_type] = type_(default_factory=lambda: DEFAULT_VALUE)) -> web.Response:
        pass

    return (
        (handler_1, SpecifyBothDefaultAndOptionalError),
        (handler_2, SpecifyBothDefaultAndOptionalError),
        (handler_3, SpecifyBothDefaultFactoryAndOptionalError),
        (handler_4, SpecifyBothDefaultAndOptionalError),
        (handler_5, SpecifyBothDefaultFactoryAndOptionalError),
    )


@pytest.mark.parametrize('type_', can_default_params)
async def test_can_default_params(
        type_: Type[ParamFieldInfo],
) -> None:
    app = web.Application()
    for handler, exc in _create_all_handlers_type(Any, type_):
        with pytest.raises(exc):
            app.add_routes([web.post('/', handler)])


@pytest.mark.parametrize('type_', not_default_params)
async def test_cant_default_params(
        type_: Type[ParamFieldInfo],
) -> None:
    app = web.Application()
    for handler, _ in _create_all_handlers_type(Any, type_):
        with pytest.raises(ParameterCannotBeOptionalError):
            app.add_routes([web.post('/', handler)])
