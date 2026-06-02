"""End-to-end pipeline: ingest -> clean -> analyze -> forecast -> figures.

Running this regenerates every figure in ``reports/figures/`` and writes a
``reports/metrics.json`` with the headline numbers used in the narrative.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless rendering
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

from . import analyze, clean, ingest, forecast as fc

REPO_ROOT = Path(__file__).resolve().parents[2]
FIG_DIR = REPO_ROOT / "reports" / "figures"
METRICS_PATH = REPO_ROOT / "reports" / "metrics.json"

_MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _billions(ax) -> None:
    # FRED reports AIRRPMTSI in thousands of passenger-miles, so the raw values
    # (~5e7-1e8) are billions of actual miles: value(thousands) / 1e6 = billions.
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v/1e6:.0f}B"))


@dataclass
class Results:
    covid: dict
    seasonal: analyze.SeasonalProfile
    forecast: fc.Forecast


def run(*, refresh: bool = False) -> Results:
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    if refresh:
        ingest.download()
    raw = ingest.load_raw()
    series = clean.to_series(raw)

    covid = analyze.covid_impact(series)
    seasonal = analyze.seasonal_profile(series)
    decomp = analyze.decompose(series)
    forecast = fc.forecast(series)

    _plot_history(series, covid)
    _plot_decomposition(decomp)
    _plot_seasonality(seasonal)
    _plot_backtest(forecast.backtest)
    _plot_forecast(forecast)

    metrics = {
        "series": "U.S. Air Revenue Passenger-Miles (FRED AIRRPMTSI)",
        "observations": int(series.shape[0]),
        "range": [str(series.index.min().date()), str(series.index.max().date())],
        "covid": {
            "trough_date": str(covid["trough_date"].date()),
            "trough_drop_pct_yoy": round(covid["trough_drop_pct_yoy"], 1),
            "recovery_date": str(covid["recovery_date"].date()) if covid["recovery_date"] is not None else None,
        },
        "seasonality": {
            "peak_month": _MONTHS[seasonal.peak_month - 1],
            "trough_month": _MONTHS[seasonal.trough_month - 1],
            "peak_to_trough_ratio": round(seasonal.peak_to_trough_ratio, 3),
        },
        "backtest": {
            "horizon_months": int(forecast.backtest.test.shape[0]),
            "mape_pct": round(forecast.backtest.mape, 2),
            "rmse": round(forecast.backtest.rmse, 1),
            "mae": round(forecast.backtest.mae, 1),
        },
        "forecast_next_12m_mean": round(float(forecast.mean.mean()), 1),
    }
    METRICS_PATH.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return Results(covid=covid, seasonal=seasonal, forecast=forecast)


# --- figures ---------------------------------------------------------------

def _plot_history(series, covid) -> None:
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.plot(series.index, series.values, color="#2563eb", lw=1.4)
    ax.axvline(covid["trough_date"], color="#dc2626", ls="--", lw=1, alpha=0.8)
    ax.annotate(
        f"COVID trough\n{covid['trough_drop_pct_yoy']:.0f}% YoY",
        xy=(covid["trough_date"], series.loc[covid["trough_date"]]),
        xytext=(10, 60), textcoords="offset points", color="#dc2626", fontsize=9,
        arrowprops=dict(arrowstyle="->", color="#dc2626"),
    )
    ax.set_title("U.S. Air Revenue Passenger-Miles, monthly (FRED AIRRPMTSI)")
    ax.set_ylabel("Passenger-miles"); _billions(ax)
    ax.grid(alpha=0.25)
    fig.tight_layout(); fig.savefig(FIG_DIR / "01_history.png", dpi=130); plt.close(fig)


def _plot_decomposition(decomp) -> None:
    fig, axes = plt.subplots(4, 1, figsize=(11, 8), sharex=True)
    for ax, col, color in zip(
        axes, ["observed", "trend", "seasonal", "resid"],
        ["#111827", "#2563eb", "#059669", "#9ca3af"],
    ):
        ax.plot(decomp.index, decomp[col], color=color, lw=1.1)
        ax.set_ylabel(col); ax.grid(alpha=0.2)
    axes[0].set_title("STL decomposition (trend / seasonal / residual)")
    fig.tight_layout(); fig.savefig(FIG_DIR / "02_decomposition.png", dpi=130); plt.close(fig)


def _plot_seasonality(seasonal) -> None:
    fig, ax = plt.subplots(figsize=(9, 4.5))
    idx = seasonal.monthly_index
    ax.bar([_MONTHS[m - 1] for m in idx.index], (idx.values - 1) * 100,
           color=["#2563eb" if v >= 1 else "#93c5fd" for v in idx.values])
    ax.axhline(0, color="#374151", lw=0.8)
    ax.set_title("Seasonal index by month (deviation from annual mean, 2022+)")
    ax.set_ylabel("% vs. annual mean"); ax.grid(alpha=0.25, axis="y")
    fig.tight_layout(); fig.savefig(FIG_DIR / "03_seasonality.png", dpi=130); plt.close(fig)


def _plot_backtest(bt) -> None:
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(bt.train.index[-18:], bt.train.values[-18:], color="#9ca3af", lw=1.2, label="train")
    ax.plot(bt.test.index, bt.test.values, color="#111827", lw=2, label="actual (held out)")
    ax.plot(bt.predicted.index, bt.predicted.values, color="#dc2626", lw=2, ls="--", label="forecast")
    ax.set_title(f"Backtest on held-out 12 months, MAPE {bt.mape:.1f}%")
    ax.set_ylabel("Passenger-miles"); _billions(ax); ax.grid(alpha=0.25); ax.legend()
    fig.tight_layout(); fig.savefig(FIG_DIR / "04_backtest.png", dpi=130); plt.close(fig)


def _plot_forecast(forecast) -> None:
    fig, ax = plt.subplots(figsize=(11, 5))
    h = forecast.history
    ax.plot(h.index, h.values, color="#2563eb", lw=1.4, label="history (current regime)")
    ax.plot(forecast.mean.index, forecast.mean.values, color="#dc2626", lw=2, label="forecast")
    ax.fill_between(forecast.mean.index, forecast.lower.values, forecast.upper.values,
                    color="#dc2626", alpha=0.15, label="95% interval")
    ax.set_title("12-month demand forecast (Holt-Winters, post-recovery regime)")
    ax.set_ylabel("Passenger-miles"); _billions(ax); ax.grid(alpha=0.25); ax.legend()
    fig.tight_layout(); fig.savefig(FIG_DIR / "05_forecast.png", dpi=130); plt.close(fig)


if __name__ == "__main__":
    res = run()
    print("Pipeline complete. Figures in reports/figures/, metrics in reports/metrics.json")
    print(f"Backtest MAPE: {res.forecast.backtest.mape:.1f}%")
