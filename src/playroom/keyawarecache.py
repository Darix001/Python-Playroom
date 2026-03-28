import itertools as it
import operator as op
from collections.abc import Callable, Iterator, Sequence
from functools import wraps
from string import digits
from typing import Any, Generic, TypeVar

rdigits = digits[::-1]


K = TypeVar("K")
V = TypeVar("V")

# Alias for the default factory that takes a Key (K) and returns a Value (V)
FactoryFunc = Callable[[K], V]


class KeyAwareCache(dict[K, V], Generic[K, V]):
    __slots__ = "_factory"
    _factory: FactoryFunc[K, V]

    def __init__(self, factory: FactoryFunc[K, V], /):
        if not callable(factory):
            raise TypeError("first argument must be callable")
        self._factory = factory

    def __missing__(self, key: K, /) -> V:
        self[key] = value = self._factory(key)
        return value
