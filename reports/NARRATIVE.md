# Forecasting U.S. air-travel demand through a structural break

## The question

Can we produce a reliable 12-month forecast of U.S. air-travel demand from a
single public monthly series, when that series contains one of the largest
demand shocks in the history of commercial aviation?

The data is U.S. Air Revenue Passenger-Miles, monthly from January 2000 to
February 2026 (FRED series `AIRRPMTSI`, 314 observations). It is a good proxy
for travel demand: it moves with the economy, has a strong and stable seasonal
shape, and it captured the pandemic in full.

## What the data shows

Three things stand out before any modeling.

**A persistent summer-peaked seasonality.** Demand peaks in July and troughs in
February, and the peak month runs about 1.4x the trough month. That ratio has
been stable across two decades, which is what makes the series forecastable at
all.

**A long-run upward trend** interrupted by every major demand event of the
period: a visible dip after 2001, a softer one through the 2008 recession, and
then the pandemic.

**A structural break in 2020 that no ordinary model should be asked to learn
through.** Demand fell 96% year-over-year at the April 2020 trough. It did not
return to its 2019 average until July 2022. A model fit across that window
would try to reconcile near-zero demand with full demand inside one set of
seasonal and trend parameters, and it would do both badly.

## The modeling decision

The central judgment call here is not which algorithm to use. It is *what data
to fit it on*. I treat the pandemic as a regime change rather than noise and
fit the forecast on the post-recovery regime (July 2021 onward), where the
current relationship between trend, season, and level holds. The full history
is still used for context and for the seasonal-shape analysis, but not for the
forward model.

The model itself is Holt-Winters exponential smoothing with an additive trend
and a multiplicative seasonal term. Multiplicative seasonality is the right
shape because the size of the summer peak scales with the overall level of
demand, not by a fixed number of miles.

## Does it work

I held out the most recent 12 months, fit on everything before, and forecast
the holdout. The forecast tracked actual demand to a **1.15% mean absolute
percentage error**. On a series this seasonal and this far from its shock, that
is a strong result, and it is honest: the test months were never seen by the
model.

Prediction intervals on the forward forecast are built from the spread of the
backtest errors rather than the model's nominal confidence bands, so the
uncertainty shown is the uncertainty the model actually demonstrated out of
sample.

## What I would not claim

This is a univariate forecast. It assumes the near future looks like the
recovered regime and carries no information about a new shock: a recession, a
fuel-price spike, or another disruption would break it, exactly as 2020 broke
any model trained before it. The right way to read the forward forecast is "the
seasonal demand path if current conditions hold," not "what will happen."

That caveat is the point of the project as much as the forecast is. Knowing
when a model's assumptions stop holding, and saying so, is the difference
between a number and an answer.
