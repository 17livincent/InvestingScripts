# AGENTS.md

Repo-specific context for `InvestingScripts`.

## Repo Purpose

Python stock-analysis scripts rank `watchlists.json` companies using AlphaVantage input, local PostgreSQL calculated tables, and generated comparison outputs under `data/`.

## Files And Data Surfaces

- `RequestAndSave.py`: AlphaVantage requests; raw cache under `data/AlphaVantage/<TICKER>/`.
- `docker-compose.yml`: local PostgreSQL service definition.
- `DBConnection.py`: local PostgreSQL engine; reads `.env`, using `INVESTING_DATABASE_URL` first, then `INVESTING_DB_*` or `POSTGRES_*`.
- `InitDB.py`: local PostgreSQL schema.
- `TickerData.py`: updates database tables and `data_updates`.
- `OperationalMetrics.py` , `ValuationMetrics.py` , `ForwardMetrics.py`: calculated metrics stored in PostgreSQL.
- `TimeSeriesDaily.py`: stock daily adjusted cache for charts.
- `IndexData.py`: index catalog plus index daily data for benchmark charts.
- `Comparisons.py`: `data/*_Comparison.json`, chart PNGs, and daily snapshots.
- `watchlists.json`: stock tickers plus optional AlphaVantage index symbols that are chart-only.

## Local Runtime Facts

- Use `uv run ...`.
- `.env.example` is the commit-safe template for local database settings.
- AlphaVantage API key comes from `pass show Keys/AlphaVantagePremium`.

## Checks and Formatting

- `uvx ruff check ...`
- `uvx ruff format ...`

## Side Effects And Guardrails

- AlphaVantage calls can hit API/rate limits.
- Local PostgreSQL writes are real side effects.
- Generated `data/` artifacts and local JSON files are ignored.
- Saved JSON fallback behavior can mask AlphaVantage request failures.

## Sharp Edges

- Date handling mixes quarter statement dates, weekly prices, daily stock prices, daily index dates, and timezone-aware update timestamps.
- Some SQL strings interpolate ticker values; parameterize new user-input paths.
- Index daily data is parsed for charts but not persisted.
- Missing local caches can raise `FileNotFoundError`.
