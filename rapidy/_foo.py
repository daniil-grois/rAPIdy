from typing import Any, Union, get_origin, get_args


def annotation_is_optional(annotation: Any) -> bool:
    if not get_origin(annotation) is Union:
        return False

    return type(None) in get_args(annotation)
