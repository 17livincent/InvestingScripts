# AGENTS.md

Guidance for coding agents working in this repository.

## Project Overview

This repository is a small Python project for stock analysis. Its overall goal is to rank and screen stocks for medium- to long-term investing, with an emphasis on business quality, durable growth, valuation discipline, and balance-sheet risk. It pulls company, financial statement, share count, weekly price, daily adjusted price, and daily index data from the AlphaVantage API, stores raw payloads under `data/`, calculates operational and valuation metrics with pandas, writes tables to a Supabase Postgres database, and generates comparison graphs for symbols in `watchlists.json`.

Core modules:

- `RequestAndSave.py`: AlphaVantage request helpers and local JSON saving.
- `DBConnection.py`: Supabase SQLAlchemy engine creation.
- `InitDB.py`: database table definitions, insert statements, and initialization.
- `TickerData.py`: main update orchestration for companies, fundamentals, prices, shares, operational metrics, and valuation metrics.
- `OperationalMetrics.py`: transforms saved statements into fundamentals and operational metrics.
- `ValuationMetrics.py`: combines fundamentals, weekly prices, and shares to calculate valuation metrics.
- `TimeSeriesDaily.py`: fetches AlphaVantage `TIME_SERIES_DAILY_ADJUSTED` data for a ticker, persists successful responses under `data/<TICKER>/`, and returns filtered daily OHLC data as a dataframe.
- `IndexData.py`: fetches and caches the AlphaVantage index catalog, requests daily `INDEX_DATA` for index symbols, and returns filtered daily OHLC data as a dataframe.
- `Comparisons.py`: updates stock tickers in `watchlists.json`, includes index symbols in daily price-change charts, prints ranked stock comparisons, writes operational, valuation, and daily price-change comparison PNGs under `data/`, and writes scored watchlist comparison JSON files for stocks.

## Environment

- Python version: `>=3.12`.
- Dependencies are declared in `pyproject.toml`.
- The repo appears to be managed with `uv`; use `uv sync` if dependencies need to be installed.
- Prefer running scripts through the project environment:

```bash
uv run python InitDB.py
uv run python TickerData.py -t MA
uv run python Comparisons.py
```

If `uv` is unavailable, use the local `.venv` or another Python 3.12+ environment with the dependencies from `pyproject.toml`.

## Secrets And External Services

Do not hard-code, print, commit, or replace secrets.

The scripts read credentials from GNU `pass`:

- AlphaVantage API key: `pass show Keys/AlphaVantagePremium`
- Supabase password: `pass show Password/Supabase`

`DBConnection.py` contains the Supabase host/user connection string template. Treat database writes as real production-like side effects unless the user says otherwise.

Networked scripts can call AlphaVantage and Supabase. Be mindful of API rate limits; existing update code sleeps briefly between some AlphaVantage calls and uses the `data_updates` table to avoid unnecessary refreshes.

## Data And Generated Artifacts

Generated/local data lives under `data/`:

- `data/<TICKER>/*.json`: raw AlphaVantage payloads.
- `data/<TICKER>/TIME_SERIES_DAILY_ADJUSTED.json`: raw persisted daily adjusted time series payload from `TimeSeriesDaily.py`.
- `data/<TICKER>/calculated_fundamentals.csv`: local calculated output if generated.
- `data/INDEX_CATALOG.json`: cached AlphaVantage index catalog used to distinguish stock tickers from index symbols in watchlists.
- `data/* Operational Comparisons.png`: matplotlib operational comparison charts.
- `data/* Valuation Comparisons.png`: matplotlib valuation comparison charts.
- `data/* Time Series Daily Comparisons.png`: matplotlib daily close percent-change comparison charts, which may include stock tickers and index symbols.
- `data/*_Comparison.json`: scored watchlist comparison output from `Comparisons.py`.

