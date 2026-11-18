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
