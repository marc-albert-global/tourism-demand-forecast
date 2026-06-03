# tourism-demand-forecast

[![CI](https://github.com/marc-albert-global/tourism-demand-forecast/actions/workflows/ci.yml/badge.svg)](https://github.com/marc-albert-global/tourism-demand-forecast/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![lint: ruff](https://img.shields.io/badge/lint-ruff-261230)
![types: mypy](https://img.shields.io/badge/types-mypy-2a6db2)
![License: MIT](https://img.shields.io/badge/license-MIT-green)

**Forecast monthly travel demand from a single public series, and know whether
the model is actually worth its complexity.** End to end: ingest, clean,
profile seasonality, quantify the COVID shock, then backtest a forecast
*against a do-nothing-clever baseline* so the recommendation is grounded, not
assumed.

The honest result up front: on this recovered, highly seasonal series, a
seasonal-naive baseline (0.93% MAPE) slightly **beats** the Holt-Winters model
(1.15% MAPE). That is the point of the project. The disciplined comparison tells
you where a sophisticated model does not earn its keep, and the genuinely hard,
valuable work is detecting and handling the structural break, not squeezing the
last decimal of MAPE.

> Scope: a reproducible study on public FRED data, not a production system.

---

## Impact at a glance

| | |
|---|---|
| Forecast error (held-out 12 mo) | Holt-Winters **1.15% MAPE**, seasonal-naive **0.93% MAPE** |
| Headline judgment | the simple baseline wins here; complexity is not justified on this series |
| Structural break handled | COVID trough **-96.4% YoY** (Apr 2020), recovery Jul 2022, modeled explicitly |
| Seasonality | peaks **July**, troughs **February**, ~1.43x peak-to-trough |
| Reproducibility | committed data + figures; `pytest` enforces the model-vs-baseline check |

Every number is produced by committed code on committed data (`python -m tourism_forecast.pipeline`).

---

## Problem and context

A planning team needs a 12-month demand forecast and, more importantly, needs
to trust it. The baseline state is usually "someone extrapolates last year by
hand." The catch in this series is a once-in-a-generation shock: demand fell 96%
in 2020 and did not recover until mid-2022. Any forecast that learns *through*
that shock is wrong. So the real questions are: how do you handle the break, and
is a fitted model even better than the obvious baseline?

## Approach and the key judgment call

The central decision is not the algorithm, it is **what data to fit on.** I
treat the pandemic as a regime change and fit the forecast on the post-recovery
regime (2021-07 onward), keeping the full history only for context and the
seasonality profile. The model is Holt-Winters (additive trend, multiplicative
seasonality). Then, instead of reporting its MAPE in isolation, I score it
against a **seasonal-naive baseline** (each month predicted by the same month a
year earlier) on the identical held-out window.

## Results

![Backtest vs baseline](reports/figures/04_backtest.png)

Both methods track the recovered series tightly; the naive baseline is fractionally
better (0.93% vs 1.15% MAPE). On a smooth, strongly seasonal signal that is
expected, and saying so is more useful than a misleading "my model wins."

![History and the COVID shock](reports/figures/01_history.png)
![Seasonal decomposition](reports/figures/02_decomposition.png)

## From demo to deployment

How this maps to a real forecasting engagement:

- **Swap the data, keep the method.** The public FRED series stands in for a client's own monthly history; the pipeline is series-agnostic.
- **Recommend the baseline when it wins.** The disciplined output here would be: ship the seasonal-naive baseline, spend the saved complexity budget on monitoring. That is a cheaper, more dependable production choice, and being willing to say it is the senior move.
- **The real deliverable is break detection.** The 2020 lesson generalizes: production forecasting fails at regime changes. A deployment needs a monitor that flags when recent error jumps (a new structural break) and pauses automated forecasts, exactly the failure the COVID handling models.
- **Cost is negligible** (CPU-seconds per refit), so the operating cost is governance and monitoring, not compute.

## Methodology

- **Baseline is explicit and scored on the same window** (`seasonal_naive_mape`); the model only "counts" if it beats it, and here it does not.
- The pandemic is handled as a **regime split**, stated rather than hidden.
- Prediction intervals come from the **empirical backtest residual spread**, not the model's optimistic nominal bands.
- A test (`test_seasonal_naive_baseline_is_computed_and_competitive`) enforces that the comparison is always computed.

## Quickstart

```bash
git clone https://github.com/marc-albert-global/tourism-demand-forecast.git
cd tourism-demand-forecast
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

python -m tourism_forecast.pipeline   # regenerates figures + metrics.json
ruff check src tests && mypy && pytest -q  # lint + type-check + 6 tests, offline
```

## Limitations

- Univariate: no exogenous drivers (price, capacity, macro). A real shock breaks it, exactly as 2020 broke any pre-2020 model.
- The model does not beat the naive baseline on this series; on noisier or trend-shifting series the balance can flip, which is why the comparison is built in.
- Single series, monthly, US air travel; other domains will behave differently.

## Roadmap

- Add exogenous regressors (capacity, price indices) and re-run the baseline comparison.
- Calibrate prediction intervals against realized coverage.
- A drift/break monitor that pauses automated forecasts when recent error spikes.
- Multi-series support with per-series model-vs-baseline selection.

## Data

U.S. Air Revenue Passenger-Miles (FRED `AIRRPMTSI`), public domain. Provenance
in [`data/README.md`](data/README.md). Full analytical narrative in
[`reports/NARRATIVE.md`](reports/NARRATIVE.md).

## License

MIT © 2026 Marc Albert
