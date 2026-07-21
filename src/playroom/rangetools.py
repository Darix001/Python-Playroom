import math
import operator as op
from dataclasses import dataclass

from .numtools import bytes_of_int

range_args = op.attrgetter("start", "stop", "step")


def tobytes(rng: range, /) -> bytes:
    return b"".join(map(op.methodcaller("to_bytes", bytes_of_int(rng.stop)), rng))


def pstdev(rng: range, /) -> float:
    """Compute the popular standard deviation of the range."""
    return math.sqrt(pvar(rng))


def pvar(rng: range, /) -> float:
    """Computes the popular variance of the range."""
    if (n := len(rng)) <= 1:
        return 0.0
    return (((n**2) - 1) * (rng.step**2)) / 12


pvariance = pvar


def nbytes(rng: range, /):
    return bytes_of_int(rng.stop) * len(rng)


def var(rng: range, /) -> float:
    if (n := len(rng)) <= 1:
        return 0.0
    return ((rng.step**2) * (n * (n + 1))) / 12


def stdev(rng: range, /) -> float:
    return math.sqrt(var(rng))


def mean(rng: range, /) -> float:
    return (rng.start + rng[-1]) / 2


def argmin(rng: range, /) -> int:
    return 0 if rng.step > 0 else len(rng) - 1


def argmax(rng: range, /) -> int:
    return 0 if rng.step < 0 else len(rng) - 1


def min_max(rng: range, /) -> tuple[int, int]:
    t = rng.start, rng.stop
    return t if rng.step > 0 else t[::-1]


def rmin(rng: range, /) -> int:
    return rng.start if rng.step > 0 else rng.stop


def rmax(rng: range, /) -> int:
    return rng.start if rng.step < 0 else rng.stop


def isdisjoint(rng: range, other: range) -> bool:
    return not intersect_two_ranges(rng, other)


def extended_gcd(a: int, b: int):
    """Returns (gcd, x, y) such that a*x + b*y = gcd."""
    if not a:
        return b, 0, 1
    gcd, x1, y1 = extended_gcd(b % a, a)
    x = y1 - (b // a) * x1
    y = x1
    return gcd, x, y


def intersect_two_ranges(r1: range, r2: range) -> range:
    # 1. Handle empty ranges
    if not r1 or not r2:
        return range(0)

    # 2. Extract parameters (This helper assumes positive steps for simplicity)
    # If negative steps are allowed, they should be normalized to positive first.
    start1, stop1, step1 = r1.start, r1.stop, r1.step
    start2, stop2, step2 = r2.start, r2.stop, r2.step

    if step1 < 0 or step2 < 0:
        raise NotImplementedError("This simplified solution assumes positive steps.")

    # 3. Solve the system: start1 + x * step1 = start2 + y * step2
    # Which simplifies to: x * step1 - y * step2 = start2 - start1
    # This is a Diophantine equation of the form: A*x + B*y = C
    a, b, c = step1, -step2, start2 - start1
    gcd, x_coeff, _ = extended_gcd(a, abs(b))

    # If the difference in starts is not divisible by the GCD of the steps,
    # they can never align.
    if not (c % gcd):
        return range(0)

    # 4. Find the first alignment point (smallest positive x)
    # Scale our solution up to match 'c'
    factor = c // gcd
    x_scaled = x_coeff * factor

    # The step of the modular solution is step2 // gcd
    mod_step = abs(b) // gcd
    x_aligned = x_scaled % mod_step

    # Calculate actual starting value
    common_start = start1 + x_aligned * step1

    # 5. Determine the intersection bounds
    common_step = math.lcm(step1, step2)
    common_stop = min(stop1, stop2)

    # Ensure our start is within bounds
    actual_start = max(start1, start2)
    if common_start < actual_start:
        # Shift the start forward by common_steps until it falls inside the overlap
        needed_steps = math.ceil((actual_start - common_start) / common_step)
        common_start += needed_steps * common_step

    if common_start >= common_stop:
        return range(0)

    return range(common_start, common_stop, common_step)


def issubrange(rng: range, other: range) -> bool:
    return not rng.step % other.step and rng.start in other and rng[-1] in other


def issuperrange(rng: range, other: range) -> bool:
    return issubrange(other, rng)


def sum(rng: range, /) -> int:
    if rng:
        return (len(rng) * (rng[0] + rng[-1])) // 2
    return 0


def prod(rng: range, /) -> int:
    if not rng or 0 in rng:
        return 0
    elif rng.step == rng.start == 1:
        return math.factorial(rng.stop - 1)
    else:
        return math.prod(rng)


@dataclass
class Number:
    __slots__ = "x"
    x: int

    def __add__(self, rng: range):
        return range(rng.start + self.x, rng.stop + self.x, rng.step)

    __radd__ = __add__

    def __sub__(self, rng: range):
        return range(rng.start + self.x, rng.stop + self.x, rng.step)

    __rsub__ = __sub__

    def __mul__(self, rng: range):
        return range(rng.start * self.x, rng.stop * self.x, rng.step * self.x)

    __rmul__ = __mul__

    def __floordiv__(self, rng: range):
        return range(rng.start // self.x, rng.stop // self.x, rng.step // self.x)

    __rfloordiv__ = __floordiv__

    def __lshift__(self, rng: range):
        return range(rng.start << self.x, rng.stop << self.x, rng.step << self.x)

    __rlshift__ = __lshift__


def invert(rng: range, /) -> range:
    return range(~rng.start, ~rng.stop, -rng.step)


def pos(rng: range, /) -> range:
    return rng


def neg(rng: range, /) -> range:
    return range(-rng.start, -rng.stop, -rng.step)


inv = invert


def gt(rng: range, other):
    pass
