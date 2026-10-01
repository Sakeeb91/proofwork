# Week 2: Polynomials over F_p and the Fibonacci trace: Implementation Plan

> **For agentic workers:** execute task by task, in order. Steps use checkbox (`- [ ]`) syntax. Each task ends with its own commit and push. Keep `git commit` in a Bash call of its own (a local hook misfires when it shares a call with `rm` or `grep -n`).

**Goal:** Close the week 1 Lean gap (roots of unity) and build week 2 of the toy STARK: polynomial arithmetic over F_p, Lagrange interpolation, the FibonacciSq trace polynomial, and its low-degree extension, matching STARK 101 Part 1 value for value.

**Architecture:** Part A adds one theorem and two computed values to the existing Lean file. Part B adds three small Python modules next to `field.py`: `polynomial.py` (pure algebra), `domain.py` (subgroups and cosets of F_p^*), `fibonacci.py` (the STARK 101 Part 1 pipeline). Lean and Python are tied by shared constants asserted on both sides.

**Tech stack:** Python 3.11+ with `uv` and `pytest`, no runtime dependencies. Lean `v4.35.0-rc3` with Mathlib `v4.35.0-rc3`.

**Base commit for the final diff review:** `e2390f23d50979ab17015ac58a92418bc76c3c07`

**Baseline at that commit:** `uv run pytest` gives `44 passed`. `lake build` gives `Build completed successfully (1964 jobs)`.

**Out of scope:** Merkle trees, the Fiat-Shamir channel, constraints, FRI, FFT/NTT, TLA+, CI.

---

## Background a new reader needs

A STARK turns "I ran this computation correctly" into "this function is a polynomial of low degree". Week 2 builds the first half of that sentence.

1. Run the computation and record every step. That list is the **trace**. Ours is FibonacciSq: a_0 = 1, a_1 = 3141592, a_{n+2} = a_{n+1}^2 + a_n^2, 1023 entries.
2. Pick 1023 points g^0, ..., g^1022 where g generates a subgroup G of size 1024. Find the unique polynomial f of degree at most 1022 with f(g^i) = a_i. That is **interpolation**.
3. Evaluate f on a much larger set (8192 points) that is disjoint from G. That is the **low-degree extension**. It is a Reed-Solomon codeword: two different polynomials of degree below 1023 agree on at most 1022 of the 8192 points, so a prover who cheats anywhere is wrong almost everywhere, and a few random queries catch it.

