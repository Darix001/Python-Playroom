import builtins
import copy
import math
import operator
import os
from collections import ChainMap
from collections.abc import Callable
from dataclasses import dataclass
from functools import partial
from operator import attrgetter
from types import FunctionType, MethodType
from typing import Any


def delegate(attr: str, doc: str | None = None) -> property:
    return property(attrgetter(attr), doc=doc)


def attach_to_class(cls) -> partial[Callable]:
    return partial(add_method, cls, None)


def add_method(cls, name: str | None, func):
    if not name:
        name = func.__name__
    setattr(cls, name, func)
    func.__qualname__ = f"{cls.__name__}.{name}"
    func.__module__ = cls.__module__
    return func


class instance_method(property):
    __slots__ = ()
    fget: partial

    def __init__(self, func: Callable, doc: str | None = None):
        super().__init__(partial(MethodType, func), doc=doc)

    __call__ = delegate("fget")

    @property
    def __isabstractmethod__(self, /) -> bool:
        return getattr(self.fget.args[0], "__isabstractmethod__", False)


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


@dataclass(frozen=True, repr=False, slots=True)
class SetNameFactory[T]:
    factory: Callable[[str], T]
    attacher: Callable[[type, str, T], Any] = add_method

    def __set_name__(self, cls: type, name: str):
        self.attacher(cls, name, self.factory(name))


UNARY_METHODS = ("__abs__", "__pos__", "__neg__", "__inv__", "__invert__")
SEQUENCE_UNARY_METHODS = ("__iter__", "__reversed__", "__bool__", "__len__")
SEQUENCE_BINARY_METHODS = ("__getitem__", "__delitem__")
SEQUENCE_METHODS = SEQUENCE_UNARY_METHODS + SEQUENCE_BINARY_METHODS
ARITHMETIC_METHODS = (
    "__add__",
    "__sub__",
    "__truediv__",
    "__floordiv__",
    "__mul__",
    "__pow__",
    "__mod__",
)
LOGICAL_METHODS = ("__and__", "__or__", "__xor__")
BINARY_METHODS = ARITHMETIC_METHODS + LOGICAL_METHODS
RIGHT_ARITHMETIC_METHODS = (
    "__radd__",
    "__rsub__",
    "__rtruediv__",
    "__rfloordiv__",
    "__rmul__",
    "__rpow__",
    "__rmod__",
)
RIGHT_LOGICAL_METHODS = ("__rand__", "__ror__", "__rxor__")


dunder_functions_lookup = ChainMap({}, *map(vars, (builtins, operator, math, copy, os)))


def dunder_method_factory(func: Callable[[Callable], Callable], /):
    @SetNameFactory
    def factory(name: str, /):
        return func(dunder_functions_lookup[name.strip("_")])

    return factory
