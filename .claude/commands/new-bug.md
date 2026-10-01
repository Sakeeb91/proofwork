Add a known, PUBLIC ZK soundness bug to SoundBench.

Bug source (URL or advisory): $ARGUMENTS

1. Confirm the bug is publicly disclosed. If not, stop and tell me.
2. Create `01-soundbench/bugs/<project>-<short-name>/` from `01-soundbench/bugs/_template/`.
3. Fill `metadata.yaml` with sources. Leave fields blank where unknown; never guess.
4. Pin the vulnerable commit and the fixed commit. Add a minimal reproducing test that fails on the vulnerable version and passes on the fix, run inside the Docker env.
5. Summarize the bug for me in 3 sentences with the underlying math (what constraint was missing).
