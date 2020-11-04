import sys
import datetime
from functools import wraps
from typing import Tuple, Type, Any, Callable

import settings


def safe(exceptions: Tuple[Type[Exception], ...]=(Exception, ), return_val: Any=None):
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exceptions:
                return return_val
        return wrapper if not settings.DEBUG else func
    return decorator



def error(*exceptions):
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                print(e)
                sys.exit(1)
        return wrapper if not settings.DEBUG else func
    return decorator


def seconds_to_datetime(seconds: int):
    epoch = datetime.datetime(1900, 1, 1)
    hours = int(seconds / 3600)
    seconds -= hours * 3600
    minutes = int(seconds / 60)
    return epoch + datetime.timedelta(hours=hours, minutes=minutes)


def split(items: list, item_selector:Callable):
    _items = items[:]
    slices = [[]]

    while _items:
        item = _items.pop(0)
        if item_selector(item):
            slices.append([])
        else:
            slices[-1].append(item)

    return slices

def first(items, item_selector):
    for item in items:
        if item_selector(item):
            return item