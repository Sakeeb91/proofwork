"""Tests for evaluation domains: subgroups of F_p^* and their cosets."""

import pytest

from toy_stark.domain import coset, subgroup
from toy_stark.field import P, FieldElement


def test_subgroup_lists_powers_of_the_root_of_unity_in_order():
    w = FieldElement.primitive_root_of_unity(8)
    assert subgroup(8) == [w**i for i in range(8)]


def test_subgroup_starts_at_one_and_has_n_distinct_elements():
    G = subgroup(1024)
    assert G[0] == FieldElement.one()
    assert len(G) == len(set(G)) == 1024


def test_subgroup_is_closed_under_multiplication():
    G = subgroup(16)
    members = set(G)
    assert all(a * b in members for a in G for b in G)


def test_subgroup_rejects_sizes_not_dividing_p_minus_1():
    with pytest.raises(ValueError):
        subgroup(5)


def test_coset_is_the_subgroup_scaled_by_the_offset():
    offset = FieldElement.generator()
    assert coset(offset, 8) == [offset * x for x in subgroup(8)]


def test_coset_of_generator_is_disjoint_from_the_subgroup():
    # The generator g = 5 is not in any proper subgroup, so g * H never
    # meets H. The low-degree extension is evaluated on such a coset so
    # that it shares no point with the trace domain.
    H = subgroup(64)
    assert set(coset(FieldElement.generator(), 64)).isdisjoint(H)


def test_coset_rejects_zero_offset():
    with pytest.raises(ValueError):
        coset(FieldElement.zero(), 8)


def test_stark101_generators_match_lean():
    # Theorems g_trace_value and h_eval_value in
    # 02-lean/ToyStark/ToyStark/Field.lean prove these same two values.
    assert subgroup(1024)[1] == FieldElement(1855261384)
    assert subgroup(8192)[1] == FieldElement(1734477367)
    assert (P - 1) // 1024 == 3 * 2**20
