from rapidy import web

from tutorial_01.app import create_app

if __name__ == '__main__':
    web.run_app(create_app(), port=8080)
