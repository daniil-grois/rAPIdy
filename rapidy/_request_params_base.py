from enum import Enum


class ValidateType(str, Enum):
    no_validate = 'no_validate'
    complex_param = 'complex_param'
    single_param = 'single_param'

    def is_no_validate(self) -> bool:
        return self == self.no_validate

    def is_complex_param(self) -> bool:
        return self == self.complex_param

    def is_single_param(self) -> bool:
        return self == self.single_param


class ParamType(str, Enum):
    path = 'path'
    query = 'query'
    header = 'header'
    cookie = 'cookie'
    body = 'body'
