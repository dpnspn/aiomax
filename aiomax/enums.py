from enum import StrEnum


class HTTPMethod(StrEnum):
    """HTTP methods and descriptions

    Methods from the following RFCs are all observed:

        * RFC 7231: Hypertext Transfer Protocol (HTTP/1.1), obsoletes 2616
        * RFC 5789: PATCH Method for HTTP
    """

    CONNECT = 'CONNECT'
    DELETE = 'DELETE'
    GET = 'GET'
    HEAD = 'HEAD'
    OPTIONS = 'OPTIONS'
    PATCH = 'PATCH'
    POST = 'POST'
    PUT = 'PUT'
    TRACE = 'TRACE'
