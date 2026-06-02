"""Tests run on the committed data snapshot — no network required."""

import pandas as pd

from tourism_forecast import analyze, clean, forecast, ingest


def _series():
    return clean.to_series(ingest.load_raw())


def test_clean_produces_monthly_series():
    s = _series()
    assert isinstance(s, pd.Series)
    assert s.index.freqstr == "MS"
    assert not s.isna().any()
    assert s.shape[0] > 250  # ~2000 onward


def test_covid_break_detected():
    impact = analyze.covid_impact(_series())
    # The 2020 collapse was a ~90% YoY drop at the trough.
    assert impact["trough_drop_pct_yoy"] < -70
    assert impact["trough_date"].year in (2020, 2021)


def test_seasonality_summer_peak():
    profile = analyze.seasonal_profile(_series())
    # Air travel peaks in summer; trough in winter.
    assert profile.peak_month in (6, 7, 8)
    assert profile.peak_to_trough_ratio > 1.0


def test_backtest_is_reasonable():
    bt = forecast.backtest(_series())
    assert bt.test.shape[0] == 12
    # A seasonal model on the recovered regime should beat ~15% MAPE.
    assert bt.mape < 15.0


def test_forecast_horizon_and_intervals():
    fcst = forecast.forecast(_series(), horizon=12)
    assert len(fcst.mean) == 12
    assert (fcst.upper >= fcst.mean).all()
    assert (fcst.lower <= fcst.mean).all()
