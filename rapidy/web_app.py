import asyncio
import json
import logging
import warnings
from functools import partial, update_wrapper
from typing import Any, cast, Dict, Iterable, Iterator, List, Mapping, Optional, Tuple

from aiohttp.abc import AbstractMatchInfo
from aiohttp.log import web_logger
from aiohttp.web_app import Application as AiohttpApplication, CleanupError
from aiohttp.web_exceptions import HTTPUnprocessableEntity
from aiohttp.web_middlewares import _fix_request_current_app
from aiohttp.web_urldispatcher import MatchInfoError

from rapidy import hdrs
from rapidy._annotation_container import AnnotationContainer, create_annotation_container, HandlerEnumType
from rapidy._client_errors import _normalize_errors
from rapidy.constants import CLIENT_MAX_SIZE
from rapidy.media_types import ApplicationJSON
from rapidy.typedefs import Handler, Middleware
from rapidy.web_request import Request
from rapidy.web_response import StreamResponse

__all__ = (
    'Application',
    'CleanupError',
)

from rapidy.web_urldispatcher import UrlDispatcher


class Application(AiohttpApplication):
    def __init__(
            self,
            *,
            logger: logging.Logger = web_logger,
            router: Optional[UrlDispatcher] = None,
            middlewares: Iterable[Middleware] = (),
            handler_args: Optional[Mapping[str, Any]] = None,
            client_max_size: int = CLIENT_MAX_SIZE,
            client_errors_response_field_name: str = 'errors',
            loop: Optional[asyncio.AbstractEventLoop] = None,
            debug: Any = ...,
    ) -> None:
        # TODO: Add a check that in body extractors the size does not exceed the client size

        super().__init__(
            logger=logger,
            router=router,
            middlewares=middlewares,
            handler_args=handler_args,
            client_max_size=client_max_size,
            loop=loop,
            debug=debug,
        )

        # NOTE: override aiohttp router
        self._router = UrlDispatcher()

        self._client_errors_response_field_name = client_errors_response_field_name

        self._middleware_annotation_containers: Dict[int, AnnotationContainer] = {}

    def _add_middleware_annotation_container(self, middleware: Middleware) -> None:
        self._middleware_annotation_containers[id(middleware)] = create_annotation_container(
            middleware,
            handler_type=HandlerEnumType.middleware,
        )

    def _get_middleware_annotation_container(self, middleware: Middleware) -> Optional[AnnotationContainer]:
        return self._middleware_annotation_containers.get(id(middleware))

    def _prepare_middleware(self) -> Iterator[Tuple[Middleware, bool]]:  # FIXME: refactor
        for middleware in reversed(self._middlewares):
            if getattr(middleware, '__middleware_version__', None) == 1:
                self._add_middleware_annotation_container(middleware)
                yield middleware, True
            else:
                warnings.warn(
                    'rAPIdy does not support Old-style middleware - please use @middleware decorator.\n'
                    'If you are using middlewares with a nested middlewares wrapped by @middleware -\n'
                    'make sure that in Application(middlewares=[...]) you pass its instance.\n\n'
                    'Example:\n'
                    '>> app = Application(middlewares=[parametrized_middleware(<some_attr>=<some_value>)])',
                    DeprecationWarning,
                    stacklevel=2,
                )
                yield middleware, False

        yield _fix_request_current_app(self), True

    async def _handle(self, request: Request) -> StreamResponse:  # noqa: C901  # FIXME: refactor
        loop = asyncio.get_event_loop()
        debug = loop.get_debug()
        match_info = await self._router.resolve(request)
        if debug:  # pragma: no cover
            if not isinstance(match_info, AbstractMatchInfo):
                raise TypeError(
                    'match_info should be AbstractMatchInfo '
                    'instance, not {!r}'.format(match_info),
                )
        match_info.add_app(self)

        match_info.freeze()

        resp = None
        request._match_info = match_info
        expect = request.headers.get(hdrs.EXPECT)
        if expect:  # aiohttp code  # pragma: no cover
            resp = await match_info.expect_handler(request)
            await request.writer.drain()

        if resp is None:
            handler = match_info.handler

            if isinstance(match_info, MatchInfoError):
                return await handler(request)

            annotation_container = match_info.route.get_method_container(request.method)

            if self._run_middlewares:
                async def w_handler(request: Request) -> StreamResponse:  # noqa: WPS442
                    return await self._get_handler_response(request, handler, annotation_container)

                for app in match_info.apps[::-1]:
                    for middleware, new_style in app._middlewares_handlers:
                        if new_style:
                            validated_request_data_for_middleware = await self._validate_request_for_middleware(
                                app=app, request=request, middleware=middleware,
                            )
                            w_handler = update_wrapper(
                                partial(middleware, handler=w_handler, **validated_request_data_for_middleware),
                                w_handler,
                            )
                        else:
                            w_handler = await middleware(app, w_handler)

                resp = await w_handler(request)

            else:
                return await self._get_handler_response(request, handler, annotation_container)

        return resp

    async def _get_handler_response(
            self,
            request: Request,
            handler: Handler,
            annotation_container: AnnotationContainer,
    ) -> StreamResponse:
        validate_request_data_for_handler = await self._validate_request_for_handler(
            request=request,
            annotation_container=annotation_container,
        )

        if annotation_container.is_method_container:
            return await handler(request, **validate_request_data_for_handler)

        if annotation_container.request_exist:
            validate_request_data_for_handler[annotation_container.request_param_name] = request

        return await handler(**validate_request_data_for_handler)

    async def _validate_request_for_handler(
            self,
            request: Request,
            annotation_container: AnnotationContainer,
    ) -> Dict[str, Any]:
        return await self._validate_request(annotation_container=annotation_container, request=request)

    async def _validate_request_for_middleware(
            self,
            app: 'Application',
            request: Request,
            middleware: Middleware,
    ) -> Dict[str, Any]:
        annotation_container = app._get_middleware_annotation_container(middleware)
        if annotation_container:
            return await self._validate_request(annotation_container=annotation_container, request=request)

        return {}

    async def _validate_request(
            self,
            annotation_container: AnnotationContainer,
            request: Request,
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
            response_errors = {self._client_errors_response_field_name: _normalize_errors(errors)}
            response_errors_body = json.dumps(response_errors)

            raise HTTPUnprocessableEntity(content_type=ApplicationJSON, text=response_errors_body)

        return values
