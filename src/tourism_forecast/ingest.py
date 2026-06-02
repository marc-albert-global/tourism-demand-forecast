"""Data ingestion.

Source: U.S. Air Revenue Passenger-Miles (series ``AIRRPMTSI``) from FRED,
Federal Reserve Bank of St. Louis. Monthly, not seasonally adjusted — we want
the seasonality intact for forecasting. A snapshot lives in ``data/raw/`` so
the pipeline is fully reproducible offline; ``download()`` re-fetches the
latest from FRED on demand.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

FRED_SERIES = "AIRRPMTSI"
FRED_CSV_URL = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={FRED_SERIES}"

REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_PATH = REPO_ROOT / "data" / "raw" / "air_rpm.csv"


def download(dest: Path = RAW_PATH) -> Path:
    """Fetch the latest series from FRED and write it to ``dest``."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    frame = pd.read_csv(FRED_CSV_URL)
    frame.to_csv(dest, index=False)
    return dest


def load_raw(path: Path = RAW_PATH) -> pd.DataFrame:
    """Load the committed raw snapshot (no network)."""
    return pd.read_csv(path)
