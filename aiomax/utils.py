from inspect import signature
from typing import Callable, Literal

import aiohttp

from aiomax.types import Attachment

from . import buttons, exceptions


def get_message_body(
    text: "str | None" = None,
    format: "Literal['markdown', 'html'] | None" = None,
    reply_to: "int | None" = None,
    notify: bool = True,
    keyboard: """list[list[buttons.Button]] \
        | buttons.KeyboardBuilder \
        | None""" = None,
    attachments: "list[Attachment] | Attachment | None" = None,
) -> dict:
    """
    Returns the body of the message as json.
    """
    body = {"text": text, "format": format, "notify": notify}

    # replying
    if reply_to:
        body["link"] = {"type": "reply", "mid": reply_to}

    # keyboard
    if keyboard:
        if isinstance(keyboard, buttons.KeyboardBuilder):
            keyboard = keyboard.to_list()

        body["attachments"] = [
            {
                "type": "inline_keyboard",
                "payload": {
                    "buttons": [
                        [
                            i.to_json() if isinstance(i, buttons.Button) else i
                            for i in row
                        ]
                        for row in keyboard
                    ]
                },
            }
        ]

    if attachments:
        if "attachments" not in body:
            body["attachments"] = []

        if not isinstance(attachments, list):
            attachments = [attachments]

        for at in attachments or []:
            if not hasattr(at, "as_dict"):
                raise exceptions.AiomaxException(
                    "This attachmentcannot be sent"
                )
            body["attachments"].append(at.as_dict())

    if attachments == [] and "attachments" not in body:
        body["attachments"] = []

    return body


def context_kwargs(func: Callable, **kwargs):
    """
    Returns only those kwargs, that callable accepts
    """
    params = list(signature(func).parameters.keys())

    kwargs = {kw: arg for kw, arg in kwargs.items() if kw in params}

    return kwargs


async def get_exception(response: aiohttp.ClientResponse):
    if response.status in range(200, 300):
        return None

    if response.content_type == "text/plain":
        text = await response.text()
        description = None

    elif response.content_type == "application/json":
        resp_json = await response.json()
        text = resp_json.get("code")
        description = resp_json.get("message")

    else:
        return Exception(f"Unknown error: {await response.read()}")

    if text.startswith("Invalid access_token"):
        return exceptions.InvalidToken()

    if (
        text == "attachment.not.ready"
        or description == "Key: errors.process.attachment.video.not.processed"
    ):
        return exceptions.AttachmentNotReady()

    if text == "chat.not.found":
        return exceptions.ChatNotFound(description)

    if description == "text: size must be between 0 and 4000":
        return exceptions.IncorrectTextLength()

    if text == "internal.error":
        if description:
            return exceptions.InternalError(description.split()[-1])
        return exceptions.InternalError()

    if text == "access.denied":
        return exceptions.AccessDeniedException(description)

    if text == "not.found":
        return exceptions.NotFoundException(description)

    return exceptions.UnknownErrorException(text, description)
