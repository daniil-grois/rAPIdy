from json import JSONDecodeError
from typing import cast, Dict, Optional, Tuple, Union
from urllib.parse import parse_qsl, unquote

from aiohttp import BodyPartReader, MultipartReader
from aiohttp.abc import Request
from aiohttp.streams import EmptyStreamReader, StreamReader
from aiohttp.typedefs import JSONDecoder
from multidict import MultiDict

from rapidy import hdrs
from rapidy._client_errors import (
    BodyDataSizeExceedError,
    ExtractJsonError,
    ExtractMultipartError,
    ExtractMultipartPartError,
)
from rapidy._parsers import parse_multi_params
from rapidy.media_types import ApplicationJSON
from rapidy.typedefs import DictStrAny, DictStrListAny, DictStrListStr, DictStrStr


async def extract_path(request: Request) -> DictStrStr:
    return dict(request.match_info)


async def extract_headers(request: Request) -> Optional[DictStrStr]:
    headers = request.headers
    if not headers:
        return None

    return parse_multi_params(request.headers)  # type: ignore[return-value]


async def extract_cookies(request: Request) -> Optional[DictStrStr]:
    cookies = request.cookies
    if not cookies:
        return None

    return dict(cookies)


async def extract_query(request: Request) -> Optional[DictStrStr]:
    query = request.rel_url.query
    if not query:
        return None

    return parse_multi_params(query)  # type: ignore[return-value]


async def extract_body_stream(request: Request, max_size: int) -> Optional[StreamReader]:
    if not request.body_exists:
        return None

    # TODO: custom StreamReader with body_max_size
    return request.content


async def extract_body_bytes(request: Request, max_size: int) -> Optional[bytes]:
    if not request.body_exists:
        return None

    return await _read_full_body(request=request, max_size=max_size)


async def extract_body_text(request: Request, max_size: int) -> Optional[str]:
    if not request.body_exists:
        return None

    return await _read_body_text(request=request, max_size=max_size)


async def extract_body_json(
        request: Request,
        max_size: int,
        json_decoder: JSONDecoder,
) -> Optional[DictStrAny]:
    if not request.body_exists:
        return None

    text_body = await extract_body_text(request=request, max_size=max_size)
    try:
        return json_decoder(text_body)
    except JSONDecodeError as json_decode_err:
        raise ExtractJsonError(json_decode_err_msg=json_decode_err.args[0])


async def extract_body_x_www_form(
        request: Request,
        max_size: int,
        attrs_case_sensitive: bool,
        duplicated_attrs_parse_as_array: bool,
) -> Optional[Union[DictStrStr, DictStrListStr]]:
    if not request.body_exists:
        return None

    text_body = await extract_body_text(request=request, max_size=max_size)
    unquotes_text = unquote(text_body)
    key_value_arr = parse_qsl(unquotes_text)

    data: Union[MultiDict[str], Dict[str, str]]

    if duplicated_attrs_parse_as_array:
        data = MultiDict()
    else:
        data = {}

    for key, value in key_value_arr:
        if attrs_case_sensitive is False:
            key = key.lower()

        if duplicated_attrs_parse_as_array:
            # NOTE: Mandatory operation, otherwise all duplicate keys will be overwritten
            data = cast(MultiDict[str], data)
            data.add(key, value)
        else:
            data[key] = value

    return parse_multi_params(data, parse_as_array=duplicated_attrs_parse_as_array)


async def extract_body_multi_part(
        request: Request,
        max_size: int,
        attrs_case_sensitive: bool,
        duplicated_attrs_parse_as_array: bool,
) -> Optional[Union[DictStrAny, DictStrListAny]]:
    if not request.body_exists:
        return None

    multipart_reader = await _get_multipart_reader(request)

    data: Union[MultiDict[Union[bytearray, str]], Dict[str, Union[bytearray, str]]]

    if duplicated_attrs_parse_as_array:
        data = MultiDict()
    else:
        data = {}

    part_num = 1

    available_bytes_to_read = max_size
    # NOTE: For multipart, the body length exceed is checked for useful information only

    while True:
        part = await _get_next_part(multipart_reader=multipart_reader, current_part_num=part_num)
        if part is None:
            break
        if not isinstance(part, BodyPartReader):  # pragma: no cover  # NOTE: Scenario is impossible.
            break

        part_name = _get_part_name(part=part, current_part_num=part_num)

        part_data, updated_available_bytes_to_read = await _get_part_data(
            part=part,
            available_bytes_to_read=available_bytes_to_read,
            body_max_size=max_size,
        )

        available_bytes_to_read = updated_available_bytes_to_read

        payload = _get_part_data_payload(part=part, part_data=part_data)

        if attrs_case_sensitive is False:
            part_name = part_name.lower()

        if duplicated_attrs_parse_as_array:
            # NOTE: Mandatory operation, otherwise all duplicate keys will be overwritten
            data = cast(MultiDict[Union[bytearray, str]], data)
            data.add(part_name, payload)
        else:
            data[part_name] = payload

        part_num += 1

    return parse_multi_params(data, parse_as_array=duplicated_attrs_parse_as_array)


