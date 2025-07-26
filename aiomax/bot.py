import asyncio
import logging
import os
from collections.abc import AsyncIterator
from typing import IO, BinaryIO, Literal

import aiofiles
import aiohttp

from . import buttons, exceptions, fsm, utils
from .cache import MessageCache
from .router import Router
from .types import (
    Attachment,
    AudioAttachment,
    BotCommand,
    BotStartPayload,
    Callback,
    Chat,
    ChatCreatePayload,
    ChatMembershipPayload,
    ChatTitleEditPayload,
    CommandContext,
    FileAttachment,
    ImageRequestPayload,
    Message,
    MessageDeletePayload,
    PhotoAttachment,
    User,
    UserMembershipPayload,
    VideoAttachment,
)

bot_logger = logging.getLogger("aiomax.bot")


class Bot(Router):
    def __init__(
        self,
        access_token: str,
        command_prefixes: "str | list[str]" = "/",
        mention_prefix: bool = True,
        case_sensitive: bool = True,
        default_format: "Literal['markdown', 'html'] | None" = None,
        max_messages_cached: int = 10000,
    ):
        """
        Bot init

        :param access_token: Bot access token from https://max.ru/masterbot
        :param command_prefixes: List of command prefixes or a command prefix
        :param mention_prefix: Whether to respond to commands starting with
        the ping of the bot
        :param case_sensitive: If False the bot will respond to commands
        regardless of case
        :param default_format: Default message formatting mode
        :param max_messages_cached: Maximum number of messages to cache.
        Set to 0 to disable caching
        """
        super().__init__(case_sensitive)

        self.access_token: str = access_token
        self.session = None
        self.polling = False

        self.command_prefixes: str | list[str] = command_prefixes
        self.mention_prefix: bool = mention_prefix
        self.default_format: str | None = default_format
        self.cache: MessageCache | None = (
            MessageCache(max_messages_cached)
            if max_messages_cached > 0
            else None
        )

        self.id: int | None = None
        self.username: str | None = None
        self.name: str | None = None
        self.description: str | None = None
        self.bot_commands: list[BotCommand] = None

        self.marker: int | None = None

        self.storage = fsm.FSMStorage()

    async def get(self, *args, **kwargs):
        """
        Sends a GET request to the API.
        """
        if self.session is None:
            raise Exception("Session is not initialized")

        params = kwargs.get("params", {})
        params["access_token"] = self.access_token
        if "params" in kwargs:
            del kwargs["params"]

        response = await self.session.get(*args, params=params, **kwargs)

        exception = await utils.get_exception(response)

        if not exception:
            return response
        raise exception

    async def post(self, *args, **kwargs):
        """
        Sends a POST request to the API.
        """
        if self.session is None:
            raise Exception("Session is not initialized")

        params = kwargs.get("params", {})
        params["access_token"] = self.access_token
        if "params" in kwargs:
            del kwargs["params"]

        response = await self.session.post(*args, params=params, **kwargs)

        exception = await utils.get_exception(response)

        if not exception:
            return response
        raise exception

    async def patch(self, *args, **kwargs):
        """
        Sends a PATCH request to the API.
        """
        if self.session is None:
            raise Exception("Session is not initialized")

        params = kwargs.get("params", {})
        params["access_token"] = self.access_token
        if "params" in kwargs:
            del kwargs["params"]

        response = await self.session.patch(*args, params=params, **kwargs)

        exception = await utils.get_exception(response)

        if not exception:
            return response
        raise exception

    async def put(self, *args, **kwargs):
        """
        Sends a PUT request to the API.
        """
        if self.session is None:
            raise Exception("Session is not initialized")

        params = kwargs.get("params", {})
        params["access_token"] = self.access_token
        if "params" in kwargs:
            del kwargs["params"]

        response = await self.session.put(*args, params=params, **kwargs)

        exception = await utils.get_exception(response)

        if not exception:
            return response
        raise exception

    async def delete(self, *args, **kwargs):
        """
        Sends a DELETE request to the API.
        """
        if self.session is None:
            raise Exception("Session is not initialized")

        params = kwargs.get("params", {})
        params["access_token"] = self.access_token
        if "params" in kwargs:
            del kwargs["params"]

        response = await self.session.delete(*args, params=params, **kwargs)

        exception = await utils.get_exception(response)

        if not exception:
            return response
        raise exception

    # send requests

    async def get_me(self) -> User:
        """
        Returns info about the bot.
        """
        response = await self.get("https://botapi.max.ru/me")
        user = await response.json()
        user = User.from_json(user)

        # caching info
        self.id = user.user_id
        self.username = user.username
        self.name = user.name
        self.bot_commands = user.commands
        self.description = user.description
        return user

    async def patch_me(
        self,
        name: "str | None" = None,
        description: "str | None" = None,
        commands: "list[BotCommand] | None" = None,
        photo: "ImageRequestPayload | None" = None,
    ) -> User:
        """
        Allows you to change info about the bot. Fill in only the fields that
        need to be updated.

        :param name: Bot display name
        :param description: Bot description
        :param commands: Commands supported by the bot. To remove all commands,
        pass an empty list.
        :param photo: Bot profile pictur
        """
        if commands:
            commands = [i.as_dict() for i in commands]
        if photo:
            photo = photo.as_dict()

        payload = {
            "name": name,
            "description": description,
            "commands": commands,
            "photo": photo,
        }
        payload = {k: v for k, v in payload.items() if v}

        response = await self.patch("https://botapi.max.ru/me", json=payload)
        data = await response.json()

        # caching info
        if name:
            self.name = name
        if commands:
            self.bot_commands = commands
        if description:
            self.description = description

        return User.from_json(data)

    async def get_chats(
        self, count_per_iter: int = 100
    ) -> AsyncIterator[Chat]:
        """
        Returns an asynchronous interator of chats the bot is in.

        :param count_per_iter: The number of chats to fetch per request.
        """
        marker = None

        while True:
            params = {
                "count": count_per_iter,
                "marker": marker,
            }
            params = {k: v for k, v in params.items() if v}
            response = await self.get(
                "https://botapi.max.ru/chats", params=params
            )
            data = await response.json()

            for chat in data["chats"]:
                yield Chat.from_json(chat)

            marker = data.get("marker", None)
            if marker is None:
                break

    async def chat_by_link(self, link: str) -> Chat:
        """
        Returns chat by a link or username.

        :param link: Public chat link or username.
        """
        response = await self.get(f"https://botapi.max.ru/chats/{link}")
        json = await response.json()

        return Chat.from_json(json)

    async def get_chat(self, chat_id: int) -> Chat:
        """
        Returns information about a chat.

        :param chat_id: The ID of the chat.
        """
        response = await self.get(f"https://botapi.max.ru/chats/{chat_id}")
        json = await response.json()

        return Chat.from_json(json)

    async def get_pin(self, chat_id: int) -> "Message | None":
        """
        Returns pinned message in the chat as ``. None if there is no pinned
        message

        :param chat_id: The ID of the chat.
        """
        response = await self.get(f"https://botapi.max.ru/chats/{chat_id}/pin")
        json = await response.json()

        if json["message"] is None:
            return None

        return Message.from_json(json)

    async def pin(
        self, chat_id: int, message_id: str, notify: "bool | None" = None
    ):
        """
        Pin a message in a chat

        :param chat_id: The ID of the chat.
        :param message_id: The ID of the message to pin.
        :param notify: Whether to notify users about the pin. True by default.
        """
        payload = {"message_id": message_id, "notify": notify}
        payload = {k: v for k, v in payload.items() if v}

        response = await self.put(
            f"https://botapi.max.ru/chats/{chat_id}/pin", json=payload
        )
        return await response.json()

    async def delete_pin(self, chat_id: int):
        """
        Delete pinned message in the chat

        :param chat_id: The ID of the chat.
        """
        response = await self.delete(
            f"https://botapi.max.ru/chats/{chat_id}/pin"
        )

        return await response.json()

    async def my_membership(self, chat_id: int) -> User:
        """
        Returns information about the bot's membership in the chat.

        :param chat_id: The ID of the chat.
        """
        response = await self.get(
            f"https://botapi.max.ru/chats/{chat_id}/members/me"
        )
        json = await response.json()

        return User.from_json(json)

    async def leave_chat(self, chat_id: int):
        """
        Remove the bot from the chat.

        :param chat_id: The ID of the chat.
        """
        response = await self.delete(
            f"https://botapi.max.ru/chats/{chat_id}/members/me"
        )

        return await response.json()

    async def get_admins(self, chat_id: int) -> list[User]:
        """
        Returns a list of administrators in the chat.

        :param chat_id: The ID of the chat.
        """
        response = await self.get(
            f"https://botapi.max.ru/chats/{chat_id}/members/admins"
        )

        users = [User.from_json(i) for i in (await response.json())["members"]]

        return users

    async def get_memberships(
        self, chat_id: int, user_ids: "list[int] | int"
    ) -> "list[User] | User | None":
        """
        Returns a list of memberships in the chat for the users with the
        specified ID.
        """
        params = {
            "user_ids": user_ids if isinstance(user_ids, list) else [user_ids]
        }
        response = await self.get(
            f"https://botapi.max.ru/chats/{chat_id}/members", params=params
        )

        users = [User.from_json(i) for i in (await response.json())["members"]]

        if isinstance(user_ids, list):
            return users
        else:
            return users[0] if len(users) > 0 else None

    async def get_members(
        self, chat_id: int, count_per_iter: int = 100
    ) -> AsyncIterator[User]:
        """
        Returns an asynchronous interator of members in the chat.

        :param chat_id: The ID of the chat.
        :param count_per_iter: The number of users to fetch per request.
        """
        marker = None

        while True:
            params = {
                "count": count_per_iter,
                "marker": marker,
            }
            params = {k: v for k, v in params.items() if v}
            response = await self.get(
                f"https://botapi.max.ru/chats/{chat_id}/members", params=params
            )
            data = await response.json()

            for user in data["members"]:
                yield User.from_json(user)

            marker = data.get("marker", None)
            if marker is None:
                break

    async def add_members(self, chat_id: int, users: list[int]):
        """
        Adds users to the chat.

        :param chat_id: The ID of the chat.
        :param users: List of user IDs to add.
        """

        response = await self.post(
            f"https://botapi.max.ru/chats/{chat_id}/members",
            json={"user_ids": users},
        )

        return await response.json()

    async def kick_member(
        self, chat_id: int, user_id: int, block: "bool | None" = None
    ):
        """
        Removes a user from the chat.

        :param chat_id: The ID of the chat.
        :param user_id: The ID of the user to remove.
        :param block: Whether to block the user. Ignored by default.
        """

        params = {"chat_id": chat_id, "user_id": user_id, "block": block}
        params = {k: v for k, v in params.items() if v}

        if block is not None:
            params["block"] = str(block)

        response = await self.delete(
            f"https://botapi.max.ru/chats/{chat_id}/members/", params=params
        )

        return await response.json()

    async def patch_chat(
        self,
        chat_id: int,
        icon: "ImageRequestPayload | None" = None,
        title: "str | None" = None,
        pin: "str | None" = None,
        notify: "bool | None" = None,
    ) -> Chat:
        """
        Allows you to edit chat information, like the name,
        icon and pinned message.

        :param chat_id: ID of the chat to change
        :param icon: Chat picture
        :param title: Chat name. From 1 to 200 characters
        :param pin: ID of the message to pin
        :param notify: Whether to notify users about the edit. True by default.
        """

        payload = {
            "icon": icon.as_dict() if icon else None,
            "title": title,
            "pin": pin,
            "notify": notify,
        }
        payload = {k: v for k, v in payload.items() if v}

        response = await self.patch(
            f"https://botapi.max.ru/chats/{chat_id}", json=payload
        )
        json = await response.json()

        return Chat.from_json(json)

    async def post_action(self, chat_id: int, action: str):
        """
        Allows you to show a badge about performing an action in a chat, like
        "typing". Also allows for marking messages as read.

        :param chat_id: ID of the chat to do the action in
        :param action: The action to perform
        """

        response = await self.post(
            f"https://botapi.max.ru/chats/{chat_id}/actions",
            json={"action": action},
        )

        return await response.json()

    async def _upload(
        self, data: "IO | str", type: str, field_name: str = "data"
    ) -> dict:
        """
        Uploads a file to the server. Returns raw JSON with the token.

        :param data: File-like object or path to the file
        :param type: File type
        :param field_name: Name of the form field sent to the API
        """
        if isinstance(data, str):
            async with aiofiles.open(data, "rb") as f:
                data = await f.read()

        form = aiohttp.FormData()
        form.add_field(field_name, data)

        url_resp = await self.post(
            "https://botapi.max.ru/uploads", params={"type": type}
        )
        url_json = await url_resp.json()
        token_resp = await self.session.post(url_json["url"], data=form)

        if type in {"audio", "video"}:
            return url_json

        token_json = await token_resp.json()
        return token_json

    async def upload_image(self, data: "BinaryIO | str") -> PhotoAttachment:
        """
        Uploads an image to the server and returns a PhotoAttachment.

        :param data: File-like object or path to the file
        """
        raw_photo = await self._upload(data, "image")
        token = list(raw_photo["photos"].values())[0]["token"]
        return PhotoAttachment(token=token)

    async def upload_video(self, data: "BinaryIO | str") -> VideoAttachment:
        """
        Uploads a video to the server and returns a VideoAttachment.

        :param data: File-like object or path to the file
        """
        raw_video = await self._upload(data, "video")
        token = raw_video["token"]
        return VideoAttachment(token=token)

    async def upload_audio(self, data: "BinaryIO | str") -> AudioAttachment:
        """
        Uploads an audio file to the server and returns an AudioAttachment.

        :param data: File-like object or path to the file
        """
        raw_audio = await self._upload(data, "audio")
        token = raw_audio["token"]
        return AudioAttachment(token=token)

    async def upload_file(
        self, data: "IO | str", filename: "str | None" = None
    ) -> FileAttachment:
        """
        Uploads a file to the server and returns a FileAttachment.

        :param data: File-like object or path to the file
        :param filename: Filename that will be uploaded
        """
        if filename is None:
            if isinstance(data, str):
                filename = os.path.basename(data)
            elif hasattr(data, "name"):
                filename = data.name
            else:
                raise exceptions.FilenameNotProvided(
                    "filename is required for use with "
                    f"object of type {type(data).__name__}"
                )

        raw_file = await self._upload(data, "file", filename)
        token = raw_file["token"]
        return FileAttachment(token=token)

    async def send_message(
        self,
        text: "str | None" = None,
        chat_id: "int | None" = None,
        user_id: "int | None" = None,
        format: "Literal['markdown', 'html', 'default'] | None" = "default",
        reply_to: "int | None" = None,
        notify: bool = True,
        disable_link_preview: bool = False,
        keyboard: """list[list[buttons.Button]] \
        | buttons.KeyboardBuilder \
        | None""" = None,
        attachments: "list[Attachment] | Attachment | None" = None,
    ) -> Message:
        """
        Allows you to send a message to a user or in a chat.

        :param text: Message text. Up to 4000 characters
        :param chat_id: Chat ID to send the message in.
        :param user_id: User ID to send the message to.
        :param format: Message format. Bot.default_format by default
        :param reply_to: ID of the message to reply to. Optional
        :param notify: Whether to notify users about the message.
            True by default.
        :param disable_link_preview: Whether to disable link embedding
            in messages. True by default
        :param keyboard: An inline keyboard to attach to the message
        :param attachments: List of attachments
        """
        # error checking
        if chat_id is None and user_id is None:
            raise exceptions.AiomaxException(
                "Either chat_id or user_id must be provided"
            )
        if not (chat_id is None or user_id is None):
            raise exceptions.AiomaxException(
                "Both chat_id and user_id cannot be provided"
            )

        # sending
        params = {
            "chat_id": chat_id,
            "user_id": user_id,
            "disable_link_preview": str(disable_link_preview).lower(),
        }
        params = {k: v for k, v in params.items() if v}

        if format == "default":
            format = self.default_format

        body = utils.get_message_body(
            text, format, reply_to, notify, keyboard, attachments
        )

        try:
            response = await self.post(
                "https://botapi.max.ru/messages", params=params, json=body
            )
            json = await response.json()
            if not json.get("success", True):
                raise await utils.get_exception(response)
            message = Message.from_json(json["message"])
            message.bot = self
            return message

        except exceptions.AttachmentNotReady:
            await asyncio.sleep(1)
            return await self.send_message(
                text=text,
                chat_id=chat_id,
                user_id=user_id,
                format=format,
                reply_to=reply_to,
                notify=notify,
                disable_link_preview=disable_link_preview,
                attachments=attachments,
            )

    async def edit_message(
        self,
        message_id: str,
        text: "str | None" = None,
        format: "Literal['markdown', 'html', 'default'] | None" = "default",
        reply_to: "int | None" = None,
        notify: bool = True,
        keyboard: """list[list[buttons.Button]] \
        | buttons.KeyboardBuilder \
        | None""" = None,
        attachments: "list[Attachment] | Attachment | None" = None,
    ) -> Message:
        """
        Allows you to edit a message.

        :param message_id: ID of the message to edit
        :param text: Message text. Up to 4000 characters
        :param format: Message format. Bot.default_format by default
        :param reply_to: ID of the message to reply to. Optional
        :param notify: Whether to notify users about the message.
            True by default.
        :param keyboard: An inline keyboard to attach to the message
        :param attachments: List of attachments
        """
        # editing
        params = {"message_id": message_id}
        if format == "default":
            format = self.default_format

        body = utils.get_message_body(
            text, format, reply_to, notify, keyboard, attachments
        )

        try:
            response = await self.put(
                "https://botapi.max.ru/messages", params=params, json=body
            )
            json = await response.json()
            if not json.get("success", True):
                raise await utils.get_exception(response)
            message = Message.from_json(json)
            message.bot = self
            return message

        except exceptions.AttachmentNotReady:
            await asyncio.sleep(1)
            return await self.edit_message(
                message_id=message_id,
                text=text,
                format=format,
                reply_to=reply_to,
                notify=notify,
                keyboard=keyboard,
                attachments=attachments,
            )

    async def delete_message(self, message_id: str):
        """
        Allows you to delete a message in chat.

        :param message_id: ID of the message to delete
        """
        # editing
        params = {"message_id": message_id}

        response = await self.delete(
            "https://botapi.max.ru/messages", params=params
        )

        json = await response.json()
        if not json["success"]:
            raise Exception(json["message"])

    async def get_message(self, message_id: str) -> Message:
        """
        Allows you to fetch message's info.

        :param message_id: ID of the message to get info of
        """
        try:
            response = await self.get(
                f"https://botapi.max.ru/messages/{message_id}"
            )

            data = await response.json()

            return Message.from_json(data)
        except exceptions.NotFoundException:
            raise exceptions.MessageNotFoundException from None

    async def get_updates(self, limit: int = 100) -> tuple[int, dict]:
        """
        Get bot updates / events.

        :param limit: Maximum amount of updates to return.
        """
        payload = {"limit": limit, "marker": self.marker}
        payload = {k: v for k, v in payload.items() if v}

        response = await self.get(
            "https://botapi.max.ru/updates", params=payload
        )
        json = await response.json()
        if "marker" in json:
            self.marker = json["marker"]

        return json

    async def handle_update(self, update: dict):
        """
        Handles an update.
        """
        update_type = update["update_type"]

        if update_type == "message_created":
            message = Message.from_json(update["message"])
            message.bot = self
            message.user_locale = update.get("user_locale")
            cursor = fsm.FSMCursor(self.storage, message.sender.user_id)

            # caching
            if self.cache:
                self.cache.add_message(message)

            # handling commands
            prefixes = (
                self.command_prefixes
                if not isinstance(self.command_prefixes, str)
                else [self.command_prefixes]
            )
            prefixes = list(prefixes)
            handled = False
            block = False

            if self.mention_prefix:
                prefixes.extend([f"@{self.username} {i}" for i in prefixes])

            for prefix in prefixes:
                if len(message.body.text) <= len(prefix):
                    continue

                if self.case_sensitive:
                    if not message.body.text.startswith(prefix):
                        continue
                else:
                    if not message.body.text.lower().startswith(
                        prefix.lower()
                    ):
                        continue

                command = message.body.text[len(prefix) :]
                name = command.split()[0]
                check_name = name if self.case_sensitive else name.lower()
                args = " ".join(command.split()[1:])

                if check_name not in self.commands:
                    bot_logger.debug(f'Command "{name}" not handled')
                    continue

                if len(self.commands[check_name]) == 0:
                    bot_logger.debug(f'Command "{name}" not handled')
                    continue

                for i in self.commands[check_name]:
                    kwargs = utils.context_kwargs(i.call, cursor=cursor)
                    asyncio.create_task(
                        i.call(
                            CommandContext(self, message, name, args), **kwargs
                        )
                    )

                    if not i.as_message:
                        block = True

                bot_logger.debug(f'Command "{name}" handled')

            # handling
            handled = False

            for handler in self.handlers["message_created"]:
                if not handler.detect_commands and block:
                    continue

                filters = [filter(message) for filter in handler.filters]

                if all(filters):
                    kwargs = utils.context_kwargs(handler.call, cursor=cursor)
                    asyncio.create_task(handler.call(message, **kwargs))
                    handled = True

            # handle logs
            if handled:
                bot_logger.debug(f'Message "{message.body.text}" handled')
            else:
                bot_logger.debug(f'Message "{message.body.text}" not handled')

        if update_type == "message_edited":
            message = Message.from_json(update["message"])
            message.bot = self
            message.user_locale = update.get("user_locale")
            cursor = fsm.FSMCursor(self.storage, message.sender.user_id)

            # caching
            old_message = None
            if self.cache:
                old_message = self.cache.get_message(message.id)
                self.cache.add_message(message)

            # handling
            for handler in self.handlers[update_type]:
                filters = [filter(message) for filter in handler.filters]

                if all(filters):
                    kwargs = utils.context_kwargs(
                        handler.call,
                        cursor=cursor,
                    )
                    asyncio.create_task(
                        handler.call(old_message, message, **kwargs)
                    )

            # handle logs
            bot_logger.debug(f'Message "{message.body.text}" edited')

        if update_type == "message_removed":
            payload = MessageDeletePayload.from_json(update, self)

            if payload.user_id:
                cursor = fsm.FSMCursor(self.storage, payload.user_id)
            else:
                cursor = None

            # handling
            for handler in self.handlers[update_type]:
                filters = [filter(payload) for filter in handler.filters]

                if all(filters):
                    kwargs = utils.context_kwargs(handler.call, cursor=cursor)
                    asyncio.create_task(handler.call(payload, **kwargs))

            # handle logs
            bot_logger.debug(f'Message "{payload.content}" deleted')

        if update_type == "bot_started":
            payload = BotStartPayload.from_json(update, self)
            cursor = fsm.FSMCursor(self.storage, payload.user.user_id)

            bot_logger.debug(f'User "{payload.user!r}" started bot')

            for i in self.handlers[update_type]:
                kwargs = utils.context_kwargs(i, cursor=cursor)
                asyncio.create_task(i(payload, **kwargs))

        if update_type == "chat_title_changed":
            payload = ChatTitleEditPayload.from_json(update)
            cursor = fsm.FSMCursor(self.storage, payload.user.user_id)

            bot_logger.debug(
                f'User "{payload.user!r} '
                f"changed title of chat {payload.chat_id}"
            )

            for i in self.handlers[update_type]:
                kwargs = utils.context_kwargs(i, cursor=cursor)
                asyncio.create_task(i(payload, **kwargs))

        if update_type == "bot_added" or update_type == "bot_removed":
            payload = ChatMembershipPayload.from_json(update)
            cursor = fsm.FSMCursor(self.storage, payload.user.user_id)

            for i in self.handlers[update_type]:
                kwargs = utils.context_kwargs(i, cursor=cursor)
                asyncio.create_task(i(payload, **kwargs))

        if update_type == "user_added" or update_type == "user_removed":
            payload = UserMembershipPayload.from_json(update)
            cursor = fsm.FSMCursor(self.storage, payload.user.user_id)

            for i in self.handlers[update_type]:
                kwargs = utils.context_kwargs(i, cursor=cursor)
                asyncio.create_task(i(payload, **kwargs))

        if update_type == "message_callback":
            handled = False

            callback = Callback.from_json(
                update["callback"],
                update.get("message"),
                update.get("user_locale"),
                self,
            )

            cursor = fsm.FSMCursor(self.storage, callback.user.user_id)

            for handler in self.handlers[update_type]:
                filters = [filter(callback) for filter in handler.filters]

                if all(filters):
                    kwargs = utils.context_kwargs(handler.call, cursor=cursor)
                    asyncio.create_task(handler.call(callback, **kwargs))
                    handled = True

            if handled:
                bot_logger.debug(f'Callback "{callback.payload}" handled')
            else:
                bot_logger.debug(f'Callback "{callback.payload}" not handled')

        if update_type == "message_chat_created":
            payload = ChatCreatePayload.from_json(update)
            bot_logger.debug(f'Created chat "{payload.start_payload}"')

            for i in self.handlers[update_type]:
                asyncio.create_task(i(payload))

    async def start_polling(
        self, session: "aiohttp.ClientSession | None" = None
    ):
        """
        Starts polling.

        :param session: Custom aiohttp client session
        """
        self.polling = True

        if not session:
            session = aiohttp.ClientSession()

        async with session:
            self.session = session

            # self info (this will cache the info automatically)
            await self.get_me()

            bot_logger.info(
                f"Started polling with bot "
                f"@{self.username} ({self.id}) - {self.name}"
            )

            # ready event
            for i in self.handlers["on_ready"]:
                asyncio.create_task(i())

            while self.polling:
                try:
                    updates = await self.get_updates()

                    for update in updates["updates"]:
                        await self.handle_update(update)

                except Exception as e:
                    bot_logger.exception(e)
                    await asyncio.sleep(3)

                except asyncio.exceptions.CancelledError:
                    break  # Python 3.9 throws an error when exit() is used

        self.session = None
        self.polling = False

    def run(self, *args, **kwargs):
        """
        Shortcut for `asyncio.run(Bot.start_polling())`
        """
        asyncio.run(self.start_polling(*args, **kwargs))
