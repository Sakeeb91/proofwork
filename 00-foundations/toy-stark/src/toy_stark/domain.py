"""Evaluation domains: multiplicative subgroups of F_p^* and their cosets.

For n dividing p - 1, the powers of a primitive n-th root of unity w form a
subgroup of size n:

    H = {1, w, w^2, ..., w^(n-1)},   w^n = 1

A coset is that subgroup multiplied through by a fixed nonzero element c:

    c * H = {c, c w, c w^2, ..., c w^(n-1)}

Intuition: F_p^* is a single cycle of p - 1 points, g^0, g^1, ..., g^(p-2).
H is every ((p-1)/n)-th point on that cycle, and c * H is the same pattern
shifted along the cycle, so (when c is outside H) it shares no point with H. STARKs put the trace on a subgroup and the low-degree extension on a
coset of a larger subgroup.
"""

from __future__ import annotations

from toy_stark.field import FieldElement


def subgroup(n: int) -> list[FieldElement]:
    """[w^0, w^1, ..., w^(n-1)] for the primitive n-th root of unity w."""
    w = FieldElement.primitive_root_of_unity(n)
    elements = [FieldElement.one()]
    for _ in range(n - 1):
        elements.append(elements[-1] * w)
    return elements


def coset(offset: FieldElement, n: int) -> list[FieldElement]:
    """[offset * w^i for i in range(n)]. The offset must be nonzero."""
    if offset.is_zero():
        raise ValueError("a coset offset must be nonzero")
    return [offset * x for x in subgroup(n)]
