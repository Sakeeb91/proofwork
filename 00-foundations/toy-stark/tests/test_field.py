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
