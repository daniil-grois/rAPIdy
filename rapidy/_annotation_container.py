import inspect
from abc import ABC, abstractmethod
from types import FunctionType
from typing import Any, Dict, Iterator, Optional, Set, Union

from aiohttp.web_request import Request
from typing_extensions import get_args

from rapidy._annotation_extractor import create_attribute_field_info, NotParameterError
from rapidy._base_exceptions import RapidyException
from rapidy._client_errors import ExtractError
from rapidy._fields import BaseModelField
from rapidy._validators import validate_request_param_data
from rapidy.request_params import create_param_model_field_by_request_param, HTTPRequestParamType, ParamFieldInfo
from rapidy.typedefs import Handler, MethodHandler, Middleware, ValidateReturn

_Handler = Union[FunctionType, Middleware]


class AnotherDataExtractionTypeAlreadyExistsError(RapidyException):
    message = (
        'Attribute with this data extraction type cannot be added to the handler - '
        'another data extraction type is already use in handler.'
    )


class RequestFieldAlreadyExistsError(RapidyException):
    message = (
        'Error during attribute definition in the handler - request param defined twice.'
        'The error may be because the first attribute of the handler is not annotated.'
        'By default, `rAPIdy` will pass `web.Request` to the first attribute if it has no type annotation.'
    )


class AttributeAlreadyExistsError(RapidyException):
    message = 'Attribute with this name or alias already exists.'


class ParamAnnotationContainer(ABC):
    all_data: bool

    def __init__(self, extractor: Any, http_request_param_type: HTTPRequestParamType) -> None:
        self._extractor = extractor
        self._http_request_param_type = http_request_param_type
        self._map_model_fields_by_alias: Dict[str, BaseModelField] = {}

    async def get_request_data(self, request: Request) -> ValidateReturn:
        raw_data = request._cache.get(self._http_request_param_type)

        if not raw_data:
            try:
                raw_data = await self._extractor(request)
            except ExtractError as exc:
                return {}, [exc.get_error_info(loc=(self._http_request_param_type,))]

            request._cache[self._http_request_param_type] = raw_data

        return validate_request_param_data(
            required_fields_map=self._map_model_fields_by_alias,
            raw_data=raw_data,
            all_data=self.all_data,
        )

    @abstractmethod
    def add_field(self, param_name: str, field_info: ParamFieldInfo, handler: _Handler) -> None:  # pragma: no cover
        pass

    def _add_field(self, param_name: str, field_info: ParamFieldInfo, handler: _Handler) -> None:
        model_field = create_param_model_field_by_request_param(
            annotated_type=field_info.annotation,
            field_info=field_info,
            param_name=param_name,
            param_default=field_info.default,
            param_default_factory=field_info.default_factory,
        )
        extraction_name = model_field.alias or model_field.name

        if self._map_model_fields_by_alias.get(extraction_name):
            raise AttributeAlreadyExistsError.create_with_handler_and_attr_info(handler=handler, attr_name=param_name)

        self._map_model_fields_by_alias[extraction_name] = model_field


class ParamAnnotationContainerAll(ParamAnnotationContainer):
    all_data = True

    def __init__(self, extractor: Any, http_request_param_type: HTTPRequestParamType):
        super().__init__(extractor, http_request_param_type)
        self._is_defined = False

    def add_field(self, param_name: str, field_info: ParamFieldInfo, handler: _Handler) -> None:
        if self._is_defined:
            raise AnotherDataExtractionTypeAlreadyExistsError.create_with_handler_and_attr_info(
                handler=handler,
                attr_name=param_name,
            )

        self._add_field(param_name=param_name, field_info=field_info, handler=handler)
        self._is_defined = True


class ParamAnnotationContainerSingle(ParamAnnotationContainer):
    all_data = False

    def __init__(self, extractor: Any, http_request_param_type: HTTPRequestParamType) -> None:
        super().__init__(extractor, http_request_param_type)
        self._added_field_info_class_names: Set[str] = set()

    def add_field(self, param_name: str, field_info: ParamFieldInfo, handler: _Handler) -> None:
        # NOTE: Make sure that the user does not want to extract two parameters using different data extractors.
        self._added_field_info_class_names.add(field_info.__class__.__name__)

        if len(self._added_field_info_class_names) > 1 or field_info.extract_all:
            raise AnotherDataExtractionTypeAlreadyExistsError.create_with_handler_and_attr_info(
                handler=handler,
                attr_name=param_name,
            )

        self._add_field(param_name=param_name, field_info=field_info, handler=handler)


class AnnotationContainer:
    def __init__(self, handler: Union[Handler, MethodHandler, Middleware]) -> None:
        self._handler = handler
        self._params: Dict[str, ParamAnnotationContainer] = {}
        self._request_exists: bool = False
        self._request_param_name: Optional[str] = None

    def __iter__(self) -> Iterator[ParamAnnotationContainer]:
        for param_container in self._params.values():
            if param_container:
                yield param_container

    def set_request_field(self, request_param_name: str) -> None:
        if self.request_exists:
            raise RequestFieldAlreadyExistsError.create_with_handler_info(handler=self._handler)

        self._request_exists = True
        self._request_param_name = request_param_name

    @property
    def request_exists(self) -> bool:
        return self._request_exists

    @property
    def request_param_name(self) -> str:
        if not self._request_exists or not self._request_param_name:
            raise

        return self._request_param_name

    def add_param(self, name: str, field_info: ParamFieldInfo) -> None:
        param_container = self._get_or_create_param_container(field_info=field_info)
        param_container.add_field(param_name=name, field_info=field_info, handler=self._handler)

    def _get_or_create_param_container(self, field_info: ParamFieldInfo) -> ParamAnnotationContainer:
        param_container = self._params.get(field_info.http_request_param_type)
        if not param_container:
            return self._create_param_container(field_info=field_info)

        return param_container

    def _create_param_container(self, field_info: ParamFieldInfo) -> ParamAnnotationContainer:
        param_container = param_annotation_container_factory(field_info=field_info)
        self._params[field_info.http_request_param_type] = param_container
        return param_container


def create_annotation_container(handler: _Handler, is_func_handler: bool = False) -> AnnotationContainer:
    container = AnnotationContainer(handler=handler)

    endpoint_signature = inspect.signature(handler)
    signature_params = endpoint_signature.parameters.items()

    num_of_extracted_signatures = 0

    for param_name, param in signature_params:
        num_of_extracted_signatures += 1

        try:
            field_info = create_attribute_field_info(param=param, handler=handler)
        except NotParameterError:
            if is_func_handler:
                if not get_args(param.annotation):
                    # FIXME: Fix the processing logic for the 1-st attribute to return a specific error
                    if issubclass(Request, param.annotation) or num_of_extracted_signatures == 1:
                        container.set_request_field(param_name)

            continue

        container.add_param(name=param_name, field_info=field_info)

    return container


def param_annotation_container_factory(field_info: ParamFieldInfo) -> ParamAnnotationContainer:
    if field_info.extract_all:
        return ParamAnnotationContainerAll(
            extractor=field_info.extractor, http_request_param_type=field_info.http_request_param_type,
        )

    return ParamAnnotationContainerSingle(
        extractor=field_info.extractor, http_request_param_type=field_info.http_request_param_type,
    )
