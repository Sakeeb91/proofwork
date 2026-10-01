# proofwork: instructions for Claude

## What this repo is
A research lab with one owner (Sakeeb, theoretical physics background, AI safety researcher, new to cryptography).
Goals, in order: (1) real understanding, (2) publishable artifacts, (3) community contribution.

## How to work with me
- Teach as you build. When you introduce a cryptographic concept, give the equation and one sentence of intuition in a code comment or the PR description.
- Prefer small, verifiable steps. Run code and tests before saying something works.
- Never invent citations, CVE numbers, or benchmark numbers. Every claim in `docs/` or `paper/` needs a source link.
- Write prose without em dashes and without filler.

## Layout
- `00-foundations/toy-stark/`: Python, educational, readability over speed.
- `01-soundbench/`: flagship benchmark. See its own CLAUDE.md.
- `02-lean/`: notes and scratch Lean. Real contributions happen in a fork of ArkLib, linked in `02-lean/README.md`.
- `04-reading-circle/sessions/`: one folder per session.
- `docs/decisions/`: one short ADR per design decision (template in `docs/decisions/000-template.md`).

## Tooling
- Python: `uv` (`uv run pytest`). Lean: `lake`. ZK toolchains (circom, noir, halo2, zkVMs) run only inside Docker images in `01-soundbench/env/`.

## Hard rules (security research)
- Exploit code runs only against local copies in Docker. Never against mainnet, testnets, or anyone's live deployment.
- Never add private keys, seed phrases, or API keys to the repo. Use `.env` (gitignored).
- If any agent run finds a bug that is NOT already public, stop, write it to `01-soundbench/disclosures/` (gitignored), and tell me. We disclose privately to the maintainer before anything is published.
