from more_itertools import iequals

from fib import Fib

fib_obj = Fib(10)
fib_list = [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]


def test_fib_to_list():
    assert fib_obj.to_list() == fib_list


def test_fib_iter():
    assert iequals(fib_obj, fib_list)


def test_fib_reversed():
    assert iequals(reversed(fib_obj), reversed(fib_list))


# def test_fib_list_reverse():
#     assert fib_obj.to_list(reverse=True) == fib_list[::-1]
