# ADR 003: Dense coefficient polynomials with schoolbook algorithms
Date: 2026-10-01
Status: accepted

## Context
Week 2 of the toy STARK needs polynomials over F_p: arithmetic, evaluation,
division, and interpolation through up to 1023 points. The code is
educational (see `CLAUDE.md`: readability over speed).

## Decision
- A polynomial is an immutable tuple of `FieldElement` coefficients, lowest
  degree first, with trailing zeros removed. `coefficients[i]` multiplies X^i.
- The zero polynomial has the empty tuple and degree -1, the convention
  used by STARK 101's `polynomial.py`
  (https://github.com/fxfactorial/stark101/blob/master/tutorial/polynomial.py).
- Multiplication is schoolbook, evaluation is Horner's rule, division is
  long division.
- Interpolation is Lagrange in its O(n^2) form: build the vanishing
  polynomial Z(X) = prod (X - x_j) once, then for each point divide out
  (X - x_i). The textbook form that multiplies out each basis polynomial
  separately is O(n^3) and too slow in pure Python for n = 1023.
- No FFT or NTT yet.

## Consequences
- Every algorithm fits on one screen and matches its textbook formula.
- Interpolating 1023 points and evaluating on 8192 points takes seconds,
  not milliseconds. Full-size tests may need a `slow` marker; this is
  decided by measurement in the week 2 plan.
- The fast route is the number-theoretic transform over the 2^k subgroups,
  which is why ADR 001 chose a prime with p - 1 divisible by 2^30. It is
  deferred until a later week needs it.
