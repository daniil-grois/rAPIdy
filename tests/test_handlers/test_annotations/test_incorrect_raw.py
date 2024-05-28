import pytest

from rapidy._fields import (
    ParameterCannotHaveExtractAllAttrAsFalseError,
    ParameterCannotHaveValidateAttrAsTrueError,
    ParamFieldInfo,
)
from rapidy.request_params import BytesBody, StreamBody, TextBody

ONLY_RAW_EXTRACT_PARAMS = (BytesBody, TextBody, StreamBody)


@pytest.mark.parametrize('type_', ONLY_RAW_EXTRACT_PARAMS)
async def test_only_raw_param_cannot_have_validate_attr_as_true(type_: ParamFieldInfo) -> None:
    with pytest.raises(ParameterCannotHaveValidateAttrAsTrueError):
        type_(validate=True)


@pytest.mark.parametrize('type_', ONLY_RAW_EXTRACT_PARAMS)
async def test_only_raw_param_cannot_have_extract_all_attr_as_false(type_: ParamFieldInfo) -> None:
    with pytest.raises(ParameterCannotHaveExtractAllAttrAsFalseError):
        type_(extract_all=False)
