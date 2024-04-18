from rapidy._version import AIOHTTP_VERSION_TUPLE

if AIOHTTP_VERSION_TUPLE >= (3, 9, 0):
    from aiohttp.web_exceptions import HTTPMove, NotAppKeyWarning

from aiohttp.typedefs import LooseHeaders
from aiohttp.web_exceptions import (
    HTTPAccepted,
    HTTPBadGateway,
    HTTPBadRequest,
    HTTPClientError,
    HTTPConflict,
    HTTPCreated,
    HTTPError,
    HTTPException,
    HTTPExpectationFailed,
    HTTPFailedDependency,
    HTTPForbidden,
    HTTPFound,
    HTTPGatewayTimeout,
    HTTPGone,
    HTTPInsufficientStorage,
    HTTPInternalServerError,
    HTTPLengthRequired,
    HTTPMethodNotAllowed,
    HTTPMisdirectedRequest,
    HTTPMovedPermanently,
    HTTPMultipleChoices,
    HTTPNetworkAuthenticationRequired,
    HTTPNoContent,
    HTTPNonAuthoritativeInformation,
    HTTPNotAcceptable,
    HTTPNotExtended,
    HTTPNotFound,
    HTTPNotImplemented,
    HTTPNotModified,
    HTTPOk,
    HTTPPartialContent,
    HTTPPaymentRequired,
    HTTPPermanentRedirect,
    HTTPPreconditionFailed,
    HTTPPreconditionRequired,
    HTTPProxyAuthenticationRequired,
    HTTPRedirection,
    HTTPRequestEntityTooLarge,
    HTTPRequestHeaderFieldsTooLarge,
    HTTPRequestRangeNotSatisfiable,
    HTTPRequestTimeout,
    HTTPRequestURITooLong,
    HTTPResetContent,
    HTTPSeeOther,
    HTTPServerError,
    HTTPServiceUnavailable,
    HTTPSuccessful,
    HTTPTemporaryRedirect,
    HTTPTooManyRequests,
    HTTPUnauthorized,
    HTTPUnavailableForLegalReasons,
    HTTPUnprocessableEntity,
    HTTPUnsupportedMediaType,
    HTTPUpgradeRequired,
    HTTPUseProxy,
    HTTPVariantAlsoNegotiates,
    HTTPVersionNotSupported,
)

__all = [
    'HTTPException',
    'HTTPError',
    'HTTPRedirection',
    'HTTPSuccessful',
    'HTTPOk',
    'HTTPCreated',
    'HTTPAccepted',
    'HTTPNonAuthoritativeInformation',
    'HTTPNoContent',
    'HTTPResetContent',
    'HTTPPartialContent',
    'HTTPMove',
    'HTTPMultipleChoices',
    'HTTPMovedPermanently',
    'HTTPFound',
    'HTTPSeeOther',
    'HTTPNotModified',
    'HTTPUseProxy',
    'HTTPTemporaryRedirect',
    'HTTPPermanentRedirect',
    'HTTPClientError',
    'HTTPBadRequest',
    'HTTPUnauthorized',
    'HTTPPaymentRequired',
    'HTTPForbidden',
    'HTTPNotFound',
    'HTTPMethodNotAllowed',
    'HTTPNotAcceptable',
    'HTTPProxyAuthenticationRequired',
    'HTTPRequestTimeout',
    'HTTPConflict',
    'HTTPGone',
    'HTTPLengthRequired',
    'HTTPPreconditionFailed',
    'HTTPRequestEntityTooLarge',
    'HTTPRequestURITooLong',
    'HTTPUnsupportedMediaType',
    'HTTPRequestRangeNotSatisfiable',
    'HTTPExpectationFailed',
    'HTTPMisdirectedRequest',
    'HTTPUnprocessableEntity',
    'HTTPFailedDependency',
    'HTTPUpgradeRequired',
    'HTTPPreconditionRequired',
    'HTTPTooManyRequests',
    'HTTPRequestHeaderFieldsTooLarge',
    'HTTPUnavailableForLegalReasons',
    'HTTPServerError',
    'HTTPInternalServerError',
    'HTTPNotImplemented',
    'HTTPBadGateway',
    'HTTPServiceUnavailable',
    'HTTPGatewayTimeout',
    'HTTPVersionNotSupported',
    'HTTPVariantAlsoNegotiates',
    'HTTPInsufficientStorage',
    'HTTPNotExtended',
    'HTTPNetworkAuthenticationRequired',
    'NotAppKeyWarning',
]

if AIOHTTP_VERSION_TUPLE >= (3, 9, 0):
    __all.extend([
        'HTTPMove',
        'NotAppKeyWarning',
    ])

__all__ = tuple(__all)
