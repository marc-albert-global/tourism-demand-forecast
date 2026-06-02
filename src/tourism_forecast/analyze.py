"""Exploratory analysis: seasonality, trend, and the COVID structural break."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from statsmodels.tsa.seasonal import STL


@dataclass
class SeasonalProfile:
    peak_month: int
    trough_month: int
    peak_to_trough_ratio: float
    monthly_index: pd.Series  # mean seasonal factor by calendar month (1=Jan)


def seasonal_profile(series: pd.Series) -> SeasonalProfile:
    """Average within-year seasonal shape, computed on a stable recent window.

    We use a post-recovery window so the COVID collapse doesn't distort the
    seasonal factors. Each month is expressed relative to the annual mean.
    """
    recent = series[series.index >= "2022-01-01"]
    by_month = recent.groupby(recent.index.month).mean()
    index = by_month / by_month.mean()
    return SeasonalProfile(
        peak_month=int(index.idxmax()),
        trough_month=int(index.idxmin()),
        peak_to_trough_ratio=float(index.max() / index.min()),
        monthly_index=index,
    )


def decompose(series: pd.Series, period: int = 12) -> "pd.DataFrame":
    """STL decomposition into trend / seasonal / residual components."""
    result = STL(series, period=period, robust=True).fit()
    return pd.DataFrame(
        {
            "observed": series,
            "trend": result.trend,
            "seasonal": result.seasonal,
            "resid": result.resid,
        }
    )


def covid_impact(series: pd.Series) -> dict:
    """Quantify the pandemic shock and the recovery point.

    Returns the trough month, the drop vs. the prior year, and the first month
    that recovered to its 2019 level.
    """
    trough_date = series["2020-01-01":"2021-12-31"].idxmin()
    trough_value = series.loc[trough_date]
    prior_year = series.loc[trough_date - pd.DateOffset(years=1)]
    drop_pct = (trough_value / prior_year - 1) * 100

    baseline_2019 = series["2019-01-01":"2019-12-31"].mean()
    post = series[series.index >= "2021-01-01"]
    recovered = post[post >= baseline_2019]
    recovery_date = recovered.index[0] if len(recovered) else None

    return {
        "trough_date": trough_date,
        "trough_drop_pct_yoy": drop_pct,
        "baseline_2019_mean": baseline_2019,
        "recovery_date": recovery_date,
    }
