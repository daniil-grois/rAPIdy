from functools import partial, wraps
from typing import Any, cast, Dict, List, Type, TYPE_CHECKING

from rapidy import hdrs
from rapidy._annotation_container import AnnotationContainer, create_annotation_container
from rapidy._client_errors import _normalize_errors
from rapidy.typedefs import Handler, HandlerType, MethodHandler, Middleware
from rapidy.web_exceptions import HTTPValidationFailure
from rapidy.web_middlewares import middleware as middleware_deco
from rapidy.web_response import StreamResponse

if TYPE_CHECKING:
    from rapidy.web_request import Request
    from rapidy.web_urldispatcher import View


async def validate_request(
        request: 'Request',
        annotation_container: AnnotationContainer,
        errors_response_field_name: str,
) -> Dict[str, Any]:
    values: Dict[str, Any] = {}
    errors: List[Dict[str, Any]] = []

    for param_container in annotation_container:
        param_values, param_errors = await param_container.get_request_data(request)
        if param_errors:
            errors += param_errors
        else:
            values.update(cast(Dict[str, Any], param_values))

    if errors:
        raise HTTPValidationFailure(
            validation_failure_field_name=errors_response_field_name,
            errors=_normalize_errors(errors),
        )

    return values


def handler_validation_wrapper(handler: Handler) -> Handler:
    annotation_container = create_annotation_container(handler, is_func_handler=True)

    @wraps(handler)
    async def inner(request: 'Request') -> StreamResponse:
        validated_data = await validate_request(
            request=request,
            annotation_container=annotation_container,
            errors_response_field_name=request._cache['errors_response_field_name'],  # FIXME
        )

        if annotation_container.request_exists:
            validated_data[annotation_container.request_param_name] = request

        return await handler(**validated_data)

    return inner


def view_validation_wrapper(view: Type['View']) -> 'View':
    annotation_containers = {}

    for method in (  # noqa: WPS335 WPS352
        handler_attr
        for handler_attr in dir(view)
        if handler_attr.upper() in hdrs.METH_ALL
    ):
        method_handler: MethodHandler = getattr(view, method)
        annotation_containers[method.lower()] = create_annotation_container(method_handler)

    @wraps(view)
    async def inner(request: 'Request') -> StreamResponse:
        instance_view = view(request)
        method_name = request.method.lower()

        try:
            annotation_container = annotation_containers[method_name]
        except KeyError:
            instance_view._raise_allowed_methods()
            raise  # for linters only

        try:
            method = getattr(instance_view, method_name)  # noqa: WPS442
        except AttributeError:
            instance_view._raise_allowed_methods()
            raise  # for linters only

        validated_data = await validate_request(
            request=request,
            annotation_container=annotation_container,
            errors_response_field_name=request._cache['errors_response_field_name'],  # FIXME
        )

        setattr(instance_view, method_name, partial(method, **validated_data))

        return await instance_view

    return inner


def middleware_validation_wrapper(middleware: Middleware) -> Middleware:
    annotation_container = create_annotation_container(middleware)

    @middleware_deco
    async def inner(request: 'Request', handler: HandlerType) -> StreamResponse:
        validated_data = await validate_request(
            request=request,
            annotation_container=annotation_container,
            errors_response_field_name=request._cache['errors_response_field_name'],  # FIXME
        )
        return await middleware(request, handler, **validated_data)

    return inner
