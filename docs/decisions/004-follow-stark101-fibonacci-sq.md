# ADR 004: Prove STARK 101's FibonacciSq statement, with its parameters
Date: 2026-10-01
Status: accepted

## Context
`docs/roadmap.md` says the toy STARK "proves and verifies a Fibonacci
trace". The tutorial this track follows, STARK 101
(https://starkware.co/stark-101/), does not use the plain Fibonacci
recurrence. Part 1
(https://github.com/fxfactorial/stark101/blob/master/tutorial/Stark101-part1.ipynb)
uses the FibonacciSq sequence a_{n+2} = a_{n+1}^2 + a_n^2 and publishes
check values for it.

## Decision
Use the tutorial's statement and parameters exactly:

- Trace: a_0 = 1, a_1 = 3141592, a_{n+2} = a_{n+1}^2 + a_n^2, 1023 entries.
  The claim to be proved is a_1022 = 2338775057.
- Trace domain: the first 1023 elements of the subgroup G of size 1024.
- Evaluation domain: the coset 5 * H, where H is the subgroup of size 8192
  (a blowup factor of 8).

Functions take the sizes as parameters so tests can also run a small
instance.

## Consequences
- Our intermediate values can be compared with the notebook's asserts:
  a_1022 = 2338775057 and f(2) = 1302089273.
- The recurrence has degree 2, so the constraint polynomials in later weeks
  have higher degree than plain Fibonacci would give. For this project that
  is a benefit: it exercises the degree bookkeeping.
- "Fibonacci" in the roadmap should be read as FibonacciSq.
- The notebook's SHA-256 checks are not reproduced: they hash StarkWare's
  own string formatting of field elements.
