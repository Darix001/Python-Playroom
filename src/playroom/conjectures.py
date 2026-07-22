from collections.abc import Generator
from math import isqrt, trunc


def collatz(x: int) -> Generator[int]:
    while x != 1:
        div, mod = divmod(x, 2)
        yield (x := (x * 3) + 1 if mod else div)


def juggler(x: int) -> Generator[int]:
    while x != 1:
        yield (x := trunc(x**1.5) if x % 2 else isqrt(x))
