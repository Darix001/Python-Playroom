from collections.abc import Callable
from dataclasses import dataclass
from functools import partial
from itertools import repeat
from string import digits
from typing import Optional, Self, TypeVar

rdigits = digits[::-1]


K = TypeVar("K")
V = TypeVar("V")

# Alias for the default factory that takes a Key (K) and returns a Value (V)


@dataclass(frozen=True)
class KeyAwareCache[K, V](dict[K, V]):
    __slots__ = "_factory"
    factory: Callable[[K], V]

    def __init__(self, factory: Callable[[K], V], iterable=(), /, **kw):
        if not callable(factory):
            raise TypeError("first argument must be callable")
        object.__setattr__(self, "factory", factory)
        super().__init__(iterable, **kw)

    def __missing__(self, key: K, /) -> V:
        self[key] = value = self.factory(key)
        return value


class SentinelDict[K, V, S](dict[K, V | S]):
    __slots__ = "__missing__"
    __missing__: partial[S]

    @property
    def factory(self, /) -> partial[S]:
        return self.__missing__

    def __init__(
        self, sentinel: S, misses_limit: Optional[int] = None, /, iterable=(), **kw
    ):
        self.__missing__ = partial(
            next,
            repeat(sentinel, misses_limit)
            if misses_limit is not None
            else repeat(sentinel),
        )
        super().__init__(iterable, **kw)
