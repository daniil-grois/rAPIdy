from typing import AsyncGenerator

import pytest
from aiohttp import FormData, MultipartWriter


@pytest.fixture
async def multipart_writer() -> AsyncGenerator[MultipartWriter, None]:
    with MultipartWriter('form-data') as multipart_data:
        yield multipart_data


@pytest.fixture
async def x_www_form_writer() -> FormData:
    return FormData()
