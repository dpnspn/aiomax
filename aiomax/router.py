import logging
from copy import deepcopy
from typing import Callable

from . import exceptions
from .filters import normalize_filter
from .types import CommandHandler, Handler, MessageHandler
from . import utils

bot_logger = logging.getLogger("aiomax.bot")


class Router:
    def __init__(
        self,
        case_sensitive: bool = True,
    ):
        """
        Router init
        :param case_sensitive: If False the bot will respond to commands
            regardless of case
        """
        self._handlers: dict[str, list[Handler]] = {
            "message_created": [],
            "on_ready": [],
            "bot_started": [],
            "message_callback": [],
            "message_chat_created": [],
            "message_edited": [],
            "message_removed": [],
            "chat_title_changed": [],
            "bot_added": [],
            "bot_removed": [],
            "user_added": [],
            "user_removed": [],
            "on_exception": [],
        }  # handlers in this router
        self._commands: dict[
            str, list[CommandHandler]
        ] = {}  # commands in this router
        self.case_sensitive: bool = case_sensitive
        self.parent = None  # Parent bot of this router
        self.routers: list[Router] = []
        self.filters: dict[str, list[Callable]] = {
            "message_created": [],
            "message_edited": [],
            "message_removed": [],
            "message_callback": [],
        }


    @staticmethod
    async def check_filters(
        filters: "list[Callable] | Callable",
        obj: any):
        """
        Calls filter(s) and returns 
        """
        if not isinstance(filters, list):
            filters = [filters]
        
        for filter in filters:
            if utils.is_async(filter):
                result = await filter(obj)
            else:
                result = filter(obj)
            if not result:
                return False
        return True
    

    @staticmethod
    def wrap_filters(
        filters: tuple["Callable | str | None", ...], mode: str = "and"
    ) -> Callable:
        """
        Normalize multiple filters into a single callable.

        :param filters: filters to combine
        :param mode: "and" (default) — all filters must pass,
                     "or" — at least one filter must pass.
        """
        normalized_filters = []

        for filter_ in filters:
            if filter_ is None:
                continue
            normalized_filters.append(normalize_filter(filter_))

        if not normalized_filters:
            return lambda message: True

        if mode == "and":
            async def combined_filter(message):
                return await Router.check_filters(normalized_filters, message)
        elif mode == "or":
            async def combined_filter(message):
                return any(await Router.check_filters(f, message) for f in
                           normalized_filters)
        else:
            raise ValueError(f"Unsupported mode: {mode}. Use 'and' or 'or'.")

        return combined_filter

    # routers

    @property
    def handlers(self) -> dict[str, list[Handler]]:
        """
        Returns all handlers in this and all the child routers.
        """
        out = deepcopy(self._handlers)

        for router in self.routers:
            for handler_type in out:
                out[handler_type].extend(router.handlers[handler_type])

        return out

    @property
    def commands(self) -> dict[str, list[CommandHandler]]:
        """
        Returns all commands in this and all the child routers.
        """
        out = deepcopy(self._commands)
        for router in self.routers:
            out.update(router.commands)
        return out

    @property
    def bot(self):
        """
        Returns the bot this router is attached to.
        """
        if self.parent is None:
            return None

        if self.parent.parent is None:
            return self.parent
        return self.parent.parent

    def add_router(self, router: "Router"):
        if router.parent is not None:
            raise ValueError("Router already has a parent")

        router.parent = self
        self.routers.append(router)

    def remove_router(self, router: "Router"):
        if router not in self.routers:
            raise ValueError("Router not found")

        router.parent = None
        self.routers.remove(router)

    # decorators

    def on_message(
        self,
        *filters: "Callable | str | None",
        mode: str = "and",
        detect_commands: bool = False,
    ):
        """
        Decorator for receiving messages.
        """

        def decorator(func):
            new_filter = self.wrap_filters(filters, mode=mode)

            self._handlers["message_created"].append(
                MessageHandler(
                    call=func,
                    deco_filter=new_filter,
                    router_filters=self.filters["message_created"],
                    detect_commands=detect_commands,
                )
            )
            return func

        return decorator

    def on_message_edit(
        self, *filters: "Callable | str | None", mode: str = "and"
    ):
        """
        Decorator for editing messages.
        """

        def decorator(func):
            new_filter = self.wrap_filters(filters, mode=mode)

            self._handlers["message_edited"].append(
                Handler(
                    call=func,
                    deco_filter=new_filter,
                    router_filters=self.filters["message_edited"],
                )
            )
            return func

        return decorator

    def on_message_delete(
        self, *filters: "Callable | str | None", mode: str = "and"
    ):
        """
        Decorator for deleted messages.
        """

        def decorator(func):
            new_filter = self.wrap_filters(filters, mode=mode)

            self._handlers["message_removed"].append(
                Handler(
                    call=func,
                    deco_filter=new_filter,
                    router_filters=self.filters["message_removed"],
                )
            )
            return func

        return decorator

    def on_bot_start(self):
        """
        Decorator for handling bot start.
        """

        def decorator(func):
            self._handlers["bot_started"].append(Handler(call=func))
            return func

        return decorator

    def on_chat_title_change(self):
        """
        Decorator for handling chat title changes.
        """

        def decorator(func):
            self._handlers["chat_title_changed"].append(Handler(call=func))
            return func

        return decorator

    def on_bot_add(self):
        """
        Decorator for handling bot invitations in groups.
        """

        def decorator(func):
            self._handlers["bot_added"].append(Handler(call=func))
            return func

        return decorator

    def on_bot_remove(self):
        """
        Decorator for handling bot kicks from groups.
        """

        def decorator(func):
            self._handlers["bot_removed"].append(Handler(call=func))
            return func

        return decorator

    def on_user_add(self):
        """
        Decorator for handling user joins.
        """

        def decorator(func):
            self._handlers["user_added"].append(Handler(call=func))
            return func

        return decorator

    def on_user_remove(self):
        """
        Decorator for handling user leaves.
        """

        def decorator(func):
            self._handlers["user_removed"].append(Handler(call=func))
            return func

        return decorator

    def on_exception(self):
        """
        Decorator for handling errors in handlers.
        """

        def decorator(func):
            self._handlers["on_exception"].append(Handler(call=func))
            return func

        return decorator

    def on_ready(self):
        """
        Decorator that gets called when the bot session starts.
        """

        def decorator(func):
            self._handlers["on_ready"].append(Handler(call=func))
            return func

        return decorator

    def on_button_callback(
        self, *filters: "Callable | str | None", mode: str = "and"
    ):
        """
        Decorator for receiving button presses.
        """

        def decorator(func):
            new_filter = self.wrap_filters(filters, mode=mode)

            self._handlers["message_callback"].append(
                Handler(
                    call=func,
                    deco_filter=new_filter,
                    router_filters=self.filters["message_callback"],
                )
            )
            return func

        return decorator

    def on_button_chat_create(self):
        """
        Decorator for receiving chat button presses.
        """

        def decorator(func):
            self._handlers["message_chat_created"].append(Handler(call=func))
            return func

        return decorator

    def on_command(
        self,
        name: "str | None" = None,
        aliases: "list[str] | None" = None,
        description: "str | None" = None,
        as_message: bool = False,
    ):
        """
        Decorator for receiving commands.

        :param name: Command name
        :param aliases: List of alternative names for this command
        :param description: Command description that will be uploaded to
            server when bot starts if autosync_commands in Bot is True
        :param as_message: Whether to trigger on_message decorator
            when this command is invoked
        """

        if aliases is None:
            aliases = []

        def decorator(func):
            # command name
            if name is None:
                command_name = func.__name__
            else:
                if " " in name:
                    raise exceptions.AiomaxException(
                        f'Command name "{name}" cannot contain spaces'
                    )

                command_name = name

            check_name = (
                command_name.lower()
                if not self.case_sensitive
                else command_name
            )
            if check_name not in self._commands:
                self._commands[check_name] = []
            self._commands[check_name].append(
                CommandHandler(func, as_message, description)
            )

            # aliases
            for i in aliases:
                if " " in i:
                    raise exceptions.AiomaxException(
                        f'Command alias "{i}" cannot contain spaces'
                    )

                check_name = i.lower() if not self.case_sensitive else i
                if check_name not in self._commands:
                    self._commands[check_name] = []
                self._commands[check_name].append(
                    CommandHandler(func, as_message)
                )
            return func

        return decorator

    # filters

    def add_message_filter(self, filter: "Callable"):
        self.filters["message_created"].append(filter)

    def add_message_edit_filter(self, filter: "Callable"):
        self.filters["message_edited"].append(filter)

    def add_message_delete_filter(self, filter: "Callable"):
        self.filters["message_removed"].append(filter)

    def add_button_callback_filter(self, filter: "Callable"):
        self.filters["message_callback"].append(filter)
