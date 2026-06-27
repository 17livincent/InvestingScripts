# AGENTS.md

`InvestingScripts`.

## Project Shape

Python stock-analysis scripts that rank `watchlists.json` companies by quality, growth, valuation, and risk. AlphaVantage payloads are cached in `data/AlphaVantage/`; calculated tables go to Supabase; comparison JSON/PNG outputs go under `data/`.

Key files:

- `RequestAndSave.py`: AlphaVantage request/cache helpers.
- `DBConnection.py`: Supabase SQLAlchemy engine.
- `InitDB.py`: table definitions, inserts, initialization.
- `TickerData.py`: per-ticker update orchestration.
- `OperationalMetrics.py`: fundamentals and operational metrics.
- `ValuationMetrics.py`: valuation metrics from fundamentals, prices, and shares.
- `TimeSeriesDaily.py`: cached `TIME_SERIES_DAILY_ADJUSTED` stock data for graphing.
- `IndexData.py`: cached index catalog plus uncached daily `INDEX_DATA`.
- `Comparisons.py`: watchlist updates, stock/index daily charts, scored comparison outputs.

## Runtime And Side Effects

- Use `uv run python ...`; common commands are `InitDB.py`, `TickerData.py`, and `Comparisons.py`.
- Note `Comparisons.py` without `--skip_update` may take a long time.
- Treat AlphaVantage calls and Supabase writes as real side effects.
- Force a table refresh with `uv run python TickerData.py -t <TICKER> -u <TABLE_NAME>`; valid names come from `InitDB.TABLE_NAMES`.

## Data

- `data/AlphaVantage/<TICKER>/*.json`: cached company, fundamentals, shares, weekly prices, daily adjusted prices.
- `data/AlphaVantage/<TICKER>/TIME_SERIES_DAILY_ADJUSTED.json`: stock daily cache.
- `data/AlphaVantage/INDEX_CATALOG.json`: index-symbol catalog.
- `data/*_Comparison.json`: scored watchlist rows.
- `data/* Operational Comparisons.png`, `data/* Valuation Comparisons.png`, `data/* Time Series Daily Comparisons.png`: charts.
- `data/daily_snapshots/YYYY-MM-DD/`: daily-update snapshots dated by local US Pacific time.

`watchlists.json` entries may be stocks or AlphaVantage index symbols such as `SPX`; indexes are only used in daily performance charts and are not scored.

## Caveats

- Date handling mixes quarter statement dates, weekly prices, daily stock prices, daily index dates, and timezone-aware update timestamps.
- Some SQL strings interpolate ticker values; parameterize new user-input paths.
- `RequestAndSave.get_api_key()` strips the AlphaVantage key from `pass` output.
- AlphaVantage errors/rate limits fall back to saved files when possible; missing caches can raise `FileNotFoundError`.
- Generated `data/` artifacts and local JSON files are ignored; do not commit them unless explicitly requested.
