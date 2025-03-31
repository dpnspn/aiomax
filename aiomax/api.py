import asyncio
from typing import *
import aiohttp
from .classes import *

import logging
bot_logger = logging.getLogger("aiomax.bot")

class Bot:
    def __init__(self,
        access_token: str,
        command_prefixes: "str | list[str]" = "/",
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
        self.handlers: dict[str, list] = {
            'message_created': [],
            'on_ready': [],
            'bot_started': []
        }
        self.commands: dict[str, list] = {}
        self.command_prefixes: "str | list[str]" = command_prefixes
        self.mention_prefix: bool = mention_prefix
        self.case_sensitive: bool = case_sensitive
        self.default_format: "str | None" = default_format
        
        self.id: "int | None" = None
        self.username: "str | None" = None
        self.name: "str | None" = None
        self.description: "str | None" = None
        self.bot_commands: list[BotCommand] = None
    

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

    def on_message(self):
        '''
        Decorator for receiving messages.
        '''
        def decorator(func): 
            self.handlers["message_created"].append(func)
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
    

    def on_command(self, name: str, aliases: list[str] = []):
        '''
        Decorator for receiving commands.
        '''
        def decorator(func): 
            # command name
            assert ' ' not in name, 'Command name cannot contain spaces'

            check_name = name.lower() if not self.case_sensitive else name
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
        commands: "list[BotCommand] | None" = None,
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
    
    
    async def get_chats(self, count: "int | None" = None, marker: "int | None" = None):
        '''
        Returns information about the chats the bot is in.
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

        return await response.json()
    
    
    async def get_chat(self, chatId: int):
        '''
        Returns information about a chat.

        :param chatId: The ID of the chat.
        '''
        response = await self.get(f"https://botapi.max.ru/chats/{chatId}")

        return await response.json()
    
    async def get_pin(
            self,
            chatId: int
    ):
        '''
        Returns pinned message in the chat. None if there is no pinned message

        :param chatId: The ID of the chat.
        '''

        response = await self.get(f"https://botapi.max.ru/chats/{chatId}/pin")

        return await response.json()

    async def pin(
            self,
            chatId: int,
            message_id: str,
            notify: bool | None = None
    ):
        '''
        Pin a message in a chat

        :param chatId: The ID of the chat.
        :param message_id: The ID of the message to pin.
        :param notify: Whether to notify users about the pin. True by default.
        '''

        payload = {
            "message_id": message_id,
            "notify": notify
        }
        payload = {k: v for k, v in payload.items() if v}

        response = await self.put(
            f"https://botapi.max.ru/chats/{chatId}/pin", json=payload
        )
        return await response.json()

    async def patch_chat(
        self,
        chatId: int,
        icon: PhotoAttachmentRequestPayload | None = None,
        title: str | None = None,
        pin: str | None = None,
        notify: bool | None = None
    ):
        '''
        Allows you to edit chat information, like the name,
        icon and pinned message.

        :param chatId: ID of the chat to change
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
            f"https://botapi.max.ru/chats/{chatId}", json=payload
        )
        return await response.json()


    async def post_action(self, chatId: int, action: str):
        '''
        Allows you to show a badge about performing an action in a chat, like
        "typing". Also allows for marking messages as read.
        
        :param chatId: ID of the chat to do the action in
        :param action: Constant from aiomax.types.Actions
        '''

        response = await self.post(f"https://botapi.max.ru/chats/{chatId}/actions", json={"action": action})

        return await response.json()
    

    async def upload(self, data: IO | str, type: str):
        '''
        Uploads a file to the server.

        :param data: File-like object or path to the file
        :param type: File type
        '''

        if isinstance(data, str):
            data = open(data, 'rb')
        
        url_resp = await self.post('https://botapi.max.ru/uploads', params={"type": type})
        url_json = await url_resp.json()
        print(url_json)
        token_resp = await self.session.post(url_json['url'], data={'data': data}, headers={'Content-Type': 'multipart/form-data'})
        token_json = await token_resp.json()

        try:
            return token_json['token']
        except:
            print(token_resp.status)
            print(token_json)
    

    async def upload_image(self, data: BinaryIO | str):
        token = await self.upload(data, 'image')
        return PhotoAttachment(PhotoPayload(token=token))
    

    async def upload_video(self, data: BinaryIO | str):
        token = await self.upload(data, 'video')
        return VideoAttachment(MediaPayload(token=token))
    

    async def upload_audio(self, data: BinaryIO | str):
        token = await self.upload(data, 'audio')
        return AudioAttachment(MediaPayload(token=token))
    

    async def upload_file(self, data: IO | str):
        token = await self.upload(data, 'file')
        return FileAttachment(MediaPayload(token=token))


    async def send_message(self,
        text: str,
        chatId: "int | None" = None,
        userId: "int | None" = None,
        format: "Literal['markdown', 'html', 'default'] | None" = 'default',
        reply_to: "int | None" = None,
        notify: bool = True,
        disable_link_preview: bool = False,
        attachments: "list[Attachment] | None" = None
    ) -> Message:
        '''
        Allows you to send a message to a user or in a chat.
        
        :param text: Message text. Up to 4000 characters
        :param chatId: Chat ID to send the message in.
        :param userId: User ID to send the message to.
        :param format: Message format. Bot.default_format by default
        :param reply_to: ID of the message to reply to. Optional
        :param notify: Whether to notify users about the message. True by default.
        :param disable_link_preview: Whether to disable link embedding in messages. True by default
        :param attachments: List of attachments. Optional
        '''
        # error checking
        assert len(text) < 4000, "Message must be less than 4000 characters"
        assert chatId or userId, "Either chatId or userId must be provided"
        assert not (chatId and userId), "Both chatId and userId cannot be provided"
        for i, at in enumerate(attachments or []):
            # todo: implement all attachment types in https://github.com/max-messenger/max-bot-api-client-ts/blob/main/examples/attachments-bot.ts
            assert hasattr(at, 'as_dict'), 'Attachment must be an image, a video, an audio or a file'
            attachments[i] = at.as_dict()

        # sending
        params = {
            "chat_id": chatId,
            "user_id": userId,
            "disable_link_preview": str(disable_link_preview).lower()
        }
        if format == 'default':
            format = self.default_format
        body = {
            "text": text,
            "format": format,
            "notify": notify,
            "attachments": attachments
        }
        params = {k: v for k, v in params.items() if v}

        # replying
        if reply_to:
            body['link'] = {
                "type": 'reply',
                "mid": reply_to
            }

        response = await self.post(
            f"https://botapi.max.ru/messages", params=params, json=body
        )
        if response.status != 200:
            raise Exception(await response.text())
        
        json = await response.json()
        return Message.from_json(json['message'])


    async def reply(self,
        text: str,
        message: Message,
        format: "Literal['markdown', 'html', 'default'] | None" = 'default',
        notify: bool = True,
        disable_link_preview: bool = False
        # todo attachments
    ) -> Message:
        '''
        Allows you to reply to a message easily.
        
        :param text: Message text. Up to 4000 characters
        :param message: Message to reply to
        :param format: Message format. Bot.default_format by default
        :param notify: Whether to notify users about the message. True by default.
        :param disable_link_preview: Whether to disable link embedding in messages. True by default
        '''
        return await self.send_message(
            text, message.recipient.chat_id, format=format,
            reply_to=message.body.message_id, notify=notify,
            disable_link_preview=disable_link_preview
        )


    async def edit_message(self,
        messageId: int,
        text: str,
        format: "Literal['markdown', 'html', 'default'] | None" = 'default',
        reply_to: "int | None" = None,
        notify: bool = True,
        # todo attachments
    ) -> Message:
        '''
        Allows you to edit a message.
        
        :param messageId: ID of the message to edit
        :param text: Message text. Up to 4000 characters
        :param format: Message format. Bot.default_format by default
        :param reply_to: ID of the message to reply to. Optional
        :param notify: Whether to notify users about the message. True by default.
        '''
        # error checking
        assert len(text) < 4000, "Message must be less than 4000 characters"

        # editing
        params = {
            "message_id": messageId
        }
        if format == 'default':
            format = self.default_format
        body = {
            "text": text,
            "format": format,
            "notify": notify
        }

        # replying
        if reply_to:
            body['link'] = {
                "type": 'reply',
                "mid": reply_to
            }

        response = await self.put(
            f"https://botapi.max.ru/messages", params=params, json=body
        )
        if response.status != 200:
            raise Exception(await response.text())
        
        json = await response.json()
        if not json['success']:
            raise Exception(json['message'])


    async def delete_message(self,
        messageId: int
    ) -> Message:
        '''
        Allows you to delete a message in chat.
        
        :param messageId: ID of the message to delete
        '''
        # editing
        params = {
            "message_id": messageId
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
    #     messageId: int
    # ) -> Message:
    #     '''
    #     Allows you to fetch message's info.
        
    #     :param messageId: ID of the message to get info of
    #     '''
    #     assert messageId.startswith('mid.'), "Message ID invalid"

    #     messageId = messageId[4:]

    #     # editing
    #     response = await self.get(
    #         f"https://botapi.max.ru/messages/{messageId}"
    #     )
    #     if response.status != 200:
    #         raise Exception(await response.text())
        
    #     return Message.from_json(await response.json())
    # fix - for some reason API replies with "invalid message_id"


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
            message.user_locale = update.get('user_locale', None)

            for i in self.handlers[update_type]:
                await i(message)

            # handling commands
            prefixes = self.command_prefixes if type(self.command_prefixes) != str\
                else [self.command_prefixes]
            prefixes = list(prefixes)

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
                    continue
                
                for i in self.commands[check_name]:
                    await i(CommandContext(
                        self, message, name, args
                    ))
                    return
                
        if update_type == 'bot_started':
            for i in self.handlers[update_type]:
                await i(BotStartPayload.from_json(update))
    

    async def start_polling(self):
        '''
        Starts polling.

        Cannot be called twice.
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