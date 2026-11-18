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

Qwen3.5:9b (9 billion parameters, local Ollama, 65,536-token context) was used for initial exploration through Claude Code. The attempted Ollama Cloud switch to `glm-5.3-flash` returned a billing error before it answered. Ryan then used Claude Sonnet 4.6 through Claude Pro for the successful `/new-feature` run and used the same Claude subscription for the Agent SDK self-audit. OpenAI Codex (GPT-6) assisted with verification, experiments and drafting. Parameter counts for the two hosted models were unavailable.

- **Agent contributions.** Sonnet implemented the matching-workday feature in `src/features.py`. Codex verified the results on all 714 eligible dates and expressed the same feature with an explicit shift before the rolling averages. Codex wrote the named-date test, the raw-column and unseen-weather tests, the validation comparison, the target-transformation experiment, the raw-file checksum, the fault-reproduction workflow and its documentation, and this report draft. It verified the raw counts and ran fault injections in a disposable checkout.
- **Student decisions and remaining review.** Ryan selected the course starter, ran the baseline, and chose to move agent inference off his laptop when local turns took several minutes. The split and two baselines were prescribed by the starter. Codex proposed the matching-day feature, the daily-change transformation, and the operating-cost assumption in Exercise 5. Those proposals and the evidence for them are identified in the decision log for Ryan's review.
