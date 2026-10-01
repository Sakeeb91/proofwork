# Handoff

Last updated: 2026-10-01, after week 2 of the toy STARK.
Read this with `CLAUDE.md` and `docs/roadmap.md`. It records state that is
not obvious from the code.

## Where things stand

Repo: https://github.com/Sakeeb91/proofwork (private), branch `main`, no CI.

| Track | State |
|---|---|
| `00-foundations/toy-stark` | Weeks 1 and 2 done: field, polynomials, domains, FibonacciSq trace and low-degree extension. 107 tests, about 5 s. |
| `02-lean/ToyStark` | Lean mirror of week 1: p is prime, `ZMod P` is a field, 5 has order p - 1, and for n dividing p - 1, 5^((p-1)/n) has order n. No mirror of week 2 yet. |
| `01-soundbench` | Scaffold only. |
| `03-agent-wallet` | Parked. TLA+ is reserved for it (ADR 002). |
| `04-reading-circle` | Scaffold only. |
| ZK Hack puzzles (roadmap, weeks 1 to 4) | None started. |

Python modules in `00-foundations/toy-stark/src/toy_stark/`:

- `field.py`: `FieldElement`, `P = 3 * 2^30 + 1`, generator 5, `primitive_root_of_unity(n)`.
- `polynomial.py`: `Polynomial` (immutable, coefficients lowest degree first, zero has degree -1), `vanishing_polynomial`, `interpolate` (Lagrange, O(n^2)).
- `domain.py`: `subgroup(n)`, `coset(offset, n)`.
- `fibonacci.py`: `fibonacci_sq_trace`, `trace_polynomial`, `low_degree_extension`, constants `A1`, `TRACE_LENGTH`, `BLOWUP`.

Values that tie the pieces together (STARK 101 Part 1):

| Quantity | Value | Checked where |
|---|---|---|
| a_1022 | 2338775057 | `tests/test_fibonacci.py` |
| f(2), f the trace polynomial | 1302089273 | `tests/test_fibonacci.py` |
| g = 5^((p-1)/1024) | 1855261384 | Lean `g_trace_value`, `tests/test_domain.py` |
| h = 5^((p-1)/8192) | 1734477367 | Lean `h_eval_value`, `tests/test_domain.py` |
| 5^1000 | 80135535 | Lean `five_pow_1000`, `tests/test_field.py` |

## How to run

Python, from `00-foundations/toy-stark/`:

    uv run pytest

Lean, from `02-lean/ToyStark/`:

    export PATH="$HOME/.elan/bin:$PATH"   # elan is installed but not on the default PATH
    lake exe cache get                    # only on a fresh clone; about 7 GB
    lake build

Expected: `107 passed` and `Build completed successfully` with no `sorry`
warning.

## Decisions

| ADR | Decision |
|---|---|
| `docs/decisions/001-prime-field.md` | F_p with p = 3 * 2^30 + 1, generator 5, Fermat inverse. |
| `docs/decisions/002-lean-for-maths-tla-for-wallet.md` | Lean 4 with Mathlib for the mathematics; TLA+ deferred to the agent wallet; no `native_decide` unless flagged. |
| `docs/decisions/003-polynomial-representation.md` | Dense coefficient tuples, schoolbook algorithms, O(n^2) Lagrange, no FFT yet. |
| `docs/decisions/004-follow-stark101-fibonacci-sq.md` | Prove STARK 101's FibonacciSq statement with its exact parameters. "Fibonacci" in the roadmap means FibonacciSq. |

Plans live in `docs/plans/`. The week 2 plan,
`docs/plans/2026-10-01-week2-polynomials.md`, ends with a Reviews section
recording what each reviewer found and what was done about it. Lean
attempts, including what failed, are in `02-lean/log.md`.

## Working rules

From `CLAUDE.md`: teach as you build (equation plus one sentence of
intuition in a comment), small verifiable steps, no invented citations or
numbers, no em dashes, no secrets in the repo.

