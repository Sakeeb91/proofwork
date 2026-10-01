# ADR 002: Lean 4 for the mathematics, TLA+ deferred to the agent wallet
Date: 2026-10-01
Status: accepted

## Context
The repo wants machine-checked guarantees alongside the Python and the
benchmark. Two tools were considered: Lean 4 (with Mathlib) and TLA+.

Lean 4 is a proof assistant: you state a theorem and the kernel checks a
proof of it. Mathlib (https://github.com/leanprover-community/mathlib4)
already contains the algebra the toy STARK rests on, for example the ring
`ZMod n` of integers mod n.

TLA+ (https://lamport.azurewebsites.net/tla/tla.html) specifies state
machines and model-checks invariants over every interleaving of their steps.

## Decision
- Use Lean 4 with Mathlib for mathematical facts behind
  `00-foundations/toy-stark`. Each week of the toy STARK gets a Lean mirror
  of its key facts, in a Lake project at `02-lean/ToyStark/`.
- Do not use TLA+ for the STARK. The prover and verifier exchange messages
  in a fixed order, so there are no interleavings for a model checker to
  explore.
- Reserve TLA+ for `03-agent-wallet`, whose core claim (spending never
  exceeds the limit under any ordering of requests) is a state-machine
  invariant. That track is parked, so no TLA+ is written now.
- Proofs should be checked by the Lean kernel. `native_decide` trusts the
  Lean compiler in addition to the kernel, so it is allowed only as a
  flagged fallback, and each use is recorded in `02-lean/log.md`.
- ArkLib contributions stay in the ArkLib fork, as `CLAUDE.md` already says.
  `02-lean/ToyStark/` is for this repo's own learning proofs.

## Consequences
- A Lean theorem is about a Lean definition, not about the Python code.
  The link between the two is differential testing: Lean definitions are
  executable, so values computed in Lean are compared with the Python.
- Mathlib is a large dependency. Its prebuilt cache is downloaded into
  `.lake/`, which is gitignored. `lake-manifest.json` pins the exact
  Mathlib revision and is committed.
- Lean needs the `elan` toolchain manager installed on the machine.
