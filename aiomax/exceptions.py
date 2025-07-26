class AiomaxException(Exception):
    """
    Default class for aiomax Exceptions
    """


class InvalidToken(AiomaxException):
    """
    Invalid token Exception
    """


class AttachmentNotReady(AiomaxException):
    """
    Attachment not ready Exception
    """


class ChatNotFound(AiomaxException):
    """
    Chat not found Exception
    """


class IncorrectTextLength(AiomaxException):
    """
    Incorrect text length Exception
    """


class InternalError(AiomaxException):
    """
    Internal error Exception
    """

    def __init__(self, id: "str | None" = None):
        self.id: str = id


class UnknownErrorException(AiomaxException):
    """
    Unknown error Exception
    """

    def __init__(self, text: str, description: "str | None" = None):
        self.text: str = text
        self.description: "str | None" = description


class AccessDeniedException(AiomaxException):
    """
    Access Denied Exception
    """

    def __init__(self, description: "str | None" = None):
        self.description: "str | None" = description


class NotFoundException(AiomaxException):
    """
    Something not found Exception
    """

    def __init__(self, description: "str | None" = None):
        self.description: "str | None" = description


class MessageNotFoundException(NotFoundException):
    """
    Child `NotFoundException` exception class that is raised
    in `Bot.get_message` function
    """


class FilenameNotProvided(AiomaxException):
    """
    Filename not provided exception
    """
