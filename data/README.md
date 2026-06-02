# Data provenance

| | |
|---|---|
| **Series** | U.S. Air Revenue Passenger-Miles |
| **Source** | FRED, Federal Reserve Bank of St. Louis — series [`AIRRPMTSI`](https://fred.stlouisfed.org/series/AIRRPMTSI) |
| **Underlying source** | U.S. Bureau of Transportation Statistics |
| **Frequency** | Monthly, not seasonally adjusted |
| **Units** | Thousands of revenue passenger-miles |
| **Coverage** | January 2000 – present |
| **License** | Public domain (U.S. federal government data) |

`raw/air_rpm.csv` is a committed snapshot so the pipeline reproduces exactly
offline. To refresh from FRED:

```python
from tourism_forecast import ingest
ingest.download()
```

or run the pipeline with `run(refresh=True)`.
