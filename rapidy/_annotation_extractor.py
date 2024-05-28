import inspect
from copy import deepcopy
from typing import Annotated, Any, cast, get_args, get_origin, Type, Union

from rapidy._base_exceptions import RapidyException
from rapidy.request_params import ParamFieldInfo
from rapidy.typedefs import Handler, Required, Undefined


class NotParameterError(Exception):
    pass


class ParameterCannotUseDefaultError(RapidyException):
    message = 'Handler attribute with Type `{class_name}` cannot have a default value.'


class ParameterCannotUseDefaultFactoryError(RapidyException):
    message = 'Handler attribute with Type `{class_name}` cannot have a default_factory.'


class SpecifyBothDefaultAndDefaultFactoryError(RapidyException):
    message = 'Cannot specify both default and default_factory in `{class_name}`.'


class ParameterCannotBeOptionalError(RapidyException):
    message = 'A parameter `{class_name}` cannot be optional.'


class SpecifyBothDefaultAndOptionalError(RapidyException):
    message = 'A parameter cannot be optional if it contains a default value in `{class_name}`.'


class SpecifyBothDefaultFactoryAndOptionalError(RapidyException):
    message = 'A parameter cannot be optional if it contains a default factory in `{class_name}`.'


class IncorrectDefineDefaultValueError(RapidyException):
    message = (
        'Default value cannot be set in `{class_name}`. '
        'You cannot specify a default value using Param(<default_value>, ...) and `=` at the same time.'
    )


def prepare_field_info(raw_field_info: Union[ParamFieldInfo, Type[ParamFieldInfo]]) -> ParamFieldInfo:
    if not isinstance(raw_field_info, ParamFieldInfo):
        if isinstance(raw_field_info, type) and issubclass(raw_field_info, ParamFieldInfo):
            raw_field_info = raw_field_info()
        else:
            raise NotParameterError

    prepared_field_info = deepcopy(raw_field_info)
    return cast(ParamFieldInfo, prepared_field_info)


def check_possibility_of_default(
        can_default: bool,
        default_exists: bool,
        default_is_none: bool,
        default_factory_exists: bool,
        param_is_optional: bool,
        handler: Handler,
        param: inspect.Parameter,
        field_info: ParamFieldInfo,
) -> None:
    if not can_default and param_is_optional:
        raise ParameterCannotBeOptionalError.create_with_handler_and_attr_info(
            handler=handler,
            attr_name=param.name,
            class_name=field_info.__class__.__name__,
        )

    if default_exists and not can_default:
        raise ParameterCannotUseDefaultError.create_with_handler_and_attr_info(
            handler=handler,
            attr_name=param.name,
            class_name=field_info.__class__.__name__,
        )

    if default_factory_exists and not can_default:
        raise ParameterCannotUseDefaultFactoryError.create_with_handler_and_attr_info(
            handler=handler,
            attr_name=param.name,
            class_name=field_info.__class__.__name__,
        )

    # NOTE: This error is caused earlier by `pydantic` for some scenarios.
    if default_exists and default_factory_exists:
        raise SpecifyBothDefaultAndDefaultFactoryError.create_with_handler_and_attr_info(
            handler=handler,
            attr_name=param.name,
            class_name=field_info.__class__.__name__,
        )

    if default_exists and not default_is_none and param_is_optional:
        raise SpecifyBothDefaultAndOptionalError.create_with_handler_and_attr_info(
            handler=handler,
            attr_name=param.name,
            class_name=field_info.__class__.__name__,
        )

    if default_factory_exists and param_is_optional:
        raise SpecifyBothDefaultFactoryAndOptionalError.create_with_handler_and_attr_info(
            handler=handler,
            attr_name=param.name,
            class_name=field_info.__class__.__name__,
        )


def get_annotated_definition_attr_default(
        param: inspect.Parameter,
        handler: Handler,
        type_: Any,
        field_info: ParamFieldInfo,
) -> Any:
    default_value_for_param_exists = param.default is not inspect.Signature.empty
    default_value_for_field_exists = check_default_value_for_field_exists(field_info)

    param_is_optional = annotation_is_optional(type_)

    default = inspect.Signature.empty

    if default_value_for_param_exists:
        default = param.default

    elif default_value_for_field_exists:
        default = field_info.default

    elif param_is_optional:
        default = None

    check_possibility_of_default(
        can_default=field_info.can_default,
        default_exists=default_value_for_param_exists or default_value_for_field_exists,
        default_is_none=default is None,
        default_factory_exists=field_info.default_factory is not None,
        param_is_optional=param_is_optional,
        handler=handler,
        param=param,
        field_info=field_info,
    )

    if default_value_for_param_exists and default_value_for_field_exists:
        raise IncorrectDefineDefaultValueError.create_with_handler_and_attr_info(
            handler=handler,
            attr_name=param.name,
            class_name=field_info.__class__.__name__,
        )

    return default


def get_default_definition_attr_default(
        handler: Handler,
        type_: Any,
        param: inspect.Parameter,
        field_info: ParamFieldInfo,
) -> Any:
    param_is_optional = annotation_is_optional(type_)

    check_possibility_of_default(
        can_default=field_info.can_default,
        default_exists=check_default_value_for_field_exists(field_info),
        default_is_none=field_info.default is None,
        default_factory_exists=field_info.default_factory is not None,
        param_is_optional=param_is_optional,
        handler=handler,
        param=param,
        field_info=field_info,
    )

    if param_is_optional:
        return None

    return field_info.default


def check_default_value_for_field_exists(field_info: ParamFieldInfo) -> bool:
    return not (field_info.default is Undefined or field_info.default is Required)


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

    if not isinstance(prepared_param_field_info, ParamFieldInfo):  # pragma: no cover
        raise

    prepared_param_field_info.annotation = type_
    prepared_param_field_info.default = default

    return prepared_param_field_info


def annotation_is_optional(annotation: Any) -> bool:
    if not get_origin(annotation) is Union:
        return False

    return type(None) in get_args(annotation)
