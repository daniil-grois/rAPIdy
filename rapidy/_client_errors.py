from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple, Type, Union

from pydantic import BaseModel, create_model

from rapidy.constants import PYDANTIC_V1, PYDANTIC_V2
from rapidy.typedefs import ErrorWrapper, ValidationErrorList

RequestErrorModel: Type[BaseModel] = create_model('Request')


class ClientBaseError(ABC, ValueError):
    type: str
    msg_template: str

    def __init__(self, *_: Any, **error_ctx: Any) -> None:
        self._err_msg = self.msg_template.format(**error_ctx)

    @abstractmethod
    def get_error_info(
            self,
            loc: Tuple[str, ...],
    ) -> Dict[str, Any]:  # pragma: no cover
        raise NotImplementedError


if PYDANTIC_V1:
    from pydantic.error_wrappers import ValidationError

    class ClientError(ClientBaseError, ABC):
        def get_error_info(
                self,
                loc: Tuple[str, ...],
        ) -> Dict[str, Any]:
            return {
                'loc': loc,
                'msg': self._err_msg,
                'type': self.type,
            }

    class RequiredFieldIsMissing(ClientError):
        type = 'value_error.missing'
        msg_template = 'field required'

    def _regenerate_error_with_loc(
            *,
            errors: List[Any],
            loc_prefix: Tuple[Union[str, int], ...],
    ) -> List[Dict[str, Any]]:
        return [
            {**err, 'loc': loc_prefix + err.get('loc', ())}
            for err in _normalize_errors(errors)
        ]

    def _normalize_errors(errors: List[Any]) -> List[Dict[str, Any]]:
        use_errors: List[Dict[str, Any]] = []
        for error in errors:
            if isinstance(error, ErrorWrapper):
                new_errors = ValidationError(errors=[error], model=RequestErrorModel).errors()
                use_errors.extend(new_errors)
            elif isinstance(error, list):
                use_errors.extend(_normalize_errors(error))
            else:
                use_errors.append(error)
        return use_errors

elif PYDANTIC_V2:
    from pydantic import ValidationError
    from pydantic_core import InitErrorDetails, PydanticCustomError

    class ClientError(ClientBaseError, ABC):  # type: ignore[no-redef]
        def get_error_info(
                self,
                loc: Tuple[str, ...],
        ) -> Dict[str, Any]:
            err = PydanticCustomError(self.type, self._err_msg)
            err_details = InitErrorDetails(type=err, loc=loc, input=input)
            return ValidationError.from_exception_data(
                title='',
                line_errors=[err_details],
                hide_input=True,
            ).errors()[0]

    class RequiredFieldIsMissing(ClientError):  # type: ignore[no-redef]
        type = 'missing'
        msg_template = 'Field required'

    def _regenerate_error_with_loc(
            *,
            errors: List[Any],
            loc_prefix: Tuple[Union[str, int], ...],
    ) -> List[Dict[str, Any]]:
        return [
            {**err, 'loc': loc_prefix + err.get('loc', ())}
            for err in errors
        ]

    def _normalize_errors(errors: List[Any]) -> ValidationErrorList:
        for error in errors:  # FIXME: ...
            error.pop('url', None)
            error.pop('input', None)
        return errors

else:
    raise Exception


class ExtractError(ClientError, ABC):
    pass


class ExtractBodyError(ExtractError, ABC):
    type = 'body_extraction'


class BodyDataSizeExceedError(ExtractBodyError):
    msg_template = 'Failed to extract body data. Body data exceeds the allowed size `{body_max_size}`'


class ExtractJsonError(ExtractBodyError):
    msg_template = 'Failed to extract body data as Json: {json_decode_err_msg}'


class ExtractMultipartError(ExtractBodyError):
    msg_template = 'Failed to extract body data as Multipart: {multipart_error}'


class ExtractMultipartPartError(ExtractMultipartError):
    msg_template = 'Failed to extract body data as Multipart. Failed to read part `{part_num}`: {multipart_error}'


# TODO:...
def _create_handler_info_msg(handler: Any) -> str:
    return (
        f'\nHandler path: `{handler.__code__.co_filename}`'
        f'\nHandler name: `{handler.__name__}`\n'
    )


def _create_handler_attr_info_msg(handler: Any, attr_name: str) -> str:
    return (
        f'{_create_handler_info_msg(handler)}'
        f'Attribute name: `{attr_name}`\n'
    )
