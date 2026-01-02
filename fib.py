import itertools as it
from collections import deque
from collections.abc import Iterable, Iterator
from functools import partial
from math import sqrt

import polars as pl

fib_deque = partial(deque, (0, 1), maxlen=2)
run_expr = pl.LazyFrame().select


def fib_func(func, /):
    def function(n: int | None = None, /) -> Iterator[int]:
        iterable = func(data := fib_deque(), n)
        return it.chain(data, it.filterfalse(data.append, iterable))

    return function


@fib_func
def fib(*args):
    if args[-1] is None:
        args = args[:-1]
    return map(sum, it.repeat(*args))


@fib_func
def fib_until(data: deque[int], stop: int):
    return iter(partial(sum, data), stop)


five_sqrt = sqrt(5)
phi = (1 + five_sqrt) / 2
psi = (1 - five_sqrt) / 2
fibc = pl.col.fib
fib_expr = (phi**fibc - psi**fibc) / five_sqrt


def polars_fib(
    size: int | Iterable[int], dtype: pl.DataType | type | pl.DataTypeExpr
) -> pl.LazyFrame:
    if isinstance(size, int):
        lf = pl.select(fib=pl.int_range(0, size, dtype=dtype), eager=False)
    else:
        lf = pl.LazyFrame({"fib": size}, {"fib": dtype})

    return lf.select(
        # Apply Binet's Formula
        fib=fib_expr.cast(dtype)
    )


def main():
    from sys import argv

    fibs = polars_fib(int(argv[-1]), pl.UInt64)
    print(fibs.collect())


if __name__ == "__main__":
    main()
