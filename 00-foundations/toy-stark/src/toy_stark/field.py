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
