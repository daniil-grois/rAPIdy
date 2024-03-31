from typing import Annotated

from pydantic import BaseModel, Field

from rapidy import web
from rapidy.request_params import Cookie, Path, CookieSchema, HeaderSchema, Header

routes = web.RouteTableDef()


@routes.get('/')
async def handler(
        host1: Annotated[str, Header(alias='Host')],
        host2: str = Header(alias='Host'),
) -> web.Response:
    return web.json_response({'data': 'success'})

app = web.Application()
app.add_routes(routes)

if __name__ == '__main__':
    web.run_app(app, host='127.0.0.1', port=8080)
