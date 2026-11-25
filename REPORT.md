# Results

The task is to forecast the number of Capital Bikeshare rides one day ahead. There are 728 daily observations from January 3, 2011 through December 31, 2012. Reindexing by calendar day exposes a gap on March 10, 2011. Building seven-day histories removes the first seven observations and the seven that immediately follow the gap. The remaining 714 days split into 348 for training in 2011, 182 for validation in the first half of 2012, and 184 for testing in the second half.

The new predictor averages rides over the previous seven calendar days with the same scheduled workday status as the forecast day. For example, the Sunday forecast for January 16 uses the preceding Sunday and Saturday. Its value is (822 + 1,248) / 2 = 1,035 rides. A Monday holiday draws on days off as well. Each count in the average is available by the morning of the forecast. If the window has no matching day, the feature uses the ordinary prior-week mean.

| Features | Forecast | Validation R² | Validation MAE | Test R² | Test MAE |
|---|---|---:|---:|---:|---:|
| Before | Training mean | -0.9318 | 2002.2 | -2.1441 | 2847.7 |
| Before | Yesterday's count | 0.4507 | 900.6 | 0.5099 | 840.1 |
| Before | Ridge | 0.6475 | 832.9 | 0.5833 | 947.1 |
| Before | Gradient boosting | 0.2185 | 1296.6 | -0.4975 | 1972.6 |
| After | Training mean | -0.9318 | 2002.2 | -2.1441 | 2847.7 |
| After | Yesterday's count | 0.4507 | 900.6 | 0.5099 | 840.1 |
| After | Ridge | 0.6459 | 830.6 | 0.5794 | 947.7 |
| After | Gradient boosting | 0.2769 | 1241.1 | -0.4272 | 1932.3 |

MAE is the mean absolute error in rides per day. Both versions use the same dates, model settings, and dependency versions. From a clean checkout with the pinned requirements installed, `make all` reproduces all eight rows in `reports/metrics.json`. The four entries under `before_feature` correspond to the first four rows.

The self-audit found no target leakage and confirmed the time split and both baselines. It raised two points worth checking. A matching-day average could rely on a single prior day, but every one of the 714 forecasts had between two and five matching days. The auditor also reported testing only two candidate triples. A separate check of all 575 sets of one, two or three of the 15 model inputs found no linear identity that reproduced the target. As a positive control, the same check recovered the known identity for casual and registered rides.

# Headline finding

The easiest way to reach R² = 1.000 here is to give the model a day's casual and registered rider counts. They add up to total ridership on every observed day, which makes the apparent forecast impossible to use that morning. Once those inputs are excluded, yesterday's count sets a much harder benchmark. With the added feature, ridge explains 57.94% of the variation on the held-out days, compared with 50.99% for persistence. Boosting on total rides scores −0.4272 on test and still beats the training mean (−2.1441). The training maximum was 6,043 rides. Of the 184 test days, 104 exceeded it, and the busiest reached 8,714. Predicting absolute levels from the earlier year leaves the booster poorly equipped for that growth. The feature was retained because it improved boosting's validation R² by 0.0584, even though ridge's validation R² decreased by 0.0016.

# Exercise 4: target transformation

How far will demand move from yesterday? Yesterday's total provides a current reference level. Train the same booster on the signed change in rides, then add its predicted change to yesterday's known count. A prediction of zero change reproduces persistence. This lets the final forecast exceed the 2011 training maximum even when the adjustment is modest. The transformation uses no future counts and fits the one-day-ahead use case. For forecasts several days ahead, yesterday's actual ridership would no longer be available at every step.

On validation this raised boosting's R² from 0.2769 to 0.6104 and reduced MAE from 1,241.1 to 827.2 rides. The feature and transformation were fixed using validation. The initial starter run had already displayed its own test scores. The final comparison evaluated the frozen changes on the holdout with no subsequent tuning. Transformed boosting reached 0.5789 test R² and 874.0 rides MAE, compared with 0.5794 and 947.7 for ridge. Run `python -m src.train --predict-change` after `make all` to reproduce the separate experiment.

# Exercise 5: ridge vs persistence

