import pytest

from aiomax.enums import HTTPMethod


async def test_authorization_header_added(bot):
    await bot.get("https://platform-api.max.ru/me")
    assert bot.session.last_call is not None
    assert "Authorization" in bot.session.last_call["headers"]
    assert bot.session.last_call["headers"]["Authorization"] == bot.access_token
    assert bot.session.last_call["method"] == HTTPMethod.GET


async def test_authorization_header_preserved(bot, faker):
    custom = faker.pystr(min_chars=10, max_chars=30)
    await bot.get("https://platform-api.max.ru/me", headers={"Authorization": custom})
    assert bot.session.last_call["headers"]["Authorization"] == custom


async def test_method_passed_for_post(bot):
    await bot.post("https://platform-api.max.ru/messages", json={"x": 1})
    assert bot.session.last_call["method"] == HTTPMethod.POST


async def test_default_params_and_headers(bot):
    await bot.get("https://platform-api.max.ru/empty")
    assert bot.session.last_call["params"] == {}
    assert "Authorization" in bot.session.last_call["headers"]


async def test_kwargs_passthrough_to_session(bot):
    await bot.post("https://platform-api.max.ru/messages", json={"x": 1}, timeout=5)
    assert bot.session.last_call["kwargs"]["json"] == {"x": 1}
    assert bot.session.last_call["kwargs"]["timeout"] == 5


async def test_returns_response_on_success(bot):
    resp = await bot.get("https://platform-api.max.ru/me")
    assert resp is not None
    assert hasattr(resp, "json")


async def test_raises_on_invalid_token_response(bot):
    class ErrorResponse:
        def __init__(self):
            self.status = 401
            self.content_type = "text/plain"

        async def json(self):
            return {"code": "Invalid access_token"}

        async def text(self):
            return "Invalid access_token: something"

        async def read(self):
            return b""

    class ErrorSession:
        def __init__(self):
            self.last_call = None

        async def request(self, method, *args, params=None, headers=None, **kwargs):
            self.last_call = {"method": method, "args": args, "params": params, "headers": headers or {}, "kwargs": kwargs}
            return ErrorResponse()

    bot.session = ErrorSession()

    with pytest.raises(Exception):
        await bot.get("https://platform-api.max.ru/me")


async def test_session_not_initialized_raises(bot):
    bot.session = None
    with pytest.raises(Exception, match="Session is not initialized"):
        await bot.get("https://platform-api.max.ru/me")


async def test_params_and_headers_not_in_kwargs(bot):
    await bot.post(
        "https://platform-api.max.ru/messages",
        params={"p": "v"},
        headers={"X-Test": "1"},
        json={"x": 1},
        timeout=3,
    )

    assert bot.session.last_call["params"] == {"p": "v"}
    assert "X-Test" in bot.session.last_call["headers"]
    assert "params" not in bot.session.last_call["kwargs"]
    assert "headers" not in bot.session.last_call["kwargs"]


async def test_explicit_empty_headers_adds_authorization(bot):
    await bot.get("https://platform-api.max.ru/empty-headers", headers={})
    assert "Authorization" in bot.session.last_call["headers"]
    assert bot.session.last_call["headers"]["Authorization"] == bot.access_token


async def test_authorization_empty_value_preserved(bot):
    await bot.get("https://platform-api.max.ru/empty-auth", headers={"Authorization": ""})

    assert "Authorization" in bot.session.last_call["headers"]
    assert bot.session.last_call["headers"]["Authorization"] == ""


async def test_session_request_exception_propagates(bot):
    class RaisingSession:
        async def request(self, *args, **kwargs):
            raise RuntimeError("network failure")

    bot.session = RaisingSession()
    with pytest.raises(RuntimeError, match="network failure"):
        await bot.get("https://platform-api.max.ru/me")
