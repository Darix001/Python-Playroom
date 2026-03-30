from __future__ import annotations

import builtins
import dataclasses as dt
import itertools as it
import operator as op
import re
from collections.abc import Callable, Iterable, Iterator
from functools import partial, reduce
from types import MethodType, ModuleType
from typing import Any, Type, TypeVar

ifuncs = ModuleType(
    "ifuncs",
    doc="This is the first module that is looked up by the register_method "
    "classmethod of Iter class. the register_method is called by __getattr__.",
)

factories = {}

modules: list[dict[str, Callable]] = [*map(vars, (ifuncs, builtins, it))]


def add_lookup_module(module: ModuleType) -> None:
    modules.append(vars(module))


def search_func(function_name: str, /):
    if func := next(
        filter(None, map(op.methodcaller("get", function_name), modules)), None
    ):
        return func
    else:
        raise ValueError("No such function found with name: " + function_name)


T_composed = TypeVar("T_composed")
R = TypeVar("R")
V = TypeVar("V")
C = TypeVar("C")


class BaseIter(Iterable):
    __slots__ = ()

    def __getattr__(self, attr: str, /) -> Callable[..., ipartial]:
        try:
            return MethodType(self.register_method(attr), self)
        except ValueError as e:
            raise AttributeError from e

    def flatten(self, /) -> ipartial:
        return ipartial(it.chain.from_iterable, self)

    def reduce(self, func: Callable[[Any, Any], V], /, *initial) -> V:
        return reduce(func, self, *initial) if initial else reduce(func, self)

    def scalar(self, func: Callable[[Iterable], R]) -> R:
        return func(self)

    @classmethod
    def register_method(cls: Type[C], method_name: str, /) -> Callable[[...], ipartial]:
        for key, factory in factories.items():
            if match := key.match(method_name):
                method = factory(match)
                break
        else:
            fn = search_func(method_name)

            def method(self, /, *args, **kw) -> ipartial:
                return ipartial(fn, self, *args, **kw)

        setattr(BaseIter, method_name, method)
        return method


class ipartial(partial, BaseIter):
    __slots__ = ()
    __iter__ = partial.__call__


@dt.dataclass(slots=True)
class Iter(BaseIter):
    iterable: Iterable = ()

    def __iter__(self, /) -> Iterator:
        return iter(self.iterable)


imethod_type = Callable[..., ipartial]
factory_type = Callable[[re.Match[str]], imethod_type]


def imethod_factory(func: factory_type | str, /):
    return (
        partial(register_imethod_factory, expr=func)
        if isinstance(func, str)
        else register_imethod_factory(func, func.__name__)
    )


def register_imethod_factory(func: factory_type, expr: str) -> factory_type:
    factories[re.compile(expr)] = func
    return func


@imethod_factory("composed_?")
def composed_pipe(match: re.Match[str], /) -> imethod_type:
    if pipe_func := search_func(match.string[match.end() :]):

        def method(
            iterable, *args: T_composed, key: Callable[[T_composed], Any] | None = None
        ) -> ipartial:
            funcs = reversed(args)
            if key is not None:
                funcs = map(key, args)
            for func in funcs:
                iterable = ipartial(pipe_func, func, iterable)
            return iterable

        return method

    else:
        raise


factories: dict[re.Pattern[str], factory_type]


if __name__ == "__main__":
    a = Iter[str]("DXctuIvfUTFD^%4#^%*&GOGuibcTRxcKY").composed_filter(
        str.isalpha,
        str.islower,
        str.isascii,
    )
    print(a.scalar(",".join), a)
