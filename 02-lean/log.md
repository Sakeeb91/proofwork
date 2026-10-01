# Lean workflow log

## 2026-10-01: p = 3 * 2^30 + 1 is prime, 5 generates F_p^*

- Target: `ToyStark.P_prime`, `ToyStark.orderOf_five`, and a `Field (ZMod P)`
  instance, in `ToyStark/ToyStark/Field.lean`. Mirrors week 1 of the Python
  toy STARK.
- Model: Claude Opus 5.5 (`claude-opus-5-5`) in Claude Code.
- Toolchain: Lean `v4.35.0-rc3`, Mathlib `v4.35.0-rc3`.
- Result: builds with no `sorry`. `#print axioms` on `P_prime`,
  `orderOf_five`, `five_pow_1000` shows only `propext`, `Classical.choice`,
  `Quot.sound`. No `native_decide`.

What worked:
- `lucas_primality` (`Mathlib/NumberTheory/LucasPrimality.lean`) for
  primality and `orderOf_eq_of_pow_and_pow_div_prime`
  (`Mathlib/GroupTheory/OrderOfElement.lean`) for the generator. Both take
  the same two hypotheses, so one pair of lemmas feeds both theorems.
- `reduce_mod_char` proves `(5 : ZMod P) ^ n = c` for n around 3 * 10^9 quickly:
  the whole file builds in about 3 seconds. It needs the modulus as a numeric literal, so `P` is
  an `abbrev` for `3221225473` with a separate lemma `P = 3 * 2^30 + 1`.
- For `x ≠ 1`: first rewrite the power to its value with an equality proved
  by `reduce_mod_char`, then `decide` on two reduced numerals.
- Reading the lemma signatures with grep in `.lake/packages/mathlib` before
  writing any proof. Both lemma names were first recalled from memory and
  both turned out to be right, but that was checked, not assumed.

Where the AI failed or guessed wrong:
- `example : Nat.Prime 3221225473 := by norm_num` fails with
  `(kernel) deep recursion detected`. The direct route does not work at this
  size without further options; Lucas does.
- `reduce_mod_char` directly on `5 ^ n ≠ 1` leaves the goal
  `3221225472 ≠ 1` unsolved. Hence the two-step form above.
- Used `ZMod.pow_card_sub_one_eq_one` without importing
  `Mathlib.FieldTheory.Finite.Basic`. The name was right, the import was
  missing.
- Put a plain `/- ... -/` comment above the imports. Mathlib's header linter
  reads that slot as a copyright header and warns. Moved the text to a
  `/-! ... -/` module doc after the imports and disabled
  `linter.style.header` in `lakefile.toml`.
- In a scratch file `decide` appeared to accept
  `(5 : ZMod 3221225473) ^ 1610612736 ≠ 1` directly. Not investigated and
  not used.

Not done yet:
- Primitive roots of unity (`w_n = 5^((p-1)/n)` has order n) in Lean.
