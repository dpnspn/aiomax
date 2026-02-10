from aiomax.enums import HTTPMethod


async def test_get_calls_request(bot):
    resp = await bot.get("https://example.com/path", params={"a": 1})

    assert bot.session.last_call["method"] == HTTPMethod.GET
    assert bot.session.last_call["args"][0] == "https://example.com/path"
    assert bot.session.last_call["params"] == {"a": 1}
    assert resp is not None


async def test_post_calls_request(bot):
    data = {"x": "y"}
    resp = await bot.post("https://example.com/post", json=data)

    assert bot.session.last_call["method"] == HTTPMethod.POST
    assert bot.session.last_call["args"][0] == "https://example.com/post"
    assert bot.session.last_call["kwargs"]["json"] == data
    assert resp is not None


async def test_patch_calls_request(bot):
    resp = await bot.patch("https://example.com/patch")

    assert bot.session.last_call["method"] == HTTPMethod.PATCH
    assert bot.session.last_call["args"][0] == "https://example.com/patch"
    assert resp is not None


async def test_put_calls_request(bot):
    resp = await bot.put("https://example.com/put", params={"p": 2})

    assert bot.session.last_call["method"] == HTTPMethod.PUT
    assert bot.session.last_call["args"][0] == "https://example.com/put"
    assert bot.session.last_call["params"] == {"p": 2}
    assert resp is not None


async def test_delete_calls_request(bot):
    resp = await bot.delete("https://example.com/delete")

    assert bot.session.last_call["method"] == HTTPMethod.DELETE
    assert bot.session.last_call["args"][0] == "https://example.com/delete"
    assert resp is not None

