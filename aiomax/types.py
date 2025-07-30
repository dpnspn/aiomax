from typing import Callable, Literal, Optional

from . import buttons, exceptions, utils


class BotCommand:
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    def as_dict(self):
        return {"name": self.name, "description": self.description}


class User:
    def __init__(
        self,
        user_id: int,
        first_name: str,
        name: str,
        is_bot: bool,
        last_activity_time: int,
        last_name: "str | None" = None,
        username: "str | None" = None,
        description: "str | None" = None,
        avatar_url: "str | None" = None,
        full_avatar_url: "str | None" = None,
        commands: "list[BotCommand] | None" = None,
        last_access_time: "int | None" = None,
        is_owner: "bool | None" = None,
        is_admin: "bool | None" = None,
        join_time: "int | None" = None,
        permissions: "list[str] | None" = None,
    ):
        self.user_id: int = user_id
        self.first_name: str = first_name
        self.last_name: str = last_name
        self.name: str = name
        self.username: "str | None" = username
        self.is_bot: bool = is_bot
        self.last_activity_time: int = last_activity_time
        self.description: "str | None" = description
        self.avatar_url: "str | None" = avatar_url
        self.full_avatar_url: "str | None" = full_avatar_url
        self.commands: "list[BotCommand] | None" = (
            [BotCommand(**i) for i in commands] if commands else None
        )
        self.last_access_time: "int | None" = last_access_time
        self.is_owner: "bool | None" = is_owner
        self.is_admin: "bool | None" = is_admin
        self.join_time: "int | None" = join_time
        self.permissions: "list[str] | None" = permissions

    def __repr__(self):
        return (
            f"{type(self).__name__}(user_id={self.user_id!r},"
            "name={self.name!r})"
        )

    def __eq__(self, other):
        if isinstance(other, User):
            return self.user_id == other.user_id
        return False

    @staticmethod
    def from_json(data: dict) -> "User | None":
        if data is None:
            return None

        return User(**data)


class Attachment:
    def __init__(self, type: str):
        self.type: str = type

    @staticmethod
    def from_json(data: dict) -> "Attachment | None":
        if data["type"] == "image":
            return PhotoAttachment.from_json(data)
        elif data["type"] == "video":
            return VideoAttachment.from_json(data)
        elif data["type"] == "audio":
            return AudioAttachment.from_json(data)
        elif data["type"] == "file":
            return FileAttachment.from_json(data)
        elif data["type"] == "sticker":
            return StickerAttachment.from_json(data)
        elif data["type"] == "contact":
            return ContactAttachment.from_json(data)
        elif data["type"] == "share":
            return ShareAttachment.from_json(data)
        elif data["type"] == "location":
            return LocationAttachment.from_json(data)
        elif data["type"] == "inline_keyboard":
            return InlineKeyboardAttachment.from_json(data)
        else:
            raise Exception(f"Unknown attachment type: {data['type']}")


class PhotoAttachment(Attachment):
    def __init__(
        self,
        url: "str | None" = None,
        token: "str | None" = None,
        photo_id: "int | None" = None,
    ):
        """
        A photo attachment. Use either `url` or `token` when uploading.

        :param url: Image URL
        :param token: Attachment token got while uploading the image
        :param photo_id: Unique photo ID. Not used when sending the attachment
        """
        super().__init__("image")
        self.url: "str | None" = url
        self.token: "str | None" = token
        self.photo_id: "int | None" = photo_id

    @staticmethod
    def from_json(data: dict) -> "PhotoAttachment | None":
        photo = PhotoAttachment(
            url=data["payload"].get("url"),
            token=data["payload"].get("token"),
            photo_id=data["payload"].get("photo_id"),
        )
        return photo

    def as_dict(self):
        data = {"type": self.type, "payload": {}}
        if self.token:
            data["payload"]["token"] = self.token
        if self.url:
            data["payload"]["url"] = self.url
        return data


class VideoAttachment(Attachment):
    def __init__(
        self,
        token: "str | None" = None,
        url: "str | None" = None,
        thumbnail: "str | None" = None,
        width: "int | None" = None,
        height: "int | None" = None,
        duration: "int | None" = None,
    ):
        """
        A video attachment. Use `token` when uploading.

        :param token: Attachment token got while uploading video
        :param url: Video URL that can be used for downloading the video
        :param thumbnail: Video thumbnail URL
        :param width: Video width
        :param height: Video height
        :param duration: Video duration
        """
        super().__init__("video")
        self.token: "str | None" = token
        self.url: "str | None" = url
        self.thumbnail: "str | None" = thumbnail
        self.width: "int | None" = width
        self.height: "int | None" = height
        self.duration: "int | None" = duration

    @staticmethod
    def from_json(data: dict) -> "VideoAttachment | None":
        return VideoAttachment(
            data["payload"].get("token", None),
            data["payload"].get("url", None),
            data.get("thumbnail", {}).get("url"),
            data.get("width"),
            data.get("height"),
            data.get("duration"),
        )

    def as_dict(self):
        return {"type": self.type, "payload": {"token": self.token}}


