from abc import ABC
from typing import Any


class RapidyException(Exception, ABC):
    border = '\n' + '-' * 30 + '\n'
    message: str

    def __init__(self, message: str) -> None:
        super().__init__(self._wrap_message(message))

    @classmethod
    def create_with_handler_info(cls, handler: Any) -> 'RapidyException':
        new_message = cls.message + '\n' + cls._create_handler_info_msg(handler)
        return cls(new_message)

    @classmethod
    def create_with_handler_and_attr_info(cls, handler: Any, attr_name: str) -> 'RapidyException':
        new_message = cls.message + '\n' + cls._create_handler_attr_info_msg(handler, attr_name)
        return cls(new_message)

    @staticmethod
    def _wrap_message(message: str) -> str:
        return RapidyException.border + message + RapidyException.border

    @staticmethod
    def _create_handler_info_msg(handler: Any) -> str:
        return (
            f'\nHandler path: `{handler.__code__.co_filename}`'
            f'\nHandler name: `{handler.__name__}`'
        )

    @staticmethod
    def _create_handler_attr_info_msg(handler: Any, attr_name: str) -> str:
        return (
            f'{RapidyException._create_handler_info_msg(handler)}'
            '\n'
            f'Attribute name: `{attr_name}`'
        )
