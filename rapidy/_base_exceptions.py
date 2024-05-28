from abc import ABC
from typing import Any, Optional


class RapidyException(Exception, ABC):
    border = '\n' + '-' * 30 + '\n'
    message: str
    # TODO: doc link

    def __init__(self, message: Optional[str] = None, **format_fields: str) -> None:
        message = message if message is not None else self.__class__.message

        if format_fields:
            message = message.format(**format_fields)

        super().__init__(self._wrap_message(message))

    @classmethod
    def create_with_handler_info(
            cls,
            handler: Any,
            **format_fields: str,
    ) -> 'RapidyException':
        new_message = cls.message + '\n' + cls._create_handler_info_msg(handler)
        return cls(new_message, **format_fields)

    @classmethod
    def create_with_handler_and_attr_info(
            cls,
            handler: Any,
            attr_name: str,
            **format_fields: str,
    ) -> 'RapidyException':
        new_message = cls.message + '\n' + cls._create_handler_attr_info_msg(handler, attr_name)
        return cls(new_message, **format_fields)

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
            f'\nAttribute name: `{attr_name}`'
        )
