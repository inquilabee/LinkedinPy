from contextlib import suppress
from functools import wraps


def ignore_exception(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        with suppress():
            func(*args, **kwargs)

    return wrapper