For staging bikes with a roughly constant cost per bike misplaced, persistence is the better of these two candidates. Ridge improves test R² by 0.0695, so it reduces squared error across the held-out period. Yet the average absolute miss grows from 840.1 to 947.7 rides, an extra 107.6 rides per day. If a few severe shortages drive most operating costs, that trade-off deserves a cost-weighted comparison. This dataset contains systemwide totals, so the numbers alone cannot establish the operational cost at individual stations. The weather predictors are also same-day observations. An actual morning deployment of ridge would need to be evaluated with weather forecasts available at decision time.

# Attribution

Qwen3.5:9b (9 billion parameters, local Ollama, 65,536-token context) ran the first Claude Code exploration on Ryan's laptop. Local turns took several minutes, and an attempted Ollama Cloud switch to `glm-5.3-flash` returned a billing error before it answered, so Ryan switched Claude Code to Claude Sonnet 4.6 on his Claude Pro subscription. OpenAI Codex (GPT-6) handled verification, the experiments and the first draft of this report. Claude Opus 5.5 checked the finished repository against the assignment on November 22, ran the peer audit on November 25, and made the last edits. Parameter counts for the three hosted models were unavailable.

**Agent-generated files and functions**

- **Claude Sonnet 4.6**
  - `src/features.py`: the first version of `cnt_prior_week_same_type`, written through `/new-feature`.
  - `reports/audit.jsonl`: the self-audit, run with `python agent/audit.py . --claude-plan`.
  - `docs/SEEDED_FAULTS.md`: the fault and repair edits quoted from the three live `/seed-fault` runs.
  - `docs/AUDIT.md`: the `leakage-auditor` report on the teammate's repository.
- **Codex (GPT-6)**
  - `src/features.py`: rewrote `cnt_prior_week_same_type` with an explicit shift before the rolling averages. Its values match Sonnet's version on all 714 dates.
  - `tests/test_leakage.py`: `test_prior_week_matching_workdays` and `test_unknown_weather_raises`.
  - `tests/test_contract.py`: `test_every_raw_column_has_a_role`.
  - `src/config.py`: `RAW_PREDICTORS`, `EXPERIMENT_FEATURE` and `RAW_SHA256`.
  - `src/ingest.py`: the raw-file checksum check.
  - `src/train.py`: the `--validation-only` and `--predict-change` options and the `before_feature` comparison.
  - `agent/audit.py`: the `--claude-plan` option, a JSON-schema tool input, Parquet support and a revised audit prompt.
  - `.claude/`: the `seed-fault` skill, the hook's `.venv/bin/python` fallback, and the read instructions that replaced the shell command in the `new-feature` skill.
  - `CLAUDE.md`, `README.md` and `.gitignore`: the edits in commit `f678f09`.
  - The 575-subset identity check, the direct hook-invocation evidence in `docs/SEEDED_FAULTS.md`, and the first draft of this report.
- **Claude Opus 5.5**
  - `CLAUDE.md`: the `/new-feature` line.
  - `docs/DECISIONS.md`: the weather-label counts and the 2026-11-22 entries.
  - `docs/SEEDED_FAULTS.md`: the live-run sections, copied from Claude Code's debug logs.
  - `REPORT.md`: this Attribution section.
  - `docs/AUDIT.md`: the headless auditor run, the independent checks, and a draft of the verdict for Ryan to confirm.
  - Verification: reran `make all` and `make test` from a fresh clone and matched all eight table rows to `reports/metrics.json`.

**Ryan's decisions**

The split, both baselines and the forbidden columns came with the starter. Codex proposed the feature, the transformation and the Exercise 5 cost assumption, and Claude Opus 5.5 proposed the last item. Ryan reviewed each proposal before keeping it. Every item has a line in `docs/DECISIONS.md`.

1. Switch Claude Code from local Qwen3.5:9b to Sonnet 4.6 after slow local turns and the Ollama Cloud billing error (2026-11-18, commit `f678f09`).
2. Keep the matching-workday feature under the starter skill's 0.01 validation-R² threshold. Boosting gained 0.0584 and ridge lost 0.0016 (2026-11-18, `f678f09`). Keep it again after the self-audit (`73d8f00`).
3. Exercise 4: fit boosting to the change from yesterday, chosen on validation, while keeping the untransformed run as the default in `reports/metrics.json` (2026-11-18, `f678f09`).
4. Exercise 5: recommend persistence over ridge at a constant cost per misplaced bike (2026-11-22, `cc823a7`).
5. Name `/new-feature` in CLAUDE.md (2026-11-22, `cc823a7`) and repeat the seeded faults through Claude Code itself (2026-11-22, `d2a9eb5`).
