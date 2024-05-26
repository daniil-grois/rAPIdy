from enum import Enum


class HTTPRequestParamType(str, Enum):  # TODO: вынести в др место?
    path = 'path'
    query = 'query'
    header = 'header'
    cookie = 'cookie'
    body = 'body'
