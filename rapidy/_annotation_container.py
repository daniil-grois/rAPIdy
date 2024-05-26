import inspect
from abc import ABC, abstractmethod
from types import FunctionType
from typing import Any, Dict, get_origin, Iterator, Optional, Set, Type, Union

from aiohttp.web_request import Request
from typing_extensions import Annotated, get_args

from rapidy._annotation_extractor import (
    get_annotated_definition_attr_default,
    get_default_definition_attr_default,
    NotParameterError,
    prepare_field_info,
)
from rapidy._client_errors import _create_handler_info_msg, ExtractError, RequiredFieldIsMissing
from rapidy._fields import ModelField
from rapidy._validators import validate_request_param_data
from rapidy.exceptions import RapidyException
from rapidy.request_params import create_param_model_field_by_request_param, HTTPRequestParamType, ParamFieldInfo
from rapidy.typedefs import Handler, MethodHandler, Middleware, NoArgAnyCallable, ValidateReturn


class AttributeAlreadyExistError(KeyError):
    pass


class AnnotationContainerAddFieldError(TypeError):
    pass


class RequestFieldAlreadyExistError(Exception):
    _base_err_msg = (
        'Error during attribute definition in the handler - request param defined twice.'
        'The error may be because the first attribute of the handler is not annotated.'
        'By default, `rAPIdy` will pass `web.Request` to the first attribute if it has no type annotation.'
    )

    def __init__(self, *args: Any, handler: Any):
        super().__init__(
            f'\n\n{self._base_err_msg} {_create_handler_info_msg(handler)}',
            *args,
        )

class AttributeDefinitionError(RapidyException):
    message = 'Attribute is already defined.'


class AddParameterError(RapidyException):
    message = (  # FIXME: refactor
        'Handler param definition error.\n'
        'Ways of defining parameters in `Handler`:\n\n'

        '* multiple individual parameters:\n'
        'def handler(h1: str = Header(), h2: str = Header()) -> ...:\n'
        '    ...\n\n'

        '* one complex parameter:\n'
        'def handler(h: str = Header(extract_all=True)) -> ...:\n'
        '    ...\n\n'

        '* parameters belonging to the same data extraction type:\n'
        'def handler(b1: str = JsonBody(), b2: str = JsonBody()) -> ...:\n'
        '    ...\n\n'

        '! Be careful parameters related to different types of data extraction will not work together:\n'
        'def handler(b1: str = JsonBody(), b2: str = TextBody()) -> ...:  # NOT WORKING\n'
        '    ...'
    )


class RequestParamDuplicateFieldHttpTypeError(RapidyException):
    message = 'Handler cannot retrieve the body in more than one way.'


class ParamAnnotationContainer(ABC):
    def __init__(self, extractor: Any, http_request_param_type: HTTPRequestParamType) -> None:
        self._extractor = extractor
        self._http_request_param_type = http_request_param_type

    @abstractmethod
    async def get_request_data(self, request: Request) -> ValidateReturn:  # noqa: WPS463 # pragma: no cover
        pass

    @abstractmethod
    def add_field(self, param_name: str, field_info: ParamFieldInfo) -> None:  # pragma: no cover
        pass


# TODO: ренейм - этот контейнер
class ValidateParamAnnotationContainer(ParamAnnotationContainer, ABC):
    single_model: bool

    def __init__(self, extractor: Any, http_request_param_type: HTTPRequestParamType) -> None:
        super().__init__(extractor=extractor, http_request_param_type=http_request_param_type)
        self._map_model_fields_by_alias: Dict[str, ModelField] = {}

    async def get_request_data(self, request: Request) -> ValidateReturn:
        raw_data = request._cache.get(self._http_request_param_type)  # FIXME: cache management should be centralized
        # TODO: декоратором? или над всеми параметрами этот метод обернуть в абстрактном классе
        if not raw_data:
            try:
                raw_data = await self._extractor(request)
            except ExtractError as exc:
                return {}, [exc.get_error_info(loc=(self._http_request_param_type,))]

            request._cache[self._http_request_param_type] = raw_data  # FIXME: cache management should be centralized

        return validate_request_param_data(
            required_fields_map=self._map_model_fields_by_alias,
            raw_data=raw_data,
            is_single_model=self.single_model,
        )

    def _add_field(self, param_name: str, field_info: ParamFieldInfo) -> None:
        model_field = create_param_model_field_by_request_param(
            annotated_type=field_info.annotation,
            field_info=field_info,
            param_name=param_name,
            param_default=field_info.default,
            param_default_factory=field_info.default_factory,
        )
        extraction_name = model_field.alias or model_field.name

        if self._map_model_fields_by_alias.get(extraction_name):
            raise AttributeAlreadyExistError

        self._map_model_fields_by_alias[extraction_name] = model_field


class ParamAnnotationContainerValidateSchema(ValidateParamAnnotationContainer):  # TODO: rename
    single_model = True

    def __init__(self, extractor: Any, http_request_param_type: HTTPRequestParamType):
        super().__init__(extractor, http_request_param_type)
        self._is_defined = False

    def add_field(self, param_name: str, field_info: ParamFieldInfo) -> None:
        if self._is_defined:
            raise AnnotationContainerAddFieldError

        self._add_field(param_name=param_name, field_info=field_info)
        self._is_defined = True


