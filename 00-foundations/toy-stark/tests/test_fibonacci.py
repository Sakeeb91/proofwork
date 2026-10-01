"""STARK 101 Part 1: trace, trace polynomial, low-degree extension."""

import pytest

from toy_stark.domain import coset, subgroup
from toy_stark.field import P, FieldElement
from toy_stark.fibonacci import (
    A1,
    BLOWUP,
    TRACE_LENGTH,
    fibonacci_sq_trace,
    low_degree_extension,
    trace_polynomial,
)


def F(n: int) -> FieldElement:
    return FieldElement(n)


# --- the trace -------------------------------------------------------------


def test_trace_starts_with_one_and_the_given_second_element():
    a = fibonacci_sq_trace(F(5), 4)
    assert a[:2] == [F(1), F(5)]


def test_small_trace_by_hand():
    # 1, 2, 2^2 + 1^2 = 5, 5^2 + 2^2 = 29
    assert fibonacci_sq_trace(F(2), 4) == [F(1), F(2), F(5), F(29)]


def test_trace_satisfies_the_recurrence_everywhere():
    a = fibonacci_sq_trace(A1, TRACE_LENGTH)
    assert len(a) == 1023
    for i in range(2, len(a)):
        assert a[i] == a[i - 1] * a[i - 1] + a[i - 2] * a[i - 2]


def test_trace_ends_at_the_stark101_value():
    # The statement the whole STARK will prove.
    assert A1 == F(3141592)
    assert fibonacci_sq_trace(A1, TRACE_LENGTH)[1022] == F(2338775057)


def test_trace_needs_at_least_two_elements():
    with pytest.raises(ValueError):
        fibonacci_sq_trace(F(2), 1)


# --- small instance: trace of 7 on a domain of 8, extended to 64 ------------


def test_small_trace_polynomial_interpolates_the_trace():
    a = fibonacci_sq_trace(F(2), 7)
    G = subgroup(8)
    f = trace_polynomial(a, G)
    assert f.degree() <= 6
    assert [f(G[i]) for i in range(7)] == a


def test_trace_polynomial_rejects_a_trace_that_does_not_fit():
    with pytest.raises(ValueError):
        trace_polynomial(fibonacci_sq_trace(F(2), 9), subgroup(8))


def test_small_low_degree_extension_has_blowup_times_domain_points():
    a = fibonacci_sq_trace(F(2), 7)
    f = trace_polynomial(a, subgroup(8))
    domain, values = low_degree_extension(f, 8 * BLOWUP)
    assert BLOWUP == 8
    assert domain == coset(FieldElement.generator(), 64)
    assert values == [f(x) for x in domain]
    assert set(domain).isdisjoint(subgroup(8))


def test_low_degree_extension_determines_the_polynomial():
    # Reed-Solomon view: any 7 of the 64 values already pin down f.
    from toy_stark.polynomial import interpolate

    a = fibonacci_sq_trace(F(2), 7)
    f = trace_polynomial(a, subgroup(8))
    domain, values = low_degree_extension(f, 64)
    assert interpolate(domain[10:17], values[10:17]) == f


def test_low_degree_extension_rejects_a_domain_too_small_for_the_degree():
    # With size <= deg f the values no longer determine f, so it is not an
    # extension of anything.
    f = trace_polynomial(fibonacci_sq_trace(F(2), 7), subgroup(8))
    assert f.degree() >= 4
    with pytest.raises(ValueError):
        low_degree_extension(f, 4)


# --- full size: STARK 101's numbers ----------------------------------------


@pytest.fixture(scope="module")
def full_trace_polynomial():
    a = fibonacci_sq_trace(A1, TRACE_LENGTH)
    return a, trace_polynomial(a, subgroup(1024))


def test_full_trace_polynomial_matches_stark101_at_2(full_trace_polynomial):
    _, f = full_trace_polynomial
    assert f.degree() <= 1022
    assert f(F(2)) == F(1302089273)  # assert from the STARK 101 notebook


def test_full_trace_polynomial_reproduces_the_whole_trace(full_trace_polynomial):
    # Every one of the 1023 points, not a sample: a polynomial that is right
    # on a sample and wrong elsewhere must not pass.
    a, f = full_trace_polynomial
    G = subgroup(1024)
    assert [f(G[i]) for i in range(1023)] == a


def horner_mod_p(coefficients: list[int], x: int) -> int:
    """Evaluate with plain integers, independently of Polynomial.__call__."""
    acc = 0
    for c in reversed(coefficients):
        acc = (acc * x + c) % P
    return acc


def test_full_low_degree_extension_matches_independent_evaluation(full_trace_polynomial):
    _, f = full_trace_polynomial
    domain, values = low_degree_extension(f, 1024 * BLOWUP)
    assert len(domain) == len(values) == len(set(domain)) == 8192
    # Domain order: domain[i] = 5 * h^i, h the generator proved in Lean.
    h = 1734477367
    assert all(domain[i].value == 5 * pow(h, i, P) % P for i in range(8192))
    # Values: checked against integer arithmetic at indices spread over the
    # whole array, including both ends.
    coeffs = [c.value for c in f.coefficients]
    for i in [*range(0, 8192, 97), 8191]:
        assert values[i].value == horner_mod_p(coeffs, domain[i].value)
