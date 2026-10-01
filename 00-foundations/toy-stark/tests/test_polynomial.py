"""Tests for polynomials over F_p."""

import random

import pytest

from toy_stark.field import P, FieldElement
from toy_stark.polynomial import Polynomial

rng = random.Random(1)


def F(n: int) -> FieldElement:
    return FieldElement(n)


def poly(*coeffs: int) -> Polynomial:
    """poly(1, 2, 3) is 1 + 2X + 3X^2."""
    return Polynomial([F(c) for c in coeffs])


def rand_poly(degree: int) -> Polynomial:
    """A random polynomial of exactly the given degree."""
    coeffs = [F(rng.randrange(P)) for _ in range(degree)]
    coeffs.append(F(rng.randrange(1, P)))  # nonzero leading coefficient
    return Polynomial(coeffs)


# --- construction, degree, equality ----------------------------------------


def test_coefficients_are_stored_lowest_degree_first():
    assert poly(1, 2, 3).coefficients == (F(1), F(2), F(3))


def test_trailing_zero_coefficients_are_trimmed():
    assert poly(1, 2, 0, 0).coefficients == (F(1), F(2))
    assert poly(1, 2, 0, 0) == poly(1, 2)


def test_degree_is_index_of_highest_nonzero_coefficient():
    assert poly(7).degree() == 0
    assert poly(0, 0, 5).degree() == 2


def test_zero_polynomial_has_degree_minus_one():
    assert Polynomial.zero().degree() == -1
    assert poly(0, 0).degree() == -1
    assert poly(0, 0).is_zero()
    assert not poly(1).is_zero()


def test_equal_polynomials_hash_alike():
    assert hash(poly(1, 2)) == hash(poly(1, 2, 0))
    assert poly(1, 2) != poly(2, 1)


def test_polynomial_is_not_equal_to_a_field_element():
    assert poly(3) != F(3)


def test_coefficients_must_be_field_elements():
    with pytest.raises(TypeError):
        Polynomial([1, 2, 3])


def test_x_is_the_degree_one_monomial():
    assert Polynomial.X() == poly(0, 1)


def test_constant_wraps_a_field_element():
    assert Polynomial.constant(F(9)) == poly(9)


# --- evaluation ------------------------------------------------------------


def test_evaluation_by_hand():
    # 1 + 2X + 3X^2 at X = 2 is 1 + 4 + 12 = 17.
    assert poly(1, 2, 3)(F(2)) == F(17)


def test_evaluation_point_must_be_a_field_element():
    with pytest.raises(TypeError):
        poly(1, 2)(3)


def test_evaluating_zero_polynomial_gives_zero():
    assert Polynomial.zero()(F(5)) == F(0)


def test_evaluation_at_zero_is_the_constant_term():
    p = rand_poly(10)
    assert p(F(0)) == p.coefficients[0]


def test_evaluation_matches_naive_sum_of_powers():
    p = rand_poly(20)
    x = F(rng.randrange(P))
    naive = F(0)
    for i, c in enumerate(p.coefficients):
        naive = naive + c * x**i
    assert p(x) == naive
