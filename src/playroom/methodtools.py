from collections.abc import Callable
from functools import partial, wraps
from operator import attrgetter, call


def pool(*funcs: Callable):
    def decorator(func, /):
        @wraps(func)
        def wrapper(*args, **kw):
            return func(*map(call, funcs, args), **kw)


def delegate(attr: str, doc=None) -> property:
    return property(attrgetter(attr), doc=doc)


def attach_to_class(cls):
    return partial(add_method, cls)


def add_method(cls, func):
    setattr(cls, func.__name__, func)
    func.__qualname__ = f"{cls.__name__}.{func.__name__}"
    func.__module__ = cls.__module__
    return func
