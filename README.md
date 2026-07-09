# aiomax

Асинхронное API для работы с мессенджером [Max](https://max.ru).

## Начало работы

[![AUR Version](https://img.shields.io/aur/version/python-aiomax?style=for-the-badge&logo=arch%20linux&logoColor=white)](https://aur.archlinux.org/packages/python-aiomax)

Чтобы установить aiomax, выполните следующую команду:

```bash
pip install aiomax
```

Чтобы установить git-версию aiomax (возможны баги и нестабильность), выполните команду:

```bash
pip install git+https://github.com/dpnspn/aiomax.git
```

> [!IMPORTANT]
> С недавнего времени для подключения к серверам Max нужен [сертификат Минцифры](https://www.gosuslugi.ru/crt).
> Если у вас не установлен сертификат, при создании класса бота можно указать параметр `use_certificate=True` - тогда aiomax будет использовать встроенный сертификат Минцифры.

> [!WARNING]
> При использовании сертификатов Минцифры государство Российской Федерации может получать доступ ко всему отправляемому трафику.
> Рекомендуется не использовать сессию бота для отправки конфиденциальных данных при установленном `use_certificate=True`.

Документация и примеры ботов [тут](https://github.com/dpnspn/aiomax/wiki)

## Aiomax Community

Обсудить aiomax / задать вопрос можно в сети чатов Aiomax Community
[Telegram](https://t.me/aiomax_chat) / [Max](https://max.ru/join/45DmBRwDNvcZVqYvf_cSCPu-_DuvYa5VmuQ4K2cmC_Q)

Новости о aiomax и Max Bot API выходят на телеграм канале [Aiomax Changelog](https://t.me/aiomax_cl)
