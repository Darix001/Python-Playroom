from collections.abc import Callable, Iterable, Iterator
from functools import partial
from itertools import starmap
from operator import call
from typing import Any, TypeVar

T_zip_with = TypeVar("T_zip_with")
R_zip_with = TypeVar("R_zip_with")


def map_keywords(funcs: Iterable[Callable], **kw) -> Iterator[Any]:
    return map(partial(call, **kw), funcs)


def zip_with(
    func: Callable[[T_zip_with], R_zip_with], *iterables: Iterable[T_zip_with]
) -> Iterator[R_zip_with]:
    return starmap(func, zip(*iterables))
