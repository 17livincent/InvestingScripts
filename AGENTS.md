# AGENTS.md

Guidance for coding agents working in this repository.

## Project Overview

This repository is a small Python project for stock analysis. It pulls company, financial statement, share count, and weekly price data from the AlphaVantage API, stores raw payloads under `data/`, calculates operational and valuation metrics with pandas, writes tables to a Supabase Postgres database, and generates comparison graphs for tickers in `watchlists.json`.

Core modules:

- `RequestAndSave.py`: AlphaVantage request helpers and local JSON saving.
- `DBConnection.py`: Supabase SQLAlchemy engine creation.
- `InitDB.py`: database table definitions, insert statements, and initialization.
- `TickerData.py`: main update orchestration for companies, fundamentals, prices, shares, operational metrics, and valuation metrics.
- `OperationalMetrics.py`: transforms saved statements into fundamentals and operational metrics.
- `ValuationMetrics.py`: combines fundamentals, weekly prices, and shares to calculate valuation metrics.
- `Comparisons.py`: updates all tickers in `watchlists.json`, prints ranked comparisons, and writes comparison PNGs under `data/`.

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

- AlphaVantage API key: `pass show Keys/AlphaVantage`
- Supabase password: `pass show Password/Supabase`

`DBConnection.py` contains the Supabase host/user connection string template. Treat database writes as real production-like side effects unless the user says otherwise.

Networked scripts can call AlphaVantage and Supabase. Be mindful of API rate limits; existing update code sleeps briefly between some AlphaVantage calls and uses the `data_updates` table to avoid unnecessary refreshes.

## Data And Generated Artifacts

Generated/local data lives under `data/`:

- `data/<TICKER>/*.json`: raw AlphaVantage payloads.
- `data/<TICKER>/calculated_fundamentals.csv`: local calculated output if generated.
- `data/* Comparisons.png`: matplotlib comparison charts.

`watchlists.json` defines the named watchlists used by `Comparisons.py`.

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
5. `Comparisons.py` runs this for every unique ticker in `watchlists.json`, then generates watchlist charts.

Use `TickerData.py -t <TICKER> -u <TABLE_NAME>` to force a table refresh by removing that ticker/table entry from `data_updates` before updating. Valid table names are based on `InitDB.TABLE_NAMES`.

## Development Practices

- Keep changes small and aligned with the current flat-script style unless a larger refactor is explicitly requested.
- Prefer pandas/SQLAlchemy APIs already used in the project over ad hoc parsing or direct database drivers.
- Preserve the existing table names and column names unless intentionally migrating schema and all dependent insert/query code.
- Be careful with date handling. The code mixes quarter-based financial statement dates, weekly price dates, and timezone-aware update timestamps.
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
- For graph changes, run `uv run python Comparisons.py` only when AlphaVantage/Supabase access is intended, then inspect the generated PNG files under `data/`.

## Known Caveats

- Some SQL query strings are built with formatted ticker values. If accepting new user input paths, prefer parameterized queries.
- `Comparisons.py` currently performs database/API work at import time. Avoid importing it from other modules unless that behavior is intended.
- `RequestAndSave.request_json()` strips the AlphaVantage key from `pass` output before building the URL; preserve that normalization when touching request code.
- AlphaVantage error/rate-limit responses are handled by falling back to saved files when possible, so missing local JSON can surface as `FileNotFoundError`.
