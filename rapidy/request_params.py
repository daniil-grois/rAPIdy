import inspect
from abc import ABC
from copy import copy
from functools import partial
from typing import Any, Optional

from aiohttp.typedefs import DEFAULT_JSON_DECODER, JSONDecoder

from rapidy._extractors import (
    extract_body_bytes,
    extract_body_json,
    extract_body_multi_part,
    extract_body_stream,
    extract_body_text,
    extract_body_x_www_form,
    extract_cookies,
    extract_headers,
    extract_path,
    extract_query,
)
from rapidy._fields import create_field, get_annotation_from_field_info, ModelField, ParamFieldInfo
from rapidy._request_params_base import HTTPRequestParamType
from rapidy.constants import MAX_BODY_SIZE
from rapidy.media_types import ApplicationBytes, ApplicationJSON, ApplicationXWWWForm, MultipartForm, TextPlain
from rapidy.typedefs import NoArgAnyCallable, Required, Undefined

__all__ = (
    'Path',
    'Header',
    'Cookie',
    'Query',
    'JsonBody',
    'FormDataBody',
    'MultipartBody',
    'BytesBody',
    'StreamBody',
    'TextBody',
)


class BodyParamAttrDefinitionError(Exception):
    pass


class DefaultDefinitionError(Exception):
    pass


class Path(ParamFieldInfo):
    http_request_param_type = HTTPRequestParamType.path
    extractor = staticmethod(extract_path)
    can_default = False


class Header(ParamFieldInfo):
    http_request_param_type = HTTPRequestParamType.header
    extractor = staticmethod(extract_headers)


class Cookie(ParamFieldInfo):
    http_request_param_type = HTTPRequestParamType.cookie
    extractor = staticmethod(extract_cookies)


class Query(ParamFieldInfo):
    http_request_param_type = HTTPRequestParamType.query
    extractor = staticmethod(extract_query)


class BodyBase(ParamFieldInfo, ABC):
    http_request_param_type = HTTPRequestParamType.body
    media_type: str

    def __init__(
            self,
            default: Any = Undefined,
            *,
            default_factory: Optional[NoArgAnyCallable] = None,
            body_max_size: Optional[int] = None,
            **field_info_kwargs: Any,
    ) -> None:
        # FIXME:
        #  now must be called after the definition of extractor in the inheritor class.
        self.body_max_size = body_max_size or MAX_BODY_SIZE

        self.extractor = partial(self.extractor, max_size=self.body_max_size)

        super().__init__(default=default, default_factory=default_factory, **field_info_kwargs)


class StreamBody(BodyBase):
    media_type = ApplicationBytes
    extractor = staticmethod(extract_body_stream)
    can_default = False
    only_raw = True


class BytesBody(BodyBase):
    media_type = ApplicationBytes
    extractor = staticmethod(extract_body_bytes)
    only_raw = True


class TextBody(BodyBase):
    media_type = TextPlain
    extractor = staticmethod(extract_body_text)
    only_raw = True


class JsonBody(BodyBase):
    media_type = ApplicationJSON
    extractor = staticmethod(extract_body_json)

    def __init__(
            self,
            default: Any = Undefined,
            *,
            default_factory: Optional[NoArgAnyCallable] = None,
            body_max_size: Optional[int] = None,  # TODO: убрать поле
            json_decoder: Optional[JSONDecoder] = None,  # TODO: убрать поле
            **field_info_kwargs: Any,
    ) -> None:
        self.extractor = partial(  # noqa: WPS601
            self.extractor,
            json_decoder=json_decoder or DEFAULT_JSON_DECODER,
        )

        super().__init__(
            default=default,
            default_factory=default_factory,
            body_max_size=body_max_size,
            **field_info_kwargs,
        )


class FormDataBody(BodyBase):
    media_type = ApplicationXWWWForm

    def __init__(
            self,
            default: Any = Undefined,
            *,
            default_factory: Optional[NoArgAnyCallable] = None,
            body_max_size: Optional[int] = None,  # TODO: убрать поле
            attrs_case_sensitive: bool = False,  # TODO: убрать поле
            duplicated_attrs_parse_as_array: bool = False,  # TODO: убрать поле
            **field_info_kwargs: Any,
    ) -> None:
        self.extractor = partial(
            extract_body_x_www_form,
            attrs_case_sensitive=attrs_case_sensitive,
            duplicated_attrs_parse_as_array=duplicated_attrs_parse_as_array,
        )

        super().__init__(
            default=default,
            default_factory=default_factory,
            body_max_size=body_max_size,
            **field_info_kwargs,
        )


class MultipartBody(BodyBase):
    media_type = MultipartForm

    def __init__(
            self,
            default: Any = Undefined,
            *,
            default_factory: Optional[NoArgAnyCallable] = None,
            body_max_size: Optional[int] = None,  # TODO: убрать поле
            attrs_case_sensitive: bool = False,  # TODO: убрать поле
            duplicated_attrs_parse_as_array: bool = False,  # TODO: убрать поле
            **field_info_kwargs: Any,
    ) -> None:
        self.extractor = partial(
            extract_body_multi_part,
            attrs_case_sensitive=attrs_case_sensitive,
            duplicated_attrs_parse_as_array=duplicated_attrs_parse_as_array,
        )

        super().__init__(
            default=default,
            default_factory=default_factory,
            body_max_size=body_max_size,
            **field_info_kwargs,
        )


def create_param_model_field_by_request_param(  # TODO: точно здесь?
        *,
        annotated_type: Any,
        field_info: ParamFieldInfo,
        param_name: str,
        param_default: Any,
        param_default_factory: Optional[NoArgAnyCallable],
) -> ModelField:
    copied_field_info = copy(field_info)

    if param_default is not inspect.Signature.empty:
        copied_field_info.default = param_default
    else:
        copied_field_info.default = Required

    if param_default_factory is not None:
        copied_field_info.default_factory = param_default_factory

    inner_attribute_type = get_annotation_from_field_info(
        annotation=annotated_type,
        field_info=field_info,
        field_name=param_name,
    )

    return create_field(
        name=param_name,
        type_=inner_attribute_type,
        field_info=copied_field_info,
    )

# TODO: будет вызываться ошибка что Deprecation
# TODO: проверить что указал все
# TODO: в all тоже все прописать
# TODO: не забыть про mypy
