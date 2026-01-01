from functools import partial
from collections import deque
import itertools as it


fib_deque = partial(deque, (0, 1), maxlen=2)


def fib():
    return it.chain(
        data := fib_deque(), it.filterfalse(data.append, map(sum, it.repeat(data)))
    )


def fib_until(stop):
    data = deque((0, 1), maxlen=2)
    return it.chain(
        data := fib_deque(), it.filterfalse(data.append, iter(partial(sum, data), stop))
    )


def main():
    print(*it.islice(fib(), 10))
    print(*fib_until(13))


if __name__ == "__main__":
    main()
