import inspect
from dataclasses import is_dataclass
from typing import Any, cast, NamedTuple, Sequence, Type, Union

from pydantic import BaseModel
from typing_extensions import Annotated, get_args, get_origin

from rapidy._client_errors import _create_handler_attr_info_msg
from rapidy._fields import ModelField, create_field
from rapidy.request_params import ParamFieldInfo, create_param_model_field_by_request_param
from rapidy.typedefs import Handler, Required, Undefined


class AnnotationData(NamedTuple):
    type_: Any
    param_field_info: ParamFieldInfo
    default_value: Any


class NotParameterError(Exception):
    pass


class ParameterCannotUseDefaultError(Exception):
    _base_err_msg = 'Handler attribute with Type `{class_name}` cannot have a default value.'

    def __init__(self, *args: Any, class_name: str, handler: Any, param_name: str) -> None:
        super().__init__(
            f'{self._base_err_msg.format(class_name=class_name)}\n{_create_handler_attr_info_msg(handler, param_name)}',
            *args,
        )


class ParameterCannotUseDefaultFactoryError(Exception):
    _base_err_msg = 'Handler attribute with Type `{class_name}` cannot have a default_factory.'

    def __init__(self, *args: Any, class_name: str, handler: Any, param_name: str) -> None:
        super().__init__(
            f'{self._base_err_msg.format(class_name=class_name)}\n{_create_handler_attr_info_msg(handler, param_name)}',
            *args,
        )


class SpecifyBothDefaultAndDefaultFactoryError(TypeError):
    _base_err_msg = 'Cannot specify both default and default_factory in `{class_name}`.'

    def __init__(self, *args: Any, class_name: str, handler: Any, param_name: str) -> None:
        super().__init__(
            f'{self._base_err_msg.format(class_name=class_name)}\n{_create_handler_attr_info_msg(handler, param_name)}',
            *args,
        )


class SpecifyBothDefaultAndOptionalError(TypeError):
    _base_err_msg = 'A parameter cannot be optional if it contains a default value in `{class_name}`.'

    def __init__(self, *args: Any, class_name: str, handler: Any, param_name: str) -> None:
        super().__init__(
            f'{self._base_err_msg.format(class_name=class_name)}\n{_create_handler_attr_info_msg(handler, param_name)}',
            *args,
        )


class SpecifyBothDefaultFactoryAndOptionalError(TypeError):
    _base_err_msg = 'A parameter cannot be optional if it contains a default factory in `{class_name}`.'

    def __init__(self, *args: Any, class_name: str, handler: Any, param_name: str) -> None:
        super().__init__(
            f'{self._base_err_msg.format(class_name=class_name)}\n{_create_handler_attr_info_msg(handler, param_name)}',
            *args,
        )


class IncorrectDefineDefaultValueError(Exception):
    _base_err_msg = (
        'Default value cannot be set in `{class_name}`. '
        'You cannot specify a default value using Param(<default_value>, ...) and `=` at the same time.'
    )

    def __init__(self, *args: Any, class_name: str, handler: Any, param_name: str) -> None:
        super().__init__(
            f'{self._base_err_msg.format(class_name=class_name)}\n{_create_handler_attr_info_msg(handler, param_name)}',
            *args,
        )


class UnsupportedSchemaDataTypeError(TypeError):
    def __init__(self, *args: Any, err_msg: str, handler: Any, param_name: str) -> None:
        super().__init__(
            f'{err_msg}\n{_create_handler_attr_info_msg(handler, param_name)}',
            *args,
        )


def _get_annotation_data_by_annotated_flow(
        attr_type: Any,
        param_field_info: ParamFieldInfo,
        handler: Handler,
        param: inspect.Parameter,
) -> AnnotationData:
    default = _get_annotated_definition_attr_default(
        handler=handler,
        type_=attr_type,
        field_info=param_field_info,
        param=param,
    )
    return AnnotationData(
        type_=attr_type,
        param_field_info=param_field_info,
        default_value=default,
    )


def _get_annotation_data_by_default_value_flow(
        handler: Handler,
        param: inspect.Parameter,
) -> AnnotationData:
    param_field_info = _prepare_field_info(param.default)
    default = _get_default_definition_attr_default(
        handler=handler,
        type_=param.annotation,
        field_info=param_field_info,
        param_name=param.name,
    )
    return AnnotationData(
        type_=param.annotation,
        param_field_info=param_field_info,
        default_value=default,
    )


