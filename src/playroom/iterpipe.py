from __future__ import annotations

import builtins
import dataclasses as dt
import functools as ft
import itertools as it
import operator as op
from collections.abc import Callable, Iterable, Iterator, Mapping
from inspect import Parameter, signature
from types import FunctionType, MethodType, ModuleType
from typing import Any, Self, SupportsIndex, Type, TypeVar

import more_itertools as mit

from . import ifuncs
from .methodtools import add_method, instance_method

modules: list[Mapping[str, Callable]] = [*map(vars, (ifuncs, builtins, it, mit))]

factories: dict[str, factory_type] = {}

T_composed = TypeVar("T_composed")
ifunc_type = Callable[..., Iterable]


R = TypeVar("R")
V = TypeVar("V")
C = TypeVar("C")

get_positional_types = op.attrgetter(
    "POSITIONAL_ONLY", "VAR_POSITIONAL", "POSITIONAL_OR_KEYWORD"
)
POSITIONALS = frozenset(get_positional_types(Parameter))


def add_lookup_module(module: ModuleType) -> None:
    modules.append(vars(module))


def search_func(function_name: str, /) -> ifunc_type:
    funcs = map(op.methodcaller("get", function_name), modules)
    func = mit.first_true(funcs, None)
    if func is None:
        raise ValueError("Function Name not found: " + function_name)
    return func


def iter_method(func: ifunc_type, /):
    return instance_method(ft.partial(ipartial, func))


def to_imethod(func: ifunc_type, /) -> Callable[..., ipartial]:
    sig = signature(func)
    nparams = len(parameters := sig.parameters)
    for i, (name, param) in enumerate(parameters.items()):
        if name.removesuffix("s") != "iterable":
            continue

        if param.kind not in POSITIONALS:
            if not name.endswith("s"):

                def method(self, /, *args, **kw) -> ipartial:
                    return ipartial(func, *args, **kw, iterable=self)
            else:
                # This kind of functions are not acceptable.
                # since it is unknown if the keyword argument type
                # is an iterator/generator of iterables of a list of iterables
                raise TypeError(
                    "Function signature with parameter iterables as keyword only"
                )

            break

        if not i:  # First positional argument is the iterable(s).
            method = instance_method(func)

        elif nparams - i == 1:  # last parameter is the iterable(s)

            def method(self, /, *args, **kw) -> ipartial:
                return ipartial(func, *args, self, **kw)

        else:  # iterable

            def method(self, /, *args, **kw) -> ipartial:
                return ipartial(func, *ifuncs.insert(args, i, self), **kw)

        break
    else:
        raise ValueError(
            f"No 'iterable(s)' parameter found in function signature for  {func!r}"
        )
    return method


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

    flatten: instance_method

    def __getattr__(self, attr: str, /) -> Callable[..., ipartial]:
        return MethodType(self.register_method(attr), self)

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
        ) or to_imethod(search_func(method_name))

        if type(method) is FunctionType:
            method.__name__ = method_name
            add_method(cls, method)
        else:
            setattr(cls, method_name, method)
        return method

    def with_pipe(iterable, /, pipe: PipeExpr) -> Self | ipartial:
        for func, args in zip(pipe.funcs, pipe.args_list):
            iterable = ipartial(map, func(*args), iterable)
        return iterable


class ipartial(ft.partial, BaseIter):
    __slots__ = ()
    __iter__ = ft.partial.__call__


BaseIter.flatten = iter_method(it.chain.from_iterable)

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


# def named_imethod_factory(
#     name: str,
# ) -> ft.partial[factory_type]:
#     return ft.partial(register_imethod_factory, name)
named_imethod_factory = ft.partial(ft.partial, register_imethod_factory)


def imethod_factory(func: factory_type) -> factory_type:
    return register_imethod_factory(getattr(func, "__name__", None) or repr(func), func)


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
def named_map(method_name: str, /, opfuncs=opfuncs) -> Callable[..., ipartial] | None:
    kind, _, func_name = method_name.rpartition("_")
    if kind not in opfuncs:
        return
    map_func = opfuncs[kind]
    pipe_func = search_func(func_name)

    def method(iterable, /, *args, **kw) -> ipartial:
        return ipartial(pipe_func, map_func(*args, **kw), iterable)

    return method


setattr(named_map, "funcs", opfuncs)


if __name__ == "__main__":
    a = MutableIter[str]("DXctuIvfUTFD^%4#^%*&GOGuibcTRxcKY").composed_filter(
        str.isalpha,
        str.islower,
        str.isascii,
    )
    print(",".join(a))
    d = MutableIter(range(10)).zip().item_map(0)
    print(bytes(d))