async def _get_multipart_reader(request: Request) -> MultipartReader:
    try:
        reader = await request.multipart()
    except Exception as read_error:
        raise ExtractMultipartError(
            multipart_error=read_error.args[0],  # TODO: specific error parsing
        )

    return reader


async def _get_part_data(
        part: BodyPartReader,
        available_bytes_to_read: int,
        body_max_size: int,
) -> Tuple[bytearray, int]:
    part_data = bytearray()

    while True:
        chunk_data, chunk_len = await _read_part_chunk(part)

        if chunk_len == 0:
            break

        available_bytes_to_read -= chunk_len

        # NOTE: The entire chunk is read and checked that it does not exceed the length,
        # while elsewhere only the next one byte is checked
        if available_bytes_to_read < 0:
            raise BodyDataSizeExceedError(body_max_size=body_max_size)

        part_data.extend(chunk_data)

    return part_data, available_bytes_to_read


async def _get_next_part(
        multipart_reader: MultipartReader,
        current_part_num: int,
) -> Optional[Union[MultipartReader, BodyPartReader]]:
    try:
        part = await multipart_reader.next()
    except AssertionError as assertion_err:
        if assertion_err.args[0] == 'Reading after EOF':  # NOTE: this is aiohttp bug
            return None
        raise assertion_err
    except Exception as value_error:
        raise ExtractMultipartPartError(
            multipart_error=value_error.args[0],  # TODO: specific error parsing
            part_num=current_part_num,
        )

    return part


def _get_part_name(
    part: BodyPartReader,
    current_part_num: int,
) -> str:
    part_name = part.name
    if part_name is None:
        raise ExtractMultipartPartError(
            multipart_error='Content-Disposition header doesnt contain `name` attr',
            part_num=current_part_num,
        )

    return part_name


async def _read_part_chunk(part: BodyPartReader) -> Tuple[bytes, int]:
    if part._at_eof:  # noqa:  WPS437
        return b'', 0

    chunk_data = await part.read_chunk(part.chunk_size)
    chunk_len = len(chunk_data)

    return chunk_data, chunk_len


def _get_part_data_payload(
    part: BodyPartReader,
    part_data: bytearray,
) -> Union[bytearray, str]:
    part_content_type = part.headers.get(hdrs.CONTENT_TYPE)

    if part_content_type and (part_content_type.startswith('text/') or part_content_type == ApplicationJSON):
        part_charset = part.get_charset(default='utf-8')
        part_decoded_data = part.decode(part_data)
        return part_decoded_data.decode(part_charset)

    return part_data


async def _read_request_buffer_chunk(n: int, request: Request) -> bytes:  # pragma: no cover
    if isinstance(request.content, EmptyStreamReader):
        return b''

    reader = request.content

    if reader._exception is not None:  # noqa:  WPS437
        raise reader._exception  # noqa:  WPS437

    while not reader._buffer and not reader._eof:  # noqa:  WPS437
        await reader._wait('BodyExtractor._read_request_buffer_chunk')  # noqa:  WPS437

    return reader._read_nowait(n)  # noqa:  WPS437


async def _read_full_body(request: Request, max_size: int) -> bytes:
    if request._read_bytes is None:  # noqa:  WPS437
        available_bytes_to_read = max_size
        body = bytearray()
        while True:
            if available_bytes_to_read > 0:
                chunk = await _read_request_buffer_chunk(available_bytes_to_read, request)
                body.extend(chunk)
                available_bytes_to_read -= len(chunk)

                if not chunk:
                    break

            else:
                is_body_size_exceeded = bool(await _read_request_buffer_chunk(1, request))
                if is_body_size_exceeded:
                    raise BodyDataSizeExceedError(body_max_size=max_size)

                break

        request._read_bytes = bytes(body)  # noqa:  WPS437

    return request._read_bytes  # noqa:  WPS437


async def _read_body_text(request: Request, max_size: int) -> str:
    bytes_body = await _read_full_body(request=request, max_size=max_size)
    encoding = request.charset or 'utf-8'
    return bytes_body.decode(encoding)
