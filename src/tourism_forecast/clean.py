"""Cleaning and shaping into a monthly time series."""

from __future__ import annotations

import pandas as pd

from .ingest import FRED_SERIES


def to_series(raw: pd.DataFrame) -> pd.Series:
    """Turn the raw FRED CSV into a clean monthly Series of passenger-miles.

    - Parse the observation date and set a month-start frequency index.
    - Coerce the value column to numeric (FRED uses '.' for missing).
    - Drop missing observations and assert the index is contiguous monthly.
    """
    frame = raw.rename(columns={"observation_date": "date", FRED_SERIES: "passenger_miles"})
    frame["date"] = pd.to_datetime(frame["date"])
    frame["passenger_miles"] = pd.to_numeric(frame["passenger_miles"], errors="coerce")
    frame = frame.dropna(subset=["passenger_miles"]).set_index("date").sort_index()

    series = frame["passenger_miles"].asfreq("MS")
    if series.isna().any():
        # Fill any internal gaps by time interpolation so the index stays regular.
        series = series.interpolate(method="time")
    series.name = "passenger_miles"
    return series
