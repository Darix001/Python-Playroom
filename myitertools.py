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

T = TypeVar("T", bound="Iter")


@attrs.frozen
class Iter:
    iterator: Iterator[Any] = attrs.field(converter=iter)

    def __iter__(self, /) -> Iterator:
        return self.iterator

    def __getattr__(self, attr: str, /) -> Callable[..., Iter]:
        return MethodType(self.register_method(attr), self)

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
                iterator = self.iterator
                for arg in args:
                    iterator = fn(arg, iterator)
                return type(self)(iterator)
        else:
            if not hasattr(fn, "__get__"):

                def method(self, *args, **kw) -> cls:
                    return type(self)(fn(self.iterator, *args, **kw))

            else:
                method = fn

        setattr(cls, fn_name, method)
        return method

    def scalar(self, func: Callable[[Iterable], Any]) -> Any:
        return func(self.iterator)

    def reduce(self, func, /, *, initial) -> Any:
        return ft.reduce(func, self.iterator, initial)


a = Iter("DXctuIvfUTFD^%4#^%*&GOGuibcTRxcKY").filter(str.isalpha, str.islower)
