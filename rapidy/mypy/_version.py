from mypy.version import __version__ as mypy_version

from rapidy._version import parse_version

MYPY_VERSION_TUPLE = parse_version(mypy_version)
