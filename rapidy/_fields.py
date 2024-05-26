from abc import ABC
from typing import Any, Dict, Optional, Tuple, Type, TYPE_CHECKING, Union

from pydantic import ValidationError
from pydantic.fields import FieldInfo as FieldInfo
from typing_extensions import Annotated

from rapidy._client_errors import _regenerate_error_with_loc
from rapidy._request_params_base import HTTPRequestParamType
from rapidy.constants import PYDANTIC_V1, PYDANTIC_V2
from rapidy.exceptions import RapidyException
from rapidy.typedefs import NoArgAnyCallable, Required, Undefined, ValidateReturn


class ParameterCannotHaveValidateAttrAsTrueError(RapidyException):
    _base_err_msg = 'Handler attribute with Type `{class_name}` cannot have `validate` value as `True`.'

    def __init__(self, *args: Any, class_name: str) -> None:
        super().__init__(f'{self._base_err_msg.format(class_name=class_name)}', *args)


class ParameterCannotHaveExtractAllAttrAsFalseError(RapidyException):
    _base_err_msg = 'Handler attribute with Type `{class_name}` cannot have `extract_all` value as `False`.'

    def __init__(self, *args: Any, class_name: str) -> None:
        super().__init__(f'{self._base_err_msg.format(class_name=class_name)}', *args)


class ParamFieldInfo(FieldInfo, ABC):
    http_request_param_type: HTTPRequestParamType
    extractor: Any
    can_default: bool = True
    only_raw: bool = False

    def __init__(
            self,
            default: Any = Undefined,
            *,
            default_factory: Optional[NoArgAnyCallable] = None,
            validate: Optional[bool] = None,
            extract_all: Optional[bool] = None,
            **field_info_kwargs: Any,
    ) -> None:
        FieldInfo.__init__(
            self,
            default=default,
            default_factory=default_factory,
            **field_info_kwargs,
        )
        if PYDANTIC_V1:
            self._validate()  # check specify both default and default_factory

        need_validate = validate is not None and validate == True

        if self.only_raw:
            if need_validate:
                raise ParameterCannotHaveValidateAttrAsTrueError(class_name=self.__class__.__name__)
            if extract_all is False:
                raise ParameterCannotHaveExtractAllAttrAsFalseError(class_name=self.__class__.__name__)

            self.validate = False
            self.extract_all = True
        else:
            self.validate = validate if validate is not None else True
            self.extract_all = extract_all if extract_all is not None else False


if PYDANTIC_V1:  # noqa: C901
    from pydantic import BaseConfig  # noqa: WPS433
    from pydantic.class_validators import Validator as Validator  # noqa: WPS433
    from pydantic.fields import ModelField as PydanticModelField  # noqa: WPS433
    from pydantic.schema import get_annotation_from_field_info  # noqa: WPS433

    if TYPE_CHECKING:  # pragma: no cover
        from pydantic.fields import BoolUndefined

    class ModelField(PydanticModelField):
        def __init__(
                self,
                name: str,
                type_: Type[Any],
                class_validators: Optional[Dict[str, Validator]],
                model_config: Type[BaseConfig],
                default: Any = None,
                default_factory: Optional[NoArgAnyCallable] = None,
                required: 'BoolUndefined' = Undefined,
                final: bool = False,
                alias: Optional[str] = None,
                field_info: Optional[FieldInfo] = None,
                **kw: Any,
        ) -> None:
            super().__init__(
                name=name,
                type_=type_,
                class_validators=class_validators,
                model_config=model_config,
                default=default,
                default_factory=default_factory,
                required=required,
                final=final,
                alias=alias,
                field_info=field_info,
            )
            http_request_param_type: Optional[HTTPRequestParamType] = kw.pop('http_request_param_type', None)
            if http_request_param_type:
                self.http_request_param_type = http_request_param_type

    def create_field(
            name: str,
            type_: Type[Any],
            field_info: ParamFieldInfo,
    ) -> ModelField:
        required = field_info.default in (Required, Undefined) and field_info.default_factory is None

        kwargs: Dict[str, Any] = {
            'name': name,
            'field_info': field_info,
            'type_': type_,
            'http_request_param_type': field_info.http_request_param_type,
            'required': required,
            'alias': field_info.alias or name,
            'default': field_info.default,
            'default_factory': field_info.default_factory,
            'class_validators': {},
            'model_config': BaseConfig,
        }
        try:
            return ModelField(**kwargs)
        except Exception:
            raise Exception(
                'Invalid args for annotated request field! '
                f'Hint: check that {type_} is a valid Pydantic field type. ',
            ) from None

elif PYDANTIC_V2:
    from dataclasses import dataclass  # noqa: WPS433

    from pydantic import TypeAdapter  # noqa: WPS433

    def get_annotation_from_field_info(annotation: Any, field_info: FieldInfo, field_name: str) -> Any:  # noqa: WPS440
        return annotation

    @dataclass
    class ModelField:  # type: ignore[no-redef]  # noqa: WPS440
        name: str
        field_info: FieldInfo
        http_request_param_type: HTTPRequestParamType

        @property
        def alias(self) -> str:
            alias = self.field_info.alias
            return alias if alias is not None else self.name

        @property
        def required(self) -> bool:
            return self.field_info.is_required()

        @property
        def default(self) -> Any:
            if self.field_info.is_required():
                return Undefined
            return self.field_info.get_default(call_default_factory=True)

        def get_default(self) -> Any:
            return self.field_info.get_default(call_default_factory=True)

        @property
        def type_(self) -> Any:
            return self.field_info.annotation

        def __post_init__(self) -> None:
            self._type_adapter: TypeAdapter[Any] = TypeAdapter(Annotated[self.field_info.annotation, self.field_info])

        def validate(
            self,
            value: Any,
            values: Dict[str, Any] = {},  # noqa: B006 WPS404
            *,
            loc: Tuple[Union[int, str], ...],
        ) -> ValidateReturn:
            try:
                return (
                    self._type_adapter.validate_python(value, from_attributes=True),
                    None,
                )
            except ValidationError as exc:
                return None, _regenerate_error_with_loc(
                    errors=exc.errors(),
                    loc_prefix=loc,
                )

    def create_field(  # noqa: WPS440
            name: str,
            type_: Type[Any],
            field_info: ParamFieldInfo,
    ) -> ModelField:
        field_info.annotation = type_
        return ModelField(  # type: ignore[call-arg]
            name=name,
            field_info=field_info,
            http_request_param_type=field_info.http_request_param_type,
        )
