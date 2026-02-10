import asyncio

import pytest
from faker import Faker
from aiomax.bot import Bot


@pytest.fixture
def faker():
    """Return a Faker instance for generating test data."""
    return Faker()


class DummyResponse:
    def __init__(self):
        self.status = 200
        self.content_type = "application/json"

    async def json(self):
        return {}

    async def text(self):
        return ""

    async def read(self):
        return b""


class DummySession:
    def __init__(self, headers):
        self.last_call = None
        self.default_headers = headers

    async def request(
        self,
        method,
        *args,
        params=None,
        headers=None,
        **kwargs,
    ):
        self.last_call = {
            "method": method,
            "args": args,
            "params": params,
            "headers": {**(self.default_headers or {}), **(headers or {})},
            "kwargs": kwargs,
        }
        await asyncio.sleep(0)
        return DummyResponse()


@pytest.fixture
def bot(faker):
    """Create a Bot with a Faker-generated token and attach a DummySession."""
    token = faker.pystr(min_chars=10, max_chars=30)
    b = Bot(token)
    b.session = DummySession(headers={"Authorization": token})
    return b
