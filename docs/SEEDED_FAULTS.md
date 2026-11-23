# Seeded faults

The new feature's named-date test was committed while failing. Its three expected values come from the raw counts on days with the matching work schedule.

## Feature test before implementation

```text
python -m pytest tests/ -q
...........F...                                                          [100%]
=================================== FAILURES ===================================
______________________ test_prior_week_matching_workdays _______________________

feats =         dteday  instant  season  ...  cnt_lag_1 cnt_lag_7   cnt_roll_7
0   2011-01-10     10.0  WINTER  ...      822.0...    1787.0  1530.142857
713 2012-12-31    731.0  WINTER  ...     1796.0     920.0  1531.428571

[714 rows x 28 columns]

    def test_prior_week_matching_workdays(feats):
        # Sun Jan 16 and the Mon Jan 17 holiday both use non-workday history.
        by_date = feats.set_index("dteday")
>       assert "cnt_prior_week_same_type" in feature_columns(feats)
E       AssertionError: assert 'cnt_prior_week_same_type' in ['temp', 'atemp', 'hum', 'windspeed', 'dayofweek', 'is_weekend', ...]
E        +  where ['temp', 'atemp', 'hum', 'windspeed', 'dayofweek', 'is_weekend', ...] = feature_columns(        dteday  instant  season  ...  cnt_lag_1 cnt_lag_7   cnt_roll_7\n0   2011-01-10     10.0  WINTER  ...      822.0...    1787.0  1530.142857\n713 2012-12-31    731.0  WINTER  ...     1796.0     920.0  1531.428571\n\n[714 rows x 28 columns])

tests/test_leakage.py:72: AssertionError
=========================== short test summary info ============================
FAILED tests/test_leakage.py::test_prior_week_matching_workdays - AssertionEr...
1 failed, 14 passed in 1.39s
make: *** [test] Error 1
```

## How the fault checks were run

Codex introduced these changes one at a time in a disposable checkout of the working pipeline. For each Python edit it ran the full suite, supplied a representative PostToolUse Edit event to the actual project hook on stdin, recorded stderr and exit status, and repaired the edit in the next Codex turn. These are direct hook invocations. The output does not establish delivery through an interactive Claude session.