class AudioAttachment(Attachment):
    def __init__(
        self,
        url: "str | None" = None,
        token: "str | None" = None,
        transcription: "str | None" = None,
    ):
        """
        An audio attachment. Use `token` when uploading.

        :param token: Attachment token got while uploading audio
        :param transcription: Audio transcription
        """
        super().__init__("audio")
        self.url: str = url
        self.token: str = token
        self.transcription: "str | None" = transcription

    @staticmethod
    def from_json(data: dict) -> "AudioAttachment | None":
        return AudioAttachment(
            data["payload"]["url"],
            data["payload"]["token"],
            data.get("transcription"),
        )

    def as_dict(self):
        return {"type": self.type, "payload": {"token": self.token}}


class FileAttachment(Attachment):
    def __init__(
        self,
        token: str,
        url: "str | None" = None,
        filename: "str | None" = None,
        size: "int | None" = None,
    ):
        """
        A file attachment. Use `token` when uploading.

        :param token: Attachment token got while uploading the file
        :param url: File URL that can be used for downloading the file
        :param filename: File name
        :param size: File size
        """
        super().__init__("file")
        self.url: "str | None" = url
        self.token: str = token
        self.filename: "str | None" = filename
        self.size: "int | None" = size

    @staticmethod
    def from_json(data: dict) -> "FileAttachment | None":
        return FileAttachment(
            data["payload"]["token"],
            data["payload"].get("url"),
            data.get("filename"),
            data.get("size"),
        )

    def as_dict(self):
        return {"type": self.type, "payload": {"token": self.token}}


class StickerAttachment(Attachment):
    def __init__(
        self,
        code: str,
        url: "str | None" = None,
        width: "int | None" = None,
        height: "int | None" = None,
    ):
        """
        A sticker attachment. Use `code` when uploading.

        :param code: Sticker code
        :param url: Sticker URL that can be used for downloading the sticker
        :param width: Sticker width
        :param height: Sticker height
        """
        super().__init__("sticker")
        self.code: str = code
        self.url: "str | None" = url
        self.width: int = width
        self.height: int = height

    @staticmethod
    def from_json(data: dict) -> "StickerAttachment | None":
        sticker = StickerAttachment(
            data["payload"]["code"],
            data["payload"].get("url"),
            data.get("width"),
            data.get("height"),
        )
        return sticker

    def as_dict(self) -> dict:
        return {"type": "sticker", "payload": {"code": self.code}}


class ContactAttachment(Attachment):
    def __init__(
        self,
        name: "str | None" = None,
        contact_id: "int | None" = None,
        vcf_info: "str | None" = None,
        vcf_phone: "str | None" = None,
        max_info: "User | None" = None,
    ):
        """
        A contact attachment.

        :param name: Contact name. Only used when sending
        :param contact_id: Contact user ID (if sending a Max user).
            Only used when sending contacts
        :param vcf_info: Contact's information in vCard format
        :param vcf_phone: Contact's phone number.
            Only used when sending contacts
        :param max_info: User object if contact is a user.
            Only used when recieving contacts, use `contact_id` instead
        """
        super().__init__("contact")
        self.name: "str | None" = name
        self.contact_id: "int | None" = contact_id
        self.vcf_info: "str | None" = vcf_info
        self.vcf_phone: "str | None" = vcf_phone
        self.max_info: "User | None" = max_info

    @staticmethod
    def from_json(data: dict) -> "ContactAttachment | None":
        return ContactAttachment(
            vcf_info=data.get("vcf_info"),
            max_info=User.from_json(data.get("max_info")),
        )

    def as_dict(self) -> dict:
        return {
            "type": self.type,
            "payload": {
                "name": self.name,
                "contact_id": self.contact_id,
                "vcf_info": self.vcf_info,
                "vcf_phone": self.vcf_phone,
            },
        }


class ShareAttachment(Attachment):
    def __init__(
        self,
        url: "str | None" = None,
        token: "str | None" = None,
        title: "str | None" = None,
        description: "str | None" = None,
        image_url: "str | None" = None,
    ):
        """
        Link preview. Use `url` and `token` when uploading

        :param url: Link URL
        :param token: Attachment token
        :param title: Preview title
        :param description: Preview description
        :param image_url: Preview image URL
        """
        super().__init__("share")
        self.url: "str | None" = url
        self.token: "str | None" = token
        self.title: "str | None" = title
        self.description: "str | None" = description
        self.image_url: "str | None" = image_url

    @staticmethod
    def from_json(data: dict) -> "ShareAttachment | None":
        return ShareAttachment(
            data["payload"].get("url", None),
            data["payload"].get("token", None),
            data.get("title"),
            data.get("description"),
            data.get("image_url"),
        )

    def as_dict(self) -> dict:
        return {
            "type": self.type,
            "payload": {"url": self.url, "token": self.token},
        }


