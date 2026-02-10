import aiohttp


def test_init_session_creates_client_session(monkeypatch):
    """_init_session should create an aiohttp.ClientSession with Authorization header when session is None."""
    from aiomax.bot import Bot

    class DummyClientSession:
        def __init__(self, *, headers=None):
            # emulate aiohttp.ClientSession API enough for the test
            self.headers = headers or {}

        async def close(self):
            pass

    # replace aiohttp.ClientSession with our dummy
    monkeypatch.setattr(aiohttp, "ClientSession", DummyClientSession)

    token = "sometoken"
    b = Bot(token)

    # ensure session starts as None
    assert b.session is None

    b._init_session()

    # after init, session should be instance of DummyClientSession
    assert isinstance(b.session, DummyClientSession)
    assert b.session.headers.get("Authorization") == token


def test_init_session_does_not_overwrite_existing_session(monkeypatch):
    """If session already set, _init_session should not call ClientSession again or overwrite it."""
    from aiomax.bot import Bot

    class ExplodingClientSession:
        def __init__(self, *args, **kwargs):
            raise RuntimeError("Should not be called")

    monkeypatch.setattr(aiohttp, "ClientSession", ExplodingClientSession)

    b = Bot("token")
    # set an existing session
    existing_session = object()
    b.session = existing_session

    # should not raise
    b._init_session()

    assert not isinstance(b.session, ExplodingClientSession)
    assert b.session is existing_session

