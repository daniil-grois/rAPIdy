import inspect
from copy import deepcopy
from typing import Any, cast, Type, Union

from rapidy._client_errors import _create_handler_attr_info_msg
from rapidy._foo import annotation_is_optional
from rapidy.request_params import ParamFieldInfo
from rapidy.typedefs import Handler, Required, Undefined


# TODO: ошибки на рапидовские вывести
#  ошибки должны содержать ссылку на доку
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


class ParameterCannotBeOptionalError(TypeError):
    _base_err_msg = 'A parameter `{class_name}` cannot be optional.'

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
        raise ParameterCannotBeOptionalError(
            class_name=field_info.__class__.__name__,
            handler=handler,
            param_name=param.name,
        )

    if default_exists and not can_default:
        raise ParameterCannotUseDefaultError(
            class_name=field_info.__class__.__name__,
            handler=handler,
            param_name=param.name,
        )

    if default_factory_exists and not can_default:
        raise ParameterCannotUseDefaultFactoryError(
            class_name=field_info.__class__.__name__,
            handler=handler,
            param_name=param.name,
        )

    # NOTE: описать что для некоторых сценариев раньше отшибет пидантик
    if default_exists and default_factory_exists:
        raise SpecifyBothDefaultAndDefaultFactoryError(
            class_name=field_info.__class__.__name__,
            handler=handler,
            param_name=param.name,
        )

    if default_exists and not default_is_none and param_is_optional:
        raise SpecifyBothDefaultAndOptionalError(
            class_name=field_info.__class__.__name__,
            handler=handler,
            param_name=param.name,
        )

    if default_factory_exists and param_is_optional:
        raise SpecifyBothDefaultFactoryAndOptionalError(
            class_name=field_info.__class__.__name__,
            handler=handler,
            param_name=param.name,
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
        raise IncorrectDefineDefaultValueError(
            class_name=field_info.__class__.__name__,
            handler=handler,
            param_name=param.name,
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