class LocationAttachment(Attachment):
    def __init__(
        self,
        latitude: float,
        longitude: float,
    ):
        super().__init__("location")
        self.latitude: float = latitude
        self.longitude: float = longitude

    @staticmethod
    def from_json(data: dict) -> "LocationAttachment | None":
        return LocationAttachment(data["latitude"], data["longitude"])

    def as_dict(self) -> dict:
        return {
            "type": "location",
            "latitude": self.latitude,
            "longitude": self.longitude,
        }


class InlineKeyboardAttachment(Attachment):
    def __init__(
        self,
        payload: list[list[buttons.Button]],
    ):
        super().__init__("inline_keyboard")
        self.payload: list[list[buttons.Button]] = payload

    @staticmethod
    def from_json(data: dict) -> "InlineKeyboardAttachment | None":
        return InlineKeyboardAttachment(
            [
                [buttons.Button.from_json(j) for j in i]
                for i in data["payload"]["buttons"]
            ]
        )


class MessageRecipient:
    def __init__(self, chat_id: "int | None", chat_type: str):
        self.chat_id: "int | None" = chat_id
        self.chat_type: str = chat_type

    def __repr__(self):
        return (
            f"{type(self).__name__}(chat_id={self.chat_id!r},"
            f"chat_type={self.chat_type!r})"
        )

    def __eq__(self, other):
        if isinstance(other, MessageRecipient):
            return self.chat_id == other.chat_id
        return False

    @staticmethod
    def from_json(data: dict) -> "MessageRecipient":
        if data is None:
            return None

        return MessageRecipient(
            chat_id=data["chat_id"], chat_type=data["chat_type"]
        )


class Markup:
    def __init__(
        self,
        type: Literal[
            "strong",
            "emphasized",
            "monospaced",
            "link",
            "strikethrough",
            "underline",
            "user_mention",
            "heading",
            "highlighted",
        ],
        start: int,
        length: int,
        user_link: "str | None" = None,
        user_id: "int | None" = None,
        url: "str | None" = None,
    ):
        """
        A markup element

        :param type: Markup type
        :param start: Start position
        :param length: Length
        :param user_link: Username. `None` if markup type is not `user_link`
        :param user_id: User ID. `None` if markup type is not `user_link`
        :param url: URL. `None` if markup type is not `link`
        """
        self.type: Literal[
            "strong",
            "emphasized",
            "monospaced",
            "link",
            "strikethrough",
            "underline",
            "user_mention",
            "heading",
            "highlighted",
        ] = type
        self.start: int = start
        self.length: int = length

        self.user_link: "str | None" = user_link
        self.user_id: "int | None" = user_id
        self.url: "str | None" = url

    @staticmethod
    def from_json(data: dict) -> "Markup | None":
        if data is None:
            return None

        if data["type"] == "user_mention":
            return Markup(
                data["type"],
                data["from"],
                data["length"],
                user_link=data.get("user_link"),
                user_id=data.get("user_id"),
            )
        elif data["type"] == "link":
            return Markup(
                data["type"], data["from"], data["length"], url=data["url"]
            )

        return Markup(data["type"], data["from"], data["length"])


class MessageBody:
    def __init__(
        self,
        mid: str,
        seq: int,
        text: "str | None",
        attachments: "list[Attachment] | None",
        markup: "list[Markup] | None" = None,
    ):
        self.message_id: str = mid
        self.seq: int = seq
        self.text: "str | None" = text
        self.attachments: "list[Attachment] | None" = attachments
        self.markup: "list[Markup] | None" = markup

    @staticmethod
    def from_json(data: dict) -> "MessageBody":
        if data is None:
            return None

        return MessageBody(
            mid=data["mid"],
            seq=data["seq"],
            text=data["text"],
            attachments=[
                Attachment.from_json(x) for x in data.get("attachments", [])
            ],
            markup=[Markup.from_json(x) for x in data.get("markup", [])],
        )


class LinkedMessage:
    def __init__(
        self,
        type: str,
        message: MessageBody,
        sender: User,
        chat_id: "int | None" = None,
    ):
        self.type: str = type
        self.message: MessageBody = message
        self.sender: User = sender
        self.chat_id: "int | None" = chat_id

    @staticmethod
    def from_json(data: dict) -> "LinkedMessage":
        if data is None:
            return None

        return LinkedMessage(
            type=data["type"],
            message=MessageBody.from_json(data["message"]),
            sender=User.from_json(data.get("sender")),
            chat_id=data.get("chat_id"),
        )

    @property
    def user_id(self):
        return self.sender.user_id


