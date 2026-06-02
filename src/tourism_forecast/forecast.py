"""Forecasting: backtest a seasonal model and project demand forward.

Modeling choice, the series has a severe COVID structural break (2020-2021)
that does not represent normal demand dynamics. Training a single model across
it would let the collapse and snap-back contaminate the seasonal and trend
estimates. So we fit on the **post-recovery regime** (configurable start),
backtest on a held-out tail, and project forward from the current regime. This
is a judgment call stated explicitly rather than a silent default.

Model: Holt-Winters exponential smoothing with additive trend and
multiplicative seasonality (seasonal amplitude scales with the level, which is
the right shape for passenger volume).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing

REGIME_START = "2021-07-01"  # post-collapse recovery onward


@dataclass
class Backtest:
    train: pd.Series
    test: pd.Series
    predicted: pd.Series
    mape: float
    rmse: float
    mae: float


@dataclass
class Forecast:
    history: pd.Series
    mean: pd.Series
    lower: pd.Series
    upper: pd.Series
    backtest: Backtest


def _fit(series: pd.Series) -> ExponentialSmoothing:
    return ExponentialSmoothing(
        series,
        trend="add",
        seasonal="mul",
        seasonal_periods=12,
        initialization_method="estimated",
    ).fit()


def _metrics(actual: pd.Series, predicted: pd.Series) -> tuple[float, float, float]:
    err = actual - predicted
    mape = float((np.abs(err / actual)).mean() * 100)
    rmse = float(np.sqrt((err**2).mean()))
    mae = float(np.abs(err).mean())
    return mape, rmse, mae


def backtest(series: pd.Series, *, regime_start: str = REGIME_START, horizon: int = 12) -> Backtest:
    """Hold out the last `horizon` months, fit on the rest, score the forecast."""
    regime = series[series.index >= regime_start]
    train, test = regime.iloc[:-horizon], regime.iloc[-horizon:]
    model = _fit(train)
    predicted = model.forecast(horizon)
    predicted.index = test.index
    mape, rmse, mae = _metrics(test, predicted)
    return Backtest(train=train, test=test, predicted=predicted, mape=mape, rmse=rmse, mae=mae)


def forecast(series: pd.Series, *, regime_start: str = REGIME_START, horizon: int = 12) -> Forecast:
    """Backtest, then refit on the full regime and project `horizon` months out.

    Prediction intervals are derived from the backtest residual spread
    (±1.96σ), an honest empirical band rather than the model's nominal CIs.
    """
    bt = backtest(series, regime_start=regime_start, horizon=horizon)

    regime = series[series.index >= regime_start]
    model = _fit(regime)
    mean = model.forecast(horizon)
    future_index = pd.date_range(regime.index[-1] + pd.offsets.MonthBegin(), periods=horizon, freq="MS")
    mean.index = future_index

    resid_std = float((bt.test - bt.predicted).std())
    lower = mean - 1.96 * resid_std
    upper = mean + 1.96 * resid_std

    return Forecast(history=regime, mean=mean, lower=lower, upper=upper, backtest=bt)
