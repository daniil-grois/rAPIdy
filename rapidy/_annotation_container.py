import inspect
from abc import ABC, abstractmethod
from types import FunctionType
from typing import Any, Dict, Iterator, Optional, Set, Type, Union

from aiohttp.web_request import Request
from typing_extensions import get_args, get_origin

from rapidy._annotation_extractor import extract_handler_attr_annotations, NotParameterError, \
    create_model_field_by_handler_signature_param
from rapidy._client_errors import _create_handler_attr_info_msg, _create_handler_info_msg, ExtractError, \
    RequiredFieldIsMissing
from rapidy._fields import ModelField
from rapidy._validators import validate_request_param_data
from rapidy.request_params import create_param_model_field_by_request_param, ParamFieldInfo, ParamType, ValidateType
from rapidy.typedefs import Handler, MethodHandler, Middleware, NoArgAnyCallable, ValidateReturn


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


class AttributeAlreadyExistError(KeyError):
    pass


class AttributeDefinitionError(Exception):
    _base_err_msg = 'Attribute is already defined.'

    def __init__(self, *args: Any, handler: Any, param_name: str):
        super().__init__(
            f'{self._base_err_msg}\n{_create_handler_attr_info_msg(handler, param_name)}',
            *args,
        )


class RequestParamError(Exception):
    _base_err_msg = (
        'Error during attribute definition in the handler:\n'
        '1. It is not possible to use multiple types of attribute extraction in one handler.\n'
        '2. For a handler attribute, you cannot define two Schemas or two Raw data extractors.'
    )

    def __init__(self, *args: Any, handler: Any):
        super().__init__(
            f'{self._base_err_msg}\n{_create_handler_info_msg(handler)}',
            *args,
        )


class ParamAnnotationContainer(ABC):
    def __init__(self, extractor: Any, param_type: ParamType) -> None:
        self._extractor = extractor
        self._param_type = param_type

    @abstractmethod
    async def get_request_data(self, request: Request) -> ValidateReturn:  # noqa: WPS463 # pragma: no cover
        pass

    @abstractmethod
    def add_field(
            self,
            model_field: ModelField,
            # param_name: str,
            # annotation: Type[Any],
            # field_info: ParamFieldInfo,
            # param_default: Any,
            # param_default_factory: Optional[NoArgAnyCallable],
    ) -> None:  # pragma: no cover
        pass


class ParamAnnotationContainerOnlyExtract(ParamAnnotationContainer):
    def __init__(self, extractor: Any, param_type: ParamType, param_name: str) -> None:
        super().__init__(extractor=extractor, param_type=param_type)
        self._param_name = param_name
        self._param_default = None
        self._param_default_factory = None
        self._is_defined = False
        self._is_optional = False

    def add_field(
            self,
            model_field: ModelField,
            # param_name: str,
            # annotation: Type[Any],
            # field_info: ParamFieldInfo,
            # param_default: Any,
            # param_default_factory: Optional[NoArgAnyCallable],
    ) -> None:
        if self._is_defined:
            raise AnnotationContainerAddFieldError

        # if get_origin(annotation) is Union:
        #     union_attributes = get_args(annotation)
        #     if type(None) in union_attributes:
        #         self._is_optional = True

        self._is_defined = True

    async def get_request_data(self, request: Request) -> ValidateReturn:
        raw_data = request._cache.get(self._param_type)  # FIXME: cache management should be centralized
        if raw_data:
            return raw_data

        try:
            raw_data = await self._extractor(request)
        except ExtractError as exc:
            return {}, [exc.get_error_info(loc=(self._param_type,))]

        if raw_data is None:
            if self._is_optional:
                return {self._param_name: None}, []

            return {}, [RequiredFieldIsMissing().get_error_info(loc=(self._param_type,))]

        request._cache[self._param_type] = raw_data  # FIXME: cache management should be centralized

        return {self._param_name: raw_data}, []


class ValidateParamAnnotationContainer(ParamAnnotationContainer, ABC):
    single_model: bool

    def __init__(self, extractor: Any, param_type: ParamType):
        super().__init__(extractor=extractor, param_type=param_type)
        self._map_model_fields_by_alias: Dict[str, ModelField] = {}

    async def get_request_data(self, request: Request) -> ValidateReturn:
        raw_data = request._cache.get(self._param_type)  # FIXME: cache management should be centralized
        if not raw_data:
            try:
                raw_data = await self._extractor(request)
            except ExtractError as exc:
                return {}, [exc.get_error_info(loc=(self._param_type,))]

            request._cache[self._param_type] = raw_data  # FIXME: cache management should be centralized

        return validate_request_param_data(
            required_fields_map=self._map_model_fields_by_alias,
            raw_data=raw_data,
            is_single_model=self.single_model,
        )

    def _add_field(
            self,
            # param_name: str,
            # annotated_type: Type[Any],
            # field_info: ParamFieldInfo,
            # param_default: Any,
            # param_default_factory: Optional[NoArgAnyCallable],
            model_field: ModelField,
    ) -> None:
        # model_field = create_param_model_field_by_request_param(
        #     annotated_type=annotated_type,
        #     field_info=field_info,
        #     param_name=param_name,
        #     param_default=param_default,
        #     param_default_factory=param_default_factory,
        # )
        extraction_name = model_field.alias or model_field.name

        if self._map_model_fields_by_alias.get(extraction_name):
            raise AttributeAlreadyExistError

        self._map_model_fields_by_alias[extraction_name] = model_field