class Message:
    def __init__(
        self,
        recipient: MessageRecipient,
        body: MessageBody,
        timestamp: float,
        sender: User,
        link: "LinkedMessage | None" = None,
        views: "int | None" = None,
        url: "str | None" = None,
        bot=None,
    ):
        self.recipient: MessageRecipient = recipient
        self.body: "MessageBody | None" = body
        self.timestamp: "float | None" = timestamp / 1000
        self.sender: "User | None" = sender
        self.link: "LinkedMessage | None" = link
        self.views: "int | None" = views
        self.url: "str | None" = url
        self.user_locale: "str | None" = None
        self.bot = bot

    def __repr__(self):
        return f"{type(self).__name__}(text={self.body.text!r})"

    def __str__(self):
        return self.body.text

    def __eq__(self, other):
        if isinstance(other, Message):
            return self.id == other.id
        return False

    @property
    def id(self) -> str:
        return self.body.message_id

    @property
    def content(self) -> str:
        return self.body.text

    @property
    def user_id(self):
        return self.sender.user_id

    @staticmethod
    def from_json(data: dict) -> "Message":
        return Message(
            recipient=MessageRecipient.from_json(data.get("recipient")),
            body=MessageBody.from_json(data.get("body")),
            timestamp=data.get("timestamp"),
            sender=User.from_json(data.get("sender")),
            link=LinkedMessage.from_json(data.get("link")),
            views=data.get("stat", {}).get("views", None),
            url=data.get("url"),
        )

    def resolve_mention(
        self,
        replies: bool = True,
        message_text: bool = True,
        skip_bot: bool = True,
    ) -> "int | None":
        """
        Finds who was mentioned in this message
            and returns the user ID if found.

        :param replies: Whether to check for this message's link author.
        :param message_text: Whether to check for mentions in message text.
        :param skip_bot: Whether to ignore mentions of the bot.
        """
        if replies and self.link and self.link.type == "reply":
            if (
                skip_bot
                and self.bot
                and self.link.sender.user_id == self.bot.id
            ):
                pass
            else:
                return self.link.sender.user_id

        if message_text:
            for i in self.body.markup:
                if i.type != "user_mention":
                    continue
                if skip_bot and self.bot and i.user_id == self.bot.id:
                    continue
                if skip_bot and self.bot and i.user_link == self.bot.username:
                    continue
                return i.user_id

    async def send(
        self,
        text: "str | None" = None,
        format: "Literal['html', 'markdown', 'default'] | None" = "default",
        notify: bool = True,
        disable_link_preview: bool = False,
        keyboard: """list[list[buttons.Button]] \
        | buttons.KeyboardBuilder \
        | None""" = None,
        attachments: "list[Attachment] | Attachment | None" = None,
    ) -> "Message":
        """
        Send a message to the chat that the message is sent.

        :param text: Message text. Up to 4000 characters
        :param format: Message format. Bot.default_format by default
        :param notify: Whether to notify users about the message.
            True by default.
        :param disable_link_preview: Whether to disable link preview.
            False by default
        :param keyboard: An inline keyboard to attach to the message
        :param attachments: List of attachments
        """
        if self.bot is None:
            return
        return await self.bot.send_message(
            text,
            chat_id=self.recipient.chat_id,
            format=format,
            notify=notify,
            disable_link_preview=disable_link_preview,
            keyboard=keyboard,
            attachments=attachments,
        )

    async def reply(
        self,
        text: "str | None" = None,
        format: "Literal['html', 'markdown', 'default'] | None" = "default",
        notify: bool = True,
        disable_link_preview: bool = False,
        keyboard: """list[list[buttons.Button]] \
        | buttons.KeyboardBuilder \
        | None""" = None,
        attachments: "list[Attachment] | Attachment | None" = None,
    ) -> "Message":
        """
        Reply to this message.

        :param text: Message text. Up to 4000 characters
        :param format: Message format. Bot.default_format by default
        :param notify: Whether to notify users about the message.
            True by default.
        :param disable_link_preview: Whether to disable link preview.
            False by default
        :param keyboard: An inline keyboard to attach to the message
        :param attachments: List of attachments
        """
        if self.bot is None:
            return
        return await self.bot.send_message(
            text,
            chat_id=self.recipient.chat_id,
            format=format,
            notify=notify,
            disable_link_preview=disable_link_preview,
            keyboard=keyboard,
            attachments=attachments,
            reply_to=self.id,
        )

    async def edit(
        self,
        text: "str | None" = None,
        format: "Literal['html', 'markdown', 'default'] | None" = "default",
        reply_to: "int | None" = None,
        notify: bool = True,
        keyboard: """list[list[buttons.Button]] \
        | buttons.KeyboardBuilder \
        | None""" = None,
        attachments: "list[Attachment] | Attachment | None" = None,
    ) -> "Message":
        """
        Edit a message

        :param text: Message text. Up to 4000 characters
        :param format: Message format. Bot.default_format by default
        :param notify: Whether to notify users about the message.
            True by default.
        :param disable_link_preview: Whether to disable link preview.
            False by default
        :param keyboard: An inline keyboard to attach to the message
        :param attachments: List of attachments
        """
        if self.bot is None:
            return
        return await self.bot.edit_message(
            self.id,
            text,
            format=format,
            notify=notify,
            keyboard=keyboard,
            reply_to=reply_to,
            attachments=attachments,
        )

    async def delete(self):
        if self.bot is None:
            return
        return await self.bot.delete_message(self.id)


