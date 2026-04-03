from __future__ import annotations

import builtins
import dataclasses as dt
import functools as ft
import itertools as it
import operator as op
from collections.abc import Callable, Iterable, Iterator, Mapping
from inspect import signature
from types import FunctionType, MethodType, ModuleType
from typing import Any, Self, SupportsIndex, Type, TypeVar

import more_itertools as mit

from . import ifuncs
from .methodtools import add_method

modules: list[Mapping[str, Callable]] = [*map(vars, (ifuncs, builtins, it, mit))]

factories: dict[str, factory_type] = {}


def add_lookup_module(module: ModuleType) -> None:
    modules.append(vars(module))


def search_func(function_name: str, /):
    func = mit.first_true(modules, None, op.methodcaller("get", function_name))
    if func is None:
        raise ValueError("Function Name not found: " + function_name)
    return func


T_composed = TypeVar("T_composed")


R = TypeVar("R")
V = TypeVar("V")
C = TypeVar("C")


list_field = ft.partial(dt.field, default_factory=list)


@dt.dataclass(slots=True, frozen=True)
class PipeExpr:
    args_list: list[tuple[str | Any]] = list_field()
    funcs: list[Callable[..., Callable]] = list_field()

    def __getattr__(self, attr: str, /) -> Self:
        if last_attr := self.last_attr():
            self.args_list[-1] = (f"{last_attr}.{attr}",)
        else:
            self.add(op.attrgetter, attr)
        return self

    def __call__(self, *args, **kwargs) -> Self:
        if attr := self.last_attr():
            left, _, attr = attr.rpartition(".")
            self.args_list[-1] = (left,)
        else:
            attr = "__call__"
        func = op.methodcaller
        if kwargs:
            func = ft.partial(func, **kwargs)
        self.add(func, attr, *args)
        return self

    def __getitem__(self, /, item) -> Self:
        self.add(op.itemgetter, item)
        return self

    def add(self, /, func: Callable, *args):
        self.args_list.append(args)
        self.funcs.append(func)

    def last_attr(self, /):
        if (funcs := self.funcs) and funcs[-1] is op.attrgetter:
            return self.args_list[-1][-1]

    def copy(self, /) -> Self | PipeExpr:
        return type(self)(self.args_list.copy(), self.funcs.copy())


class BaseIter(Iterable):
    __slots__ = ()

    def __getattr__(self, attr: str, /) -> Callable[..., ipartial]:
        return MethodType(self.register_method(attr), self)

    flatten = ft.partialmethod(it.chain.from_iterable)

    def reduce(self, func: Callable[[Any, Any], V], /, *initial) -> V:
        return ft.reduce(func, self, *initial) if initial else ft.reduce(func, self)

    def scalar(self, func: Callable[[Iterable], R]) -> R:
        return func(self)

    def repeat_each(iterable, times: SupportsIndex):
        return ipartial(map, it.repeat, iterable, it.repeat(times)).flatten()

    @classmethod
    def register_method(cls: Type[C], method_name: str, /) -> Callable[..., ipartial]:
        method = mit.first_true(
            map(op.methodcaller("__call__", method_name), factories.values()), None
        )
        if not method:
            parameters = signature(fn := search_func(method_name)).parameters
            if (
                iters_param := parameters.get("iterables")
            ) and iters_param.kind == iters_param.VAR_POSITIONAL:
                method = ft.partialmethod(ipartial, fn)

            elif iter_param := parameters.get("iterable"):
                if iter_param.kind == iter_param.KEYWORD_ONLY:

                    def method(self, /, *args, **kw) -> ipartial:
                        return pipe_func(*args, **kw, iterable=self)
                elif iter_param.kind in (
                    iter_param.POSITIONAL_ONLY,
                    iter_param.POSITIONAL_OR_KEYWORD,
                ):
                    pipe_func = ft.partial(ipartial, fn)
                    index = 0
                    try:
                        index = op.indexOf(param_names := parameters.keys(), "iterable")
                    except ValueError:
                        pass
                    if not index:
                        method = ft.partialmethod(ipartial, fn)

                    elif index == len(param_names) - 1:

                        def method(self, /, *args, **kw) -> ipartial:
                            return pipe_func(*args, self, **kw)
                    else:

                        def method(self, /, *args, **kw) -> ipartial:
                            return pipe_func(
                                *(args[index:] + (self,) + args[:index]), **kw
                            )
            else:
                raise ValueError(
                    "No 'iterable(s)' parameter found in function signature for function "
                    + method_name
                )

        if type(method) is FunctionType:
            method.__name__ = fn.__name__
            add_method(cls, method)
        else:
            setattr(cls, fn.__name__, method)
        return method

    def with_pipe(iterable, /, pipe: PipeExpr) -> Self | ipartial:
        for func, args in zip(pipe.funcs, pipe.args_list):
            iterable = ipartial(map, func(*args), iterable)
        return iterable


class ipartial(ft.partial, BaseIter):
    __slots__ = ()
    __iter__ = ft.partial.__call__


Iter = ft.partial(ipartial, iter)


@dt.dataclass(slots=True)
class MutableIter(BaseIter):
    iterable: Iterable = ()

    def __iter__(self, /) -> Iterator:
        return iter(self.iterable)


MutIter = MutableIter

factory_type = Callable[[str], Callable[..., ipartial] | None]


def register_imethod_factory(name: str, func: factory_type) -> factory_type:
    factories[name] = func
    return func


def imethod_factory(func: factory_type | str):
    if callable(func):
        return register_imethod_factory(func.__name__, func)
    else:
        return ft.partial(register_imethod_factory, func)


@imethod_factory
def composed_pipe(method_name: str, /) -> Callable[..., ipartial] | None:
    if not method_name.startswith("composed_"):
        return
    pipe_func = search_func(method_name[9:])

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


opfuncs: dict[str, Callable] = {
    "attr": op.attrgetter,
    "item": op.itemgetter,
    "method": op.methodcaller,
}


@imethod_factory
def property_pipe(method_name: str, /) -> Callable[..., ipartial] | None:
    kind, _, func_name = method_name.rpartition("_")
    if kind not in opfuncs:
        return
    map_func = opfuncs[kind]
    pipe_func = search_func(func_name)

    def method(iterable, /, *args, **kw) -> ipartial:
        return ipartial(pipe_func, map_func(*args, **kw), iterable)

    return method
    property_pipe.funcs = opfuncs


if __name__ == "__main__":
    a = MutableIter[str]("DXctuIvfUTFD^%4#^%*&GOGuibcTRxcKY").composed_filter(
        str.isalpha,
        str.islower,
        str.isascii,
    )
    print(",".join(a))
    d = MutableIter(zip(range(10))).item_map(0)
    print(bytes(d))
