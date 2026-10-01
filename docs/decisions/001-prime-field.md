# ADR 001: Use the prime field with p = 3 * 2^30 + 1 for the toy STARK
Date: 2026-10-01
Status: accepted

## Context
The toy STARK in `00-foundations/toy-stark` needs a finite field. The later
stages (polynomial interpolation by FFT, FRI) need evaluation domains of size
2^k, which means the multiplicative group of the field must contain subgroups
of those sizes. A subgroup of size n exists exactly when n divides p - 1.
The code is educational, so readability matters more than speed or security
level.

## Decision
Use F_p with p = 3 * 2^30 + 1 = 3221225473 and generator g = 5, implemented
as a plain Python class in `src/toy_stark/field.py`.

- This is the field used by StarkWare's STARK 101 tutorial
  (https://starkware.co/stark-101/), which this track follows. Their
  `tutorial/field.py` sets `k_modulus = 3 * 2**30 + 1` and `generator_val = 5`.
  The repository linked from that page returned 404 on 2026-10-01; the
  constants were read from a public copy at
  https://github.com/fxfactorial/stark101/blob/master/tutorial/field.py.
- p - 1 = 3 * 2^30, so primitive n-th roots of unity exist for every power
  of two n up to 2^30: w_n = g^((p-1)/n).
- p is below 2^32, so an element fits in one 32-bit word and a product in 64
  bits.
- Inverses use Fermat's little theorem, a^-1 = a^(p-2), because the one-line
  derivation is easier to teach than extended Euclid.

Primality of p, the order of g, and the orders of the roots of unity are
checked by `tests/test_field.py`, not assumed.

## Consequences
- Intermediate values can be compared directly against STARK 101.
- The field has only about 2^32 elements, so verifier challenges are drawn
  from a small set. No security level is claimed for the toy. Revisit, with
  sources, if it grows a soundness analysis.
- Pure Python object-per-element arithmetic is slow. Acceptable for a
  Fibonacci trace of about a thousand rows.