Reference values, all read from the STARK 101 Part 1 notebook (public copy at https://github.com/fxfactorial/stark101/blob/master/tutorial/Stark101-part1.ipynb, official page https://starkware.co/stark-101/) and recomputed locally on 2026-10-01:

| Quantity | Value | Source |
|---|---|---|
| a_1022 | 2338775057 | notebook assert, recomputed |
| g = 5^(3 * 2^20), order 1024 | 1855261384 | recomputed |
| h = 5^((p-1)/8192), order 8192 | 1734477367 | recomputed |
| f(2) | 1302089273 | notebook assert |

The notebook's SHA-256 checks depend on StarkWare's own string formatting of field elements and on their `channel.serialize`. They are not reproduced this week.

## File map

| File | Responsibility |
|---|---|
| `02-lean/ToyStark/ToyStark/Field.lean` (modify) | add `orderOf_rootOfUnity`, `g_trace_value`, `h_eval_value` |
| `02-lean/log.md` (modify) | log the Lean attempt |
| `00-foundations/toy-stark/src/toy_stark/polynomial.py` (create) | `Polynomial`, `vanishing_polynomial`, `interpolate` |
| `00-foundations/toy-stark/src/toy_stark/domain.py` (create) | `subgroup`, `coset` |
| `00-foundations/toy-stark/src/toy_stark/fibonacci.py` (create) | trace, trace polynomial, low-degree extension |
| `00-foundations/toy-stark/tests/test_polynomial.py` (create) | polynomial tests |
| `00-foundations/toy-stark/tests/test_domain.py` (create) | domain tests |
| `00-foundations/toy-stark/tests/test_fibonacci.py` (create) | pipeline tests against STARK 101 values |
| `00-foundations/toy-stark/pyproject.toml` (modify) | register the `slow` marker if measurement requires it |
| `docs/decisions/003-polynomial-representation.md` (create) | ADR |
| `docs/decisions/004-follow-stark101-fibonacci-sq.md` (create) | ADR |
| `docs/HANDOFF.md` (create) | handoff and kickoff prompt |

All Python commands run from `00-foundations/toy-stark/`. All Lean commands run from `02-lean/ToyStark/` with `export PATH="$HOME/.elan/bin:$PATH"` first.

---

## Part A: Lean roots of unity

### Task A1: order of w_n = 5^((p-1)/n)

**Files:** modify `02-lean/ToyStark/ToyStark/Field.lean` (insert before the `### Shared test vector` section).

- [ ] **Step 1: State the theorem with `sorry` and build.** This is the Lean form of "write the failing test": the statement must typecheck before any proof exists.

```lean
/-! ### Roots of unity -/

/-- For every n dividing p - 1, the element w_n = 5^((p-1)/n) has order
exactly n.

    order(g^k) = order(g) / gcd(order(g), k)

Intuition: g walks around a cycle of length p - 1. Taking steps of size
k = (p-1)/n, you return to the start after exactly n steps, because k
divides the cycle length. This is `primitive_root_of_unity` in the Python. -/
theorem orderOf_rootOfUnity {n : ℕ} (hn : n ∣ P - 1) :
    orderOf ((5 : ZMod P) ^ ((P - 1) / n)) = n := by
  sorry
```

Run: `lake build`. Expected: success with one `declaration uses 'sorry'` warning.

- [ ] **Step 2: Prove it.** Intended proof (lemma names verified by grep in this Mathlib: `orderOf_pow'` is in the `Monoid` section of `Mathlib/GroupTheory/OrderOfElement.lean`; `Nat.gcd_eq_right`, `Nat.div_dvd_of_dvd`, `Nat.div_div_self` are in core `Init/Data/Nat`):

```lean
theorem orderOf_rootOfUnity {n : ℕ} (hn : n ∣ P - 1) :
    orderOf ((5 : ZMod P) ^ ((P - 1) / n)) = n := by
  have hP : P - 1 ≠ 0 := by norm_num
  have hk : (P - 1) / n ≠ 0 :=
    (Nat.div_pos (Nat.le_of_dvd (Nat.pos_of_ne_zero hP) hn)
      (Nat.pos_of_dvd_of_pos hn (Nat.pos_of_ne_zero hP))).ne'
  rw [orderOf_pow' _ hk, orderOf_five, Nat.gcd_eq_right (Nat.div_dvd_of_dvd hn),
    Nat.div_div_self hn hP]
```

If a rewrite fails, read the goal Lean prints and adjust. Record every failed attempt in the log (Task A3). No `native_decide`.

Run: `lake build`. Expected: success, no `sorry` warning.

- [ ] **Step 3: Commit and push.**

```bash
git add 02-lean/ToyStark/ToyStark/Field.lean
git commit -m "Prove in Lean that 5^((p-1)/n) has order n for every n dividing p - 1"
git push
```

### Task A2: the two STARK 101 domain generators as Lean values

**Files:** modify `02-lean/ToyStark/ToyStark/Field.lean` (append inside the `### Shared test vector` section).

- [ ] **Step 1: Add the theorems.**

```lean
/-- g = 5^(3 * 2^20) = 1855261384 generates the trace domain of size 1024
(note (p-1)/1024 = 3 * 2^20). Asserted in `tests/test_domain.py`. -/
theorem g_trace_value : (5 : ZMod P) ^ ((P - 1) / 1024) = 1855261384 := by reduce_mod_char

/-- h = 5^((p-1)/8192) = 1734477367 generates the group whose coset is the
evaluation domain of size 8192. Asserted in `tests/test_domain.py`. -/
theorem h_eval_value : (5 : ZMod P) ^ ((P - 1) / 8192) = 1734477367 := by reduce_mod_char

/-- The trace-domain generator has order exactly 1024. -/
example : orderOf ((5 : ZMod P) ^ ((P - 1) / 1024)) = 1024 :=
  orderOf_rootOfUnity (by norm_num)
```

- [ ] **Step 2: Build and check axioms.** Run `lake build`, then in a scratch file outside the repo:

```lean
import ToyStark
#print axioms ToyStark.orderOf_rootOfUnity
#print axioms ToyStark.g_trace_value
```

Expected: only `propext`, `Classical.choice`, `Quot.sound`.

- [ ] **Step 3: Commit and push.**

```bash
git add 02-lean/ToyStark/ToyStark/Field.lean
git commit -m "Add Lean values for the STARK 101 trace and evaluation domain generators"
git push
```

### Task A3: log the Lean session

- [ ] **Step 1:** Append an entry to `02-lean/log.md` with the same headings as the first entry: target, model, toolchain, result, what worked, where the AI failed. Update the table in `02-lean/README.md` to list the new theorem.
- [ ] **Step 2:** Commit `02-lean/log.md` and `02-lean/README.md` together as "Log Lean roots of unity session" and push.

---

## Part B: Python polynomials

### Task B1: ADR 003, polynomial representation

**Files:** create `docs/decisions/003-polynomial-representation.md`.

- [ ] **Step 1: Write the ADR.**

```markdown
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
```

- [ ] **Step 2:** Verify the cited URL resolves (`curl -s -o /dev/null -w "%{http_code}" <url>`, expect 200) and that the file says `return -1` or equivalent for the zero polynomial's degree. If either check fails, fix the ADR text to say only what was verified.
- [ ] **Step 3:** Commit as "Add ADR 003: dense coefficient polynomials, schoolbook algorithms" and push.

### Task B2: Polynomial construction, degree, equality, evaluation

**Files:** create `tests/test_polynomial.py`, create `src/toy_stark/polynomial.py`.

- [ ] **Step 1: Write the failing tests.** `tests/test_polynomial.py`:

```python
"""Tests for polynomials over F_p."""

import random

import pytest

from toy_stark.field import P, FieldElement
from toy_stark.polynomial import Polynomial

rng = random.Random(1)


def F(n: int) -> FieldElement:
    return FieldElement(n)


def poly(*coeffs: int) -> Polynomial:
    """poly(1, 2, 3) is 1 + 2X + 3X^2."""
    return Polynomial([F(c) for c in coeffs])


def rand_poly(degree: int) -> Polynomial:
    """A random polynomial of exactly the given degree."""
    coeffs = [F(rng.randrange(P)) for _ in range(degree)]
    coeffs.append(F(rng.randrange(1, P)))  # nonzero leading coefficient
    return Polynomial(coeffs)


# --- construction, degree, equality ----------------------------------------


def test_coefficients_are_stored_lowest_degree_first():
    assert poly(1, 2, 3).coefficients == (F(1), F(2), F(3))


def test_trailing_zero_coefficients_are_trimmed():
    assert poly(1, 2, 0, 0).coefficients == (F(1), F(2))
    assert poly(1, 2, 0, 0) == poly(1, 2)


def test_degree_is_index_of_highest_nonzero_coefficient():
    assert poly(7).degree() == 0
    assert poly(0, 0, 5).degree() == 2


def test_zero_polynomial_has_degree_minus_one():
    assert Polynomial.zero().degree() == -1
    assert poly(0, 0).degree() == -1
    assert poly(0, 0).is_zero()
    assert not poly(1).is_zero()


def test_equal_polynomials_hash_alike():
    assert hash(poly(1, 2)) == hash(poly(1, 2, 0))
    assert poly(1, 2) != poly(2, 1)


def test_polynomial_is_not_equal_to_a_field_element():
    assert poly(3) != F(3)


def test_coefficients_must_be_field_elements():
    with pytest.raises(TypeError):
        Polynomial([1, 2, 3])


def test_x_is_the_degree_one_monomial():
    assert Polynomial.X() == poly(0, 1)


def test_constant_wraps_a_field_element():
    assert Polynomial.constant(F(9)) == poly(9)


# --- evaluation ------------------------------------------------------------


def test_evaluation_by_hand():
    # 1 + 2X + 3X^2 at X = 2 is 1 + 4 + 12 = 17.
    assert poly(1, 2, 3)(F(2)) == F(17)


def test_evaluating_zero_polynomial_gives_zero():
    assert Polynomial.zero()(F(5)) == F(0)


def test_evaluation_at_zero_is_the_constant_term():
    p = rand_poly(10)
    assert p(F(0)) == p.coefficients[0]


def test_evaluation_matches_naive_sum_of_powers():
    p = rand_poly(20)
    x = F(rng.randrange(P))
    naive = F(0)
    for i, c in enumerate(p.coefficients):
        naive = naive + c * x**i
    assert p(x) == naive
```

- [ ] **Step 2: Run and watch it fail.** `uv run pytest tests/test_polynomial.py -q`. Expected: collection error, `No module named 'toy_stark.polynomial'`.

- [ ] **Step 3: Implement.** `src/toy_stark/polynomial.py`:

```python
"""Polynomials in one variable over F_p.

A polynomial is a finite sum

    f(X) = c_0 + c_1 X + c_2 X^2 + ... + c_d X^d,   c_i in F_p,  c_d != 0

and d is its degree. The fact that makes polynomials useful for proofs:

    a nonzero polynomial of degree d has at most d roots.

Intuition: two different polynomials of degree at most d can agree on at most
d points, so if you evaluate them on many more than d points they disagree
almost everywhere. A small lie about the computation becomes a large,
easy-to-spot difference.
"""

from __future__ import annotations

from collections.abc import Iterable

from toy_stark.field import FieldElement


class Polynomial:
    """A polynomial stored as its coefficients, lowest degree first."""

    __slots__ = ("_coefficients",)

    def __init__(self, coefficients: Iterable[FieldElement]) -> None:
        coeffs = list(coefficients)
        for c in coeffs:
            if not isinstance(c, FieldElement):
                raise TypeError(f"coefficients must be FieldElement, got {type(c).__name__}")
        # Trailing zeros do not change the polynomial (1 + 2X + 0X^2 is
        # 1 + 2X), so remove them. Then equal polynomials have equal tuples.
        while coeffs and coeffs[-1].is_zero():
            coeffs.pop()
        self._coefficients = tuple(coeffs)

    @property
    def coefficients(self) -> tuple[FieldElement, ...]:
        """coefficients[i] multiplies X^i."""
        return self._coefficients

    @staticmethod
    def zero() -> Polynomial:
        return Polynomial([])

    @staticmethod
    def constant(c: FieldElement) -> Polynomial:
        return Polynomial([c])

    @staticmethod
    def X() -> Polynomial:
        """The polynomial X itself."""
        return Polynomial([FieldElement.zero(), FieldElement.one()])

    def is_zero(self) -> bool:
        return not self._coefficients

    def degree(self) -> int:
        """Index of the highest nonzero coefficient.

        The zero polynomial gets -1. That keeps deg(f * g) = deg f + deg g
        from being claimed for zero, and makes "deg r < deg b" a valid stop
        condition in division when the remainder is zero.
        """
        return len(self._coefficients) - 1

    def __repr__(self) -> str:
        return f"Polynomial({[c.value for c in self._coefficients]})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Polynomial):
            return NotImplemented
        return self._coefficients == other._coefficients

    def __hash__(self) -> int:
        return hash(self._coefficients)

    # Horner's rule:
    #
    #     c_0 + c_1 x + c_2 x^2 + c_3 x^3 = c_0 + x (c_1 + x (c_2 + x c_3))
    #
    # Intuition: work from the highest coefficient down, multiplying by x
    # once per step. That is d multiplications instead of computing every
    # power of x separately.
    def __call__(self, x: FieldElement) -> FieldElement:
        if not isinstance(x, FieldElement):
            raise TypeError(f"can only evaluate at a FieldElement, got {type(x).__name__}")
        result = FieldElement.zero()
        for c in reversed(self._coefficients):
            result = result * x + c
        return result
```

- [ ] **Step 4: Run and watch it pass.** `uv run pytest -q`. Expected: all pass (44 old + 13 new = 57).
- [ ] **Step 5: Commit** both files as "Add Polynomial over F_p with degree, equality, Horner evaluation" and push.

### Task B3: addition, negation, subtraction, multiplication

**Files:** modify `tests/test_polynomial.py` (append), modify `src/toy_stark/polynomial.py` (append methods to the class).

- [ ] **Step 1: Append the failing tests.**

```python
# --- ring operations -------------------------------------------------------


def test_addition_by_hand():
    assert poly(1, 2) + poly(3, 4, 5) == poly(4, 6, 5)


def test_addition_can_lower_the_degree():
    # (1 + X) + (1 - X) = 2
    assert poly(1, 1) + poly(1, -1) == poly(2)


def test_subtracting_a_polynomial_from_itself_gives_zero():
    p = rand_poly(8)
    assert p - p == Polynomial.zero()
    assert p + (-p) == Polynomial.zero()


def test_multiplication_by_hand():
    # (1 + X)(1 - X) = 1 - X^2
    assert poly(1, 1) * poly(1, -1) == poly(1, 0, -1)


def test_multiplying_by_zero_gives_zero():
    assert rand_poly(5) * Polynomial.zero() == Polynomial.zero()
    assert Polynomial.zero() * rand_poly(5) == Polynomial.zero()


def test_degree_of_product_is_sum_of_degrees():
    # Holds because F_p has no zero divisors: leading coefficients multiply
    # to something nonzero.
    a, b = rand_poly(7), rand_poly(11)
    assert (a * b).degree() == 18


def test_ring_laws_on_random_polynomials():
    for _ in range(10):
        a, b, c = rand_poly(5), rand_poly(6), rand_poly(4)
        assert a + b == b + a
        assert a * b == b * a
        assert (a + b) + c == a + (b + c)
        assert (a * b) * c == a * (b * c)
        assert a * (b + c) == a * b + a * c


def test_evaluation_is_a_ring_homomorphism():
    # Evaluating then combining equals combining then evaluating. This is
    # why a polynomial identity can be spot-checked at a random point.
    a, b = rand_poly(9), rand_poly(6)
    x = F(rng.randrange(P))
    assert (a + b)(x) == a(x) + b(x)
    assert (a * b)(x) == a(x) * b(x)


def test_scaling_by_a_field_element():
    assert poly(1, 2, 3).scale(F(2)) == poly(2, 4, 6)
    assert poly(1, 2, 3).scale(F(0)) == Polynomial.zero()
```

- [ ] **Step 2: Run and watch it fail.** Expected: `TypeError: unsupported operand` and `AttributeError: 'Polynomial' object has no attribute 'scale'`.

- [ ] **Step 3: Implement.** Append to the class:

```python
    # Add coefficient by coefficient; the shorter polynomial is padded with
    # zeros. The constructor trims any cancellation at the top.
    def __add__(self, other: Polynomial) -> Polynomial:
        if not isinstance(other, Polynomial):
            return NotImplemented
        a, b = self._coefficients, other._coefficients
        zero = FieldElement.zero()
        n = max(len(a), len(b))
        return Polynomial(
            (a[i] if i < len(a) else zero) + (b[i] if i < len(b) else zero) for i in range(n)
        )

    def __neg__(self) -> Polynomial:
        return Polynomial(-c for c in self._coefficients)

    def __sub__(self, other: Polynomial) -> Polynomial:
        if not isinstance(other, Polynomial):
            return NotImplemented
        return self + (-other)

    def scale(self, c: FieldElement) -> Polynomial:
        """Multiply every coefficient by the field element c."""
        return Polynomial(c * a for a in self._coefficients)

    # Schoolbook multiplication. The coefficient of X^k in f * g is
    #
    #     sum over i + j = k of f_i * g_j
    #
    # Intuition: every term of f meets every term of g, and X^i * X^j lands
    # in slot i + j. Cost is (deg f + 1)(deg g + 1) field multiplications.
    def __mul__(self, other: Polynomial) -> Polynomial:
        if not isinstance(other, Polynomial):
            return NotImplemented
        if self.is_zero() or other.is_zero():
            return Polynomial.zero()
        a, b = self._coefficients, other._coefficients
        out = [FieldElement.zero()] * (len(a) + len(b) - 1)
        for i, ai in enumerate(a):
            for j, bj in enumerate(b):
                out[i + j] = out[i + j] + ai * bj
        return Polynomial(out)
```

- [ ] **Step 4: Run and watch it pass.** `uv run pytest -q`. Expected: 66 passed.
- [ ] **Step 5: Commit** as "Add polynomial addition, subtraction, scaling, multiplication" and push.

### Task B4: division with remainder

**Files:** modify `tests/test_polynomial.py` (append), modify `src/toy_stark/polynomial.py` (append methods).

- [ ] **Step 1: Append the failing tests.**

```python
# --- division with remainder -----------------------------------------------


def test_division_by_hand():
    # X^2 - 1 = (X - 1)(X + 1) + 0
    q, r = divmod(poly(-1, 0, 1), poly(-1, 1))
    assert q == poly(1, 1)
    assert r == Polynomial.zero()


def test_division_with_nonzero_remainder_by_hand():
    # X^2 + 1 = (X - 1)(X + 1) + 2
    q, r = divmod(poly(1, 0, 1), poly(-1, 1))
    assert q == poly(1, 1)
    assert r == poly(2)


def test_division_identity_and_remainder_degree():
    # a = q * b + r with deg r < deg b. Existence and uniqueness of (q, r)
    # is the division theorem for polynomials over a field.
    for _ in range(20):
        a, b = rand_poly(rng.randrange(0, 15)), rand_poly(rng.randrange(0, 8))
        q, r = divmod(a, b)
        assert a == q * b + r
        assert r.degree() < b.degree()


def test_dividing_a_lower_degree_polynomial_gives_zero_quotient():
    a, b = rand_poly(3), rand_poly(5)
    assert divmod(a, b) == (Polynomial.zero(), a)


def test_exact_division_recovers_the_factor():
    a, b = rand_poly(6), rand_poly(4)
    assert (a * b) // b == a
    assert (a * b) % b == Polynomial.zero()


def test_division_by_zero_polynomial_raises():
    with pytest.raises(ZeroDivisionError):
        divmod(rand_poly(3), Polynomial.zero())


def test_remainder_theorem():
    # f(X) mod (X - a) is the constant f(a). So f(a) = 0 exactly when
    # (X - a) divides f. Constraints in a STARK are checked this way.
    f = rand_poly(12)
    a = F(rng.randrange(P))
    assert f % poly(-a.value, 1) == Polynomial.constant(f(a))
```

- [ ] **Step 2: Run and watch it fail.** Expected: `TypeError: unsupported operand type(s) for divmod()`.

- [ ] **Step 3: Implement.** Append to the class:

```python
    # Long division. Given a and b != 0, find q and r with
    #
    #     a = q * b + r,   deg r < deg b
    #
    # Intuition: the same procedure as long division of integers. Cancel
    # the leading term of what is left by subtracting the right multiple of
    # b, record that multiple in q, repeat until what is left has smaller
    # degree than b. Dividing by b's leading coefficient is where we need a
    # field: over the integers this step can fail.
    def __divmod__(self, other: Polynomial) -> tuple[Polynomial, Polynomial]:
        if not isinstance(other, Polynomial):
            return NotImplemented
        if other.is_zero():
            raise ZeroDivisionError("division by the zero polynomial")
        b = other._coefficients
        lead_inv = b[-1].inverse()
        remainder = list(self._coefficients)
        quotient = [FieldElement.zero()] * max(len(remainder) - len(b) + 1, 0)
        # shift is the power of X in the current quotient term.
        for shift in range(len(remainder) - len(b), -1, -1):
            factor = remainder[shift + len(b) - 1] * lead_inv
            quotient[shift] = factor
            for j, bj in enumerate(b):
                remainder[shift + j] = remainder[shift + j] - factor * bj
        return Polynomial(quotient), Polynomial(remainder)

    def __floordiv__(self, other: Polynomial) -> Polynomial:
        if not isinstance(other, Polynomial):
            return NotImplemented
        return divmod(self, other)[0]

    def __mod__(self, other: Polynomial) -> Polynomial:
        if not isinstance(other, Polynomial):
            return NotImplemented
        return divmod(self, other)[1]
```

- [ ] **Step 4: Run and watch it pass.** `uv run pytest -q`. Expected: 73 passed.
- [ ] **Step 5: Commit** as "Add polynomial division with remainder" and push.

### Task B5: domains (subgroups and cosets)

**Files:** create `tests/test_domain.py`, create `src/toy_stark/domain.py`.

- [ ] **Step 1: Write the failing tests.** `tests/test_domain.py`:

```python
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
```

- [ ] **Step 2: Run and watch it fail.** Expected: `No module named 'toy_stark.domain'`.

- [ ] **Step 3: Implement.** `src/toy_stark/domain.py`:

```python
"""Evaluation domains: multiplicative subgroups of F_p^* and their cosets.

For n dividing p - 1, the powers of a primitive n-th root of unity w form a
subgroup of size n:

    H = {1, w, w^2, ..., w^(n-1)},   w^n = 1

A coset is that subgroup multiplied through by a fixed nonzero element c:

    c * H = {c, c w, c w^2, ..., c w^(n-1)}

Intuition: H is n equally spaced points on a circle, and c * H is the same
circle rotated and scaled so that (when c is outside H) it shares no point
with H. STARKs put the trace on a subgroup and the low-degree extension on a
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
```

- [ ] **Step 4: Run and watch it pass.** `uv run pytest -q`. Expected: 81 passed.
- [ ] **Step 5: Commit** as "Add subgroup and coset evaluation domains" and push.

### Task B6: vanishing polynomial and Lagrange interpolation

**Files:** modify `tests/test_polynomial.py` (append), modify `src/toy_stark/polynomial.py` (append module-level functions).

- [ ] **Step 1: Append the failing tests.** Add `from toy_stark.domain import subgroup` and extend the polynomial import to `from toy_stark.polynomial import Polynomial, interpolate, vanishing_polynomial` at the top of the file, then append:

```python
# --- vanishing polynomial --------------------------------------------------


def test_vanishing_polynomial_is_zero_exactly_on_its_points():
    points = [F(3), F(10), F(77)]
    z = vanishing_polynomial(points)
    assert z.degree() == 3
    assert all(z(x) == F(0) for x in points)
    assert z(F(4)) != F(0)


def test_vanishing_polynomial_of_no_points_is_one():
    assert vanishing_polynomial([]) == poly(1)


def test_vanishing_polynomial_of_a_subgroup_is_x_to_the_n_minus_one():
    # Every element of the size-n subgroup satisfies x^n = 1, so X^n - 1
    # has those n roots, and a monic degree-n polynomial with n known roots
    # is determined. A product of n linear factors collapses to two terms.
    n = 16
    expected = Polynomial([F(-1)] + [F(0)] * (n - 1) + [F(1)])
    assert vanishing_polynomial(subgroup(n)) == expected


# --- interpolation ---------------------------------------------------------


def test_interpolation_through_two_points_is_the_line():
    # Through (0, 1) and (1, 3): f = 1 + 2X.
    assert interpolate([F(0), F(1)], [F(1), F(3)]) == poly(1, 2)


def test_interpolant_passes_through_every_point():
    xs = [F(i) for i in range(1, 21)]
    ys = [F(rng.randrange(P)) for _ in xs]
    f = interpolate(xs, ys)
    assert all(f(x) == y for x, y in zip(xs, ys))
    assert f.degree() < len(xs)


def test_interpolation_recovers_a_polynomial_from_its_values():
    # Uniqueness: a polynomial of degree < n is determined by n values.
    f = rand_poly(11)
    xs = subgroup(16)[:12]
    assert interpolate(xs, [f(x) for x in xs]) == f


def test_interpolating_constant_values_gives_a_constant():
    xs = subgroup(8)
    assert interpolate(xs, [F(7)] * 8) == poly(7)


def test_interpolating_no_points_gives_zero():
    assert interpolate([], []) == Polynomial.zero()


def test_interpolation_rejects_repeated_x_values():
    with pytest.raises(ValueError):
        interpolate([F(1), F(1)], [F(2), F(3)])


def test_interpolation_rejects_mismatched_lengths():
    with pytest.raises(ValueError):
        interpolate([F(1), F(2)], [F(3)])
```

- [ ] **Step 2: Run and watch it fail.** Expected: `ImportError: cannot import name 'interpolate'`.

- [ ] **Step 3: Implement.** Append to `src/toy_stark/polynomial.py` (module level, after the class), and add `from collections.abc import Iterable, Sequence` in place of the existing `Iterable` import:

```python
def vanishing_polynomial(points: Iterable[FieldElement]) -> Polynomial:
    """Z(X) = product of (X - x_i): the monic polynomial that is zero exactly on the points.

    Intuition: each factor (X - x_i) kills one point. "f is zero on all of
    these points" is the same statement as "Z divides f", which turns many
    separate checks into a single divisibility check.
    """
    z = Polynomial.constant(FieldElement.one())
    for x in points:
        z = z * Polynomial([-x, FieldElement.one()])
    return z


def interpolate(xs: Sequence[FieldElement], ys: Sequence[FieldElement]) -> Polynomial:
    """The unique polynomial of degree < n through the n points (x_i, y_i).

    Lagrange's formula:

        f(X) = sum over i of  y_i * L_i(X),
        L_i(X) = product over j != i of (X - x_j) / (x_i - x_j)

    Intuition: L_i is built to be 1 at x_i and 0 at every other x_j, so the
    sum picks out y_i at x_i. It is a "one-hot" basis for the points.

    Computed in O(n^2) instead of the O(n^3) of multiplying out each L_i:
    with Z(X) = product over all j of (X - x_j),

        numerator of L_i    =  Z(X) / (X - x_i)   =: Q_i(X)
        denominator of L_i  =  Q_i(x_i)

    so Z is built once and each point costs one division by a linear factor.
    """
    if len(xs) != len(ys):
        raise ValueError(f"need as many y values as x values, got {len(xs)} and {len(ys)}")
    if len(set(xs)) != len(xs):
        raise ValueError("x values must be distinct")

    z = vanishing_polynomial(xs)
    result = Polynomial.zero()
    for x, y in zip(xs, ys):
        q = z // Polynomial([-x, FieldElement.one()])
        result = result + q.scale(y / q(x))
    return result
```

- [ ] **Step 4: Run and watch it pass.** `uv run pytest -q`. Expected: 91 passed.
- [ ] **Step 5: Commit** as "Add vanishing polynomial and Lagrange interpolation" and push.

### Task B7: ADR 004, follow STARK 101's FibonacciSq statement

**Files:** create `docs/decisions/004-follow-stark101-fibonacci-sq.md`.

- [ ] **Step 1: Write the ADR.**

```markdown
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
  have higher degree than plain Fibonacci would give. That is the point of
  the tutorial's choice: it exercises the degree bookkeeping.
- "Fibonacci" in the roadmap should be read as FibonacciSq.
- The notebook's SHA-256 checks are not reproduced: they hash StarkWare's
  own string formatting of field elements.
```

- [ ] **Step 2:** Commit as "Add ADR 004: follow STARK 101's FibonacciSq statement and parameters" and push.

### Task B8: the trace, the trace polynomial, the low-degree extension

**Files:** create `tests/test_fibonacci.py`, create `src/toy_stark/fibonacci.py`.

- [ ] **Step 1: Write the failing tests.** `tests/test_fibonacci.py`:

```python
"""STARK 101 Part 1: trace, trace polynomial, low-degree extension."""

import pytest

from toy_stark.domain import coset, subgroup
from toy_stark.field import FieldElement
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


# --- full size: STARK 101's numbers ----------------------------------------


@pytest.fixture(scope="module")
def full_trace_polynomial():
    a = fibonacci_sq_trace(A1, TRACE_LENGTH)
    return a, trace_polynomial(a, subgroup(1024))


def test_full_trace_polynomial_matches_stark101_at_2(full_trace_polynomial):
    _, f = full_trace_polynomial
    assert f.degree() <= 1022
    assert f(F(2)) == F(1302089273)  # assert from the STARK 101 notebook


def test_full_trace_polynomial_reproduces_the_trace(full_trace_polynomial):
    a, f = full_trace_polynomial
    G = subgroup(1024)
    assert all(f(G[i]) == a[i] for i in range(0, 1023, 73))


def test_full_low_degree_extension_has_8192_points(full_trace_polynomial):
    _, f = full_trace_polynomial
    domain, values = low_degree_extension(f, 1024 * BLOWUP)
    assert len(domain) == len(values) == len(set(domain)) == 8192
    assert values[0] == f(FieldElement.generator())
```

- [ ] **Step 2: Run and watch it fail.** Expected: `No module named 'toy_stark.fibonacci'`.

- [ ] **Step 3: Implement.** `src/toy_stark/fibonacci.py`:

```python
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
an incorrect trace gives values that are wrong at more than 87% of them.
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
    a domain of 1024: the group must have power-of-two size, and the
    recurrence only produces 1023 values we care about.
    """
    if len(trace) > len(domain):
        raise ValueError(f"trace of length {len(trace)} does not fit a domain of {len(domain)}")
    return interpolate(domain[: len(trace)], trace)


def low_degree_extension(
    f: Polynomial, size: int
) -> tuple[list[FieldElement], list[FieldElement]]:
    """Evaluate f on the coset g * H, |H| = size, g the field generator.

    Returns (domain, values) with values[i] = f(domain[i]). The coset is
    used instead of H itself so that the evaluation domain shares no point
    with the trace domain; later weeks divide by polynomials that vanish on
    the trace domain.
    """
    domain = coset(FieldElement.generator(), size)
    return domain, [f(x) for x in domain]
```

- [ ] **Step 4: Run and measure.** `uv run pytest -q --durations=5`. Expected: 103 passed. Record the wall time of the three full-size tests.

- [ ] **Step 5: Apply the speed rule.** If the whole suite takes more than 10 seconds, mark the three full-size tests with `@pytest.mark.slow`, and change `pyproject.toml` to:

```toml
[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
markers = ["slow: full-size STARK 101 parameters, takes several seconds"]
addopts = "-m 'not slow'"
```

Then verify both `uv run pytest -q` (fast suite) and `uv run pytest -q -m slow` (full size) pass. If the suite is under 10 seconds, leave everything unmarked. Either way, write the measured times into the commit message.

- [ ] **Step 6: Commit** `tests/test_fibonacci.py`, `src/toy_stark/fibonacci.py`, and `pyproject.toml` if changed, as "Add FibonacciSq trace, trace polynomial, low-degree extension", and push.

### Task B9: update the foundations README

- [ ] **Step 1:** Replace the second bullet of `00-foundations/README.md` (which predicts `field/`, `merkle/`, `fri/`, `air/` directories) with a list of the modules that exist: `field.py`, `polynomial.py`, `domain.py`, `fibonacci.py`, each with a one-line description, and the test commands (including `-m slow` if Task B8 added the marker).
- [ ] **Step 2:** Commit as "Describe the toy-stark modules in 00-foundations/README" and push.

---

## Part C: review and handoff

### Task C1: Codex review of the diff

- [ ] **Step 1:** Run the Codex review against the base commit:

```bash
node "/Users/sakeeb/.claude/plugins/cache/openai-codex/codex/1.0.6/scripts/codex-companion.mjs" review --wait --scope branch --base e2390f23d50979ab17015ac58a92418bc76c3c07
```

- [ ] **Step 2:** For each finding: reproduce it with a failing test, fix, commit, push. Findings that are wrong get a one-line reason.
- [ ] **Step 3:** Append findings and their disposition to the Reviews section of this plan. Commit and push.

### Task C2: handoff file

- [ ] **Step 1:** Write `docs/HANDOFF.md` with these sections: current state (what exists, test counts, `git log --oneline`), how to run (`uv run pytest`, `lake build`, the `~/.elan/bin` PATH note), decisions (ADR 001 to 004 with one line each), working rules (from `CLAUDE.md` plus: atomic commits pushed immediately, test first, plan reviewed by Fable advisor and by Codex), known gaps, next steps (week 3: Merkle commitments and the Fiat-Shamir channel; week 4: constraints and FRI), and a kickoff prompt in a fenced block.
- [ ] **Step 2:** Commit as "Add handoff file with kickoff prompt" and push.

---

## Reviews

(Filled in during plan review and after implementation.)