class BotStartPayload:
    def __init__(
        self,
        chat_id: int,
        user: User,
        payload: "str | None",
        user_locale: "str | None",
        bot=None,
    ):
        self.chat_id: int = chat_id
        self.user: User = user
        self.payload: "str | None" = payload
        self.user_locale: "str | None" = user_locale
        self.bot = bot

    @staticmethod
    def from_json(data: dict, bot) -> "BotStartPayload":
        return BotStartPayload(
            chat_id=data["chat_id"],
            user=User.from_json(data["user"]),
            payload=data.get("payload"),
            user_locale=data.get("user_locale"),
            bot=bot,
        )

    @property
    def user_id(self):
        return self.user.user_id

    async def send(
        self,
        text: "str | None" = None,
        format: "Literal['html', 'markdown', 'default'] | None" = "default",
        notify: bool = True,
        disable_link_preview: bool = False,
        keyboard: """list[list[buttons.Button]] \
        | buttons.KeyboardBuilder \
        | None""" = None,
        attachments: "list[Attachment] | Attachment | None" = None,
    ) -> "Message":
        """
        Send a message to the chat where bot was started.

        :param text: Message text. Up to 4000 characters
        :param format: Message format. Bot.default_format by default
        :param notify: Whether to notify users about the message.
            True by default.
        :param disable_link_preview: Whether to disable link preview.
            False by default
        :param keyboard: An inline keyboard to attach to the message
        :param attachments: List of attachments
        """
        if self.bot is None:
            return
        return await self.bot.send_message(
            text,
            chat_id=self.chat_id,
            format=format,
            notify=notify,
            disable_link_preview=disable_link_preview,
            keyboard=keyboard,
            attachments=attachments,
        )


class CommandContext:
    def __init__(self, bot, message: Message, command_name: str, args: str):
        self.bot = bot
        self.message: Message = message
        self.sender: User = message.sender
        self.recipient: MessageRecipient = message.recipient
        self.command_name: str = command_name
        self.args_raw: str = args
        self.args: list[str] = args.split()

    async def send(
        self,
        text: "str | None" = None,
        format: "Literal['html', 'markdown', 'default'] | None" = "default",
        notify: bool = True,
        disable_link_preview: bool = False,
        keyboard: """list[list[buttons.Button]] \
        | buttons.KeyboardBuilder \
        | None""" = None,
        attachments: "list[Attachment] | Attachment | None" = None,
    ) -> Message:
        """
        Send a message to the chat that the user sent the command.

        :param text: Message text. Up to 4000 characters
        :param format: Message format. Bot.default_format by default
        :param notify: Whether to notify users about the message.
            True by default.
        :param disable_link_preview: Whether to disable link preview.
            False by default
        :param keyboard: An inline keyboard to attach to the message
        :param attachments: List of attachments
        """
        return await self.bot.send_message(
            text,
            chat_id=self.message.recipient.chat_id,
            format=format,
            notify=notify,
            disable_link_preview=disable_link_preview,
            keyboard=keyboard,
            attachments=attachments,
        )

    async def reply(
        self,
        text: "str | None" = None,
        format: "Literal['html', 'markdown', 'default'] | None" = "default",
        notify: bool = True,
        disable_link_preview: bool = False,
        keyboard: """list[list[buttons.Button]] \
        | buttons.KeyboardBuilder \
        | None""" = None,
        attachments: "list[Attachment] | Attachment | None" = None,
    ) -> Message:
        """
        Reply to the message that the user sent.

        :param text: Message text. Up to 4000 characters
        :param format: Message format. Bot.default_format by default
        :param notify: Whether to notify users about the message.
            True by default.
        :param disable_link_preview: Whether to disable link preview.
            False by default
        :param keyboard: An inline keyboard to attach to the message
        :param attachments: List of attachments
        """
        return await self.bot.send_message(
            text,
            chat_id=self.message.recipient.chat_id,
            format=format,
            notify=notify,
            disable_link_preview=disable_link_preview,
            keyboard=keyboard,
            attachments=attachments,
            reply_to=self.message.id,
        )

    @property
    def user_id(self):
        return self.sender.user_id


