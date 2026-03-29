from __future__ import annotations

import builtins
import dataclasses as dt
import functools as ft
import itertools as it
import operator as op
from collections.abc import Callable, Iterable, Iterator
from types import MethodType, ModuleType
from typing import Any, Type, TypeVar

ifuncs = ModuleType(
    "ifuncs",
    doc="This is the first module that is looked up by the register_method "
    "classmethod of Iter class. the register_method is called by __getattr__.",
)

modules: list[dict[str, Callable]] = [*map(vars, (ifuncs, builtins, it))]


def add_lookup_module(module: ModuleType) -> None:
    modules.append(vars(module))


def search_func(function_name: str, /, default: Any = None):
    return next(
        filter(None, map(op.methodcaller("get", function_name), modules)), default
    )


T_composed = TypeVar("T_composed")


def composed_pipe(method_name: str, /) -> Callable[..., ipartial] | None:
    left, sep, function_name = method_name.partition("composed_")
    if not left and sep and (pipe_func := search_func(function_name)):

        def method(
            iterable, *args: T_composed, key: Callable[[T_composed], Any] | None = None
        ) -> ipartial:
            funcs = reversed(args)
            if key is not None:
                funcs = map(key, args)
            for func in funcs:
                iterable = ipartial(pipe_func, func, iterable)
            return iterable


factories = {"composed": composed_pipe}

R = TypeVar("R")
V = TypeVar("V")
C = TypeVar("C")


class BaseIter(Iterable):
    __slots__ = ()

    def __getattr__(self, attr: str, /) -> Callable[..., ipartial]:
        return MethodType(self.register_method(attr), self)

    def flatten(self, /) -> ipartial:
        return ipartial(it.chain.from_iterable, self)

    def reduce(self, func: Callable[[Any, Any], V], /, *initial) -> V:
        return ft.reduce(func, self, *initial) if initial else ft.reduce(func, self)

    def scalar(self, func: Callable[[Iterable], R]) -> R:
        return func(self)

    @classmethod
    def register_method(cls: Type[C], method_name: str, /) -> Callable[[...], ipartial]:
        if not (
            fn := next(
                filter(None, map(op.methodcaller("get", method_name), modules)), None
            )
        ):
            raise ValueError("Function Name not found: " + method_name)

        if not (
            method := next(
                map(
                    op.methodcaller("__call__", method_name),
                    factories.values(),
                )
            )
        ):

            def method(self, /, *args, **kw) -> ipartial:
                return ipartial(fn, self, *args, **kw)

        setattr(cls, method_name, method)
        return method


class ipartial(ft.partial, BaseIter):
    __slots__ = ()
    __iter__ = ft.partial.__call__


@dt.dataclass(slots=True)
class Iter(BaseIter):
    iterable: Iterable = ()

    def __iter__(self, /) -> Iterator:
        return iter(self.iterable)


if __name__ == "__main__":
    a = Iter[str]("DXctuIvfUTFD^%4#^%*&GOGuibcTRxcKY").filter(
        str.isalpha,
        str.islower,
        str.isascii,
    )
    print(a.scalar(",".join), a)
