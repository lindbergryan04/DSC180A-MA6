# Audit of a teammate's repository (Exercise 3)

Audited https://github.com/Sweekrit-B/DSC180A-MA6 at commit `2e37d82`. The diff under review is everything since that repository's unmodified starter commit, `git diff 8ef3083 HEAD -- src tests`.

## The run

On 2026-11-25 Claude Code ran this repository's `leakage-auditor` subagent (`.claude/agents/leakage-auditor.md`) with Claude Sonnet 4.6. The session started in a throwaway clone of this repository, so the subagent definition is this repository's own, and a fresh clone of the teammate's repository was added with `--add-dir`:

```sh
claude -p "Use the leakage-auditor subagent to review a teammate's repository at <peer> \
  (cloned from https://github.com/Sweekrit-B/DSC180A-MA6). The diff under review is everything \
  since that repository's first commit, the unmodified course starter: run \
  git -C <peer> diff 8ef3083 HEAD -- src tests to see it. ..." \
  --model sonnet --add-dir <peer> --disallowedTools Edit Write NotebookEdit \
  --allowedTools Task Read Grep Glob "Bash(git:*)" "Bash(python:*)" "Bash(make:*)" \
  --output-format stream-json --verbose
```

The teammate's code ran in a Python environment installed from the same pinned `requirements.txt`. Claude Code's permission checks refused six of the subagent's Bash calls: compound commands that needed approval and attempts to write temporary scripts. It repeated those checks with allowed commands, including `python -m pytest tests/ -v`, `python -m src.features`, `python -m src.train` and `python -m src.train --target diff_roll7`. Neither repository was modified.

## Auditor output (verbatim)

Copied from the subagent's result in the session log, without the agent-id and token-usage lines Claude Code appends. The clone path is shortened to `<peer>`.

```text
I have now read all the relevant code, run the tests, and verified the arithmetic. Here is the full audit against all five checks.

---

## Methodology Review

**Repository:** `<peer>`

**Diff base:** commit `8ef3083` (unmodified course starter) to `HEAD`

---

### Check 1 — Target Leakage

No finding. `casual` and `registered` are excluded from the feature set by `FORBIDDEN` in `<peer>/src/config.py`. `feature_columns()` in `src/features.py` filters every column in `FORBIDDEN` before returning. `test_no_forbidden_features` and `test_no_feature_is_a_renamed_leak` both pass. The correlation threshold of 0.95 with `cnt` is not reached by any feature; `cnt_roll_7` is the strongest honest feature at ~0.85 correlation.

The `diff_roll7` target transform (`cnt - cnt_roll_7`) uses `cnt_roll_7` which is built with `shift(1)` before the rolling mean, so `cnt_roll_7` at time t contains only counts from t-7 through t-1. The forward transform does not expose today's `cnt` to the model indirectly.

---

### Check 2 — Temporal Ordering

No finding.

**Lag construction:** `src/features.py` line 80–82 applies `.shift(1)` before all lag and rolling aggregations. The new `temp_delta_3` feature at line 75 uses `out.temp.shift(1).rolling(3).mean()`, keeping today's temperature out of the baseline.

**Split:** `temporal_split()` in `src/train.py` lines 62–65 partitions strictly by `dteday` date string comparison against `TRAIN_END` and `VALID_END`. No random split is possible.

**Scaler fit scope:** `model.fit(train[cols], fwd(train))` at line 97 in `src/train.py` is called only on the train partition. The `StandardScaler` inside the Ridge pipeline sees only 2011 data during fitting.

---

### Check 3 — Calendar Gaps

No finding. `reindex_to_calendar()` in `src/features.py` lines 34–50 inserts an explicit NaN row for 2011-03-10 (the missing day in the mirror) before any lag or rolling window is computed. After `dropna()` at line 84, any row whose window spans the gap is removed rather than silently given a shorter window. `test_calendar_is_complete_before_lagging` verifies the gap-free index; `test_lags_are_true_calendar_lags` and `test_temp_delta_3_uses_prior_calendar_days` both check the values against calendar arithmetic, not row arithmetic, and both pass.

---

### Check 4 — Silent Row Loss

No finding. `encode_weather()` raises `ValueError` on unknown labels rather than silently producing NaN. The row-loss bound in `test_only_expected_rows_are_dropped` asserts that the number of dropped rows does not exceed `LAG_WARMUP + LAG_WARMUP * missing_days`. With `LAG_WARMUP = 7` and one missing day, the allowed loss is 14 rows; the actual loss from 728 raw rows to 714 feature rows is 14, which meets the bound exactly. No `.merge()` is used; no `.map()` on the target or feature columns can silently suppress rows.

---

### Check 5 — Unreported Baselines

No finding. `reports/metrics.json` reports three baselines alongside every model score:

- `baseline_mean` (predict the 2011 training mean)
- `baseline_persistence` (predict yesterday's count via `cnt_lag_1`)
- `baseline_roll7` (predict last week's rolling average via `cnt_roll_7`)

The persistence baseline is the most relevant comparator for a lag-driven model and its valid R² (0.4507) is reported. Ridge (valid R² 0.6843) beats persistence; HGB (valid R² 0.1722) does not, and that negative result is preserved rather than hidden. For the `diff_roll7` target transform run, `baseline_roll7` is correctly the anchor comparator (valid R² 0.5945), and HGB (0.7393) beats it on validation, which is the stated motivation for the transform.

---

### Summary

All five checks pass. No finding changes a reported number or invalidates a conclusion.
```

## Independent checks

Claude Opus 5.5 ran these on the same clone to test the auditor's claims.

- `make all` rewrote `reports/metrics.json` with no difference from the committed file.
- `make test` gave `19 passed in 0.92s`.
- Validation R² in `reports/metrics.json`: persistence 0.4507, `baseline_roll7` 0.5945, ridge 0.6843, boosting 0.1722. `python -m src.train --target diff_roll7` printed 0.7393 for boosting. All match the auditor's figures.
- The largest absolute correlation between a model input and `casual`, `registered` or `cnt` is 0.849, for `cnt_roll_7` against `cnt`.
- 728 raw rows become 714 feature rows.
- `FORBIDDEN` contains the same seven columns in both repositories.

## My verdict

The auditor found nothing that changes a number, and the independent checks agree, so I accept its result. It read `src/config.py` from my repository instead of theirs, but both files define the same `FORBIDDEN` set, so its leakage check still holds. It did not discuss that `temp_delta_3` subtracts from the same day's temperature. That follows the starter's rule that same-day weather is known at forecast time, the assumption behind every weather input in both repositories, so it is not leakage under the assignment's rules. A real morning forecast would need a temperature forecast in its place.