class CommandHandler:
    def __init__(
        self,
        call: Callable,
        as_message: bool = False,
    ):
        self.call = call
        self.as_message: bool = as_message


class Handler:
    def __init__(
        self,
        call: Callable,
        deco_filter: "Callable | None" = None,
        router_filters: Optional[list[Callable]] = None,
    ):
        if router_filters is None:
            router_filters = []

        self.call = call
        self.deco_filter: "Callable | None" = deco_filter
        self.router_filters: list[Callable] = router_filters

    @property
    def filters(self) -> list[Callable]:
        if self.deco_filter:
            return [self.deco_filter, *self.router_filters]
        return self.router_filters


class MessageHandler(Handler):
    def __init__(
        self,
        call: Callable,
        deco_filter: "Callable | None" = None,
        router_filters: Optional[list[Callable]] = None,
        detect_commands: bool = False,
    ):
        if router_filters is None:
            router_filters = []

        super().__init__(call, deco_filter, router_filters)
        self.detect_commands: bool = detect_commands


class Image:
    def __init__(
        self,
        url: str,
    ):
        """
        An image.

        :param url: Image URL
        """
        self.url: str = url

    @staticmethod
    def from_json(data: dict) -> "Image | None":
        if data is None:
            return None

        return Image(**data)


class ImageRequestPayload:
    def __init__(self, url: "str | None" = None, token: "str | None" = None):
        """
        A payload with the info about an image or avatar to send to the bot.

        Only url or token must be specified.

        :param url: Image URL
        :param token: Attachment token generated by Bot.upload_image().token
        """
        if url is None and token is None:
            raise exceptions.AiomaxException("Token or URL must be specified")
        if not (url is None or token is None):
            raise exceptions.AiomaxException(
                "Token and URL cannot be specified at the same time"
            )

        self.url: "str | None" = url
        self.token: "str | None" = token

    @staticmethod
    def from_json(data: dict) -> "ImageRequestPayload | None":
        if data is None:
            return None

        return ImageRequestPayload(**data)

    def as_dict(self):
        return {"url": self.url} if self.url else {"token": self.token}


class Chat:
    def __init__(
        self,
        chat_id: int,
        type: str,
        status: str,
        last_event_time: int,
        participants_count: int,
        is_public: bool,
        title: "str | None" = None,
        icon: "Image | None" = None,
        description: "str | None" = None,
        pinned_message: "Message | None" = None,
        owner_id: "int | None" = None,
        participants: "dict[str, int] | None" = None,
        link: "str | None" = None,
        messages_count: "str | None" = None,
        chat_message_id: "str | None" = None,
        dialog_with_user: "User | None" = None,
    ):
        self.chat_id: int = chat_id
        self.type: str = type
        self.status: str = status
        self.last_event_time: int = last_event_time
        self.participants_count: int = participants_count
        self.title: "str | None" = title
        self.icon: "Image | None" = icon
        self.is_public: bool = is_public
        self.dialog_with_user: "User | None" = dialog_with_user
        self.description: "str | None" = description
        self.pinned_message: "Message | None" = pinned_message
        self.owner_id: "int | None" = owner_id
        self.participants: "dict[int, int] | None" = (
            {int(k): v for k, v in participants.items()}
            if participants
            else None
        )
        self.link: "str | None" = link
        self.messages_count: "str | None" = messages_count
        self.chat_message_id: "str | None" = chat_message_id

    def __eq__(self, other):
        if isinstance(other, Chat):
            return self.chat_id == other.chat_id
        return False

    def __repr__(self):
        return (
            f"{self.__class__.__name__}(chat_id={self.chat_id!r},"
            f"title={self.title!r})"
        )

    @staticmethod
    def from_json(data: dict) -> "Chat | None":
        if data is None:
            return None

        return Chat(**data)


