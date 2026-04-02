from collections.abc import Callable, Iterable, Iterator
from functools import partial
from operator import call
from typing import Any


def map_keywords(funcs: Iterable[Callable], **kw) -> Iterator[Any]:
    return map(partial(call, **kw), funcs)
