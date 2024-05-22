from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple, Type, TYPE_CHECKING, Union

from aiohttp.abc import AbstractView, Request
from aiohttp.typedefs import (
    Byteish,
    DEFAULT_JSON_DECODER,
    DEFAULT_JSON_ENCODER,
    JSONDecoder,
    JSONEncoder,
    LooseCookies,
    LooseCookiesIterables,
    LooseCookiesMappings,
    LooseHeaders,
    PathLike,
    RawHeaders,
    StrOrURL,
)
from typing_extensions import TypeAlias

from rapidy.constants import PYDANTIC_V1, PYDANTIC_V2

if TYPE_CHECKING:
    from rapidy.web_response import StreamResponse

__all__ = (
    'Byteish',
    'DEFAULT_JSON_DECODER',
    'DEFAULT_JSON_ENCODER',
    'JSONEncoder',
    'JSONDecoder',
    'LooseHeaders',
    'RawHeaders',
    'StrOrURL',
    'LooseCookiesMappings',
    'LooseCookiesIterables',
    'LooseCookies',
    'Middleware',
    'Handler',
    'PathLike',
    'DictStrAny',
    'DictStrStr',
    'DictStrListAny',
    'DictStrListStr',
    'MethodHandler',
    'HandlerType',
    'HandlerOrMethod',
)

DictStrAny = Dict[str, Any]
DictStrStr = Dict[str, str]
DictStrListAny = Dict[str, List[Any]]
DictStrListStr = Dict[str, List[str]]

Handler = Callable[..., Awaitable['StreamResponse']]
MethodHandler = Callable[..., Awaitable['StreamResponse']]
HandlerType = Union[Handler, Type[AbstractView]]
Middleware = Callable[[Request, Handler], Awaitable['StreamResponse']]  # TODO: ...

HandlerOrMethod = Union[Handler, MethodHandler]

ResultValidate: TypeAlias = Dict[str, Any]
ValidationErrorList: TypeAlias = List[Dict[str, Any]]
ValidateReturn: TypeAlias = Tuple[Optional[ResultValidate], Optional[ValidationErrorList]]

RouterDeco = Callable[[HandlerType], HandlerType]

NoArgAnyCallable = Callable[[], Any]

if PYDANTIC_V1:
    from pydantic.error_wrappers import ErrorWrapper as ErrorWrapper
    from pydantic.fields import (
        Required as Required,
        Undefined as Undefined,
        UndefinedType as UndefinedType,
        Validator as Validator,
    )

elif PYDANTIC_V2:
    from pydantic_core import PydanticUndefined, PydanticUndefinedType

    Required = PydanticUndefined
    Undefined = PydanticUndefined
    UndefinedType = PydanticUndefinedType
    Validator = Any  # type: ignore[assignment,unused-ignore]

    class ErrorWrapper(Exception):  # type: ignore[no-redef]  # noqa: N818 WPS440
        pass

else:
    raise Exception
