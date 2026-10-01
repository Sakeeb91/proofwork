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

    # Add coefficient by coefficient; the shorter polynomial is padded with
    # zeros. The constructor trims any cancellation at the top.
    def __add__(self, other: Polynomial) -> Polynomial:
        if not isinstance(other, Polynomial):
            return NotImplemented
        a, b = self._coefficients, other._coefficients
        zero = FieldElement.zero()
        n = max(len(a), len(b))
        return Polynomial(
            (a[i] if i < len(a) else zero) + (b[i] if i < len(b) else zero) for i in range(n)
        )

    def __neg__(self) -> Polynomial:
        return Polynomial(-c for c in self._coefficients)

    def __sub__(self, other: Polynomial) -> Polynomial:
        if not isinstance(other, Polynomial):
            return NotImplemented
        return self + (-other)

    def scale(self, c: FieldElement) -> Polynomial:
        """Multiply every coefficient by the field element c."""
        return Polynomial(c * a for a in self._coefficients)

    # Schoolbook multiplication. The coefficient of X^k in f * g is
    #
    #     sum over i + j = k of f_i * g_j
    #
    # Intuition: every term of f meets every term of g, and X^i * X^j lands
    # in slot i + j. Cost is (deg f + 1)(deg g + 1) field multiplications.
    def __mul__(self, other: Polynomial) -> Polynomial:
        if not isinstance(other, Polynomial):
            return NotImplemented
        if self.is_zero() or other.is_zero():
            return Polynomial.zero()
        a, b = self._coefficients, other._coefficients
        out = [FieldElement.zero()] * (len(a) + len(b) - 1)
        for i, ai in enumerate(a):
            for j, bj in enumerate(b):
                out[i + j] = out[i + j] + ai * bj
        return Polynomial(out)

    # Long division. Given a and b != 0, find q and r with
    #
    #     a = q * b + r,   deg r < deg b
    #
    # Intuition: the same procedure as long division of integers. Cancel
    # the leading term of what is left by subtracting the right multiple of
    # b, record that multiple in q, repeat until what is left has smaller
    # degree than b. Dividing by b's leading coefficient is where we need a
    # field: over the integers this step can fail.
    def __divmod__(self, other: Polynomial) -> tuple[Polynomial, Polynomial]:
        if not isinstance(other, Polynomial):
            return NotImplemented
        if other.is_zero():
            raise ZeroDivisionError("division by the zero polynomial")
        b = other._coefficients
        lead_inv = b[-1].inverse()
        remainder = list(self._coefficients)
        quotient = [FieldElement.zero()] * max(len(remainder) - len(b) + 1, 0)
        # shift is the power of X in the current quotient term.
        for shift in range(len(remainder) - len(b), -1, -1):
            factor = remainder[shift + len(b) - 1] * lead_inv
            quotient[shift] = factor
            for j, bj in enumerate(b):
                remainder[shift + j] = remainder[shift + j] - factor * bj
        return Polynomial(quotient), Polynomial(remainder)

    def __floordiv__(self, other: Polynomial) -> Polynomial:
        if not isinstance(other, Polynomial):
            return NotImplemented
        return divmod(self, other)[0]

    def __mod__(self, other: Polynomial) -> Polynomial:
        if not isinstance(other, Polynomial):
            return NotImplemented
        return divmod(self, other)[1]
