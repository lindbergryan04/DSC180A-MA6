---
name: seed-fault
description: Demonstrate how the forecasting tests react to one temporary change to the feature builder. Use for a leakage, lag, or weather regression.
argument-hint: "[forbidden-column | unshifted-mean | unknown-weather]"
---

Use `$ARGUMENTS` to select one change in `src/features.py`. For
`forbidden-column`, admit `casual` into the model columns. For
`unshifted-mean`, remove the one-day shift from `cnt_roll_7`. For
`unknown-weather`, remove the exception for an unrecognized label.
If the argument is unclear, ask which behavior to demonstrate.

1. Work in a disposable checkout of the current commit with the project's
   Python environment active. Run `make test` and record the starting result.
2. Apply only the selected change with the Edit tool. Capture the automatic
   hook response. Run `make test` and copy the failed assertion. If the hook
   stays silent or the suite passes unexpectedly, record what happened.
3. Restore just the changed lines with Edit. Run `make test` and report the
   actual repair-turn count, the assertion, and the final suite result.
4. Keep the raw CSV intact. Return the evidence for `docs/SEEDED_FAULTS.md`.
