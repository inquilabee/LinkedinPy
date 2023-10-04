from contextlib import suppress
from functools import wraps


def ignore_exception(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        with suppress():
            func(*args, **kwargs)

    return wrapper


def login_required(func):
    @wraps(func)
    def ensure_login(*args, **kwargs):
        object_ref = args[0]
        if not object_ref._user_logged_in:  # noqa
            object_ref.login()

        return func(*args, **kwargs)

    return ensure_login
