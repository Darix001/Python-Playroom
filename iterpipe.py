from __future__ import annotations

import builtins
import functools as ft
import itertools as it
import operator as op
from collections.abc import Callable, Iterable, Iterator
from types import MethodType, ModuleType
from typing import Any, Type, TypeVar

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


class BaseIter(Iterable):
    __slots__ = ()

    def __getattr__(self, attr: str, /) -> Callable[..., Iter]:
        return MethodType(self.register_method(attr), self)

    def flatten(self, /) -> ipartial:
        return ipartial(it.chain.from_iterable, self)

    def reduce(self, func: Callable[[Any, Any], V], /, *initial) -> V:
        return ft.reduce(func, self, *initial) if initial else ft.reduce(func, self)

    def scalar(self, func: Callable[[Iterable[T]], R]) -> R:
        return func(self)

    @classmethod
    def register_method(cls: Type[T], fn_name: str, /) -> Callable[[...], ipartial]:
        if not (
            fn := next(
                filter(None, map(op.methodcaller("get", fn_name), modules)), None
            )
        ):
            raise ValueError("Function Name not found: " + fn_name)

        if fn_name.startswith("filter") or fn_name.endswith(("map", "while")):

            def method(self, /, *args: Callable) -> ipartial:
                iterator = self
                for arg in args:
                    iterator = ipartial(fn, arg, iterator)
                return iterator
        else:

            def method(self, /, *args, **kw) -> ipartial:
                return ipartial(fn, self, *args, **kw)

        setattr(cls, fn_name, method)
        return method


class ipartial(ft.partial, BaseIter):
    __slots__ = ()
    __iter__ = ft.partial.__call__


@attrs.define
class Iter(BaseIter):
    iterable: Iterable[T] = ()

    def __iter__(self, /) -> Iterator:
        return iter(self.iterable)


if __name__ == "__main__":
    a = Iter[str]("DXctuIvfUTFD^%4#^%*&GOGuibcTRxcKY").filter(
        str.isalpha,
        str.islower,
        str.isascii,
    )
    print(a.scalar(",".join), a)