def _get_annotation_data(handler: Handler, param: Any) -> AnnotationData:
    a = create_model_field_by_handler_signature_param(handler, param)

    annotation_origin = get_origin(param.annotation)

    if annotation_origin is Annotated:
        annotated_args = get_args(param.annotation)
        if len(annotated_args) != 2:
            raise NotParameterError

        return _get_annotation_data_by_annotated_flow(
            attr_type=annotated_args[0],
            param_field_info=_prepare_field_info(annotated_args[1]),
            handler=handler,
            param=param,
        )

    if param.default is inspect.Signature.empty:
        raise NotParameterError

    return _get_annotation_data_by_default_value_flow(
        handler=handler,
        param=param,
    )


def _prepare_field_info(raw_field_info: Union[ParamFieldInfo, Type[ParamFieldInfo]]) -> ParamFieldInfo:
    if not isinstance(raw_field_info, ParamFieldInfo):
        if isinstance(raw_field_info, type) and issubclass(raw_field_info, ParamFieldInfo):
            raw_field_info = raw_field_info()
        else:
            raise NotParameterError

    return cast(ParamFieldInfo, raw_field_info)


def _get_annotated_definition_attr_default(
        param: inspect.Parameter,
        handler: Handler,
        type_: Any,
        field_info: ParamFieldInfo,
) -> Any:
    default_value_for_param_exists = param.default is not inspect.Signature.empty
    default_value_for_field_exists = check_default_value_for_field_exists(field_info)
    default_factory_for_field_exists = check_default_factory_for_field_exists(field_info)

    default_exists = default_value_for_param_exists or default_value_for_field_exists
    can_default = field_info.can_default and not field_info.validate_type.is_no_validate()  # TODO: почему этой проверки нет в дефолте
    param_is_optional = is_optional(type_)

    if default_exists and not can_default:
        raise ParameterCannotUseDefaultError(
            class_name=field_info.__class__.__name__,
            handler=handler,
            param_name=param.name,
        )

    if default_factory_for_field_exists and not can_default:
        raise ParameterCannotUseDefaultFactoryError(
            class_name=field_info.__class__.__name__,
            handler=handler,
            param_name=param.name,
        )

    if default_exists and default_factory_for_field_exists:
        if field_info.default_factory is not None:
            raise SpecifyBothDefaultAndDefaultFactoryError(
                class_name=field_info.__class__.__name__,
                handler=handler,
                param_name=param.name,
            )

    if default_value_for_param_exists and default_value_for_field_exists:
        raise IncorrectDefineDefaultValueError(
            class_name=field_info.__class__.__name__,
            handler=handler,
            param_name=param.name,
        )

    default = inspect.Signature.empty

    if default_value_for_param_exists:
        default = param.default

    elif default_value_for_field_exists:
        default = field_info.default

    elif param_is_optional:
        default = None

    default_is_none = default is None

    if default_value_for_field_exists and not default_is_none and param_is_optional:
        raise SpecifyBothDefaultAndOptionalError(
            class_name=field_info.__class__.__name__,
            handler=handler,
            param_name=param.name,
        )

    if default_factory_for_field_exists and param_is_optional:
        raise SpecifyBothDefaultFactoryAndOptionalError(
            class_name=field_info.__class__.__name__,
            handler=handler,
            param_name=param.name,
        )

    return default


def _get_default_definition_attr_default(
        handler: Handler,
        type_: Any,
        param: inspect.Parameter,
        field_info: ParamFieldInfo,
) -> Any:
    default_value_for_field_exists = check_default_value_for_field_exists(field_info)
    default_factory_for_field_exists = check_default_factory_for_field_exists(field_info)

    can_default = field_info.can_default

    param_is_optional = is_optional(type_)
    default_is_none = field_info.default is None

    if field_info.default is not Undefined and not can_default:
        raise ParameterCannotUseDefaultError(
            class_name=field_info.__class__.__name__,
            handler=handler,
            param_name=param.name,
        )

    if field_info.default_factory is not None and not can_default:
        raise ParameterCannotUseDefaultFactoryError(
            class_name=field_info.__class__.__name__,
            handler=handler,
            param_name=param.name,
        )

    if default_value_for_field_exists and not default_is_none and param_is_optional:
        raise SpecifyBothDefaultAndOptionalError(
            class_name=field_info.__class__.__name__,
            handler=handler,
            param_name=param.name,
        )

    if default_factory_for_field_exists and param_is_optional:
        raise SpecifyBothDefaultFactoryAndOptionalError(
            class_name=field_info.__class__.__name__,
            handler=handler,
            param_name=param.name,
        )

    if param_is_optional:
        return None

    return field_info.default


