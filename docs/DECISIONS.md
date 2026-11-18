# Decisions

One line per methodological decision: what you chose, why, and what it changed.
Agents append here via the `/new-feature` skill; you append here by hand.

- Exclude `casual`, `registered`: they sum to `cnt` exactly. Leaky model R^2 1.000 -> honest ridge 0.583.
- Exclude `cnt_2d_bfr`: a shipped 2-day lag we cannot test the alignment of. Build our own lags instead.
- Exclude `instant`, `yr`, `days_since_2011`: time indexes let a tree predict a flat constant past 2011 and a linear model extrapolate a trend we have no grounds for.
- Split 2011 / H1 2012 / H2 2012 by date. Test set touched once, after all feature work.
- Report mean and persistence baselines with every score. Persistence (test R^2 0.510, MAE 840) is within 0.07 R^2 of ridge and beats it on MAE; that caveat goes in the report.

- 2026-11-18 — Verified the raw file spans Jan 3, 2011 to Dec 31, 2012. March 10, 2011 is the only internal calendar gap. All 728 rows satisfy the target identity, so the same-day rider components stay excluded.
- 2026-11-18 — Codex proposed averaging the previous seven calendar days that match the forecast day's workday/holiday schedule. The schedule and every contributing count are available before the forecast. On 182 validation days, ridge R² changed from 0.6475 to 0.6459 (−0.0016) and boosting from 0.2185 to 0.2769 (+0.0584). Retain the feature for the shared comparison because boosting cleared the 0.01 decision threshold.
- 2026-11-18 — Select a single target transformation on validation: fit boosting to the change from yesterday and add yesterday's observed total back to the prediction. This raised validation R² from 0.2769 to 0.6104 and reduced MAE from 1,241.1 to 827.2 rides. The transformation is feasible for one-day-ahead forecasts with yesterday's final count.
- 2026-11-18 — Keep the untransformed run as the default. Use the validation-only command while experimenting, and fix the feature and transformation before evaluating them on the held-out period. The starter's test scores were already displayed during setup.
- 2026-11-18 — Document the matching-day history window, validation command, and fault-reproduction skill in CLAUDE.md so a future session uses the same rules.
- 2026-11-18 — Ryan ran the feature workflow on Claude Pro with Sonnet 4.6 after local Qwen ran slowly and the Ollama Cloud trial returned a billing error. Codex verified identical feature values on all 714 modeling dates when simplifying the implementation.
- 2026-11-18 — Retain the feature after the self-audit. All 714 eligible days had at least two matching days in their history. Codex checked all 575 one-, two- and three-input subsets for a same-day linear target identity and reproduced the known identity in a separate positive control.
