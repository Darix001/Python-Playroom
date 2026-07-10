from collections.abc import Callable
from dataclasses import dataclass
from functools import partial
from operator import attrgetter
from types import FunctionType, MethodType
from typing import Any


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


@dataclass
class ReadOnlyPrivateDescriptor:
    doc: str | None = None

    def __set_name__(self, owner, name):
        self.name = name
        setattr(owner, name, property(attrgetter("_" + name), doc=self.doc))


class PrivateDescriptor(ReadOnlyPrivateDescriptor):
    @staticmethod
    def fset(self, value, /):
        self.attrname = value

    @staticmethod
    def fdel(self, /):
        del self.attrname

    def __set_name__(self, owner: type, name: str):
        fget = attrgetter(name := "_" + name)
        co_names = (name,)
        fset = replace_code_co_names(co_names, self.fset, "set_" + name)
        fdel = replace_code_co_names(co_names, self.fdel, "del_" + name)

        setattr(owner, name, property(fget, fset, fdel, self.doc))


def replace_code_co_names(
    co_names: tuple[str],
    func: FunctionType,
    /,
    *args,
    globals=globals(),
):
    return FunctionType(func.__code__.replace(co_names=co_names), globals, *args)


@dataclass
class SetNameFactory:
    __slots__ = ()
    factory: Callable[[str], Callable[..., Any]]

    def __set_name__(self, cls, name):
        add_method(cls, self.factory(name))
