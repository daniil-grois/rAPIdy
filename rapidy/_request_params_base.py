from enum import Enum


class HTTPRequestParamType(str, Enum):
    path = 'path'
    query = 'query'
    header = 'header'
    cookie = 'cookie'
    body = 'body'
