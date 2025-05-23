# Фильтры

Фильтры - функции, которые помогают фильтровать ивенты, полученные через некоторые декораторы.

## Встроенные фильтры

В подмодуле `aiomax.filters` есть несколько встроенных фильтров.

Пример использования встроенного фильтра (в данном случае `aiomax.filters.startswith`):

```py
@bot.on_message(aiomax.filters.startswith('папайя'))
async def dialog(message: aiomax.Message):
    pass # Содержимое функции
```

### `aiomax.filters.equals(content: str)`

Фильтр проверяет, чтобы контент был равен данной строке.

Поддерживает `Bot.on_message` и `Bot.on_button_callback`.

- `content` - строка, с которой нужно сравнить контент

### `aiomax.filters.has(content: str)`

Фильтр проверяет, чтобы контент содержал в себе данную строку.

Поддерживает `Bot.on_message` и `Bot.on_button_callback`.

- `content` - строка, которая должна содержаться в контенте

### `aiomax.filters.startswith(prefix: str)`

Фильтр проверяет, чтобы контент начинался с определенного префикса.

Поддерживает `Bot.on_message` и `Bot.on_button_callback`.

- `prefix` - строка, с которой должен начинаться контент

### `aiomax.filters.endswith(suffix: str)`

Фильтр проверяет, чтобы контент заканчивался на определенный суффикс.

Поддерживает `Bot.on_message` и `Bot.on_button_callback`.

- `suffix` - строка, на которую должен заканчиваться контент

### `aiomax.filters.regex(pattern: str)`

Фильтр проверяет, чтобы контент соответствовал регулярному выражению.

Поддерживает `Bot.on_message` и `Bot.on_button_callback`.

- `pattern` - регулярное выражение

### `aiomax.filters.papaya`

Проверяет, является ли предпоследнее слово в сообщении "папайя".

Вызывать фильтр не нужно.

Поддерживает `Bot.on_message` и `Bot.on_button_callback`.

## Написание собственных фильтров

При написании собственных фильтров у вас есть 3 варианта:

### lambda-выражения

Самый короткий вариант, для небольших фильтров. Пишется чаще всего в одну строку.

Пример для проверки на то, что сообщение отправлено в ЛС боту:

```py
@bot.on_message(lambda message: message.recipient.chat_type == 'dialog')
async def dialog(message: aiomax.Message):
    pass # Содержимое функции
```

### Функции

Использование функций через `def` занимает больше места, но помогает избежать повторов кода, если один и тот же фильтр используется несколько раз.

Пример для проверки на то, что сообщение отправлено в ЛС боту:

```py
def in_dialog(message: aiomax.Message):
    return message.recipient.chat_type == 'dialog'

@bot.on_message(in_dialog) # Обратите внимание, что вызывать функцию не нужно!
async def dialog(message: aiomax.Message):
    pass # Содержимое функции
```

### Классы

Классы используются для более сложных фильтров, принимающих различные аргументы.

Пример фильтра, принимающего тип чата и проверяющего, что сообщение отправлено именно в чате этого типа:

```py
class ChatTypeFilter:
    def __init__(self, chat_type):
        self.chat_type = chat_type

    def __call__(self, message: aiomax.Message):
        return message.recipient.chat_type == self.chat_type

@bot.on_message(ChatTypeFilter('dialog'))
async def dialog(message: aiomax.Message):
    pass # Содержимое функции
```