On 2026-11-22 the three code faults were repeated through Claude Code itself, so the hook fired on the agent's own Edit calls. Each run invoked the project's `/seed-fault` skill headless with Claude Sonnet 4.6 (Ryan's Claude subscription) in a throwaway clone of commit `cc823a7`:

```sh
claude -p "/seed-fault <fault>" --model sonnet --permission-mode acceptEdits \
  --output-format stream-json --verbose --debug-file <fault>.debug.log
```

Two more options were passed. `--settings` pointed Claude Code at the Anthropic API instead of the local Ollama endpoint in `.claude/settings.json`, and `--append-system-prompt` said the directory was already a disposable clone. The command ran under `env -i` because the parent Claude desktop session exports `CLAUDE_CODE_SIMPLE`, which disables hooks in child sessions. The session transcript does not store PostToolUse hook output, so the hook evidence below is copied from the `--debug-file` log, where Claude Code writes `Hook PostToolUse:Edit (PostToolUse) error:` followed by the hook's stderr. A first forbidden-column attempt without that log left no record of the hook and was repeated with logging. The clone path is shortened to `<clone>`. In every run the repair Edit triggered the hook again, which passed without output.

## A same-day component reaches the model

In `feature_columns`, replaced `if c not in FORBIDDEN` with `if c not in FORBIDDEN or c == "casual"`.

The full suite exited with code 2. Its last lines were

```text
=========================== short test summary info ============================
FAILED tests/test_leakage.py::test_no_forbidden_features - AssertionError: fo...
1 failed, 16 passed in 1.44s
make: *** [test] Error 1
```

The hook exited with code 2 and wrote the following to stderr.

```text
Leakage tests failed after editing /private/tmp/ma6-evidence.m3encmV8/candidate/src/features.py:
feats =         dteday  instant  ...   cnt_roll_7  cnt_prior_week_same_type
0   2011-01-10     10.0  ...  1344.000000         ...               1380.333333
713 2012-12-31    731.0  ...  1531.428571               1642.500000

[714 rows x 29 columns]

    def test_no_forbidden_features(feats):
        """Guards the gate, not the data: feature_columns() excludes FORBIDDEN by
        construction, so this cannot discover a *new* leaky column. What it
        catches is someone editing feature_columns() or FORBIDDEN -- which is
        exactly the fault the Step 7 hook demonstrates."""
        cols = set(feature_columns(feats))
>       assert not (cols & FORBIDDEN), f"forbidden columns in feature set: {cols & FORBIDDEN}"
E       AssertionError: forbidden columns in feature set: {'casual'}
E       assert not ({'atemp', 'casual', 'cnt_lag_1', 'cnt_lag_7', 'cnt_prior_week_same_type', 'cnt_roll_7', ...} & {'casual', 'cnt', 'cnt_2d_bfr', 'days_since_2011', 'instant', 'registered', ...})

tests/test_leakage.py:31: AssertionError
=========================== short test summary info ============================
FAILED tests/test_leakage.py::test_no_forbidden_features - AssertionError: fo...
1 failed, 8 passed in 0.28s
```

Repair took one Codex turn. Removed the exception for `casual`.

```text
python -m pytest tests/ -q
.................                                                        [100%]
17 passed in 1.00s
```

### Live Claude Code run

Sonnet's fault edit:

```diff
-    return [c for c in numeric if c not in FORBIDDEN]
+    return [c for c in numeric if c not in FORBIDDEN or c == "casual"]
```

Hook stderr from the debug log:

```text
Leakage tests failed after editing <clone>/src/features.py:
feats =         dteday  instant  ...   cnt_roll_7  cnt_prior_week_same_type
0   2011-01-10     10.0  ...  1344.000000         ...               1380.333333
713 2012-12-31    731.0  ...  1531.428571               1642.500000

[714 rows x 29 columns]

    def test_no_forbidden_features(feats):
        """Guards the gate, not the data: feature_columns() excludes FORBIDDEN by
        construction, so this cannot discover a *new* leaky column. What it
        catches is someone editing feature_columns() or FORBIDDEN -- which is
        exactly the fault the Step 7 hook demonstrates."""
        cols = set(feature_columns(feats))
>       assert not (cols & FORBIDDEN), f"forbidden columns in feature set: {cols & FORBIDDEN}"
E       AssertionError: forbidden columns in feature set: {'casual'}
E       assert not ({'atemp', 'casual', 'cnt_lag_1', 'cnt_lag_7', 'cnt_prior_week_same_type', 'cnt_roll_7', ...} & {'casual', 'cnt', 'cnt_2d_bfr', 'days_since_2011', 'instant', 'registered', ...})

tests/test_leakage.py:31: AssertionError
=========================== short test summary info ============================
FAILED tests/test_leakage.py::test_no_forbidden_features - AssertionError: fo...
1 failed, 8 passed in 0.28s
```

`make test` then ended with

```text
FAILED tests/test_leakage.py::test_no_forbidden_features - AssertionError: fo...
1 failed, 16 passed in 1.01s
make: *** [test] Error 1
```

Repair took one Edit, Sonnet's next tool call after that `make test`. Sonnet did not rerun `make test` after the repair. Afterwards the clone had no uncommitted changes, and a separate `python -m pytest tests/ -q` there gave `17 passed in 1.27s`.

## The seven-day mean includes the forecast day

In the `cnt_roll_7` assignment, replaced `out[TARGET].shift(1).rolling(LAG_WARMUP).mean()` with `out[TARGET].rolling(LAG_WARMUP).mean()`.

The full suite exited with code 2. Its last lines were

```text
=========================== short test summary info ============================
FAILED tests/test_leakage.py::test_rolling_mean_excludes_today - assert np.fl...
1 failed, 16 passed in 0.94s
make: *** [test] Error 1
```

The hook exited with code 2 and wrote the following to stderr.

```text
Leakage tests failed after editing /private/tmp/ma6-evidence.m3encmV8/candidate/src/features.py:
[714 rows x 29 columns]

    def test_rolling_mean_excludes_today(feats):
        """cnt_roll_7 must be the mean of the 7 calendar days *before* today."""
        by_date = feats.set_index("dteday")[TARGET]
        date = feats.dteday.iloc[200]
        window = [date - pd.Timedelta(days=k) for k in range(1, 8)]
        if all(d in by_date.index for d in window):
            expected = sum(by_date[d] for d in window) / 7
>           assert feats.set_index("dteday").cnt_roll_7[date] == pytest.approx(expected)
E           assert np.float64(4389.0) == 4414.857142857143 ± 0.00441486
E             
E             comparison failed
E             Obtained: 4389.0
E             Expected: 4414.857142857143 ± 0.00441486

tests/test_leakage.py:57: AssertionError
=========================== short test summary info ============================
FAILED tests/test_leakage.py::test_rolling_mean_excludes_today - assert np.fl...
1 failed, 8 passed in 0.25s
```

Repair took one Codex turn. Restored the shift before the rolling mean.

```text
python -m pytest tests/ -q
.................                                                        [100%]
17 passed in 0.88s
```

### Live Claude Code run

Sonnet's fault edit:

```diff
-    out["cnt_roll_7"] = out[TARGET].shift(1).rolling(LAG_WARMUP).mean()
+    out["cnt_roll_7"] = out[TARGET].rolling(LAG_WARMUP).mean()
```

Hook stderr from the debug log:

```text
Leakage tests failed after editing <clone>/src/features.py:
[714 rows x 29 columns]

    def test_rolling_mean_excludes_today(feats):
        """cnt_roll_7 must be the mean of the 7 calendar days *before* today."""
        by_date = feats.set_index("dteday")[TARGET]
        date = feats.dteday.iloc[200]
        window = [date - pd.Timedelta(days=k) for k in range(1, 8)]
        if all(d in by_date.index for d in window):
            expected = sum(by_date[d] for d in window) / 7
>           assert feats.set_index("dteday").cnt_roll_7[date] == pytest.approx(expected)
E           assert np.float64(4389.0) == 4414.857142857143 ± 0.00441486
E             
E             comparison failed
E             Obtained: 4389.0
E             Expected: 4414.857142857143 ± 0.00441486

tests/test_leakage.py:57: AssertionError
=========================== short test summary info ============================
FAILED tests/test_leakage.py::test_rolling_mean_excludes_today - assert np.fl...
1 failed, 8 passed in 0.23s
```

`make test` then ended with

```text
FAILED tests/test_leakage.py::test_rolling_mean_excludes_today - assert np.fl...
1 failed, 16 passed in 0.95s
make: *** [test] Error 1
```

Repair took one Edit, Sonnet's next tool call after that `make test`. The final `make test` gave `17 passed in 1.19s`.

## An unknown weather label is silently accepted

Removed the `if unknown` block and its `raise ValueError` from `encode_weather`. A synthetic unseen label exercises this path even though every label in the supplied CSV is known.

The full suite exited with code 2. Its last lines were

```text
=========================== short test summary info ============================
FAILED tests/test_leakage.py::test_unknown_weather_raises - Failed: DID NOT R...
1 failed, 16 passed in 0.93s
make: *** [test] Error 1
```

The hook exited with code 2 and wrote the following to stderr.

```text
Leakage tests failed after editing /private/tmp/ma6-evidence.m3encmV8/candidate/src/features.py:
........F                                                                [100%]
=================================== FAILURES ===================================
_________________________ test_unknown_weather_raises __________________________

    def test_unknown_weather_raises():
>       with pytest.raises(ValueError, match="unmapped weather labels"):
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       Failed: DID NOT RAISE ValueError

tests/test_leakage.py:81: Failed
=========================== short test summary info ============================
FAILED tests/test_leakage.py::test_unknown_weather_raises - Failed: DID NOT R...
1 failed, 8 passed in 0.24s
```

Repair took one Codex turn. Restored the explicit exception for unknown labels.

```text
python -m pytest tests/ -q
.................                                                        [100%]
17 passed in 0.95s
```

### Live Claude Code run

Sonnet's fault edit:

```diff
     known = series.dropna()
-    unknown = set(known.unique()) - set(WEATHER_ORDER)
-    if unknown:
-        raise ValueError(f"unmapped weather labels: {sorted(unknown)}")
     return series.map(WEATHER_ORDER).astype(float)
```

Hook stderr from the debug log:

```text
Leakage tests failed after editing <clone>/src/features.py:
........F                                                                [100%]
=================================== FAILURES ===================================
_________________________ test_unknown_weather_raises __________________________

    def test_unknown_weather_raises():
>       with pytest.raises(ValueError, match="unmapped weather labels"):
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       Failed: DID NOT RAISE ValueError

tests/test_leakage.py:81: Failed
=========================== short test summary info ============================
FAILED tests/test_leakage.py::test_unknown_weather_raises - Failed: DID NOT R...
1 failed, 8 passed in 0.22s
```

`make test` then ended with

```text
FAILED tests/test_leakage.py::test_unknown_weather_raises - Failed: DID NOT R...
1 failed, 16 passed in 0.93s
make: *** [test] Error 1
```

Repair took one Edit, Sonnet's next tool call after that `make test`. The final `make test` gave `17 passed in 0.90s`.

## A change to the raw CSV outside the feature editor

In the disposable checkout, Codex copied a fixture with one extra blank line onto the scratch copy of the raw CSV. Pandas reads the same records from either file. The Edit/Write matcher does not run the leakage hook for a shell file copy. A SHA-256 check during `make data` caught the byte change before the feature stage. The original assignment CSV stayed intact.

The altered copy produced this output and exit code 2.

```text
python -m src.ingest
raw CSV checksum mismatch; check the source file
make: *** [data] Error 1
```

Restoring the original bytes produced this result.

```text
python -m src.ingest
OK ingest: 728 rows, 2011-01-03 -> 2012-12-31
```
