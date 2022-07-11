class EmptyAPIResponseError(Exception):
    """В случае, если словарь пуст."""

    pass


class ResponseException(Exception):
    """Исключение неправильного ответа."""

    pass
