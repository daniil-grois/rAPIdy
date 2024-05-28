from typing import Any

import pytest

from rapidy import web
from rapidy._annotation_container import AnotherDataExtractionTypeAlreadyExistsError
from rapidy.request_params import (
    Path,
    Header,
    Cookie,
    Query,
    JsonBody,
    FormDataBody,
    MultipartBody,
    BytesBody,
    StreamBody,
    TextBody,
)

PARAMS = (
    Path,
    Header,
    Cookie,
    Query,
    JsonBody,
    FormDataBody,
    MultipartBody,
)

BODY_PARAMS = (
    JsonBody,
    FormDataBody,
    MultipartBody,
    BytesBody,
    StreamBody,
    TextBody,
)


@pytest.mark.parametrize('type_', PARAMS)
async def test_check_single_and_complex_params(type_: Any) -> None:
    async def handler1(p1: Any = type_(), p2: Any = type_(extract_all=True)) -> Any:
        return web.Response()

    async def handler2(p1: Any = type_(extract_all=True), p2: Any = type_()) -> Any:
        return web.Response()

    app = web.Application()

    with pytest.raises(AnotherDataExtractionTypeAlreadyExistsError):
        app.add_routes([web.post('/', handler1)])

    with pytest.raises(AnotherDataExtractionTypeAlreadyExistsError):
        app.add_routes([web.post('/', handler2)])


@pytest.mark.parametrize('type_1', BODY_PARAMS)
@pytest.mark.parametrize('type_2', BODY_PARAMS)
async def test_body_diff_types(type_1: Any, type_2: Any) -> None:
    if (
        type_1().__class__.__name__ == type_2().__class__.__name__
        and not type_1().extract_all
        and not type_2().extract_all
    ):
        return

    async def handler(p1: Any = type_1(), p2: Any = type_2()) -> Any:
        return web.Response()

    app = web.Application()
    with pytest.raises(AnotherDataExtractionTypeAlreadyExistsError):
        app.add_routes([web.post('/', handler)])