`watchlists.json` defines the named watchlists used by `Comparisons.py`. Entries may be stock tickers or AlphaVantage index symbols such as `SPX`; index symbols are used for daily performance charts only.

The `.gitignore` currently ignores `*.json`, `data/`, `.venv`, `uv.lock`, `.python-version`, and `__pycache__`. Even if ignored files are present locally, avoid deleting or regenerating them unless the task requires it.

## Database Schema And Update Flow

`InitDB.py` defines these database tables:

- `companies`
- `fundamentals`
- `operational_metrics`
- `prices_weekly`
- `shares_outstanding`
- `valuation_metrics`
- `data_updates`
- `report_dates`

Normal update flow:

1. `TickerData.add_update_ticker()` checks the last update in `data_updates` or latest table dates.
2. Company overview, fundamentals, shares outstanding, and weekly prices are refreshed only when stale.
3. Operational metrics are recalculated from `fundamentals`.
4. Valuation metrics are recalculated from fundamentals, operational metrics, prices, and shares.
5. `Comparisons.py` separates stock tickers from index symbols using `IndexData.get_index_list()`, runs the stock update flow for every unique stock ticker in `watchlists.json`, fetches recent daily stock and index series for comparison charts, then generates watchlist charts and scored comparison JSON.

Daily adjusted stock time series data is currently used for graphing only. It is requested directly through `TimeSeriesDaily.get_time_series_daily_adjusted()`, persisted as local JSON when AlphaVantage returns `Time Series (Daily)`, and loaded from `data/<TICKER>/TIME_SERIES_DAILY_ADJUSTED.json` when the request does not return daily time series data. It is not written to a database table by the normal update flow.

Daily index time series data is requested through `IndexData.get_index_time_series_daily()` for AlphaVantage index symbols in watchlists. Index daily data is used for the `Time Series Daily Comparisons` chart only, is not scored, and is not written to a database table.

Use `TickerData.py -t <TICKER> -u <TABLE_NAME>` to force a table refresh by removing that ticker/table entry from `data_updates` before updating. Valid table names are based on `InitDB.TABLE_NAMES`.

## Comparison Scoring

`Comparisons.py` builds comparison rows from the latest operational and valuation metrics, then adds trailing history summaries before scoring each watchlist. Operational history is loaded over six years, valuation history over two years, but the trailing summary fields are:

- Three-year operational averages: `ttm_roic_3yr_avg`, `revenue_growth_yoy_3yr_avg`, `ttm_operating_margin_3yr_avg`, and `ttm_fcf_margin_3yr_avg`.
- Three-year operational volatility: `ttm_roic_3yr_std`, used with `ttm_roic_3yr_avg` to rank quality consistency.
- Two-year valuation medians: `pe_ttm_2yr_median`, `ev_ebit_2yr_median`, and `ev_fcf_2yr_median`.

Trailing summaries are calculated from rows whose `date` is within the requested year window relative to the latest available date in that dataframe. A summary returns missing data unless at least `MIN_HISTORY_OBSERVATIONS` valid numeric observations are available.

Scores are percentile ranks within the current watchlist, not absolute market scores. Higher ranks are better. For valuation multiples and debt-to-equity, lower raw values rank higher. Current valuation-to-median discounts are computed as current multiple divided by the matching two-year median, and lower discount ratios rank higher.

Score components and weights:

- `quality_score` uses `ttm_roic_perc_rank` 45%, `ttm_operating_margin_perc_rank` 20%, `ttm_fcf_margin_perc_rank` 15%, and `quality_consistency_perc_rank` 20%. Quality consistency ranks `ttm_roic_3yr_avg - ttm_roic_3yr_std`.
- `growth_score` uses current `revenue_growth_yoy_perc_rank` 60% and `revenue_growth_yoy_3yr_avg_perc_rank` 40%.
- `valuation_score` uses current `pe_ttm_perc_rank`, `ev_ebit_perc_rank`, and `ev_fcf_perc_rank` at 23.33% each, plus `pe_ttm_discount_perc_rank`, `ev_ebit_discount_perc_rank`, and `ev_fcf_discount_perc_rank` at 10% each.
- `risk_score` uses `debt_to_equity_perc_rank` 50%, `ttm_fcf_margin_perc_rank` 30%, and `ttm_operating_margin_perc_rank` 20%. Negative debt-to-equity values are treated as 5 and clipped at 5 before ranking.

