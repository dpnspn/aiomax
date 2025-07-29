from typing import Literal


class Button:
    def __init__(
        self,
        type: Literal[
            "callback",
            "link",
            "request_geo_location",
            "request_contact",
            "chat",
        ],
        text: str,
    ):
        """
        Base button class
        """
        self.type: Literal[
            "callback",
            "link",
            "request_geo_location",
            "request_contact",
            "chat",
        ] = type
        self.text: str = text

    @staticmethod
    def from_json(data: dict) -> "Button":
        if data["type"] == "callback":
            return CallbackButton.from_json(data)
        elif data["type"] == "link":
            return LinkButton.from_json(data)
        elif data["type"] == "request_geo_location":
            return GeolocationButton.from_json(data)
        elif data["type"] == "request_contact":
            return ContactButton.from_json(data)
        elif data["type"] == "chat":
            return ChatButton.from_json(data)
        elif data["type"] == "message":
            return MessageButton.from_json(data)
        elif data["type"] == "open_app":
            return WebAppButton.from_json(data)
        else:
            raise Exception(f"Unknown button type: {data['type']}")

    def to_json(self) -> dict:
        return {"type": self.type, "text": self.text}


class CallbackButton(Button):
    def __init__(
        self,
        text: str,
        payload: str,
        intent: Literal["default", "positive", "negative"] = "default",
    ):
        """
        Callback button

        :param text: Button text
        :param payload: Payload that will be sent to the bot when the button is
            pressed
        :param intent: Intent of the button (changes appearance on client)
        """
        super().__init__("callback", text)
        self.payload: str = payload
        self.intent: Literal["default", "positive", "negative"] = intent

    @staticmethod
    def from_json(data: dict) -> "CallbackButton":
        return CallbackButton(data["text"], data["payload"], data["intent"])

    def to_json(self) -> dict:
        return {
            "type": "callback",
            "text": self.text,
            "payload": self.payload,
            "intent": self.intent,
        }


class LinkButton(Button):
    def __init__(
        self,
        text: str,
        url: str,
    ):
        """
        URL button on a message

        :param text: Button text
        :param url: Link that the button redirects to
        """
        super().__init__("link", text)
        self.url: str = url

    @staticmethod
    def from_json(data: dict) -> "LinkButton":
        return LinkButton(data["text"], data["url"])

    def to_json(self) -> dict:
        return {"type": "link", "text": self.text, "url": self.url}


class GeolocationButton(Button):
    def __init__(
        self,
        text: str,
        quick: bool = False,
    ):
        """
        Request geolocation button on a message

        :param text: Button text
        :param quick: Whether to show a confirmational message to a user when
            pressing the button
        """
        super().__init__("request_geo_location", text)
        self.quick: bool = quick

    @staticmethod
    def from_json(data: dict) -> "GeolocationButton":
        return GeolocationButton(data["text"], data["quick"])

    def to_json(self) -> dict:
        return {
            "type": "request_geo_location",
            "text": self.text,
            "quick": self.quick,
        }


class ContactButton(Button):
    def __init__(self, text: str):
        """
        Request contact button on a message

        :param text: Button text
        """
        super().__init__("request_contact", text)

    @staticmethod
    def from_json(data: dict) -> "ContactButton":
        return ContactButton(data["text"])

    def to_json(self) -> dict:
        return {"type": "request_contact", "text": self.text}


class ChatButton(Button):
    def __init__(
        self,
        text: str,
        title: str,
        description: "str | None" = None,
        payload: "str | None" = None,
        uuid: "int | None" = None,
    ):
        """
        Chat creation button on a message

        :param text: Button text
        :param title: Name of the new chat
        :param description: Description of the new chat
        :param payload: Payload that will be sent to the bot when the chat is
            created
        :param uuid: Chat UUID, assigned when new message is sent.
            Provide when editing message
        """
        super().__init__("chat", text)
        self.title: str = title
        self.description: str | None = description
        self.payload: str | None = payload
        self.uuid: int | None = uuid

    @staticmethod
    def from_json(data: dict) -> "ChatButton":
        return ChatButton(
            data["text"],
            data.get("chat_title"),
            data.get("chat_description"),
            data.get("start_payload"),
            data.get("uuid"),
        )

    def to_json(self) -> dict:
        return {
            "type": "chat",
            "text": self.text,
            "chat_title": self.title,
            "chat_description": self.description,
            "start_payload": self.payload,
            "uuid": self.uuid,
        }


class WebAppButton(Button):
    def __init__(self, text: str, bot: "str | int"):
        """
        Open web app button

        :param text: Button text
        :param bot: Bot ID, username or link of which to open
            the web app
        """
        super().__init__("open_app", text)
        self.bot: "str | int" = bot

    @staticmethod
    def from_json(data: dict) -> "WebAppButton":
        bot = data.get("contact_id", data.get("web_app"))
        return WebAppButton(data["text"], bot)

    def to_json(self) -> dict:
        data = {"type": "open_app", "text": self.text}
        if isinstance(self.bot, int):
            data["contact_id"] = self.bot
        else:
            data["web_app"] = self.bot
        return data


class MessageButton(Button):
    def __init__(self, text: str):
        """
        Send text to chat button

        :param text: Button text. Will be sent to the chat when a user
            presses the button
        """
        super().__init__("message", text)

    @staticmethod
    def from_json(data: dict) -> "MessageButton":
        return MessageButton(data["text"])

    def to_json(self) -> dict:
        return {"type": "message", "text": self.text}


# builder


class KeyboardBuilder:
    def __init__(self):
        """
        Keyboard builder
        """
        self.buttons: list[list[Button]] = []

    def to_list(self) -> list[list[dict]]:
        """
        Returns a serialised interpretation of the keyboard to put in a message
        """
        return [[button.to_json() for button in row] for row in self.buttons]

    def add(self, *buttons: Button):
        """
        Add buttons to the last row of the keyboard
        """
        if len(self.buttons) == 0:
            self.buttons.append([])

        self.buttons[-1].extend(buttons)
        return self

    def row(self, *buttons: Button):
        """
        Add a row of buttons
        """
        self.buttons.append(list(buttons))
        return self

    def table(self, in_row: int, *buttons: Button):
        """
        Adds multiple rows of buttons so that there are `in_row` buttons
            in each row

        :param in_row: How many buttons to put in each row
        """
        counter = 0

        for button in buttons:
            if counter == 0:
                self.row()
                counter = in_row

            self.add(button)
            counter -= 1
        return self