class ParamAnnotationContainerValidateParams(ValidateParamAnnotationContainer):
    single_model = False

    def __init__(self, extractor: Any, http_request_param_type: HTTPRequestParamType) -> None:
        super().__init__(extractor, http_request_param_type)

        # FIXME: нужен единый подход к проверке - сейчас это два костыля
        self._added_field_info_class_names: Set[Type[ParamFieldInfo]] = set()

    def add_field(self, param_name: str, field_info: ParamFieldInfo) -> None:
        # NOTE: Make sure that the user does not want to extract two parameters using different data extractors.
        self._added_field_info_class_names.add(field_info.__class__.__name__)

        # FIXME: это защищает body - чтобы нельзя разные имена было юзать - разные типы извлечений
        #  не самое удачное решение
        if len(self._added_field_info_class_names) > 1 or field_info.extract_all:
            raise AnnotationContainerAddFieldError  # TODO: одна ошибка

        if field_info.extract_all:
            raise AnnotationContainerAddFieldError  # TODO: другая ошибка

        self._add_field(param_name=param_name, field_info=field_info)


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
            raise RequestFieldAlreadyExistError(handler=self._handler)

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
        try:
            param_container.add_field(param_name=name, field_info=field_info)
        except AttributeAlreadyExistError:
            raise AttributeDefinitionError.create_with_handler_and_attr_info(handler=self._handler, attr_name=name)

    def _get_or_create_param_container(self, field_info: ParamFieldInfo) -> ParamAnnotationContainer:
        param_container = self._params.get(field_info.http_request_param_type)
        if not param_container:
            return self._create_param_container(field_info=field_info)

        return param_container

    def _create_param_container(self, field_info: ParamFieldInfo) -> ParamAnnotationContainer:
        param_container = param_annotation_container_factory(field_info=field_info)
        self._params[field_info.http_request_param_type] = param_container
        return param_container


def create_annotation_container(
        handler: Union[FunctionType, Middleware],
        is_func_handler: bool = False,
) -> AnnotationContainer:
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

        try:
            container.add_param(name=param_name, field_info=field_info)
        except AnnotationContainerAddFieldError:
            raise AddParameterError.create_with_handler_info(handler=handler)

    return container


def param_annotation_container_factory(field_info: ParamFieldInfo) -> ParamAnnotationContainer:
    if field_info.extract_all:
        return ParamAnnotationContainerValidateSchema(
            extractor=field_info.extractor, http_request_param_type=field_info.http_request_param_type,
        )

    return ParamAnnotationContainerValidateParams(
        extractor=field_info.extractor, http_request_param_type=field_info.http_request_param_type,
    )

# TODO вынестипотом отсюда
def create_attribute_field_info(handler: Handler, param: inspect.Parameter) -> ParamFieldInfo:
    annotation_origin = get_origin(param.annotation)

    if annotation_origin is Annotated:
        annotated_args = get_args(param.annotation)
        if len(annotated_args) != 2:
            raise NotParameterError

        type_, param_field_info = annotated_args

        prepared_param_field_info = prepare_field_info(param_field_info)
        default = get_annotated_definition_attr_default(
            param=param, handler=handler, type_=type_, field_info=prepared_param_field_info,
        )

    else:
        if param.default is inspect.Signature.empty:
            raise NotParameterError

        type_, param_field_info = param.annotation, param.default

        prepared_param_field_info = prepare_field_info(param_field_info)
        default = get_default_definition_attr_default(
            param=param, handler=handler, type_=param.annotation, field_info=prepared_param_field_info,
        )

    if not isinstance(prepared_param_field_info, ParamFieldInfo):
        raise Exception  # TODO

    prepared_param_field_info.annotation = type_
    prepared_param_field_info.default = default

    return prepared_param_field_info

    # TODO: ModelField будет создан и только под извлекающиеся -> похуй это для единообразия
    #  просто не будем дергать метод валидации, чисто дефолт достанем

    # TODO: некоторые типы данных не будут поддержаны пидантиком -> что с ними делать?

    # TODO: нужен ли метод create_param_model_field_by_request_param - или это костыль FastApi

    # TODO: сначала создать -> во время сборки проверять

    # Чтобы экстрактить данные которые не мб модельками
    # тут просто нужно уже сам параметр создавать и потом его в конйетенр кидать
    # параметр пусть определяет что с собой делать и нужна ли ему модель
    # или пусть внутри крейтит по типу фиелд инфо

    # param_annotation_container = param_annotation_container_factory(
    #     param_name=param.name,
    #     validate_type=prepared_param_field_info.validate_type,
    #     extractor=prepared_param_field_info.extractor,
    #     param_type=prepared_param_field_info.param_type,
    # )
    #
    #
    # return create_param_model_field_by_request_param(
    #     annotated_type=type_,
    #     field_info=prepared_param_field_info,
    #     param_name=param.name,
    #     param_default=prepared_param_field_info.default,
    #     param_default_factory=prepared_param_field_info.default_factory,
    # )
