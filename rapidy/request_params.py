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
from rapidy._request_params_base import ParamType, ValidateType
from rapidy.constants import MAX_BODY_SIZE
from rapidy.media_types import ApplicationBytes, ApplicationJSON, ApplicationXWWWForm, MultipartForm, TextPlain
from rapidy.typedefs import NoArgAnyCallable, Required, Undefined

__all__ = (
    'BytesBody',
    'Cookie',
    'CookieSchema',
    'CookieRaw',
    'FormDataBody',
    'FormDataBodySchema',
    'FormDataBodyRaw',
    'Header',
    'HeaderSchema',
    'HeaderRaw',
    'JsonBody',
    'JsonBodySchema',
    'JsonBodyRaw',
    'MultipartBody',
    'MultipartBodySchema',
    'MultipartBodyRaw',
    'Path',
    'PathSchema',
    'PathRaw',
    'Query',
    'QuerySchema',
    'QueryRaw',
    'StreamBody',
    'TextBody',
)


class BodyParamAttrDefinitionError(Exception):
    pass


class DefaultDefinitionError(Exception):
    pass


class PathBase(ParamFieldInfo):
    param_type = ParamType.path
    extractor = staticmethod(extract_path)
    can_default = False


class Path(PathBase):
    validate_type = ValidateType.single_param


class PathSchema(PathBase):
    validate_type = ValidateType.complex_param


class PathRaw(PathBase):
    validate_type = ValidateType.no_validate


class HeaderBase(ParamFieldInfo):
    param_type = ParamType.header
    extractor = staticmethod(extract_headers)


class Header(HeaderBase):
    validate_type = ValidateType.single_param


class HeaderSchema(HeaderBase):
    validate_type = ValidateType.complex_param


class HeaderRaw(HeaderBase):
    validate_type = ValidateType.no_validate


class CookieBase(ParamFieldInfo):
    param_type = ParamType.cookie
    extractor = staticmethod(extract_cookies)


class Cookie(CookieBase):
    validate_type = ValidateType.single_param


class CookieSchema(CookieBase):
    validate_type = ValidateType.complex_param


class CookieRaw(CookieBase):
    validate_type = ValidateType.no_validate


class QueryBase(ParamFieldInfo):
    param_type = ParamType.query
    extractor = staticmethod(extract_query)


class Query(QueryBase):
    validate_type = ValidateType.single_param


class QuerySchema(QueryBase):
    validate_type = ValidateType.complex_param


class QueryRaw(QueryBase):
    validate_type = ValidateType.no_validate


class BodyBase(ParamFieldInfo, ABC):
    param_type = ParamType.body
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
    validate_type = ValidateType.no_validate
    can_default = False


class BytesBody(BodyBase):
    media_type = ApplicationBytes
    extractor = staticmethod(extract_body_bytes)
    validate_type = ValidateType.no_validate
    can_default = False


class TextBody(BodyBase):
    media_type = TextPlain
    extractor = staticmethod(extract_body_text)
    validate_type = ValidateType.no_validate
    can_default = False


