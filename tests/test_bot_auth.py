import pytest

from aiomax.enums import HTTPMethod
from aiomax import exceptions


async def test_request_sends_authorization_header_by_default(bot):
    """When no headers are passed, Bot._request should send the bot's
    configured Authorization header stored in the session's default headers.
    """
    resp = await bot._request(HTTPMethod.GET, "https://example.com")

    # ensure session.request was called with the method and headers
    assert bot.session.last_call["method"] == HTTPMethod.GET
    assert (
        bot.session.last_call["headers"]["Authorization"] == bot.access_token
    )
    # response should be returned as-is when there's no error
    assert resp is not None


async def test_request_uses_custom_headers(bot):
    """When headers are passed explicitly, they should be forwarded to the
    underlying session request and not replaced by the session's defaults.
    """
    custom_headers = {"Authorization": "custom-token", "X-Test": "1"}

    resp = await bot._request(
        HTTPMethod.POST, "https://example.com", headers=custom_headers
    )

    assert bot.session.last_call["method"] == HTTPMethod.POST
    assert bot.session.last_call["headers"] == custom_headers
    assert resp is not None


async def test_request_raises_on_invalid_token():
    """If the API returns an error indicating an invalid token, the helper
    should raise the appropriate exception (InvalidToken).
    """

    class BadResponse:
        def __init__(self):
            self.status = 401
            self.content_type = "application/json"

        async def json(self):
            # utils.get_exception expects a JSON object with `code` and `message`.
            return {"code": "Invalid access_token: token_expired", "message": None}

        async def text(self):
            return "Invalid access_token: token_expired"

        async def read(self):
            return b""


    class BadSession:
        def __init__(self):
            self.last_call = None

        async def request(self, method, *args, params=None, headers=None, **kwargs):
            self.last_call = {"method": method, "args": args, "params": params, "headers": headers, "kwargs": kwargs}
            return BadResponse()


    # create a fresh Bot instance and attach the BadSession
    from aiomax.bot import Bot

    b = Bot("some-token")
    b.session = BadSession()

    with pytest.raises(exceptions.InvalidToken):
        await b._request(HTTPMethod.GET, "https://example.com")


# --- New tests to improve coverage for Bot._request ---

async def test_request_raises_when_session_not_initialized():
    """If the bot hasn't initialized a session, _request should raise."""
    from aiomax.bot import Bot

    b = Bot("token")
    b.session = None

    with pytest.raises(Exception) as exc:
        await b._request(HTTPMethod.GET, "https://example.com")

    assert str(exc.value) == "Session is not initialized"


async def test_request_forwards_params_and_kwargs(bot):
    """Ensure params and arbitrary kwargs (like json) are forwarded to session.request."""
    params = {"count": 1}
    payload = {"foo": "bar"}

    resp = await bot._request(
        HTTPMethod.PUT, "https://example.com/resource", params=params, json=payload
    )

    assert bot.session.last_call["method"] == HTTPMethod.PUT
    assert bot.session.last_call["params"] == params
    assert bot.session.last_call["kwargs"]["json"] == payload
    assert resp is not None


async def test_request_raises_on_access_denied():
    """When API returns access.denied code, _request should raise AccessDeniedException."""

    class DeniedResponse:
        def __init__(self):
            self.status = 403
            self.content_type = "application/json"

        async def json(self):
            return {"code": "access.denied", "message": "Not allowed"}

        async def text(self):
            return "access.denied"

        async def read(self):
            return b""


    class DeniedSession:
        def __init__(self):
            self.last_call = None

        async def request(self, method, *args, params=None, headers=None, **kwargs):
            self.last_call = {"method": method, "args": args, "params": params, "headers": headers, "kwargs": kwargs}
            return DeniedResponse()


    from aiomax.bot import Bot

    b = Bot("token")
    b.session = DeniedSession()

    with pytest.raises(exceptions.AccessDeniedException):
        await b._request(HTTPMethod.DELETE, "https://example.com")

