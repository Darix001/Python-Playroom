import builtins
import dataclasses as dt
import functools as ft
import itertools as it
import operator as op
import types
from collections.abc import Callable, Iterable, Iterator
from typing import Any

modules = [builtins, it, op]


@dt.dataclass
class JIterator:
    iterator: Iterator[Any]
    __slots__ = "iterator"
    iterator = dt.field()

    def __init__(self, iterable: Iterable, /):
        self.iterator = iter(iterable)

    def __iter__(self, /):
        return self.iterator

    def __getattr__(self, attr: str, /):
        return types.MethodType(self.dummy_method, attr)

    def dummy_method(self, method_name, /, *args):
        if not (
            fn := next(
                filter(None, map(getattr, modules, it.repeat(method_name))), None
            )
        ):
            raise AttributeError("Function Name not found: " + method_name)

        if not args:

            def method(self, /):
                fn(self.iterator)

        elif all(map(callable, args)):

            def method(self, /, *args: Callable):
                iterator = self.iterator
                for arg in args:
                    iterator = fn(arg, iterator)
                self.iterator = Iterator
        else:
            return NotImplemented

        setattr(type(self), method_name, method)
        return method(self, *args)

    def reduce(self, func, /, *, initial):
        return ft.reduce(func, self.iterator, initial)


breakpoint()
