# Foundations
- `toy-stark/`: STARK from scratch, following StarkWare's STARK 101 and Thaler's *Proofs, Arguments, and Zero-Knowledge*.

## Modules in `toy-stark/src/toy_stark/`

| Module | What it is |
|---|---|
| `field.py` | The prime field F_p, p = 3 * 2^30 + 1: arithmetic, inverse, generator, roots of unity |
| `polynomial.py` | Polynomials over F_p: arithmetic, Horner evaluation, division with remainder, vanishing polynomial, Lagrange interpolation |
| `domain.py` | Evaluation domains: subgroups of F_p^* and their cosets |
| `fibonacci.py` | STARK 101 Part 1: the FibonacciSq trace, its trace polynomial, its low-degree extension |

Still to come: Merkle commitments, the Fiat-Shamir channel, constraints, FRI.

## Running the tests
From `toy-stark/`:

    uv run pytest

The Lean mirror of the field facts is in `02-lean/ToyStark/`. Design decisions are in `docs/decisions/`.
