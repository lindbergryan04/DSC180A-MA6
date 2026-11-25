"""Stage 3: temporal split, fit, evaluate, write metrics.

Two baselines and two models, on purpose.

  baseline_mean         predict the 2011 average for every day
  baseline_persistence  predict yesterday's count (cnt_lag_1)
  ridge                 standardised linear model on the audited features
  hgb                   gradient-boosted trees on the same features

The mean baseline shows what "the distribution moved" costs. Persistence
is the baseline that actually matters: ridge's features are dominated by
lagged demand, so if it cannot beat "yesterday again" it has learned
nothing worth reporting. The booster is there because it fails, and the
reason it fails is the headline result.

Run: python -m src.train
"""
import argparse
import json

import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin, clone
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from src.config import EXPERIMENT_FEATURE, METRICS, PROCESSED, TARGET, TRAIN_END, VALID_END
from src.features import feature_columns


class PersistenceBaseline(BaseEstimator, RegressorMixin):
    """Predict a single lagged column unchanged. Nothing is fit."""

    def __init__(self, column: str = "cnt_lag_1"):
        self.column = column

    def fit(self, X, y=None):
        if self.column not in X.columns:
            raise ValueError(f"persistence baseline needs column {self.column!r}")
        return self

    def predict(self, X):
        return X[self.column].to_numpy(dtype=float)


MODELS = {
    "baseline_mean": DummyRegressor(strategy="mean"),
    "baseline_persistence": PersistenceBaseline("cnt_lag_1"),
    "ridge": make_pipeline(StandardScaler(), Ridge(alpha=1.0)),
    "hgb": HistGradientBoostingRegressor(random_state=0, max_iter=300),
}


def temporal_split(df: pd.DataFrame):
    """Split by date, never at random. A random split on a time series
    puts tomorrow in train and today in test."""
    train = df[df.dteday <= TRAIN_END]
    valid = df[(df.dteday > TRAIN_END) & (df.dteday <= VALID_END)]
    test = df[df.dteday > VALID_END]
    return train, valid, test


def scores(actual, predicted):
    return {
        "r2": round(float(r2_score(actual, predicted)), 4),
        "mae": round(float(mean_absolute_error(actual, predicted)), 1),
    }


def score_models(columns, train, evaluation, models=MODELS):
    results = {}
    for name, estimator in models.items():
        model = clone(estimator).fit(train[columns], train[TARGET])
        results[name] = {
            split: scores(part[TARGET], model.predict(part[columns]))
            for split, part in evaluation.items()
        }
    return results


def change_from_yesterday(columns, train, evaluation):
    """Fit a tree to daily changes and return forecasts to the rides scale."""
    change = train[TARGET] - train["cnt_lag_1"]
    booster = clone(MODELS["hgb"]).fit(train[columns], change)
    return {
        split: scores(part[TARGET], part["cnt_lag_1"] + booster.predict(part[columns]))
        for split, part in evaluation.items()
    }


def fit_and_score(validation_only=False, predict_change=False, df=None):
    df = pd.read_parquet(PROCESSED) if df is None else df
    columns = feature_columns(df)
    train, valid, test = temporal_split(df)
    evaluation = {"valid": valid} if validation_only else {"valid": valid, "test": test}
    if predict_change:
        baselines = {n: m for n, m in MODELS.items() if n.startswith("baseline_")}
        return {
            **score_models(columns, train, evaluation, baselines),
            "hgb_change": change_from_yesterday(columns, train, evaluation),
        }

    before = [c for c in columns if c != EXPERIMENT_FEATURE]
    if len(before) == len(columns):
        raise ValueError("experimental feature missing; run make features")
    return {
        "n_features": len(columns), "features": columns, "n_train": len(train),
        "n_valid": len(valid), "n_test": len(test),
        **score_models(columns, train, evaluation),
        "before_feature": score_models(before, train, evaluation),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--validation-only", action="store_true")
    parser.add_argument("--predict-change", action="store_true")
    args = parser.parse_args()
    result = fit_and_score(args.validation_only, args.predict_change)
    if not args.validation_only and not args.predict_change:
        METRICS.parent.mkdir(parents=True, exist_ok=True)
        METRICS.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
