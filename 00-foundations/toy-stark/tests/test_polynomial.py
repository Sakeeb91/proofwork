"""Tests for polynomials over F_p."""

import random

import pytest

from toy_stark.domain import subgroup
from toy_stark.field import P, FieldElement
from toy_stark.polynomial import Polynomial, interpolate, vanishing_polynomial

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


# --- ring operations -------------------------------------------------------


def test_addition_by_hand():
    assert poly(1, 2) + poly(3, 4, 5) == poly(4, 6, 5)


def test_addition_can_lower_the_degree():
    # (1 + X) + (1 - X) = 2
    assert poly(1, 1) + poly(1, -1) == poly(2)


def test_subtracting_a_polynomial_from_itself_gives_zero():
    p = rand_poly(8)
    assert p - p == Polynomial.zero()
    assert p + (-p) == Polynomial.zero()


def test_multiplication_by_hand():
    # (1 + X)(1 - X) = 1 - X^2
    assert poly(1, 1) * poly(1, -1) == poly(1, 0, -1)


def test_multiplying_by_zero_gives_zero():
    assert rand_poly(5) * Polynomial.zero() == Polynomial.zero()
    assert Polynomial.zero() * rand_poly(5) == Polynomial.zero()


def test_degree_of_product_is_sum_of_degrees():
    # Holds because F_p has no zero divisors: leading coefficients multiply
    # to something nonzero.
    a, b = rand_poly(7), rand_poly(11)
    assert (a * b).degree() == 18


def test_ring_laws_on_random_polynomials():
    for _ in range(10):
        a, b, c = rand_poly(5), rand_poly(6), rand_poly(4)
        assert a + b == b + a
        assert a * b == b * a
        assert (a + b) + c == a + (b + c)
        assert (a * b) * c == a * (b * c)
        assert a * (b + c) == a * b + a * c


def test_evaluation_is_a_ring_homomorphism():
    # Evaluating then combining equals combining then evaluating. This is
    # why a polynomial identity can be spot-checked at a random point.
    a, b = rand_poly(9), rand_poly(6)
    x = F(rng.randrange(P))
    assert (a + b)(x) == a(x) + b(x)
    assert (a * b)(x) == a(x) * b(x)


def test_scaling_by_a_field_element():
    assert poly(1, 2, 3).scale(F(2)) == poly(2, 4, 6)
    assert poly(1, 2, 3).scale(F(0)) == Polynomial.zero()


# --- division with remainder -----------------------------------------------


def test_division_by_hand():
    # X^2 - 1 = (X - 1)(X + 1) + 0
    q, r = divmod(poly(-1, 0, 1), poly(-1, 1))
    assert q == poly(1, 1)
    assert r == Polynomial.zero()


def test_division_with_nonzero_remainder_by_hand():
    # X^2 + 1 = (X - 1)(X + 1) + 2
    q, r = divmod(poly(1, 0, 1), poly(-1, 1))
    assert q == poly(1, 1)
    assert r == poly(2)


def test_division_identity_and_remainder_degree():
    # a = q * b + r with deg r < deg b. Existence and uniqueness of (q, r)
    # is the division theorem for polynomials over a field.
    for _ in range(20):
        a, b = rand_poly(rng.randrange(0, 15)), rand_poly(rng.randrange(0, 8))
        q, r = divmod(a, b)
        assert a == q * b + r
        assert r.degree() < b.degree()


def test_dividing_a_lower_degree_polynomial_gives_zero_quotient():
    a, b = rand_poly(3), rand_poly(5)
    assert divmod(a, b) == (Polynomial.zero(), a)


def test_exact_division_recovers_the_factor():
    a, b = rand_poly(6), rand_poly(4)
    assert (a * b) // b == a
    assert (a * b) % b == Polynomial.zero()


def test_floor_division_and_mod_with_nonzero_remainder():
    # X^2 + 1 = (X - 1)(X + 1) + 2
    assert poly(1, 0, 1) // poly(-1, 1) == poly(1, 1)
    assert poly(1, 0, 1) % poly(-1, 1) == poly(2)


def test_division_by_zero_polynomial_raises():
    with pytest.raises(ZeroDivisionError):
        divmod(rand_poly(3), Polynomial.zero())


def test_remainder_theorem():
    # f(X) mod (X - a) is the constant f(a). So f(a) = 0 exactly when
    # (X - a) divides f. Constraints in a STARK are checked this way.
    f = rand_poly(12)
    a = F(rng.randrange(P))
    assert f % poly(-a.value, 1) == Polynomial.constant(f(a))


# --- vanishing polynomial --------------------------------------------------


def test_vanishing_polynomial_is_zero_on_its_points_and_has_their_count_as_degree():
    points = [F(3), F(10), F(77)]
    z = vanishing_polynomial(points)
    assert z.degree() == 3
    assert all(z(x) == F(0) for x in points)
    assert z(F(4)) != F(0)


def test_vanishing_polynomial_of_no_points_is_one():
    assert vanishing_polynomial([]) == poly(1)


def test_vanishing_polynomial_rejects_repeated_points():
    with pytest.raises(ValueError):
        vanishing_polynomial([F(1), F(1)])


def test_vanishing_polynomial_of_a_subgroup_is_x_to_the_n_minus_one():
    # Every element of the size-n subgroup satisfies x^n = 1, so X^n - 1
    # has those n roots, and a monic degree-n polynomial with n known roots
    # is determined. A product of n linear factors collapses to two terms.
    n = 16
    expected = Polynomial([F(-1)] + [F(0)] * (n - 1) + [F(1)])
    assert vanishing_polynomial(subgroup(n)) == expected


# --- interpolation ---------------------------------------------------------


def test_interpolation_through_two_points_is_the_line():
    # Through (0, 1) and (1, 3): f = 1 + 2X.
    assert interpolate([F(0), F(1)], [F(1), F(3)]) == poly(1, 2)


def test_interpolant_passes_through_every_point():
    xs = [F(i) for i in range(1, 21)]
    ys = [F(rng.randrange(P)) for _ in xs]
    f = interpolate(xs, ys)
    assert all(f(x) == y for x, y in zip(xs, ys))
    assert f.degree() < len(xs)


def test_interpolation_recovers_a_polynomial_from_its_values():
    # Uniqueness: a polynomial of degree < n is determined by n values.
    f = rand_poly(11)
    xs = subgroup(16)[:12]
    assert interpolate(xs, [f(x) for x in xs]) == f


def test_interpolating_constant_values_gives_a_constant():
    xs = subgroup(8)
    assert interpolate(xs, [F(7)] * 8) == poly(7)


def test_interpolating_no_points_gives_zero():
    assert interpolate([], []) == Polynomial.zero()


def test_interpolation_rejects_repeated_x_values():
    with pytest.raises(ValueError):
        interpolate([F(1), F(1)], [F(2), F(3)])


def test_interpolation_rejects_mismatched_lengths():
    with pytest.raises(ValueError):
        interpolate([F(1), F(2)], [F(3)])
