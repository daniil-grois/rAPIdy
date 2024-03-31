from rapidy import web
from tutorial_01.views import routes


def create_app() -> web.Application:
    app = web.Application()
    app.add_routes(routes)
    return app
