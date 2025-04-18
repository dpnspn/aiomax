import asyncio
from typing import *
import aiohttp

from .utils import get_message_body
from .classes import *
from json import JSONDecodeError

import logging
bot_logger = logging.getLogger("aiomax.bot")

class Bot:
    def __init__(self,
        access_token: str,
        command_prefixes: "str | List[str]" = "/",
        mention_prefix: bool = True,
        case_sensitive: bool = True,
        default_format: "Literal['markdown', 'html'] | None" = None
    ):
        '''
        Bot init
        '''
        self.access_token: str = access_token
        self.session = None
        self.polling = False
        self.handlers: dict[str, List[Handler]] = {
            'message_created': [],
            'on_ready': [],
            'bot_started': [],
            'message_callback': []
        }
        self.commands: dict[str, list] = {}
        self.command_prefixes: "str | List[str]" = command_prefixes
        self.mention_prefix: bool = mention_prefix
        self.case_sensitive: bool = case_sensitive
        self.default_format: "str | None" = default_format
        
        self.id: "int | None" = None
        self.username: "str | None" = None
        self.name: "str | None" = None
        self.description: "str | None" = None
        self.bot_commands: List[BotCommand] = None
    

    async def get(self, *args, **kwargs):
        '''
        Sends a GET request to the API.
        '''
        if self.session == None:
            raise Exception("Session is not initialized")
        
        params = kwargs.get('params', {})
        params['access_token'] = self.access_token
        if 'params' in kwargs:
            del kwargs['params']
        return await self.session.get(*args, params=params, **kwargs)
    
    
    async def post(self, *args, **kwargs):
        '''
        Sends a POST request to the API.
        '''
        if self.session == None:
            raise Exception("Session is not initialized")
        
        params = kwargs.get('params', {})
        params['access_token'] = self.access_token
        if 'params' in kwargs:
            del kwargs['params']
        return await self.session.post(*args, params=params, **kwargs)
    
    
    async def patch(self, *args, **kwargs):
        '''
        Sends a PATCH request to the API.
        '''
        if self.session == None:
            raise Exception("Session is not initialized")
        
        params = kwargs.get('params', {})
        params['access_token'] = self.access_token
        if 'params' in kwargs:
            del kwargs['params']
        return await self.session.patch(*args, params=params, **kwargs)
    
    
    async def put(self, *args, **kwargs):
        '''
        Sends a PUT request to the API.
        '''
        if self.session == None:
            raise Exception("Session is not initialized")
        
        params = kwargs.get('params', {})
        params['access_token'] = self.access_token
        if 'params' in kwargs:
            del kwargs['params']
        return await self.session.put(*args, params=params, **kwargs)
    
    
    async def delete(self, *args, **kwargs):
        '''
        Sends a DELETE request to the API.
        '''
        if self.session == None:
            raise Exception("Session is not initialized")
        
        params = kwargs.get('params', {})
        params['access_token'] = self.access_token
        if 'params' in kwargs:
            del kwargs['params']
        return await self.session.delete(*args, params=params, **kwargs)
    

    # decorators

    def on_message(self, filter: "Callable | str | None" = None):
        '''
        Decorator for receiving messages.
        '''
        def decorator(func):
            new_filter = filter
            if isinstance(filter, str):
                new_filter = lambda message: message.body.text == filter
            self.handlers["message_created"].append(Handler(call=func, filter=new_filter))
            return func
        return decorator


    def on_bot_start(self):
        '''
        Decorator for handling bot start.
        '''
        def decorator(func): 
            self.handlers["bot_started"].append(func)
            return func
        return decorator
    

    def on_ready(self):
        '''
        Decorator for receiving messages.
        '''
        def decorator(func): 
            self.handlers["on_ready"].append(func)
            return func
        return decorator


    def on_button_callback(self, filter: "Callable | None" = None):
        '''
        Decorator for receiving button presses.
        '''
        def decorator(func): 
            self.handlers["message_callback"].append(Handler(call=func, filter=filter))
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
            if check_name not in self.commands:
                self.commands[check_name] = []
            self.commands[check_name].append(func)

            # aliases
            for i in aliases:
                assert ' ' not in i, 'Command alias cannot contain spaces'

                check_name = i.lower() if not self.case_sensitive else i
                if check_name not in self.commands:
                    self.commands[check_name] = []
                self.commands[check_name].append(func)
            return func
        return decorator
        

    # send requests

    async def get_me(self) -> User:
        '''
        Returns info about the bot.
        '''
        response = await self.get(f"https://botapi.max.ru/me")
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
        commands: "List[BotCommand] | None" = None,
        photo: "PhotoAttachmentRequestPayload | None" = None
    ) -> User:
        '''
        Allows you to change info about the bot. Fill in only the fields that
        need to be updated.
        
        :param name: Bot display name
        :param description: Bot description
        :param commands: Commands supported by the bot. To remove all commands,
        pass an empty list.
        :param photo: Bot profile picture
        '''
        if commands:
            commands = [i.as_dict() for i in commands]   
        if photo:
            photo = photo.as_dict()
        
        payload = {
            "name": name,
            "description": description,
            "commands": commands,
            "photo": photo
        }
        payload = {k: v for k, v in payload.items() if v}

        response = await self.patch(f"https://botapi.max.ru/me", json=payload)
        data = await response.json()

        if response.status != 200:
            raise Exception(data['message'])
    
        # caching info
        if name:
            self.name = name
        if commands:
            self.bot_commands = commands
        if description:
            self.description = description
        
        if response.status == 200:
            return User.from_json(data)
        else:
            bot_logger.error(f"Failed to update bot info: {data}. ")
    
    
    async def get_chats(self, count: "int | None" = None, marker: "int | None" = None) -> List[Chat]:
        '''
        Returns the chats the bot is in.
        The result includes a list of chats and a marker for moving to the next page.

        :param count:  Number of chats requested. 50 by default
        :param marker: Pointer to the next page of data. Defaults to first page
        '''
        params = {
            "count": count,
            "marker": marker,
        }
        params = {k: v for k, v in params.items() if v}

        response = await self.get("https://botapi.max.ru/chats", params=params)
        data = await response.json()
        chats = [Chat.from_json(i) for i in data['chats']]

        return chats
    

    async def chat_by_link(self, link: str) -> Chat:
        '''
        Returns chat by a link or username.
 
        :param link: Public chat link or username.
        '''
        response = await self.get(f"https://botapi.max.ru/chats/{link}")
        json = await response.json()

        return Chat.from_json(json)
    
    
    async def get_chat(self, chat_id: int) -> Chat:
        '''
        Returns information about a chat.

        :param chat_id: The ID of the chat.
        '''
        response = await self.get(f"https://botapi.max.ru/chats/{chat_id}")
        json = await response.json()

        return Chat.from_json(json)
    
    
    async def get_pin(self, chat_id: int) -> "Message | None":
        '''
        Returns pinned message in the chat as ``. None if there is no pinned message

        :param chat_id: The ID of the chat.
        '''
        response = await self.get(f"https://botapi.max.ru/chats/{chat_id}/pin")
        json = await response.json()

        if json['message'] == None:
            return None

        return Message.from_json(json)


    async def pin(self,
        chat_id: int,
        message_id: str,
        notify: bool | None = None
    ):
        '''
        Pin a message in a chat

        :param chat_id: The ID of the chat.
        :param message_id: The ID of the message to pin.
        :param notify: Whether to notify users about the pin. True by default.
        '''
        payload = {
            "message_id": message_id,
            "notify": notify
        }
        payload = {k: v for k, v in payload.items() if v}

        response = await self.put(
            f"https://botapi.max.ru/chats/{chat_id}/pin", json=payload
        )
        return await response.json()


    async def delete_pin(self, chat_id: int):
        '''
        Delete pinned message in the chat

        :param chat_id: The ID of the chat.
        '''
        response = await self.delete(f"https://botapi.max.ru/chats/{chat_id}/pin")

        return await response.json()
    
    
    async def my_membership(self, chat_id: int) -> User:
        '''
        Returns information about the bot's membership in the chat.

        :param chat_id: The ID of the chat.
        '''
        response = await self.get(f"https://botapi.max.ru/chats/{chat_id}/members/me")
        json = await response.json()

        return User.from_json(json)


    async def leave_chat(self, chat_id: int):
        '''
        Remove the bot from the chat.

        :param chat_id: The ID of the chat.
        '''
        response = await self.delete(f"https://botapi.max.ru/chats/{chat_id}/members/me")

        return await response.json()


    async def get_admins(self, chat_id: int) -> List[User]:
        '''
        Returns a list of administrators in the chat.

        :param chat_id: The ID of the chat.
        '''
        response = await self.get(f"https://botapi.max.ru/chats/{chat_id}/members/admins")

        users = [User.from_json(i) for i in (await response.json())['members']]

        return users
    

    async def get_members(self, chat_id: int) -> List[User]:
        '''
        Returns a list of members in the chat.

        :param chat_id: The ID of the chat.
        '''

        response = await self.get(f"https://botapi.max.ru/chats/{chat_id}/members")

        users = [User.from_json(i) for i in (await response.json())['members']]

        return users
    
    
    async def add_members(self,
        chat_id: int,
        users: List[int]
    ):
        '''
        Adds users to the chat.

        :param chat_id: The ID of the chat.
        :param users: List of user IDs to add.
        '''

        response = await self.post(f"https://botapi.max.ru/chats/{chat_id}/members", json={"user_ids": users})

        return await response.json()
  

    async def kick_member(
        self,
        chat_id: int,
        user_id: int,
        block: "bool | None" = None
    ):
        '''
        Removes a user from the chat.

        :param chat_id: The ID of the chat.
        :param user_id: The ID of the user to remove.
        :param block: Whether to block the user. Ignored by default.
        '''

        params = {
            "chat_id": chat_id,
            "user_id": user_id,
            "block": block
        }
        params = {k: v for k, v in params.items() if v}
        
        if block != None:
            params["block"] = str(block)

        response = await self.delete(f"https://botapi.max.ru/chats/{chat_id}/members/", params=params)

        return await response.json()
    

    async def patch_chat(self,
        chat_id: int,
        icon: PhotoAttachmentRequestPayload | None = None,
        title: str | None = None,
        pin: str | None = None,
        notify: bool | None = None
    ) -> Chat:
        '''
        Allows you to edit chat information, like the name,
        icon and pinned message.

        :param chat_id: ID of the chat to change
        :param icon: Chat picture
        :param title: Chat name. From 1 to 200 characters
        :param pin: ID of the message to pin
        :param notify: Whether to notify users about the edit. True by default.
        '''

        payload = {
            "icon": icon,
            "title": title,
            "pin": pin,
            "notify": notify
        }
        payload = {k: v for k, v in payload.items() if v}

        response = await self.patch(
            f"https://botapi.max.ru/chats/{chat_id}", json=payload
        )
        json = await response.json()

        return Chat.from_json(json)
    

    async def post_action(self, chat_id: int, action: str):
        '''
        Allows you to show a badge about performing an action in a chat, like
        "typing". Also allows for marking messages as read.
        
        :param chat_id: ID of the chat to do the action in
        :param action: Constant from aiomax.types.Actions
        '''

        response = await self.post(f"https://botapi.max.ru/chats/{chat_id}/actions", json={"action": action})

        return await response.json()
    

    async def upload(self, data: IO | str, type: str) -> dict:
        '''
        Uploads a file to the server.

        :param data: File-like object or path to the file
        :param type: File type
        '''

        if isinstance(data, str):
            data = open(data, 'rb')
        
        form = aiohttp.FormData()
        form.add_field('data', data)
        url_resp = await self.post('https://botapi.max.ru/uploads', params={"type": type})
        url_json = await url_resp.json()
        token_resp = await self.session.post(url_json['url'], data=form)
        if type in {'audio', 'video'}:
            return url_json
        token_json = await token_resp.json()

        return token_json
    

    async def upload_image(self, data: BinaryIO | str):
        raw_photo = await self.upload(data, 'image')
        token = list(raw_photo['photos'].values())[0]['token']
        return PhotoAttachment(PhotoPayload(token=token))
    

    async def upload_video(self, data: BinaryIO | str):
        raw_video = await self.upload(data, 'video')
        token = raw_video['token']
        return VideoAttachment(MediaPayload(token=token))
    

    async def upload_audio(self, data: BinaryIO | str):
        raw_audio = await self.upload(data, 'audio')
        token = raw_audio['token']
        return AudioAttachment(MediaPayload(token=token))
    

    async def upload_file(self, data: IO | str):
        raw_file = await self.upload(data, 'file')
        token = raw_file['token']
        return FileAttachment(MediaPayload(token=token))


    async def send_message(self,
        text: str,
        chat_id: "int | None" = None,
        user_id: "int | None" = None,
        format: "Literal['markdown', 'html', 'default'] | None" = 'default',
        reply_to: "int | None" = None,
        notify: bool = True,
        disable_link_preview: bool = False,
        keyboard: "List[List[buttons.Button]] | None | buttons.KeyboardBuilder" = None,
        attachments: "list[Attachment] | None" = None
    ) -> Message:
        '''
        Allows you to send a message to a user or in a chat.
        
        :param text: Message text. Up to 4000 characters
        :param chat_id: Chat ID to send the message in.
        :param user_id: User ID to send the message to.
        :param format: Message format. Bot.default_format by default
        :param reply_to: ID of the message to reply to. Optional
        :param notify: Whether to notify users about the message. True by default.
        :param disable_link_preview: Whether to disable link embedding in messages. True by default
        :param keyboard: An inline keyboard to attach to the message
        :param attachments: List of attachments
        '''
        # error checking
        text = str(text)
        assert len(text) < 4000, "Message must be less than 4000 characters"
        assert chat_id or user_id, "Either chat_id or user_id must be provided"
        assert not (chat_id and user_id), "Both chat_id and user_id cannot be provided"

        # sending
        params = {
            "chat_id": chat_id,
            "user_id": user_id,
            "disable_link_preview": str(disable_link_preview).lower()
        }
        params = {k: v for k, v in params.items() if v}

        if format == 'default':
            format = self.default_format

        body = get_message_body(text, format, reply_to, notify, keyboard, attachments)

        response = await self.post(
            f"https://botapi.max.ru/messages", params=params, json=body
        )
        if response.status != 200:
            exception = Exception(await response.text())
            retry = False
            try:
                err_json = await response.json()
                if err_json['code'] == 'attachment.not.ready':
                    retry = True
            except:
                raise exception
            if retry:
                await asyncio.sleep(1)
                return await self.send_message(text=text, chat_id=chat_id, user_id=user_id, format=format, reply_to=reply_to, notify=notify, disable_link_preview=disable_link_preview, attachments=attachments)
            else:
                raise exception
        
        json = await response.json()
        return Message.from_json(json['message'])


    async def reply(self,
        text: str,
        message: Message,
        format: "Literal['markdown', 'html', 'default'] | None" = 'default',
        notify: bool = True,
        disable_link_preview: bool = False,
        keyboard: "List[List[buttons.Button]] | None" = None,
        attachments: "list[Attachment] | None" = None
    ) -> Message:
        '''
        Allows you to reply to a message easily.
        
        :param text: Message text. Up to 4000 characters
        :param message: Message to reply to
        :param format: Message format. Bot.default_format by default
        :param notify: Whether to notify users about the message. True by default.
        :param disable_link_preview: Whether to disable link embedding in messages. True by default
        :param keyboard: An inline keyboard to attach to the message
        :param attachments: List of attachments
        '''
        return await self.send_message(
            text, message.recipient.chat_id, format=format,
            reply_to=message.body.message_id, notify=notify,
            disable_link_preview=disable_link_preview, keyboard=keyboard, attachments=attachments
        )


    async def edit_message(self,
        message_id: int,
        text: str,
        format: "Literal['markdown', 'html', 'default'] | None" = 'default',
        reply_to: "int | None" = None,
        notify: bool = True,
        keyboard: "List[List[buttons.Button]] | None" = None,
        # todo attachments
    ) -> Message:
        '''
        Allows you to edit a message.
        
        :param message_id: ID of the message to edit
        :param text: Message text. Up to 4000 characters
        :param format: Message format. Bot.default_format by default
        :param reply_to: ID of the message to reply to. Optional
        :param notify: Whether to notify users about the message. True by default.
        :param keyboard: An inline keyboard to attach to the message
        '''
        # error checking
        assert len(text) < 4000, "Message must be less than 4000 characters"

        # editing
        params = {
            "message_id": message_id
        }
        if format == 'default':
            format = self.default_format
            
        body = get_message_body(text, format, reply_to, notify, keyboard)

        response = await self.put(
            f"https://botapi.max.ru/messages", params=params, json=body
        )
        if response.status != 200:
            raise Exception(await response.text())
        
        json = await response.json()
        if not json['success']:
            raise Exception(json['message'])


    async def delete_message(self,
        message_id: int
    ):
        '''
        Allows you to delete a message in chat.
        
        :param message_id: ID of the message to delete
        '''
        # editing
        params = {
            "message_id": message_id
        }

        response = await self.delete(
            f"https://botapi.max.ru/messages", params=params
        )
        if response.status != 200:
            raise Exception(await response.text())
        
        json = await response.json()
        if not json['success']:
            raise Exception(json['message'])


    # async def get_message(self,
    #     message_id: int
    # ) -> Message:
    #     '''
    #     Allows you to fetch message's info.
        
    #     :param message_id: ID of the message to get info of
    #     '''
    #     assert message_id.startswith('mid.'), "Message ID invalid"

    #     message_id = message_id[4:]

    #     # editing
    #     response = await self.get(
    #         f"https://botapi.max.ru/messages/{message_id}"
    #     )
    #     if response.status != 200:
    #         raise Exception(await response.text())
        
    #     return Message.from_json(await response.json())
    # todo fix - for some reason API replies with "invalid message_id"


    async def get_updates(self, limit: int = 100, marker: "int | None" = None) -> tuple[int, dict]:
        '''
        Get bot updates / events. If `marker` is provided, will return updates
        newer than it. If not, will return all updates since last time this was called.
        
        :param marker: Pointer to the next page of data.
        '''
        payload = {
            "limit": limit,
            "marker": marker
        }
        payload = {k: v for k, v in payload.items() if v}

        response = await self.get(
            f"https://botapi.max.ru/updates", params=payload
        )

        return await response.json()
    

    async def handle_update(self, update: dict):
        '''
        Handles an update.
        '''
        update_type = update['update_type']


        if update_type == "message_created":
            message = Message.from_json(update["message"])
            message.bot = self
            message.user_locale = update.get('user_locale', None)
            HANDLED = False

            for handler in self.handlers['message_created']:
                if handler.filter:
                    if handler.filter(message):
                        await handler.call(message)
                        HANDLED = True
                else:
                    await handler.call(message)
                    HANDLED = True
            
            # handle logs
            if HANDLED:
                bot_logger.debug(f"Message \"{message.body.text}\" handled")
            else:
                bot_logger.debug(f"Message \"{message.body.text}\" not handled")

            # handling commands
            prefixes = self.command_prefixes if type(self.command_prefixes) != str\
                else [self.command_prefixes]
            prefixes = list(prefixes)
            HANDLED = False

            if self.mention_prefix:
                prefixes.extend([f'@{self.username} {i}' for i in prefixes])

            for prefix in prefixes:
                if len(message.body.text) <= len(prefix):
                    continue

                prefix = prefix if self.case_sensitive else prefix.lower()
                if not message.body.text.startswith(prefix):
                    continue

                command = message.body.text[len(prefix):]
                name = command.split()[0]
                check_name = name if self.case_sensitive else name.lower()
                args = ' '.join(command.split()[1:])
                
                if check_name not in self.commands:
                    bot_logger.debug(f"Command \"{name}\" not handled")
                    return

                if len(self.commands[check_name]) == 0:
                    bot_logger.debug(f"Command \"{name}\" not handled")
                    return

                for i in self.commands[check_name]:
                    await i(CommandContext(
                        self, message, name, args
                    ))

                bot_logger.debug(f"Command \"{name}\" handled")
                return
                
                
        if update_type == 'bot_started':
            payload = BotStartPayload.from_json(update)
            bot_logger.debug(f"User \"{payload.user!r}\" started bot")

            for i in self.handlers[update_type]:
                await i(payload)

                
        if update_type == 'message_callback':
            HANDLED = False

            callback = Callback.from_json(
                update['callback'], update.get('user_locale', None), self
            )

            for handler in self.handlers[update_type]:     
                if handler.filter:
                    if handler.filter(callback):
                        await handler.call(callback)
                        HANDLED = True
                else:
                    await handler.call(callback)
                    HANDLED = True
                
            if HANDLED:
                bot_logger.debug(f"Callback \"{callback.payload}\" handled")
            else:
                bot_logger.debug(f"Callback \"{callback.payload}\" not handled")

    async def start_polling(self):
        '''
        Starts polling.
        '''
        self.polling = True

        async with aiohttp.ClientSession() as session:
            self.session = session

            # self info (this will cache the info automatically)
            await self.get_me()

            bot_logger.info(f"Started polling with bot @{self.username} ({self.id}) - {self.name}")

            # ready event
            for i in self.handlers['on_ready']:
                await i()

            while self.polling:
                try:
                    updates = await self.get_updates()
                    
                    for update in updates["updates"]:
                        await self.handle_update(update)

                except Exception as e:
                    bot_logger.error(f"Error while handling updates: {e}")
                    await asyncio.sleep(3)

        self.session = None
        self.polling = False

    def run(self):
        '''
        Shortcut for `asyncio.run(bot.start_polling())`
        '''
        asyncio.run(self.start_polling())