class JsonBodyBase(BodyBase):
    media_type = ApplicationJSON
    extractor = staticmethod(extract_body_json)

    def __init__(
            self,
            default: Any = Undefined,
            *,
            default_factory: Optional[NoArgAnyCallable] = None,
            body_max_size: Optional[int] = None,
            json_decoder: Optional[JSONDecoder] = None,
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


class JsonBody(JsonBodyBase):
    validate_type = ValidateType.single_param

    def __init__(
            self,
            default: Any = Undefined,
            *,
            default_factory: Optional[NoArgAnyCallable] = None,
            body_max_size: Optional[int] = None,
            json_decoder: Optional[JSONDecoder] = None,
            **field_info_kwargs: Any,
    ) -> None:
        if body_max_size is not None or json_decoder is not None:
            raise BodyParamAttrDefinitionError(
                'A single JsonBody parameter does not allow to determine `body_max_size` or `json_decoder`. '
                'Please use JsonSchema or JsonRaw.',
            )

        super().__init__(
            default=default,
            default_factory=default_factory,
            body_max_size=body_max_size,
            json_decoder=json_decoder,
            **field_info_kwargs,
        )


class JsonBodySchema(JsonBodyBase):
    validate_type = ValidateType.complex_param


class JsonBodyRaw(JsonBodyBase):
    validate_type = ValidateType.no_validate


class FormDataBodyBase(BodyBase):
    media_type = ApplicationXWWWForm

    def __init__(
            self,
            default: Any = Undefined,
            *,
            default_factory: Optional[NoArgAnyCallable] = None,
            body_max_size: Optional[int] = None,
            attrs_case_sensitive: bool = False,
            duplicated_attrs_parse_as_array: bool = False,
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


class FormDataBody(FormDataBodyBase):
    validate_type = ValidateType.single_param

    def __init__(
            self,
            default: Any = Undefined,
            *,
            default_factory: Optional[NoArgAnyCallable] = None,
            body_max_size: Optional[int] = None,
            attrs_case_sensitive: bool = False,
            duplicated_attrs_parse_as_array: bool = False,
            **field_info_kwargs: Any,
    ) -> None:
        if (
            body_max_size is not None
            or attrs_case_sensitive
            or duplicated_attrs_parse_as_array
        ):
            raise BodyParamAttrDefinitionError(
                'A single FormDataBody parameter does not allow to determine '
                '`body_max_size` or `attrs_case_sensitive` or `duplicated_attrs_parse_as_array`. '
                'Please use FormDataSchema or FormDataRaw.',
            )

        super().__init__(
            default=default,
            default_factory=default_factory,
            body_max_size=body_max_size,
            attrs_case_sensitive=attrs_case_sensitive,
            duplicated_attrs_parse_as_array=duplicated_attrs_parse_as_array,
            **field_info_kwargs,
        )


class FormDataBodySchema(FormDataBodyBase):
    validate_type = ValidateType.complex_param


class FormDataBodyRaw(FormDataBodyBase):
    validate_type = ValidateType.no_validate


class MultipartBodyBase(BodyBase):
    media_type = MultipartForm

    def __init__(
            self,
            default: Any = Undefined,
            *,
            default_factory: Optional[NoArgAnyCallable] = None,
            body_max_size: Optional[int] = None,
            attrs_case_sensitive: bool = False,
            duplicated_attrs_parse_as_array: bool = False,
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


class MultipartBody(MultipartBodyBase):
    validate_type = ValidateType.single_param

    def __init__(
            self,
            default: Any = Undefined,
            *,
            default_factory: Optional[NoArgAnyCallable] = None,
            body_max_size: Optional[int] = None,
            attrs_case_sensitive: bool = False,
            duplicated_attrs_parse_as_array: bool = False,
            **field_info_kwargs: Any,
    ) -> None:
        if (
            body_max_size is not None
            or attrs_case_sensitive
            or duplicated_attrs_parse_as_array
        ):
            raise BodyParamAttrDefinitionError(
                'A single MultipartBody parameter does not allow to determine '
                '`body_max_size` or `attrs_case_sensitive` or `duplicated_attrs_parse_as_array`. '
                'Please use MultipartBodySchema or MultipartBodyRaw.',
            )

        super().__init__(
            default=default,
            default_factory=default_factory,
            body_max_size=body_max_size,
            attrs_case_sensitive=attrs_case_sensitive,
            duplicated_attrs_parse_as_array=duplicated_attrs_parse_as_array,
            **field_info_kwargs,
        )


class MultipartBodySchema(MultipartBodyBase):
    validate_type = ValidateType.complex_param


class MultipartBodyRaw(MultipartBodyBase):
    validate_type = ValidateType.no_validate


def create_param_model_field_by_request_param(
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
