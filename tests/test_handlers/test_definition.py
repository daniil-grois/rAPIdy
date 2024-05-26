# from http import HTTPStatus
# from typing import Any, Dict
#
# import pytest
# from aiohttp.web_routedef import RouteTableDef
# from pydantic import BaseModel
# from pytest import param
# from pytest_aiohttp.plugin import AiohttpClient
# from typing_extensions import Annotated
#
# from rapidy import web
# from rapidy.request_params import (
#     Cookie,
#     FormDataBody,
#     Header,
#     JsonBody,
#     Query,
#     # TODO: miltipart
# )
# from rapidy.web import Application
#
#
# class Schema(BaseModel):
#     attr: str
#
#
# def _create_method_annotated_attr_def(type_: Any, param: Any, expected_data: Any) -> Any:
#     async def post(
#             attr: Annotated[type_, param],
#     ) -> web.Response:
#         assert attr == expected_data
#         return web.Response()
#
#     return post
#
#
# def _create_method_default_attr_def(type_: Any, param: Any, expected_data: Any) -> Any:
#     async def post(
#             attr: type_ = param,
#     ) -> web.Response:
#         assert attr == expected_data
#         return web.Response()
#
#     return post
#
#
# def _create_route_method_annotated_attr_def(type_: Any, param: Any, expected_data: Any, routes: Any) -> Any:
#     @routes.post('/')
#     async def post(
#             attr: Annotated[type_, param],
#     ) -> web.Response:
#         assert attr == expected_data
#         return web.Response()
#
#     return post
#
#
# def _create_route_method_default_attr_def(type_: Any, param: Any, expected_data: Any, routes: Any) -> Any:
#     @routes.post('/')
#     async def post(
#             attr: type_ = param,
#     ) -> web.Response:
#         assert attr == expected_data
#         return web.Response()
#
#     return post
#
#
# def _create_class_handler_as_annotated_def(type_: Any, param: Any, expected_data: Any) -> Any:
#     class Foo(web.View):
#         async def post(
#                 self,
#                 attr: Annotated[type_, param],
#         ) -> web.Response:
#             assert attr == expected_data
#             return web.Response()
#
#     return Foo
#
#
# def _create_class_handler_as_default_def(type_: Any, param: Any, expected_data: Any) -> Any:
#     class Foo(web.View):
#         async def post(
#                 self,
#                 attr: type_ = param,
#         ) -> web.Response:
#             assert attr == expected_data
#             return web.Response()
#
#     return Foo
#
#
# def _create_class_extended_handler_success(type_: Any, param: Any, expected_data: Any) -> Any:
#     class Foo(web.View):
#         def __init__(self, request: web.Request) -> None:
#             super().__init__(request)
#             self.foo = 'foo'
#
#         async def post(
#                 self,
#                 attr: type_ = param,
#         ) -> web.Response:
#             assert self.foo
#             assert attr == expected_data
#             return web.Response()
#
#     return Foo
#
#
# success_definition_test_parameters = [
#     param(str, Header, {'headers': {'attr': 'attr'}}, 'attr', id='header-param'),
#     param(str, Cookie, {'cookies': {'attr': 'attr'}}, 'attr', id='cookie-param'),
#     param(str, Query, {'params': {'attr': 'attr'}}, 'attr', id='query-param'),
#     param(str, JsonBody, {'json': {'attr': 'attr'}}, 'attr', id='body-json-param'),
#     param(str, FormDataBody, {'data': {'attr': 'attr'}}, 'attr', id='body-form-data-param'),
#     param(Schema, HeaderSchema, {'headers': {'attr': 'attr'}}, Schema(attr='attr'), id='header-schema'),
#     param(Schema, CookieSchema, {'cookies': {'attr': 'attr'}}, Schema(attr='attr'), id='cookie-schema'),
#     param(Schema, QuerySchema, {'params': {'attr': 'attr'}}, Schema(attr='attr'), id='query-schema'),
#     param(Schema, JsonBodySchema, {'json': {'attr': 'attr'}}, Schema(attr='attr'), id='body-json-schema'),
#     param(Schema, FormDataBodySchema, {'data': {'attr': 'attr'}}, Schema(attr='attr'), id='body-form-schema'),
#     param(Dict[str, Any], CookieRaw, {'cookies': {'attr': 'attr'}}, {'attr': 'attr'}, id='cookie-raw'),
#     param(Dict[str, Any], QueryRaw, {'params': {'attr': 'attr'}}, {'attr': 'attr'}, id='query-raw'),
#     param(Dict[str, Any], JsonBodyRaw, {'json': {'attr': 'attr'}}, {'attr': 'attr'}, id='body-json-raw'),
#     param(Dict[str, Any], FormDataBodyRaw, {'data': {'attr': 'attr'}}, {'attr': 'attr'}, id='body-form-data-raw'),
# ]
# create_method_parameters = [
#     param(_create_method_annotated_attr_def, id='attr-definition-as-annotated'),
#     param(_create_method_default_attr_def, id='attr-definition-as-default'),
# ]
# create_method_as_decorated_route_func_parameters = [
#     param(_create_route_method_annotated_attr_def, id='attr-definition-as-annotated'),
#     param(_create_route_method_annotated_attr_def, id='attr-definition-as-default'),
# ]
# create_view_parameters = [
#     param(_create_class_handler_as_annotated_def, id='attr-definition-as-annotated'),
#     param(_create_class_handler_as_default_def, id='attr-definition-as-default'),
#     param(_create_class_extended_handler_success, id='extended-view'),
# ]
#
#
# @pytest.mark.parametrize('type_, param, request_kw, expected_data', success_definition_test_parameters)
# @pytest.mark.parametrize('handler_creation_func', create_method_parameters)
# async def test_success_func_def(
#         aiohttp_client: AiohttpClient,
#         type_: Any,
#         param: Any,
#         request_kw: Dict[str, Any],
#         expected_data: Any,
#         handler_creation_func: Any,
# ) -> None:
#     handler = handler_creation_func(type_=type_, param=param, expected_data=expected_data)
#
#     app = Application()
#     app.add_routes([web.post('/', handler)])
#
#     await _test(aiohttp_client, app, request_kw)
#
#
# @pytest.mark.parametrize('type_, param, request_kw, expected_data', success_definition_test_parameters)
# @pytest.mark.parametrize('handler_creation_func', create_method_as_decorated_route_func_parameters)
# async def test_success_func_def_with_routes_deco(
#         aiohttp_client: AiohttpClient,
#         type_: Any,
#         param: Any,
#         request_kw: Dict[str, Any],
#         expected_data: Any,
#         handler_creation_func: Any,
# ) -> None:
#     routes = RouteTableDef()
#
#     handler_creation_func(
#         type_=type_, param=param, expected_data=expected_data, routes=routes,
#     )
#
#     app = Application()
#     app.add_routes(routes)
#
#     await _test(aiohttp_client, app, request_kw)
#
#
# @pytest.mark.parametrize('type_, param, request_kw, expected_data', success_definition_test_parameters)
# @pytest.mark.parametrize('handler_creation_func', create_view_parameters)
# async def test_success_class_def_as_view(
#         aiohttp_client: AiohttpClient,
#         type_: Any,
#         param: Any,
#         request_kw: Dict[str, Any],
#         expected_data: Any,
#         handler_creation_func: Any,
# ) -> None:
#     handler = handler_creation_func(type_, param, expected_data)
#
#     app = Application()
#     app.add_routes([web.view('/', handler)])
#
#     await _test(aiohttp_client, app, request_kw)
#
#
# @pytest.mark.parametrize('type_, param, request_kw, expected_data', success_definition_test_parameters)
# @pytest.mark.parametrize('handler_creation_func', create_view_parameters)
# async def test_success_class_def_as_subapp(
#         aiohttp_client: AiohttpClient,
#         type_: Any,
#         param: Any,
#         request_kw: Dict[str, Any],
#         expected_data: Any,
#         handler_creation_func: Any,
# ) -> None:
#     handler = handler_creation_func(type_, param, expected_data)
#
#     app = Application()
#     app.add_routes([web.post('/', handler), web.put('/', handler)])
#
#     sup_app = Application()
#     sup_app.add_routes([web.post('/', handler), web.put('/', handler)])
#
#     app.add_subapp('/v1', sup_app)
#
#     await _test(aiohttp_client, app, request_kw)
#     await _test(aiohttp_client, app, request_kw, path='/v1/')
#
#
# async def _test(
#         aiohttp_client: AiohttpClient,
#         app: web.Application,
#         request_kw: Dict[str, Any],
#         path: str = '/',
# ) -> None:
#     client = await aiohttp_client(app)
#     resp = await client.post(path, **request_kw)
#
#     assert resp.status == HTTPStatus.OK
