from collections.abc import Callable
from types import SimpleNamespace
from typing import Generic, Self, TypeVar

V = TypeVar("V")
T = TypeVar("T")


class FunctionalNamespace(SimpleNamespace, Generic[T]):
    """A Functional namespace is a namespace where all attributes are
    the result of calling the function func with the values of the attributes passed."""

    __slots__ = "_factory"
    _factory: Callable[[V], T]
    __dict__: dict[str, T]

    def __init__(self, func: Callable[[V], T], /, **keywords: V):
        # We initialize the underlying dict via SimpleNamespace logic
        # but transformed by our function.
        transformed: dict[str, T] = {k: func(v) for k, v in keywords.items()}
        super().__init__(**transformed)
        object.__setattr__(self, "_factory", func)

    __getattr__: Callable[[Self, str], T]


FuncNamespace = FunctionalNamespace
