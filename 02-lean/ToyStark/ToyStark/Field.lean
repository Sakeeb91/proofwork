import Mathlib.FieldTheory.Finite.Basic
import Mathlib.NumberTheory.LucasPrimality
import Mathlib.Tactic.ReduceModChar

/-!
# The prime field F_p

The prime field F_p with p = 3 * 2^30 + 1, mirrored from
`00-foundations/toy-stark/src/toy_stark/field.py`.

The Python tests check facts about this field by running code. Here the
same facts are theorems, checked by the Lean kernel.

Mathlib's `ZMod n` is the ring of integers mod n. It is a field exactly
when n is prime, so the one thing we must supply is a proof that p is prime.
Everything else (the field laws, inverses) then comes from Mathlib.
-/
namespace ToyStark

/-- The modulus. Written as a literal so tactics can compute with it;
`P_eq` below ties it to the formula. -/
abbrev P : ℕ := 3221225473

/-- p = 3 * 2^30 + 1. -/
theorem P_eq : P = 3 * 2 ^ 30 + 1 := by norm_num

/-- p - 1 = 3 * 2^30. This factorisation is the whole reason for choosing p:
the multiplicative group has p - 1 elements, so it has a subgroup of size
2^k for every k ≤ 30. -/
theorem P_sub_one : P - 1 = 3 * 2 ^ 30 := by norm_num

/-- The only primes dividing p - 1 = 3 * 2^30 are 2 and 3.

A prime dividing a product divides one of the factors (Euclid's lemma), and
a prime dividing 2^30 divides 2. -/
theorem prime_dvd_P_sub_one {q : ℕ} (hq : q.Prime) (h : q ∣ P - 1) :
    q = 2 ∨ q = 3 := by
  rw [P_sub_one] at h
  rcases (Nat.Prime.dvd_mul hq).1 h with h3 | h2
  · exact Or.inr ((Nat.prime_dvd_prime_iff_eq hq Nat.prime_three).1 h3)
  · exact Or.inl ((Nat.prime_dvd_prime_iff_eq hq Nat.prime_two).1 (hq.dvd_of_dvd_pow h2))

/-! ### Three exponentiations

These are the same three numbers `test_generator_has_full_order` computes in
Python. The tactic `reduce_mod_char` evaluates `a ^ n` in `ZMod p` by
square-and-multiply, producing a proof with about log2(n) steps. A naive
unfolding of `^` would need about 3 billion multiplications.
-/

/-- 5^(p-1) = 1. For a prime p this is Fermat's little theorem; here we do
not know p is prime yet, so we compute it. -/
theorem five_pow_P_sub_one : (5 : ZMod P) ^ (P - 1) = 1 := by reduce_mod_char

/-- 5^((p-1)/2) = -1. -/
theorem five_pow_half : (5 : ZMod P) ^ ((P - 1) / 2) = -1 := by reduce_mod_char

/-- 5^((p-1)/3) = 1610563584. -/
theorem five_pow_third : (5 : ZMod P) ^ ((P - 1) / 3) = 1610563584 := by reduce_mod_char

/-- Neither of the two smaller powers is 1.

`decide` asks the kernel to evaluate the comparison. It is cheap here
because both sides are already reduced numbers below p. -/
theorem five_pow_div_prime_ne_one {q : ℕ} (hq : q.Prime) (h : q ∣ P - 1) :
    (5 : ZMod P) ^ ((P - 1) / q) ≠ 1 := by
  rcases prime_dvd_P_sub_one hq h with rfl | rfl
  · rw [five_pow_half]; decide
  · rw [five_pow_third]; decide

/-! ### Primality and the field -/

/-- p is prime, by the Lucas primality test:

    a^(p-1) = 1  and  a^((p-1)/q) ≠ 1 for every prime q dividing p - 1
    implies p is prime.

Intuition: the two conditions say a has multiplicative order exactly p - 1.
The invertible elements mod p number at most p - 1, with equality only when
every one of 1, ..., p - 1 is invertible, which is to say p is prime. So an
element of order p - 1 can only exist if p is prime. Fermat's theorem alone
is necessary for primality; ruling out the smaller exponents makes it
sufficient. -/
theorem P_prime : P.Prime :=
  lucas_primality P 5 five_pow_P_sub_one fun _ hq h => five_pow_div_prime_ne_one hq h

/-- Register primality so that typeclass search can find it. -/
instance : Fact P.Prime := ⟨P_prime⟩

/-- `ZMod P` is a field. Mathlib derives all the field laws (the ones the
Python tests sample on random elements) from primality alone. -/
example : Field (ZMod P) := inferInstance

/-- Fermat's little theorem for our field: a ≠ 0 implies a^(p-1) = 1.
This is what justifies `inverse()` in the Python: a⁻¹ = a^(p-2). -/
example (a : ZMod P) (ha : a ≠ 0) : a ^ (P - 1) = 1 := ZMod.pow_card_sub_one_eq_one ha

/-! ### The generator -/

/-- 5 has order exactly p - 1, so its powers are all p - 1 nonzero elements.
This is the Lean form of `test_generator_has_full_order`. -/
theorem orderOf_five : orderOf (5 : ZMod P) = P - 1 :=
  orderOf_eq_of_pow_and_pow_div_prime (by norm_num) five_pow_P_sub_one
    fun _ hq h => five_pow_div_prime_ne_one hq h

/-! ### Roots of unity -/

/-- For every n dividing p - 1, the element w_n = 5^((p-1)/n) has order
exactly n.

    order(g^k) = order(g) / gcd(order(g), k)

Intuition: g walks around a cycle of length p - 1. Taking steps of size
k = (p-1)/n, you return to the start after exactly n steps, because k
divides the cycle length. This is `primitive_root_of_unity` in the Python. -/
theorem orderOf_rootOfUnity {n : ℕ} (hn : n ∣ P - 1) :
    orderOf ((5 : ZMod P) ^ ((P - 1) / n)) = n := by
  have hP : P - 1 ≠ 0 := by norm_num
  have hk : (P - 1) / n ≠ 0 :=
    (Nat.div_pos (Nat.le_of_dvd (Nat.pos_of_ne_zero hP) hn)
      (Nat.pos_of_dvd_of_pos hn (Nat.pos_of_ne_zero hP))).ne'
  rw [orderOf_pow' _ hk, orderOf_five, Nat.gcd_eq_right (Nat.div_dvd_of_dvd hn),
    Nat.div_div_self hn hP]

/-! ### Shared test vector

The same value is asserted in `tests/test_field.py`
(`test_matches_lean_test_vector`). If the Python and the Lean model ever
disagree about arithmetic in F_p, one of the two checks fails.
-/

/-- 5^1000 = 80135535 in F_p. -/
theorem five_pow_1000 : (5 : ZMod P) ^ 1000 = 80135535 := by reduce_mod_char

end ToyStark