`get_weighted_score()` normalizes by the weights of non-missing components, so missing component data does not automatically count as zero inside a component score. After component scores are calculated, missing `quality_score`, `growth_score`, `valuation_score`, or `risk_score` values are filled with zero for `total_score`.

`total_score` is a weighted blend of `quality_score` 40%, `growth_score` 20%, `valuation_score` 20%, and `risk_score` 20%. `get_scores()` sorts by `total_score` descending, prints score columns with `quality_coverage`, `valuation_coverage`, `history_coverage`, and `classification`, and writes each watchlist to `data/<WATCHLIST>_Comparison.json`.

Classifications are based on coverage and total score: any row with minimum `quality_coverage`, `valuation_coverage`, or `history_coverage` below 0.6 is `Incomplete data`; otherwise `total_score >= 80` is `High quality candidate`, `>= 65` is `Watchlist quality`, `>= 50` is `Mixed`, and lower scores are `Low rank`.

`Comparisons.py` also fetches daily stock and index time series over the valuation time frame and post-processes the returned close values into `close_change_perc` for the `Time Series Daily Comparisons` chart. This graph shows each symbol's close percent change over the selected date range and is separate from the scoring model.

## Development Practices

- Keep changes small and aligned with the current flat-script style unless a larger refactor is explicitly requested.
- Prefer pandas/SQLAlchemy APIs already used in the project over ad hoc parsing or direct database drivers.
- Preserve the existing table names and column names unless intentionally migrating schema and all dependent insert/query code.
- Be careful with date handling. The code mixes quarter-based financial statement dates, weekly price dates, daily adjusted stock price dates, daily index dates, and timezone-aware update timestamps.
- Avoid adding broad side effects at import time. Several current files already execute work as scripts; when adding new behavior, prefer functions plus `if __name__ == "__main__":`.
- Do not commit generated `data/` artifacts or local JSON files unless the user explicitly asks.
- Do not replace the `pass`-based secret flow with checked-in `.env` values.

## Validation

There is no test suite in the current repository. For code changes, use the narrowest practical validation:

- Syntax check changed Python files:

```bash
uv run python -m py_compile <file>.py
```

- For pure calculation changes, prefer a small local pandas check using existing saved files under `data/<TICKER>/` when available.
- For database-writing changes, explain the expected side effects before running scripts that update Supabase.
- For graph changes, run `uv run python Comparisons.py` only when AlphaVantage/Supabase access is intended, then inspect the generated PNG files under `data/`, including the daily price-change comparison chart when relevant.

## Known Caveats

- Some SQL query strings are built with formatted ticker values. If accepting new user input paths, prefer parameterized queries.
- `RequestAndSave.request_data()` strips the AlphaVantage key from `pass` output before building the URL; preserve that normalization when touching request code.
- AlphaVantage error/rate-limit responses are handled by falling back to saved files when possible for saved fundamentals and weekly data, so missing local JSON can surface as `FileNotFoundError`.
- `TimeSeriesDaily.py` calls `request_data()` directly with AlphaVantage query params such as `outputsize`, `datatype`, and `entitlement`; it persists successful responses locally and falls back to the saved `TIME_SERIES_DAILY_ADJUSTED.json` file if the response lacks `Time Series (Daily)`.
- `IndexData.py` uses `request_data()` for AlphaVantage `INDEX_DATA` with a daily interval. Index rows are parsed into a dataframe for graphing, but the daily index response is not currently persisted.