class Callback:
    def __init__(
        self,
        bot,
        timestamp: int,
        callback_id: str,
        message: "Message | None",
        user: User,
        user_locale: "str | None",
        payload: "str | None" = None,
    ):
        self.bot = bot
        self.timestamp: int = timestamp
        self.callback_id: str = callback_id
        self.message: "Message | None" = message
        self.user: User = user
        self.payload: "str | None" = payload
        self.user_locale: "str | None" = user_locale

        if self.message is not None:
            self.message.bot = bot

    @property
    def content(self) -> str:
        return self.payload

    async def send(
        self,
        text: "str | None" = None,
        format: "Literal['html', 'markdown', 'default'] | None" = "default",
        notify: bool = True,
        disable_link_preview: bool = False,
        keyboard: """list[list[buttons.Button]] \
        | buttons.KeyboardBuilder \
        | None""" = None,
        attachments: "list[Attachment] | Attachment | None" = None,
    ) -> "Message":
        """
        Send a message to the chat that contains the message
            with the pressed button.

        :param text: Message text. Up to 4000 characters
        :param format: Message format. Bot.default_format by default
        :param notify: Whether to notify users about the message.
            True by default.
        :param disable_link_preview: Whether to disable link preview.
        False by default
        :param keyboard: An inline keyboard to attach to the message
        :param attachments: List of attachments
        """
        if self.bot is None:
            return

        if self.message is None:
            raise exceptions.AiomaxException("Original message not found")

        return await self.bot.send_message(
            text,
            chat_id=self.message.recipient.chat_id,
            format=format,
            notify=notify,
            disable_link_preview=disable_link_preview,
            keyboard=keyboard,
            attachments=attachments,
        )

    async def reply(
        self,
        text: "str | None" = None,
        format: "Literal['html', 'markdown', 'default'] | None" = "default",
        notify: bool = True,
        disable_link_preview: bool = False,
        keyboard: """list[list[buttons.Button]] \
        | buttons.KeyboardBuilder \
        | None""" = None,
        attachments: "list[Attachment] | Attachment | None" = None,
    ) -> "Message":
        """
        Reply to the message with the button.

        :param text: Message text. Up to 4000 characters
        :param format: Message format. Bot.default_format by default
        :param notify: Whether to notify users about the message.
            True by default.
        :param disable_link_preview: Whether to disable link preview.
            False by default
        :param keyboard: An inline keyboard to attach to the message
        :param attachments: List of attachments
        """
        if self.bot is None:
            return

        if self.message is None:
            raise exceptions.AiomaxException("Original message not found")

        return await self.bot.send_message(
            text,
            chat_id=self.message.recipient.chat_id,
            format=format,
            notify=notify,
            disable_link_preview=disable_link_preview,
            keyboard=keyboard,
            attachments=attachments,
            reply_to=self.message.id,
        )

    async def answer(
        self,
        notification: "str | None" = None,
        text: "str | None" = None,
        format: "Literal['html', 'markdown', 'default'] | None" = "default",
        notify: bool = True,
        keyboard: """list[list[buttons.Button]] \
        | buttons.KeyboardBuilder \
        | None""" = None,
        attachments: "list[Attachment] | Attachment | None" = None,
    ):
        """
        Answer the callback.

        :param notification: Notification to display to the user
        :param text: Message text. Up to 4000 characters
        :param format: Message format. Bot.default_format by default
        :param notify: Whether to notify users about the message.
        True by default.
        :param keyboard: An inline keyboard to attach to the message
        :param attachments: List of attachments
        """
        if (
            notification is None
            and text is None
            and attachments is None
            and keyboard is None
        ):
            raise exceptions.AiomaxException(
                "Either notification, text or attachments must be specified"
            )
        body = {"notification": notification, "message": None}
        if keyboard is None and self.message is not None:
            keyboard = [
                i
                for i in self.message.body.attachments
                if i.type == "inline_keyboard"
            ]
            keyboard = None if len(keyboard) == 0 else keyboard[0].payload

        if text is not None or attachments is not None or keyboard is not None:
            format = self.bot.default_format if format == "default" else format
            body["message"] = utils.get_message_body(
                text,
                format,
                notify=notify,
                keyboard=keyboard,
                attachments=attachments,
            )

        out = await self.bot.post(
            "https://botapi.max.ru/answers",
            params={"callback_id": self.callback_id},
            json=body,
        )
        return await out.json()

    @property
    def user_id(self):
        return self.user.user_id

    @staticmethod
    def from_json(
        data: dict,
        message: "dict | None",
        user_locale: "str | None" = None,
        bot=None,
    ) -> "Callback | None":
        if data is None:
            return None

        return Callback(
            bot,
            data["timestamp"],
            data["callback_id"],
            Message.from_json(message) if message is not None else None,
            User.from_json(data["user"]),
            user_locale,
            data.get("payload"),
        )


class ChatCreatePayload:
    def __init__(
        self,
        timestamp: int,
        chat: Chat,
        message_id: "str | None" = None,
        start_payload: "str | None" = None,
    ):
        """
        Payload that is sent to the `Bot.on_button_chat_create` decorator.

        :param timestamp: Timestamp of the button press
        :param chat: Created chat
        :param message_id: Message ID on which the button was
        :param start_payload: Start payload specified by the button
        """
        self.timestamp: int = timestamp
        self.chat: Chat = chat
        self.message_id: "str | None" = message_id
        self.start_payload: "str | None" = start_payload

    @staticmethod
    def from_json(data: dict) -> "ChatCreatePayload | None":
        if data is None:
            return None

        return ChatCreatePayload(
            data["timestamp"],
            Chat.from_json(data["chat"]),
            data.get("message_id"),
            data.get("start_payload"),
        )


