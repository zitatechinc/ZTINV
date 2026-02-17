# utils/current_user.py
import threading

_user_storage = threading.local()


def get_current_user():
    return getattr(_user_storage, "user", None)

def set_current_user(user):
    _user_storage.user = user