Added by Sakeeb during these sessions:

- Every change is an atomic commit, pushed to GitHub immediately.
- Every design decision gets an ADR.
- Test first: write the test, watch it fail, then implement. In Lean, state
  the theorem with `sorry`, build, then prove.
- For a multi-step task: write a plan in `docs/plans/`, have it reviewed by
  a Fable advisor and by Codex before executing, record both reviews in the
  plan, and have Codex review the final diff.

## Tooling notes that cost time

- **Codex model.** `~/.codex/config.toml` sets `model = "gpt-6.1-sol"`, which
  the account rejects ("not supported when using Codex with a ChatGPT
  account"). Reviews were run with `--model gpt-6-astra --effort high`
  through the plugin's `task` command. The plugin's `review` command has no
  `--model` flag, so it fails until the config default is changed.
- **Commit hook.** A `block-no-verify` hook wrongly blocks a Bash call that
  contains `git commit` together with things like `grep -n` or `rm -rf`.
  Keep `git commit` in a call of its own.
- **Lean.** `reduce_mod_char` evaluates big powers in `ZMod P` and needs the
  modulus as a numeric literal. `norm_num` cannot prove `Nat.Prime P`
  directly at this size. Check lemma names by grep in
  `.lake/packages/mathlib` before using them.
- **STARK 101 source.** The official repo linked from
  https://starkware.co/stark-101/ returned 404 on 2026-10-01. A public copy
  is at https://github.com/fxfactorial/stark101.

## Known gaps

- No Lean mirror of week 2 (polynomials, interpolation).
- The notebook's SHA-256 checks on the extension are not reproduced; they
  need StarkWare's serialisation and belong with the Merkle and channel
  work.
- `02-lean/README.md` has no ArkLib fork link yet.
- Mathlib is pinned at a release candidate, `v4.35.0-rc3`.
- No CI.

## Next steps

1. Week 3: Merkle tree commitments and the Fiat-Shamir channel (STARK 101
   Part 1 ending and Part 3 preliminaries). Commit to the 8192 extension
   values and reproduce the notebook's Merkle root if the serialisation can
   be matched.
2. Week 3 or 4: constraints (STARK 101 Part 2). The three FibonacciSq
   constraints as rational functions, the composition polynomial.
3. Week 4: FRI and the full prove and verify (Parts 3 and 4). Completes the
   roadmap's first milestone, with an explainer.
4. In parallel: a first ZK Hack puzzle with a writeup in `docs/notes/`.
5. Optional Lean: state "a nonzero polynomial of degree d has at most d
   roots" for `ZMod P` using Mathlib's `Polynomial`.

## Kickoff prompt for a new session

```text
Read CLAUDE.md, docs/HANDOFF.md, docs/roadmap.md, and the Reviews section
of docs/plans/2026-10-01-week2-polynomials.md. Then run the Python tests
(uv run pytest in 00-foundations/toy-stark) and the Lean build
(export PATH="$HOME/.elan/bin:$PATH"; lake build in 02-lean/ToyStark) and
tell me whether the state matches the handoff.

Task: build week 3 of the toy STARK: a Merkle tree commitment over the
8192 low-degree extension values, and the Fiat-Shamir channel, following
STARK 101. Try to reproduce the notebook's Merkle root.

Process:
- Write a plan to docs/plans/ first, with full code and tests per task.
  Have it reviewed by a Fable advisor and by Codex at high effort
  (use --model gpt-6-astra unless GPT 6.1 has become available), revise,
  and record both reviews in the plan.
- Test first. One atomic commit per logical change, pushed immediately.
  One ADR per design decision. Keep git commit in its own Bash call.
- Teach as you build: equation plus one sentence of intuition in comments.
  No invented citations or numbers. No em dashes.
- After implementing, have Codex review the diff, fix findings, then
  update docs/HANDOFF.md.
```
