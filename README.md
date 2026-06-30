# InvestingScripts

A set of Python scripts to analyze stocks.
Data is pulled from the AlphaVantage REST API. The API key is passed in via GNU `pass`.

## Local PostgreSQL

The scripts use a local PostgreSQL database by default. The runtime connection path does not use a hosted database service.

Start PostgreSQL with Docker Compose:

```bash
cp .env.example .env
docker compose up -d postgres
uv run python InitDB.py
```

`DBConnection.py` reads `.env` automatically. The default connection values are:

```bash
POSTGRES_DB=investing
POSTGRES_USER=investing
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

Change `POSTGRES_PASSWORD` in `.env` before first starting the container. You can also set `INVESTING_DATABASE_URL` to override the individual connection fields.

`InitDB.py` only creates the local schema and indexes. It does not fetch AlphaVantage data.

Run the comparison workflow after the database is initialized:

```bash
uv run python Comparisons.py
```
