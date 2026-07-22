from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass
from functools import partial, reduce
from itertools import chain, repeat
from operator import methodcaller, or_
from string import digits
from typing import Optional, SupportsIndex, TypeVar

from playroom.iterpipe import Iter

rdigits = digits[::-1]


K = TypeVar("K")
V = TypeVar("V")

# Alias for the default factory that takes a Key (K) and returns a Value (V)


@dataclass(frozen=True)
class KeyAwareCache[K, V](dict[K, V]):
    __slots__ = "factory"
    factory: Callable[[K], V]

    def __init__(self, factory: Callable[[K], V], iterable=(), /, **kw):
        if not callable(factory):
            raise TypeError("first argument must be callable")
        object.__setattr__(self, "factory", factory)
        super().__init__(iterable, **kw)

    def __missing__(self, key: K, /) -> V:
        self[key] = value = self.factory(key)
        return value

    def __repr__(self, /) -> str:
        data = super().__repr__()
        return f"{type(self).__name__}({self.factory!r}, {data})"


@dataclass(frozen=True)
class SentinelDict[K, V, S](dict[K, V | S]):
    __slots__ = "__missing__", "sentinel", "misses_limit"
    __missing__: partial[S]
    sentinel: S
    misses_limit: SupportsIndex

    @property
    def factory(self, /) -> partial[S]:
        return self.__missing__

    def __init__(
        self,
        sentinel: S,
        misses_limit: Optional[SupportsIndex] = None,
        /,
        iterable=(),
        **kw,
    ):
        super().__init__(iterable, **kw)
        object.__setattr__(
            self,
            "__missing__",
            partial(
                next,
                repeat(sentinel, misses_limit)
                if misses_limit is not None
                else repeat(sentinel),
            ),
        )
        object.__setattr__(self, "sentinel", sentinel)
        object.__setattr__(self, "misses_limit", misses_limit)

    def __repr__(self, /) -> str:
        data = super().__repr__()
        return (
            f"{type(self).__name__}({self.sentinel!r}, {self.misses_limit!r}, {data})"
        )


@dataclass(frozen=True)
class ChainMapView[K, V](Mapping[K, V]):
    __slots__ = "maps"
    maps: tuple[Mapping[K, V]]

    def __init__(self, *maps: Mapping[K, V]):
        object.__setattr__(self, "maps", maps)

    def get[T](self, key: K, default: T = None) -> V | T:
        sentinel = object()
        values = map(methodcaller("get", key, sentinel), self.maps)
        for value in values:
            if value is not sentinel:
                return value
        else:
            return default

    def copy(self, /):
        return self

    def __len__(self, /) -> int:
        return len(set().union(*self.maps))

    def __iter__(self, /) -> Iterator[K]:
        return chain.from_iterable(self.maps)

    def __reversed__(self, /) -> Iterator[K]:
        return chain.from_iterable(map(reversed, self.maps))

    def __bool__(self, /) -> bool:
        return any(self.maps)


a = ChainMapView[str, int]({"12": 12})
b = a.get("12", 21.2)
