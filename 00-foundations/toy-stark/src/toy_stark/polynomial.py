"""Polynomials in one variable over F_p.

A polynomial is a finite sum

    f(X) = c_0 + c_1 X + c_2 X^2 + ... + c_d X^d,   c_i in F_p,  c_d != 0

and d is its degree. The fact that makes polynomials useful for proofs:

    a nonzero polynomial of degree d has at most d roots.

Intuition: two different polynomials of degree at most d can agree on at most
d points, so if you evaluate them on many more than d points they disagree
almost everywhere. A small lie about the computation becomes a large,
easy-to-spot difference.
"""

from __future__ import annotations

from collections.abc import Iterable

from toy_stark.field import FieldElement


class Polynomial:
    """A polynomial stored as its coefficients, lowest degree first."""

    __slots__ = ("_coefficients",)

    def __init__(self, coefficients: Iterable[FieldElement]) -> None:
        coeffs = list(coefficients)
        for c in coeffs:
            if not isinstance(c, FieldElement):
                raise TypeError(f"coefficients must be FieldElement, got {type(c).__name__}")
        # Trailing zeros do not change the polynomial (1 + 2X + 0X^2 is
        # 1 + 2X), so remove them. Then equal polynomials have equal tuples.
        while coeffs and coeffs[-1].is_zero():
            coeffs.pop()
        self._coefficients = tuple(coeffs)

    @property
    def coefficients(self) -> tuple[FieldElement, ...]:
        """coefficients[i] multiplies X^i."""
        return self._coefficients

    @staticmethod
    def zero() -> Polynomial:
        return Polynomial([])

    @staticmethod
    def constant(c: FieldElement) -> Polynomial:
        return Polynomial([c])

    @staticmethod
    def X() -> Polynomial:
        """The polynomial X itself."""
        return Polynomial([FieldElement.zero(), FieldElement.one()])

    def is_zero(self) -> bool:
        return not self._coefficients

    def degree(self) -> int:
        """Index of the highest nonzero coefficient.

        The zero polynomial gets -1. That keeps degree() equal to
        len(coefficients) - 1, matches STARK 101, and makes "deg r < deg b"
        a valid stop condition in division when the remainder is zero. The
        price: deg(f * g) = deg f + deg g only holds when neither factor is
        zero. (The convention that keeps the rule for zero too is
        deg 0 = minus infinity.)
        """
        return len(self._coefficients) - 1

    def __repr__(self) -> str:
        return f"Polynomial({[c.value for c in self._coefficients]})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Polynomial):
            return NotImplemented
        return self._coefficients == other._coefficients

    def __hash__(self) -> int:
        return hash(self._coefficients)

    # Horner's rule:
    #
    #     c_0 + c_1 x + c_2 x^2 + c_3 x^3 = c_0 + x (c_1 + x (c_2 + x c_3))
    #
    # Intuition: work from the highest coefficient down, multiplying by x
    # once per step. That is one multiplication per coefficient instead of
    # computing every power of x separately.
    def __call__(self, x: FieldElement) -> FieldElement:
        if not isinstance(x, FieldElement):
            raise TypeError(f"can only evaluate at a FieldElement, got {type(x).__name__}")
        result = FieldElement.zero()
        for c in reversed(self._coefficients):
            result = result * x + c
        return result