def _raise_if_unsupported_union_schema_data_type(
        union_attributes: Sequence[Any],
        *,
        handler: Handler,
        param_name: str,
) -> None:
    if not (len(union_attributes) == 2 and type(None) in union_attributes):  # noqa: WPS516
        raise UnsupportedSchemaDataTypeError(
            err_msg='Schema annotated type must be a pydantic.BaseModel or dataclasses.dataclass.',
            handler=handler,
            param_name=param_name,
        )


def _raise_if_unsupported_annotation_type(
        annotation: Any,
        *,
        handler: Handler,
        param_name: str,
) -> None:
    try:
        is_subclass_of_base_model = issubclass(annotation, BaseModel)
    except TypeError as type_error_exc:
        raise UnsupportedSchemaDataTypeError(
            err_msg='Unsupported data type for schema.',
            handler=handler,
            param_name=param_name,
        ) from type_error_exc

    if not (is_subclass_of_base_model or is_dataclass(annotation)):
        raise UnsupportedSchemaDataTypeError(
            err_msg='Schema annotated type must be a pydantic.BaseModel or dataclasses.dataclass.',
            handler=handler,
            param_name=param_name,
        )


def extract_handler_attr_annotations(
        *,
        handler: Handler,
        param: inspect.Parameter,
) -> AnnotationData:
    annotation_data = _get_annotation_data(handler, param)

    if annotation_data.param_field_info.validate_type.is_complex_param():
        checked_annotation_type = annotation_data.type_

        if get_origin(annotation_data.type_) is Union:
            union_attributes = get_args(annotation_data.type_)

            _raise_if_unsupported_union_schema_data_type(union_attributes, handler=handler, param_name=param.name)

            checked_annotation_type = union_attributes[1] if union_attributes[0] == type(None) else union_attributes[0]

        _raise_if_unsupported_annotation_type(checked_annotation_type, handler=handler, param_name=param.name)

    return annotation_data



# TODO: может объединить в один, просто дефолт кидать? или выставлять его просто выше в FieldInfo
def create_model_field_by_annotated_flow(
        param: inspect.Parameter,
        param_type: Any,
        param_field_info: ParamFieldInfo,
        handler: Handler,
) -> ModelField:
    default = _get_annotated_definition_attr_default(  # TODO: апдейтить дефолт тут?
        handler=handler,
        type_=param_type,
        field_info=param_field_info,
        param=param,
    )

    param_field_info.default = default

    return create_field(
        name=param.name,
        type_=param_type,
        field_info=param_field_info,
    )


def create_model_field_by_handler_signature_param(handler: Handler, param: inspect.Parameter) -> ModelField:
    annotation_origin = get_origin(param.annotation)

    if annotation_origin is Annotated:
        annotated_args = get_args(param.annotation)
        if len(annotated_args) != 2:
            raise NotParameterError

        type_, param_field_info = annotated_args
        prepared_param_field_info = _prepare_field_info(param_field_info)
        default = _get_annotated_definition_attr_default(
            param=param, handler=handler, type_=type_, field_info=prepared_param_field_info,
        )

    else:
        if param.default is inspect.Signature.empty:
            raise NotParameterError

        type_, param_field_info = param.annotation, param.default
        prepared_param_field_info = _prepare_field_info(param_field_info)
        default = _get_default_definition_attr_default(
            param=param, handler=handler, type_=param.annotation, field_info=prepared_param_field_info,
        )

    if not isinstance(prepared_param_field_info, ParamFieldInfo):
        raise Exception  # TODO

    prepared_param_field_info.default = default

    # TODO: ModelField будет создан и только под извлекающиеся -> похуй это для единообразия
    #  просто не будем дергать метод валидации, чисто дефолт достанем

    # TODO: некоторые типы данных не будут поддержаны пидантиком -> что с ними делать?

    # TODO: нужен ли метод create_param_model_field_by_request_param - или это костыль FastApi
    return create_param_model_field_by_request_param(
        annotated_type=type_,
        field_info=prepared_param_field_info,
        param_name=param.name,
        param_default=prepared_param_field_info.default,
        param_default_factory=prepared_param_field_info.default_factory,
    )

    # return create_field(
    #     name=param.name,
    #     type_=type_,
    #     field_info=prepared_param_field_info,
    # )

def is_optional(field):  # TODO: type
    if not get_origin(field) is Union:
        return False

    return type(None) in get_args(field)


def check_default_value_for_field_exists(field_info: ParamFieldInfo) -> bool:
    return not (field_info.default is Undefined or field_info.default is Required)

def check_default_factory_for_field_exists(field_info: ParamFieldInfo) -> bool:
    return field_info.default_factory is not None
