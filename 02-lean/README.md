# Lean / ArkLib
- Fork: (add link to your ArkLib fork)
- Workflow log: `log.md`. Record each attempt: target lemma, model used, what worked, where the AI failed. This log becomes the experience report.
- `ToyStark/`: Lake project with Lean mirrors of the facts behind `00-foundations/toy-stark`. See `docs/decisions/002-lean-for-maths-tla-for-wallet.md`.

## Running the Lean proofs
Needs `elan` (https://github.com/leanprover/elan). From `02-lean/ToyStark/`:

    lake exe cache get   # download prebuilt Mathlib, about 7 GB on disk, once
    lake build

| File | Proves | Python counterpart |
|---|---|---|
| `ToyStark/Field.lean` | p = 3 * 2^30 + 1 is prime; `ZMod P` is a field; 5 has order p - 1 | `toy_stark/field.py`, `tests/test_field.py` |
