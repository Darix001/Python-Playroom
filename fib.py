import itertools as it
from collections import deque
from collections.abc import Iterator
from decimal import Decimal
from functools import partial
from math import trunc
from operator import attrgetter

fib_deque = partial(deque, (0, 1), maxlen=2)

SQRT5 = Decimal(5).sqrt()
PHI = (1 + SQRT5) / 2
PSI = (1 - SQRT5) / 2


def fib_gen():
    return it.chain(
        data := fib_deque(), it.filterfalse(data.append, map(sum, it.repeat(data)))
    )


class Fib:
    __slots__ = "indexes"
    indexes: range
    size = property(attrgetter("indexes.stop"))

    def __init__(self, n: int, /):
        self.indexes = range(n)

    def __getitem__(self, index: int, /) -> int:
        n = self.indexes[index]
        return trunc(((PHI**n - PSI**n) / SQRT5).to_integral_exact())

    def __len__(self, /) -> int:
        return self.size

    def __iter__(self, /) -> Iterator[int]:
        data = fib_deque()
        if (n := self.size) > 2:
            n -= 2
        else:
            return it.islice(data, n)
        return it.chain(
            data,
            it.filterfalse(data.append, map(sum, it.repeat(data, n))),
        )

    def __repr__(self, /):
        return f"Fib({self.size!r})"

    def __reversed__(self, /):  # PENDING
        data = deque((-self[-1], self[-2]))
        if (n := self.size) > 2:
            n -= 2
        else:
            return reversed(data) if n == 2 else it.islice(data, n)
        return map(
            abs,
            it.chain(
                data,
                it.filterfalse(data.append, map(sum, it.repeat(data, n))),
            ),
        )

    def to_list(self, /) -> list[int]:
        seq = []
        seq.extend(it.islice(it.accumulate(it.chain((0, 1), seq)), self.size))
        return seq


def main():
    from sys import argv

    n = int(argv[-1])

    fb = Fib(n)
    print(fb, fb.to_list() == list(fb))


if __name__ == "__main__":
    main()
