"""STARK 101 Part 1: from a computation to a low-degree extension.

The statement to prove: "I know a field element a_1 such that the
FibonacciSq sequence

    a_0 = 1,   a_{n+2} = a_{n+1}^2 + a_n^2

has a_1022 = 2338775057." Three steps turn the computation into an object a
verifier can spot-check:

1. Trace: the list a_0, ..., a_1022.
2. Trace polynomial: the unique f of degree <= 1022 with f(g^i) = a_i,
   where g generates a subgroup of size 1024.
3. Low-degree extension: f evaluated on 8192 points disjoint from that
   subgroup.

Intuition for step 3: it is an error-correcting code. Two different
polynomials of degree <= 1022 agree on at most 1022 of the 8192 points, so
they differ on at least 87.5% of them. That bound is about valid codewords
only: an arbitrary array of 8192 values can differ from an honest one in a
single place. Nothing is checked yet. Later steps (a commitment, constraint
checks, and the FRI low-degree test) force the prover's array to be close to
a codeword, and only then does the distance catch a bad trace.
"""

from __future__ import annotations

from toy_stark.domain import coset
from toy_stark.field import FieldElement
from toy_stark.polynomial import Polynomial, interpolate

# Parameters of STARK 101 (see docs/decisions/004-follow-stark101-fibonacci-sq.md).
A1 = FieldElement(3141592)
TRACE_LENGTH = 1023
BLOWUP = 8


def fibonacci_sq_trace(a1: FieldElement, length: int) -> list[FieldElement]:
    """[a_0, ..., a_{length-1}] with a_0 = 1, a_1 = a1, a_{n+2} = a_{n+1}^2 + a_n^2."""
    if length < 2:
        raise ValueError("the trace needs at least a_0 and a_1")
    trace = [FieldElement.one(), a1]
    while len(trace) < length:
        trace.append(trace[-1] * trace[-1] + trace[-2] * trace[-2])
    return trace


def trace_polynomial(trace: list[FieldElement], domain: list[FieldElement]) -> Polynomial:
    """The polynomial f with f(domain[i]) = trace[i].

    The trace may be shorter than the domain. STARK 101 uses 1023 values on
    a domain of 1024. Any subgroup size dividing p - 1 would work for
    interpolation; a power of two is chosen because FRI halves the domain
    each round, and 1024 is the smallest one that holds 1023 values.
    """
    if len(trace) > len(domain):
        raise ValueError(f"trace of length {len(trace)} does not fit a domain of {len(domain)}")
    return interpolate(domain[: len(trace)], trace)


def low_degree_extension(
    f: Polynomial, size: int
) -> tuple[list[FieldElement], list[FieldElement]]:
    """Evaluate f on the coset g * H, |H| = size, g the field generator.

    Returns (domain, values) with values[i] = f(domain[i]).

    Why a coset: later weeks divide by polynomials that vanish on the trace
    domain, so the evaluation domain must avoid it. That holds when the
    trace domain lies in a subgroup G contained in H and H is a proper
    subgroup: then g is not in H (a generator lies in no proper subgroup),
    so g * H and H are disjoint. This function does not check where the
    trace domain was; with the STARK 101 sizes (G of 1024 inside H of 8192)
    the condition holds.

    Requires deg f < size, so that the values determine f.
    """
    if f.degree() >= size:
        raise ValueError(f"degree {f.degree()} polynomial is not determined by {size} values")
    domain = coset(FieldElement.generator(), size)
    return domain, [f(x) for x in domain]
