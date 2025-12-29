from typing import Any
from collections.abc import Sequence, Callable, Iterator

import string
import functools as ft
import itertools as it
import operator as op


def chain_method_call(*args: str):
    return arg_compose(*map(op.methodcaller, args))


def cycle_seq(sequence: Sequence):
    return it.chain.from_iterable(it.repeat(sequence))


def composer(
    func: Callable[[list[Any], Iterator, Iterator[Callable]], Callable], /
) -> Callable:
    @ft.wraps(func)
    def compose(*funcs: Callable) -> Callable:
        return func(data := [None], cycle_seq(data), reversed(funcs))

    return compose


@composer
def compose(data, iterator, ifuncs) -> Callable:
    """Compose multiple functions into one single function."""
    first = next(ifuncs)

    for func in ifuncs:
        iterator = map(func, iterator)

    def composed(*args, **kw):
        data[0] = first(*args, **kw)
        return next(iterator)

    return composed


@composer
def arg_compose(data, iterator, ifuncs) -> Callable:
    """Compose multiple function into one.
    The first function will be called
    with only one positional argument."""

    for func in ifuncs:
        iterator = map(func, iterator)

    def composed(value, /):
        data[0] = value
        return next(iterator)

    return composed


@composer
def args_compose(data, iterator, ifuncs):
    """Compose multiple functions into one single function."""
    iterator = it.starmap(next(ifuncs), cycle_seq(data))

    for func in ifuncs:
        iterator = map(func, iterator)

    def composed(*args):
        data[0] = args
        return next(iterator)

    return composed


def zfilled(ndigits: int, /, *args: int | None):
    """Iterator over all string numbers from start to stop with fixed ndigits
    filling with zeros on the left when needed."""
    return it.islice(it.product(string.digits, repeat=ndigits), *args)


def main():
    # One arg compose
    string_fn = chain_method_call("expandtabs", "casefold", "strip")
    assert string_fn("   Name\tLastName  ") == "name    lastname"

    # Multiple args compose

    int_fn = args_compose(op.inv, pow)
    assert int_fn(12, 2) == ~(12**2)


if __name__ == "__main__":
    main()
