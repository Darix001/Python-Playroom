from __future__ import annotations

import builtins
import dataclasses as dt
import functools as ft
import itertools as it
import operator as op
from collections.abc import Callable, Iterable, Iterator, Mapping
from inspect import signature
from types import MethodType, ModuleType
from typing import Any, Self, SupportsIndex, Type, TypeVar

import more_itertools as mit

from .methodtools import add_method

ifuncs = ModuleType(
    "ifuncs",
    doc="This is the first module that is looked up by the register_method "
    "classmethod of Iter class. the register_method is called by __getattr__.",
)

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


class next_func_caller(map):
    __slots__ = ()
    __call__ = property(next)


@dt.dataclass(slots=True, frozen=True)
class PipeExpr:
    args_list: list[tuple[Any, ...]] = list_field()
    funcs: list[Callable[..., Callable]] = list_field()

    def __getattr__(self, attr: str, /) -> Self:
        if last_attr := self.last_attr():
            self.args_list[-1] = (f"{last_attr}.{attr}",)
        else:
            self.add(op.attrgetter, attr)
        return self

    def __call__(self, *args) -> Self:
        if attr := self.last_attr():
            left, _, attr = attr.rpartition(".")
            self.args_list[-1] = (left,)
        else:
            attr = "__call__"
        self.add(op.methodcaller, attr, *args)
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

    def starmap_funcs(funcs, args):
        return it.starmap(next_func_caller(op.call, funcs), args)

    def flatten(self, /) -> ipartial:
        return ipartial(it.chain.from_iterable, self)

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
            if not (iterable_param := parameters.get("iterable")):
                raise ValueError(
                    "No 'iterable' parameter found in function signature for function "
                    + method_name
                )
            if iterable_param.kind == iterable_param.POSITIONAL_ONLY:
                index = 0
                try:
                    index = op.indexOf(param_names := parameters.keys(), "iterable")
                except ValueError:
                    pass
                if not index:

                    def method(self, /, *args, **kw) -> ipartial:
                        return ipartial(fn, self, *args, **kw)

                elif index == len(param_names) - 1:

                    def method(self, /, *args, **kw) -> ipartial:
                        return ipartial(fn, *args, self, **kw)
                else:

                    def method(self, /, *args, **kw) -> ipartial:
                        return ipartial(
                            fn, self, *(args[index:] + (self,) + args[:index]), **kw
                        )
            else:

                def method(self, /, *args, **kw) -> ipartial:
                    return ipartial(fn, *args, **kw, iterable=self)

            method.__name__ = fn.__name__

        add_method(cls, method)
        return method

    def with_pipe(iterable, /, pipe: PipeExpr) -> Self | ipartial:
        funcs = it.starmap(next_func_caller(op.call, pipe.funcs), pipe.args_list)
        for func in funcs:
            iterable = ipartial(map, func, iterable)
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
    kind, _, func_name = method_name.partition("_")
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