class MessageDeletePayload:
    def __init__(
        self,
        timestamp: int,
        message: "Message | None" = None,
        message_id: "str | None" = None,
        chat_id: "int | None" = None,
        user_id: "int | None" = None,
        bot=None,
    ):
        """
        Payload that is sent to the `Bot.on_message_delete` decorator.

        :param timestamp: Timestamp of the message deletion.
        :param message: Cached Message object.
        May be None if message was not cached
        :param message_id: ID of the deleted message
        :param chat_id: ID of the chat the message was deleted in
        :param user_id: ID of the user who deleted the message
        """
        self.timestamp: int = timestamp
        self.message: "Message | None" = message
        self.message_id: "str | None" = message_id
        self.chat_id: "int | None" = chat_id
        self.user_id: "int | None" = user_id
        self.bot = bot

    @staticmethod
    def from_json(data: dict, bot) -> "MessageDeletePayload | None":
        if data is None:
            return None

        return MessageDeletePayload(
            data["timestamp"],
            bot.cache.get_message(data.get("message_id")),
            data.get("message_id"),
            data.get("chat_id"),
            data.get("user_id"),
            bot=bot,
        )

    @property
    def content(self) -> "str | None":
        if self.message is None:
            return None

        return self.message.content


class ChatTitleEditPayload:
    def __init__(
        self,
        timestamp: int,
        user: User,
        chat_id: "int | None" = None,
        title: "str | None" = None,
    ):
        """
        Payload that is sent to the `Bot.on_chat_title_change` decorator.

        :param timestamp: Timestamp of the title edit.
        :param user: User that edited the chat name.
        :param chat_id: Chat ID that had its title edited.
        :param title: New chat title
        """
        self.timestamp: int = timestamp
        self.user: User = user
        self.chat_id: "int | None" = chat_id
        self.title: "str | None" = title

    @property
    def user_id(self):
        return self.user.user_id

    @staticmethod
    def from_json(data: dict) -> "ChatTitleEditPayload | None":
        if data is None:
            return None

        return ChatTitleEditPayload(
            data["timestamp"],
            User.from_json(data["user"]),
            data.get("chat_id"),
            data.get("title"),
        )


class ChatMembershipPayload:
    def __init__(
        self,
        timestamp: int,
        user: User,
        chat_id: "int | None" = None,
        is_channel: bool = False,
    ):
        """
        Payload that is sent to the `Bot.on_bot_add`
        or `Bot.on_bot_remove` decorator.

        :param timestamp: Timestamp of the action.
        :param user: User that invited or kicked the bot.
        :param chat_id: Chat ID that the bot was invited to / kicked from.
        :param is_channel: Whether the bot got added to / kicked
        from a channel or not
        """
        self.timestamp: int = timestamp
        self.user: User = user
        self.chat_id: "int | None" = chat_id
        self.is_channel: bool = is_channel

    @property
    def user_id(self):
        return self.user.user_id

    @staticmethod
    def from_json(data: dict) -> "ChatMembershipPayload | None":
        if data is None:
            return None

        return ChatMembershipPayload(
            data["timestamp"],
            User.from_json(data["user"]),
            data.get("chat_id"),
            data.get("is_channel", False),
        )


class UserMembershipPayload:
    def __init__(
        self,
        timestamp: int,
        user: User,
        chat_id: "int | None" = None,
        is_channel: bool = False,
        initiator: "int | None" = None,
    ):
        """
        Payload that is sent to the `Bot.on_user_add` or
        `Bot.on_user_remove` decorator.

        :param timestamp: Timestamp of the action.
        :param user: User that joined or left the chat.
        :param chat_id: Chat ID that the user joined / left.
        :param is_channel: Whether the user was added to / kicked
        from a channel or not.
        :param initiator: User ID of the inviter / kicker,
        if the user got invited by another user or kicked by an admin.
        """
        self.timestamp: int = timestamp
        self.user: User = user
        self.chat_id: "int | None" = chat_id
        self.is_channel: bool = is_channel
        self.initiator: "int | None" = initiator

    @property
    def user_id(self):
        return self.user.user_id

    @staticmethod
    def from_json(data: dict) -> "UserMembershipPayload | None":
        if data is None:
            return None

        return UserMembershipPayload(
            data["timestamp"],
            User.from_json(data["user"]),
            data.get("chat_id"),
            data.get("is_channel", False),
            data.get("inviter_id", data.get("admin_id")),
        )
