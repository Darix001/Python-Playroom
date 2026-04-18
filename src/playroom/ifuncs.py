from collections.abc import Callable, Iterable, Iterator
from functools import partial
from itertools import chain, islice
from operator import call
from typing import Any


def map_keywords(funcs: Iterable[Callable], **kw) -> Iterator[Any]:
    return map(partial(call, **kw), funcs)


def insert(iterable: Iterable, n: int, *objs: Any) -> Iterator:
    return chain(islice(iterator := iter(iterable), n), objs, iterator)
