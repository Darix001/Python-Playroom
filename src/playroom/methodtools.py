from collections.abc import Callable
from functools import partial
from operator import attrgetter
from types import MethodType


def delegate(attr: str, doc: str | None = None) -> property:
    return property(attrgetter(attr), doc=doc)


def attach_to_class(cls) -> partial[Callable]:
    return partial(add_method, cls)


def add_method(cls, func):
    setattr(cls, func.__name__, func)
    func.__qualname__ = f"{cls.__name__}.{func.__name__}"
    func.__module__ = cls.__module__
    return func


class instance_method(property):
    def __init__(self, func: Callable, doc: str | None = None):
        super().__init__(partial(MethodType, func), doc=doc)

    __call__ = delegate("fget")

    @property
    def __isabstractmethod__(self, /) -> bool:
        return getattr(self.fget, "__isabstractmethod__", False)
