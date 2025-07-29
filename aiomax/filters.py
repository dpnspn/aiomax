import re

from . import exceptions


def normalize_filter(filter_):
    if isinstance(filter_, str):
        return EqualsFilter(filter_)

    elif isinstance(filter_, bool):
        return lambda _: filter_

    elif callable(filter_):
        return filter_

    raise ValueError(f"Unsupported filter type: {type(filter_)}")


class BaseFilter:
    """
    Superclass of other filters for support of bit-wise or and bit-wise and
    """

    def __or__(self, other):
        return _OrFilter(self, other)

    def __and__(self, other):
        return _AndFilter(self, other)


class _OrFilter(BaseFilter):
    """
    Class for using bit-wise or on filters
    """

    def __init__(self, filter1, filter2):
        self.filter1 = normalize_filter(filter1)
        self.filter2 = normalize_filter(filter2)

    def __call__(self, obj: any):
        return self.filter1(obj) or self.filter2(obj)


class _AndFilter(BaseFilter):
    """
    Class for using bit-wise and on filters
    """

    def __init__(self, filter1, filter2):
        self.filter1 = normalize_filter(filter1)
        self.filter2 = normalize_filter(filter2)

    def __call__(self, obj: any):
        return self.filter1(obj) and self.filter2(obj)


class EqualsFilter(BaseFilter):
    def __init__(self, content: str):
        """
        :param content: Content to check

        Checks if the content equals to the given string
        """
        self.content = content

    def __call__(self, obj: any):
        if hasattr(obj, "content"):
            return obj.content == self.content
        else:
            raise Exception(f"Class {type(object).__name__} has no content")


class HasFilter(BaseFilter):
    def __init__(self, content: str):
        """
        :param content: Content to check

        Checks if the content has the given string
        """
        self.content = content

    def __call__(self, obj: any):
        if hasattr(obj, "content"):
            return self.content in obj.content
        else:
            raise Exception(f"Class {type(object).__name__} has no content")


class StartsWithFilter(BaseFilter):
    def __init__(self, prefix: str):
        """
        :param prefix: Prefix to check

        Checks if the content starts with the given prefix
        """
        self.prefix = prefix

    def __call__(self, obj: any):
        if hasattr(obj, "content"):
            return obj.content.startswith(self.prefix)
        else:
            raise Exception(f"Class {type(object).__name__} has no content")


class EndsWithFilter(BaseFilter):
    def __init__(self, suffix: str):
        """
        :param suffix: Suffix to check

        Checks if the content ends with the given suffix
        """
        self.suffix = suffix

    def __call__(self, obj: any):
        if hasattr(obj, "content"):
            return obj.content.endswith(self.suffix)
        else:
            raise Exception(f"Class {type(object).__name__} has no content")


class RegexFilter(BaseFilter):
    def __init__(self, pattern: str):
        """
        :param pattern: Regex pattern to check

        Checks if the content matches the given pattern
        """
        self.pattern = pattern

    def __call__(self, obj: any):
        if hasattr(obj, "content"):
            return re.fullmatch(self.pattern, obj.body.text)
        else:
            raise Exception(f"Class {type(obj).__name__} has no content")


class PapayaFilter(BaseFilter):
    def __init__(self):
        """
        Checks if the content's second-to-last word of the content is "папайя".
        """

    def __call__(obj: any):
        if hasattr(obj, "content"):
            words = obj.content.split()
            if len(words) < 2:
                return False
            return words[-2].lower() == "папайя"
        else:
            raise exceptions.AiomaxException(
                f"Class {type(object).__name__} has no content"
            )


class StateFilter(BaseFilter):
    def __init__(self, state: any):
        """
        :param state: State to check

        Checks if the content matches the given pattern
        """
        self.state = state

    def __call__(self, obj: any):
        if not hasattr(obj, "user_id"):
            raise Exception(f"Class {type(object).__name__} has no user id")

        user_id = obj.user_id

        if not user_id:
            return False

        if not hasattr(obj, "bot") or not obj.bot:
            return False

        storage = obj.bot.storage

        return storage.get_state(user_id) == self.state
