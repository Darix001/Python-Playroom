from collections.abc import Callable, Generator
from itertools import islice
from operator import methodcaller


def conjecture_deco(
    func: Callable[[int], int],
) -> Callable[[int], Generator[int]]:
    def generator(x: int) -> Generator[int]:
        while x != 1:
            div, mod = divmod(x, 2)
            yield (x := func(x * 3) if mod else div)

    return generator


collatz = conjecture_deco(methodcaller("__add__", 1))

juggler = conjecture_deco(methodcaller("__floordiv__", 2))


# def collatz[T](x: T) -> Generator[T]:
#     while x != 1:
#         div, mod = divmod(x, 2)
#         yield (x := (x * 3) + 1 if mod else div)


# def juggler[T](x: T) -> Generator[T]:
#     while x != 1:
#         div, mod = divmod(x, 2)
#         yield (x := trunc((x * 3) / 2) if mod else div)


a = collatz(120)
b = tuple(islice(a, 200))
print(b)


a = juggler(120)
b = tuple(islice(a, 200))
print(b)