class ParamAnnotationContainerValidateSchema(ValidateParamAnnotationContainer):
    single_model = True

    def __init__(self, extractor: Any, param_type: ParamType):
        super().__init__(extractor, param_type)
        self._is_defined = False

    def add_field(
            self,
            model_field: ModelField,
            # param_name: str,
            # annotation: Type[Any],
            # field_info: ParamFieldInfo,
            # param_default: Any,
            # param_default_factory: Optional[NoArgAnyCallable],
    ) -> None:
        if self._is_defined:
            raise AnnotationContainerAddFieldError

        self._add_field(model_field=model_field)
        # self._add_field(param_name, annotation, field_info, param_default, param_default_factory)
        self._is_defined = True


class ParamAnnotationContainerValidateParams(ValidateParamAnnotationContainer):
    single_model = False

    def __init__(self, extractor: Any, param_type: ParamType) -> None:
        super().__init__(extractor, param_type)
        self._added_field_info_types: Set[Type[ParamFieldInfo]] = set()

    def add_field(
            self,
            model_field: ModelField,
            # param_name: str,
            # annotation: Type[Any],
            # field_info: ParamFieldInfo,
            # param_default: Any,
            # param_default_factory: Optional[NoArgAnyCallable],
            # model_field: ModelField,
    ) -> None:
        # NOTE: Make sure that the user does not want to extract two parameters using different data extractors.
        # self._added_field_info_types.add(field_info.__class__)
        # if len(self._added_field_info_types) > 1:
        #     raise AnnotationContainerAddFieldError

        self._add_field(model_field=model_field)
        # self._add_field(param_name, annotation, field_info, param_default, param_default_factory)


def param_factory(
        param_name: str, validate_type: ValidateType, param_type: ParamType, extractor: Any,
) -> ParamAnnotationContainer:
    if validate_type.is_no_validate():
        return ParamAnnotationContainerOnlyExtract(extractor=extractor, param_type=param_type, param_name=param_name)

    if validate_type.is_complex_param():
        return ParamAnnotationContainerValidateSchema(extractor=extractor, param_type=param_type)

    if validate_type.is_single_param():
        return ParamAnnotationContainerValidateParams(extractor=extractor, param_type=param_type)

    raise  # pragma: no cover


class AnnotationContainer:
    def __init__(
            self,
            handler: Union[Handler, MethodHandler, Middleware],
    ) -> None:
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

    def add_param(
            self,
            name: str,
            # annotation: Type[Any],
            field_info: ParamFieldInfo,
            model_field: ModelField,
            # default: Any,
            # default_factory: Optional[NoArgAnyCallable],
    ) -> None:
        param_container = self._get_or_create_param_container(
            type_=field_info.param_type,
            param_name=name,
            field_info=field_info,
        )
        try:
            param_container.add_field(
                model_field=model_field,
                # param_name=name,
                # annotation=annotation,
                # field_info=field_info,
                # param_default=default,
                # param_default_factory=default_factory,
            )
        except AttributeAlreadyExistError:
            raise AttributeDefinitionError(handler=self._handler, param_name=name)

    def _get_or_create_param_container(
            self,
            type_: ParamType,
            param_name: str,
            field_info: ParamFieldInfo,
    ) -> ParamAnnotationContainer:
        param_container = self._params.get(type_)

        if not param_container:
            return self._create_param_container(param_name=param_name, param_type=type_, field_info=field_info)

        return param_container

    def _create_param_container(
            self,
            param_name: str,
            param_type: ParamType,
            field_info: ParamFieldInfo,
    ) -> ParamAnnotationContainer:
        param_container = param_factory(
            param_name=param_name,
            validate_type=field_info.validate_type,
            extractor=field_info.extractor,
            param_type=param_type,
        )
        self._params[param_type] = param_container
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
            model_field = create_model_field_by_handler_signature_param(param=param, handler=handler)
            # annotation, param_field_info, default = extract_handler_attr_annotations(param=param, handler=handler)
        except NotParameterError:
            if is_func_handler:
                if not get_args(param.annotation):
                    # FIXME: Fix the processing logic for the 1-st attribute to return a specific error
                    if issubclass(Request, param.annotation) or num_of_extracted_signatures == 1:
                        container.set_request_field(param_name)

            continue

        # TODO: обработку конкретной ошибки
        container.add_param(
            name=param_name,
            field_info=model_field.field_info,
            model_field=model_field,
        )
        # if isinstance(param_field_info, ParamFieldInfo):
        #     try:
        #         container.add_param(
        #             annotation=annotation,
        #             field_info=param_field_info,
        #             name=param_name,
        #             default=default,
        #             default_factory=param_field_info.default_factory,
        #         )
        #     except AnnotationContainerAddFieldError as annotation_container_add_field_error:
        #         raise RequestParamError(handler=handler) from annotation_container_add_field_error

        # else:  # pragma: no cover
        #     raise

    return container
