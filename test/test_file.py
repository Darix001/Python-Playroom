import operator as op
import sys

sys.path.append(r"C:\Users\Daisy Garcia\Documents\Code\playroom\src")
from more_itertools import iequals

from playroom.conjectures import collatz, juggler
from playroom.dicttools import KeyAwareCache, SentinelDict
from playroom.fib import Fib
from playroom.iterpipe import MutableIter, ipartial, ipipe

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
def test_iterpipe():
    a = MutableIter[str]("DXctuIvfUTFD^%4#^%*&GOGuibcTRxcKY").composed_filter(
        str.isalpha,
        str.islower,
        str.isascii,
    )
    print(a.scalar(",".join))

    @ipipe
    def pairs_hex_blob(iterable: MutableIter[int]) -> ipartial[bytes]:
        return iterable.filterfalse(op.methodcaller("__mod__", 2)).composed_map(
            op.methodcaller("encode"), hex
        )

    print(b"-".join(pairs_hex_blob(range(12, 1200, 34))))


def test_dicttools():
    data = SentinelDict[str, int, None](None, a=2)
    assert data["a"] is not None and data["sdf"] is None

    cache = KeyAwareCache(int)
    assert cache["12"] == 12
    assert cache.get("12") == 12


def test_conjectures():
    c = collatz(3)
    j = juggler(3)
    assert tuple(c) == (10, 5, 16, 8, 4, 2, 1)
    assert tuple(j) == (5, 11, 36, 6, 2, 1)
