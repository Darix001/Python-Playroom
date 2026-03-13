import builtins
import functools as ft
import itertools as it
import operator as op
import types
from collections.abc import Callable, Iterator
from typing import Any

import attrs

modules = [builtins, it, op]


@attrs.frozen
class JIterator:
    iterator: Iterator[Any] = attrs.field(converter=iter)

    def __iter__(self, /):
        return self.iterator

    def __getattr__(self, attr: str, /):
        return types.MethodType(self.register_method(attr), self)

    @classmethod
    def register_method(cls, func_name: str, /):
        if not (
            fn := next(filter(None, map(getattr, modules, it.repeat(func_name))), None)
        ):
            raise ValueError("Function Name not found: " + func_name)

        if func_name.startswith("filter") or func_name.endswith(("map", "while")):

            def method(self, /, *args: Callable):
                iterator = self.iterator
                for arg in args:
                    iterator = fn(arg, iterator)
                return type(self)(iterator)
        else:

            def method(self, /, *args, **kw):
                return fn(self.iterator, *args, **kw)

        setattr(cls, func_name, method)
        return method

    def reduce(self, func, /, *, initial):
        return ft.reduce(func, self.iterator, initial)
