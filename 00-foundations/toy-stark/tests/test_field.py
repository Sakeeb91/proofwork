"""Tests for the prime field F_p with p = 3 * 2^30 + 1."""

import random

import pytest

from toy_stark.field import P, FieldElement

# Seeded so every run sees the same "random" elements.
rng = random.Random(0)


def rand_elem() -> FieldElement:
    return FieldElement(rng.randrange(P))


def rand_nonzero() -> FieldElement:
    return FieldElement(rng.randrange(1, P))


# --- the modulus -----------------------------------------------------------


def test_modulus_is_3_times_2_to_30_plus_1():
    assert P == 3 * 2**30 + 1 == 3221225473


def is_prime_miller_rabin(n: int) -> bool:
    """Deterministic Miller-Rabin, valid for n < 4,759,123,141 with bases 2, 7, 61.

    Write n - 1 = d * 2^s with d odd. If n is prime, then for every base a
    either a^d = 1 or a^(d * 2^r) = -1 for some r < s. A composite n fails
    this for at least one of the three bases (Jaeschke 1993).
    """
    d, s = n - 1, 0
    while d % 2 == 0:
        d, s = d // 2, s + 1
    for a in (2, 7, 61):
        x = pow(a, d, n)
        if x in (1, n - 1):
            continue
        for _ in range(s - 1):
            x = x * x % n
            if x == n - 1:
                break
        else:
            return False
    return True


def test_modulus_is_prime():
    assert P < 4_759_123_141  # range where bases 2, 7, 61 are a proof
    assert is_prime_miller_rabin(P)


def test_miller_rabin_helper_rejects_composites():
    # Guard the guard: 3 * 2^30 + 3 is even, 2^32 + 1 = 641 * 6700417.
    assert not is_prime_miller_rabin(P + 2)
    assert not is_prime_miller_rabin(641 * 6700417)


# --- construction and equality ---------------------------------------------


def test_value_is_reduced_mod_p():
    assert FieldElement(P + 5).value == 5
    assert FieldElement(-1).value == P - 1


def test_equal_residues_are_equal_and_hash_alike():
    a, b = FieldElement(1), FieldElement(P + 1)
    assert a == b
    assert hash(a) == hash(b)
    assert FieldElement(1) != FieldElement(2)


def test_element_is_not_equal_to_a_bare_int():
    # Forces callers to be explicit about which field an integer lives in.
    assert FieldElement(3) != 3


def test_elements_are_immutable():
    a = FieldElement(3)
    with pytest.raises(AttributeError):
        a.value = 4


# --- addition, subtraction, negation ---------------------------------------


def test_addition_wraps_around_the_modulus():
    assert FieldElement(P - 1) + FieldElement(2) == FieldElement(1)


def test_subtraction_wraps_below_zero():
    assert FieldElement(1) - FieldElement(2) == FieldElement(P - 1)


def test_zero_is_additive_identity():
    for _ in range(50):
        a = rand_elem()
        assert a + FieldElement.zero() == a


def test_negation_is_additive_inverse():
    for _ in range(50):
        a = rand_elem()
        assert a + (-a) == FieldElement.zero()
    assert -FieldElement.zero() == FieldElement.zero()


def test_addition_is_commutative_and_associative():
    for _ in range(50):
        a, b, c = rand_elem(), rand_elem(), rand_elem()
        assert a + b == b + a
        assert (a + b) + c == a + (b + c)


def test_subtraction_undoes_addition():
    for _ in range(50):
        a, b = rand_elem(), rand_elem()
        assert (a + b) - b == a


# --- multiplication --------------------------------------------------------


def test_multiplication_wraps_around_the_modulus():
    # (p - 1) is -1, and (-1) * (-1) = 1.
    assert FieldElement(P - 1) * FieldElement(P - 1) == FieldElement.one()


def test_one_is_multiplicative_identity():
    for _ in range(50):
        a = rand_elem()
        assert a * FieldElement.one() == a


def test_multiplication_is_commutative_and_associative():
    for _ in range(50):
        a, b, c = rand_elem(), rand_elem(), rand_elem()
        assert a * b == b * a
        assert (a * b) * c == a * (b * c)


def test_multiplication_distributes_over_addition():
    for _ in range(50):
        a, b, c = rand_elem(), rand_elem(), rand_elem()
        assert a * (b + c) == a * b + a * c


# --- inverse and division --------------------------------------------------


def test_inverse_times_self_is_one():
    for _ in range(50):
        a = rand_nonzero()
        assert a * a.inverse() == FieldElement.one()


def test_inverse_agrees_with_extended_euclid():
    # Python's pow(a, -1, p) uses the extended Euclidean algorithm, an
    # independent route to the same answer.
    for _ in range(50):
        a = rand_nonzero()
        assert a.inverse().value == pow(a.value, -1, P)


def test_zero_has_no_inverse():
    with pytest.raises(ZeroDivisionError):
        FieldElement.zero().inverse()


def test_division_undoes_multiplication():
    for _ in range(50):
        a, b = rand_elem(), rand_nonzero()
        assert (a * b) / b == a


def test_division_by_zero_raises():
    with pytest.raises(ZeroDivisionError):
        FieldElement(7) / FieldElement.zero()


# --- powers ----------------------------------------------------------------


def test_pow_matches_repeated_multiplication():
    a = rand_elem()
    acc = FieldElement.one()
    for n in range(20):
        assert a**n == acc
        acc = acc * a


def test_anything_to_the_zero_is_one():
    assert FieldElement(5) ** 0 == FieldElement.one()
    assert FieldElement.zero() ** 0 == FieldElement.one()  # empty product


def test_fermats_little_theorem():
    # a^(p-1) = 1 for every nonzero a.
    for _ in range(50):
        assert rand_nonzero() ** (P - 1) == FieldElement.one()


def test_negative_exponent_is_power_of_the_inverse():
    for _ in range(20):
        a = rand_nonzero()
        assert a**-1 == a.inverse()
        assert a**-3 == (a.inverse()) ** 3


def test_zero_to_a_negative_power_raises():
    with pytest.raises(ZeroDivisionError):
        FieldElement.zero() ** -1
