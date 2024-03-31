from typing_extensions import Annotated
from rapidy import web
from rapidy.request_params import Path, JsonBody

routes = web.RouteTableDef()


@routes.post('/')
async def create_user(
    request: web.Request,
    username: Annotated[str, JsonBody],
    password: Annotated[str, JsonBody],
    repeat_password: Annotated[str, JsonBody],
) -> web.Response:
    if username and password == repeat_password:
        return web.json_response({'result': 'success'}, status=201)

    return web.json_response({'result': 'passwords dont match'}, status=422)


@routes.get('/{user_id}')
async def get_user(
    request: web.Request,
    user_id: Annotated[str, Path],
) -> web.Response:
    return web.json_response({'user_id': user_id})


@routes.put('/{user_id}')
async def update_username(
    request: web.Request,
    new_username: Annotated[str, JsonBody],
) -> web.Response:
    return web.json_response({'new_username': new_username})
