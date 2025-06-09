
from copy import deepcopy
from typing import *
from .types import *
from .cache import *

import logging
bot_logger = logging.getLogger("aiomax.bot")


class Router:
    def __init__(self,
        case_sensitive: bool = True,
    ):
        '''
        Router init
t
        :param case_sensitive: If False the bot will respond to commands regardless of case
        '''
        self._handlers: dict[str, List[Handler]] = {
            'message_created': [],
            'on_ready': [],
            'bot_started': [],
            'message_callback': [],
            'message_chat_created': [],
            'message_edited': [],
            'message_removed': [],
            'chat_title_changed': [],
            'bot_added': [],
            'bot_removed': [],
            'user_added': [],
            'user_removed': []
        } # handlers in this router
        self._commands: dict[str, list] = {} # commands in this router
        self.case_sensitive: bool = case_sensitive
        self.parent = None # Parent bot of this router
        self.routers: List["Router"] = []
        self.filters: Dict[str, List[Callable]] = {
            'message_created': [],
            'message_edited': [],
            'message_removed': [],
            'message_callback': []
        }
        
    @staticmethod
        def wrap_filter(filter_: "Callable | list[Callable] | str | None") -> Callable:
            '''
            Normalize filter to a single callable.
            '''
            if filter_ is None:
                return lambda message: True
    
            if isinstance(filter_, str):
                return lambda message: message.content == filter_
    
            if isinstance(filter_, list):
                def combined_filter(message):
                    return all(f(message) for f in filter_)
                return combined_filter
    
            return filter_

    # routers

    @property
    def handlers(self) -> dict[str, List[Handler]]:
        '''
        Returns all handlers in this and all the child routers.
        '''
        out = deepcopy(self._handlers)

        for router in self.routers:
            for handler_type in out.keys():
                out[handler_type].extend(router.handlers[handler_type])

        return out
    

    @property
    def commands(self) -> dict[str, list]:
        '''
        Returns all commands in this and all the child routers.
        '''
        out = deepcopy(self._commands)
        for router in self.routers:
            out.update(router.commands)
        return out
    

    @property
    def bot(self) -> "Bot":
        '''
        Returns the bot this router is attached to.
        '''
        if self.parent == None:
            return None
        
        if self.parent.parent == None:
            return self.parent
        return self.parent.parent


    def add_router(self, router: "Router"):
        if router.parent != None:
            raise ValueError("Router already has a parent")
        
        router.parent = self
        self.routers.append(router)


    def remove_router(self, router: "Router"):
        if router not in self.routers:
            raise ValueError("Router not found")
        
        router.parent = None
        self.routers.remove(router)


    # decorators

    def on_message(self, filter: "Callable | list[Callable] | str | None" = None):
        '''
        Decorator for receiving messages.
        '''
        def decorator(func):
            new_filter = self.wrap_filter(filter)

            self._handlers["message_created"].append(
                Handler(call=func, deco_filter=new_filter, router_filters=self.filters['message_created'])
            )
            return func
        
        return decorator


    def on_message_edit(self, filter: "Callable | list[Callable] | str | None" = None):
        '''
        Decorator for editing messages.
        '''
        def decorator(func):
            new_filter = self.wrap_filter(filter)

            self._handlers["message_edited"].append(
                Handler(call=func, deco_filter=new_filter, router_filters=self.filters['message_edited'])
            )
            return func
        
        return decorator


    def on_message_delete(self, filter: "Callable | list[Callable] | str | None" = None):
        '''
        Decorator for deleted messages.
        '''
        def decorator(func):
            new_filter = self.wrap_filter(filter)

            self._handlers["message_removed"].append(
                Handler(call=func, deco_filter=new_filter, router_filters=self.filters['message_removed'])
            )
            return func
        
        return decorator


    def on_bot_start(self):
        '''
        Decorator for handling bot start.
        '''
        def decorator(func): 
            self._handlers["bot_started"].append(func)
            return func
        return decorator


    def on_chat_title_change(self):
        '''
        Decorator for handling chat title changes.
        '''
        def decorator(func): 
            self._handlers["chat_title_changed"].append(func)
            return func
        return decorator


    def on_bot_add(self):
        '''
        Decorator for handling bot invitations in groups.
        '''
        def decorator(func): 
            self._handlers["bot_added"].append(func)
            return func
        return decorator


    def on_bot_remove(self):
        '''
        Decorator for handling bot kicks from groups.
        '''
        def decorator(func): 
            self._handlers["bot_removed"].append(func)
            return func
        return decorator


    def on_user_add(self):
        '''
        Decorator for handling user joins.
        '''
        def decorator(func): 
            self._handlers["user_added"].append(func)
            return func
        return decorator


    def on_user_remove(self):
        '''
        Decorator for handling user leaves.
        '''
        def decorator(func): 
            self._handlers["user_removed"].append(func)
            return func
        return decorator
    

    def on_ready(self):
        '''
        Decorator for receiving messages.
        '''
        def decorator(func): 
            self._handlers["on_ready"].append(func)
            return func
        return decorator


    def on_button_callback(self, "Callable | list[Callable] | str | None" = None):
        '''
        Decorator for receiving button presses.
        '''
        def decorator(func): 
            new_filter = self.wrap_filter(filter)

            self._handlers["message_callback"].append(
                Handler(call=func, deco_filter=new_filter, router_filters=self.filters['message_callback'])
            )
            return func
        
        return decorator


    def on_button_chat_create(self):
        '''
        Decorator for receiving button presses.
        '''
        def decorator(func): 
            self._handlers["message_chat_created"].append(func)
            return func
        return decorator
    

    def on_command(self, name: "str | None" = None, aliases: List[str] = []):
        '''
        Decorator for receiving commands.
        '''
        def decorator(func): 
            # command name
            if name is None:
                command_name = func.__name__
            else:
                assert ' ' not in name, 'Command name cannot contain spaces'
                command_name = name
            
            check_name = command_name.lower() if not self.case_sensitive else command_name
            if check_name not in self._commands:
                self._commands[check_name] = []
            self._commands[check_name].append(func)

            # aliases
            for i in aliases:
                assert ' ' not in i, 'Command alias cannot contain spaces'

                check_name = i.lower() if not self.case_sensitive else i
                if check_name not in self._commands:
                    self._commands[check_name] = []
                self._commands[check_name].append(func)
            return func
        return decorator
    

    # filters

    def add_message_filter(self, filter: "Callable"):
        self.filters['message_created'].append(filter)

    def add_message_edit_filter(self, filter: "Callable"):
        self.filters['message_edited'].append(filter)

    def add_message_delete_filter(self, filter: "Callable"):
        self.filters['message_removed'].append(filter)

    def add_button_callback_filter(self, filter: "Callable"):
        self.filters['message_callback'].append(filter)
