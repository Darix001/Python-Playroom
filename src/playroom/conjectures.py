from collections.abc import Generator
from itertools import islice
from math import trunc


def collatz[T](x: T) -> Generator[T]:
    while x != 1:
        div, mod = divmod(x, 2)
        yield (x := (x * 3) + 1 if mod else div)


def juggler[T](x: T) -> Generator[T]:
    while x != 1:
        div, mod = divmod(x, 2)
        yield (x := trunc((x * 3) / 2) if mod else div)


a = collatz(120)
b = tuple(islice(a, 200))
print(b)


a = juggler(120)
b = tuple(islice(a, 200))
print(b)
