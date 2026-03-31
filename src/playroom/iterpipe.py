from __future__ import annotations

import builtins
import dataclasses as dt
import functools as ft
import itertools as it
import operator as op
import re
from collections.abc import Callable, Iterable, Iterator
from types import MethodType, ModuleType, SimpleNamespace
from typing import Any, Self, SupportsIndex, Type, TypeVar

ifuncs = ModuleType(
    "ifuncs",
    doc="This is the first module that is looked up by the register_method "
    "classmethod of Iter class. the register_method is called by __getattr__.",
)

modules: list[dict[str, Callable]] = [*map(vars, (ifuncs, builtins, it))]

factories = {}


def add_lookup_module(module: ModuleType) -> None:
    modules.append(vars(module))


def search_func(function_name: str, /):
    func = next(filter(None, map(op.methodcaller("get", function_name), modules)), None)
    if func is None:
        raise ValueError("Function Name not found: " + function_name)
    return func


T_composed = TypeVar("T_composed")


R = TypeVar("R")
V = TypeVar("V")
C = TypeVar("C")

constants: SimpleNamespace[str, int] = SimpleNamespace()
for i, const_attr in enumerate(("ATTR", "ITEM", "METHOD")):
    setattr(constants, const_attr, i)


@dt.dataclass(slots=True, frozen=True)
class PipeExpr:
    pipe: list[
        tuple[str | Any]
        | tuple[str, tuple, dict[str, Any]]
        | tuple[tuple, dict[str, Any]]
    ] = dt.field(default_factory=[].copy)
    func_ids: bytearray = dt.field(default_factory=bytearray().copy)
    funcs = (op.attrgetter, op.itemgetter, op.methodcaller)

    def __getattr__(self, attr: str, /) -> Self:
        if last_attr := self.last_attr():
            self.pipe[-1] = (f"{last_attr}.{attr}",)
        else:
            self.add(constants.ATTR, (attr,))
        return self

    def __call__(self, *args, **kw) -> Self:
        if last_attr := self.last_attr():
            self.func_ids[-1] = constants.METHOD
            self.pipe[-1] = (last_attr + ".__call__", args, kw)
        else:
            self.add(constants.METHOD, ("__call__", args, kw))

        self.pipe[-1] = (last_attr, args, kw)
        return self

    def __getitem__(self, /, item) -> Self:
        self.add(constants.ITEM, (item,))
        return self

    def add(self, /, func_id: int, obj: tuple):
        self.pipe.append(obj)
        self.func_ids.append(func_id)

    def last_attr(self, /):
        if (funcs := self.func_ids) and not funcs[-1]:
            return self.pipe[-1][-1]

    def copy(self, /) -> Self | PipeExpr:
        return type(self)(self.pipe.copy(), self.func_ids.copy())


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

    def repeat_each(iterable, times: SupportsIndex):
        return ipartial(map, it.repeat, iterable, it.repeat(times)).flatten()

    @classmethod
    def register_method(cls: Type[C], method_name: str, /) -> Callable[[...], ipartial]:
        for regexp, fn in factories.items():
            if match := regexp.match(method_name):
                method = fn(match)
        else:

            def method(self, /, *args, **kw) -> ipartial:
                return ipartial(fn, self, *args, **kw)

        setattr(cls, method_name, method)
        return method

    def with_pipe(iterable, /, pipe: PipeExpr) -> Self | ipartial:
        for func in map(ft.partial(op.getitem, pipe.funcs), pipe.func_ids):
            iterable = ipartial(map, func, iterable)
        return iterable


class ipartial(ft.partial, BaseIter):
    __slots__ = ()
    __iter__ = ft.partial.__call__


@dt.dataclass(slots=True)
class Iter(BaseIter):
    iterable: Iterable = ()

    def __iter__(self, /) -> Iterator:
        return iter(self.iterable)


factory_type = Callable[[re.Match[str]], Callable[..., ipartial]]


def imethod_factory(func, /):
    return (
        register_imethod_factory(func, func.__name__)
        if callable(func)
        else ft.partial(register_imethod_factory, expr=func)
    )


def register_imethod_factory(func: factory_type, expr: str) -> factory_type:
    factories[re.compile(expr)] = func
    return func


@imethod_factory("composed_?")
def composed_pipe(match: re.Match[str], /) -> Callable[..., ipartial]:
    pipe_func = search_func(match.string[match.end() :])

    def method(
        iterable, *args: T_composed, key: Callable[[T_composed], Any] | None = None
    ) -> ipartial:
        print(89)
        funcs = reversed(args)
        if key is not None:
            funcs = map(key, args)
        for func in funcs:
            iterable = ipartial(pipe_func, func, iterable)
        return iterable

    return method


if __name__ == "__main__":
    a = Iter[str]("DXctuIvfUTFD^%4#^%*&GOGuibcTRxcKY").composed_filter(
        str.isalpha,
        str.islower,
        str.isascii,
    )
    print(a)
    print(a.scalar(",".join))
