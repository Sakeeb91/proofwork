"""The prime field F_p with p = 3 * 2^30 + 1.

A field is a set where you can add, subtract, multiply, and divide (by
anything except zero) and the usual rules of algebra hold. The integers
mod p form a field exactly when p is prime:

    F_p = {0, 1, ..., p - 1},   a + b := (a + b) mod p,   a * b := (a * b) mod p

Intuition: it is arithmetic on a clock with p hours. Primality is what
guarantees every nonzero hour has a multiplicative inverse, so division
never gets stuck.

Why a STARK wants a finite field at all: the prover's claim is turned into
statements about polynomials, and over a finite field those polynomials can
be evaluated and compared exactly, with no rounding and with bounded size.
"""

from __future__ import annotations

# p = 3 * 2^30 + 1 = 3221225473. The same prime as StarkWare's STARK 101.
# It fits in 32 bits, and p - 1 = 3 * 2^30 is divisible by a large power of
# two, which later gives us evaluation domains of size 2^k for every k <= 30.
P = 3 * 2**30 + 1

# A generator of the multiplicative group F_p^* = F_p minus {0}: every
# nonzero element is a power of it. The tests verify this rather than trust
# it: the order of g divides p - 1 = 3 * 2^30, and g^((p-1)/2) != 1 and
# g^((p-1)/3) != 1 rule out every proper divisor.
GENERATOR = 5


class FieldElement:
    """One element of F_p, stored as its canonical representative in [0, p)."""

    __slots__ = ("_value",)

    def __init__(self, value: int) -> None:
        # Python's % always returns a result in [0, P) for positive P, even
        # for negative inputs, so -1 becomes p - 1.
        self._value = value % P

    @property
    def value(self) -> int:
        """The canonical integer representative. Read-only: elements are values."""
        return self._value

    @staticmethod
    def zero() -> FieldElement:
        """Additive identity: a + 0 = a."""
        return FieldElement(0)

    @staticmethod
    def one() -> FieldElement:
        """Multiplicative identity: a * 1 = a."""
        return FieldElement(1)

    @staticmethod
    def generator() -> FieldElement:
        """A generator g of F_p^*: its powers g^0, ..., g^(p-2) hit every nonzero element."""
        return FieldElement(GENERATOR)

    # An n-th root of unity is w with w^n = 1. It is primitive if no smaller
    # positive power is 1, so that 1, w, w^2, ..., w^(n-1) are n distinct
    # points. For any n dividing p - 1:
    #
    #     w = g^((p-1)/n)
    #
    # Intuition: g walks once around all p - 1 nonzero elements. Taking
    # steps of size (p-1)/n makes the walk close up after exactly n steps.
    # These n points are the discrete analogue of the n-th roots of unity
    # e^(2 pi i k / n) on the complex unit circle, and they are the
    # evaluation domains for the FFT and FRI later. p - 1 = 3 * 2^30 means
    # power-of-two domains exist up to size 2^30.
    @staticmethod
    def primitive_root_of_unity(n: int) -> FieldElement:
        if n <= 0 or (P - 1) % n != 0:
            raise ValueError(f"no primitive {n}-th root of unity: n must divide p - 1 = 3 * 2^30")
        return FieldElement.generator() ** ((P - 1) // n)

    def is_zero(self) -> bool:
        return self._value == 0

    def __repr__(self) -> str:
        return f"FieldElement({self._value})"

    # Two integers name the same field element iff they differ by a multiple
    # of p. Because we always store the reduced value, that is plain equality.
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FieldElement):
            return NotImplemented
        return self._value == other._value

    def __hash__(self) -> int:
        return hash(self._value)

    # (a + b) mod p. The sum of two values below p is below 2p, so one
    # reduction brings it back into range.
    def __add__(self, other: FieldElement) -> FieldElement:
        if not isinstance(other, FieldElement):
            return NotImplemented
        return FieldElement(self._value + other._value)

    # -a is the unique element with a + (-a) = 0, namely p - a (and -0 = 0).
    def __neg__(self) -> FieldElement:
        return FieldElement(-self._value)

    # a - b := a + (-b).
    def __sub__(self, other: FieldElement) -> FieldElement:
        if not isinstance(other, FieldElement):
            return NotImplemented
        return FieldElement(self._value - other._value)

    # (a * b) mod p. Python integers never overflow, so we can multiply
    # first and reduce after. In a fast implementation the product needs
    # 64 bits, which is one reason a 32-bit prime is convenient.
    def __mul__(self, other: FieldElement) -> FieldElement:
        if not isinstance(other, FieldElement):
            return NotImplemented
        return FieldElement(self._value * other._value)

    # a^n by square-and-multiply. Write n in binary, n = sum of b_i * 2^i:
    #
    #     a^n = product over i with b_i = 1 of a^(2^i)
    #
    # Intuition: squaring repeatedly gives a, a^2, a^4, a^8, ... for free,
    # and we multiply together the ones the binary digits of n select. That
    # costs about log2(n) multiplications instead of n, which is what makes
    # an exponent like p - 2 (about 3 billion) affordable.
    def __pow__(self, exponent: int) -> FieldElement:
        if not isinstance(exponent, int):
            return NotImplemented
        if exponent < 0:
            # a^(-n) := (a^-1)^n
            return self.inverse() ** (-exponent)
        result = FieldElement.one()
        square = self  # holds a^(2^i) at step i
        while exponent > 0:
            if exponent & 1:
                result = result * square
            square = square * square
            exponent >>= 1
        return result

    # Fermat's little theorem: for prime p and a != 0,
    #
    #     a^(p-1) = 1   so   a * a^(p-2) = 1   so   a^-1 = a^(p-2)
    #
    # Intuition: the p - 1 nonzero elements form a group under
    # multiplication, and raising any group element to the size of the
    # group gives the identity. The other standard route is the extended
    # Euclidean algorithm (Python's pow(a, -1, p)); the tests check that
    # both agree.
    def inverse(self) -> FieldElement:
        if self.is_zero():
            raise ZeroDivisionError("0 has no multiplicative inverse in F_p")
        return self ** (P - 2)

    # a / b := a * b^-1.
    def __truediv__(self, other: FieldElement) -> FieldElement:
        if not isinstance(other, FieldElement):
            return NotImplemented
        return self * other.inverse()
