from collections.abc import Callable
from functools import wraps
from operator import attrgetter, call


def pool(*funcs: Callable):
    def decorator(func, /):
        @wraps(func)
        def wrapper(*args, **kw):
            return func(*map(call, funcs, args), **kw)


def delegate(attr: str, doc=None) -> property:
    return property(attrgetter(attr), doc=doc)
