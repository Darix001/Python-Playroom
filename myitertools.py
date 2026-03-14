from __future__ import annotations

import builtins
import functools as ft
import itertools as it
import operator as op
from collections.abc import Callable, Iterable, Iterator
from types import MethodType, ModuleType
from typing import Any, Generic, Type, TypeVar

import attrs

ifuncs = ModuleType(
    "ifuncs",
    doc="This is the first module that is looked up by the register_method "
    "classmethod of Iter class. the register_method is called by __getattr__.",
)

modules: list[dict[str, Callable]] = [*map(vars, (ifuncs, builtins, it, op))]

T = TypeVar("T")
R = TypeVar("R")
V = TypeVar("V")


class ipartial(ft.partial):
    __slots__ = ()
    __iter__ = ft.partial.__call__


class BaseIter(Iterable):
    __slots__ = ()

    def __getattr__(self, attr: str, /) -> Callable[..., Iter]:
        return MethodType(self.register_method(attr), self)

    def scalar(self, func: Callable[[Iterable[T]], R]) -> R:
        return func(self)

    def reduce(self, func: Callable[[Any, Any], V], /, *initial) -> V:
        return ft.reduce(func, self, *initial) if initial else ft.reduce(func, self)

    @classmethod
    def register_method(cls: Type[T], fn_name: str, /) -> Callable[[...], Iter]:
        if not (
            fn := next(
                filter(None, map(op.methodcaller("get", fn_name), modules)), None
            )
        ):
            raise ValueError("Function Name not found: " + fn_name)

        if fn_name.startswith("filter") or fn_name.endswith(("map", "while")):

            def method(self, /, *args: Callable) -> cls:
                iterator = self.gen
                for arg in args:
                    iterator = ipartial(fn, arg, iterator)
                return IterPipe(iterator)
        else:
            if not hasattr(fn, "__get__"):

                def method(self, *args, **kw) -> cls:
                    return IterPipe(ipartial(fn, self.gen, *args, **kw))

            else:
                method = fn

        setattr(cls, fn_name, method)
        return method


@attrs.define
class Iter(BaseIter):
    iterable: Iterable[T]

    def __iter__(self, /) -> Iterator:
        return iter(self.iterable)

    @property
    def gen(self, /):
        return self


@attrs.define
class IterPipe(BaseIter):
    gen: ipartial

    def __iter__(self, /) -> Iterator:
        return self.gen()


a = Iter[str]("DXctuIvfUTFD^%4#^%*&GOGuibcTRxcKY").filter(str.isalpha, str.islower)
print(a.scalar(",".join))
print(a.scalar)
