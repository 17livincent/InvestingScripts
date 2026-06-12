---
name: daily-update
description: Run and summarize the InvestingScripts daily stock-watchlist update workflow. Use when the user asks for a daily update, today's data updates, a watchlist rundown, refreshed comparisons, ranked stock candidates, notable changes or trends, generated comparison charts, market/current-event context, or an explanation of the latest `data/*_Comparison.json` outputs in the InvestingScripts repo.
---

# Daily Update

## Overview

Use this skill to handle the daily InvestingScripts workflow: run the comparison update, snapshot the generated outputs, compare against the most recent prior snapshot, inspect the generated charts, research relevant market/current-event context, recommend possible watchlist improvements, and produce a ranked dashboard summary.

## Workflow

1. Use the repository root as the working directory.
2. Read `AGENTS.md` before changing or running anything that may affect the repo.
3. Inspect `watchlists.json` to identify watchlist names, stock tickers, and index symbols such as `SPX`.
4. Run the daily update with `uv run Comparisons.py` when the user asks for a daily update.
5. Check timestamps for `data/*_Comparison.json` and `data/* Comparisons.png` after the run completes.
6. Save a daily snapshot only when a daily update was requested.
7. Compare today's scored outputs to the most recent prior snapshot before today, up to 14 days old.
8. Inspect generated PNG comparison charts visually and summarize what they show.
9. Research relevant current events from the last 7 days for the market and for top candidates in each watchlist.
10. Recommend possible new watchlists or additions to existing watchlists based on market context.
11. Do not commit, delete, or regenerate unrelated `data/` artifacts unless the user explicitly asks.

## Running Updates

Run the update script when the user asks for a daily update or refreshed comparison data.

Use:

```bash
uv run Comparisons.py
```

Expected side effects:

- Calls AlphaVantage for stock, share, and daily/index data when stale.
- Reads/writes Supabase tables through the existing project flow.
- Writes comparison PNGs and `data/<WATCHLIST>_Comparison.json` files.
- May hit API rate limits or fall back to local JSON files.

If `uv` is unavailable, do not perform the daily update. Report that the update is blocked because the required runner is missing.

## Snapshots And Trends

After a successful daily update, create a snapshot under:

```text
data/daily_snapshots/YYYY-MM-DD/
```

Include:

- copies of `data/*_Comparison.json`
- a copy of `watchlists.json`
- a small `metadata.json` with run timestamp, update command, generated comparison JSON names, generated PNG names, and the prior snapshot used for comparison
- generated PNG files when useful for later visual comparison

For notable changes, compare today's scored JSON outputs against the most recent snapshot before today, looking back up to 14 days. If no prior snapshot exists in that window, say so clearly.

Focus trend notes on:

- rank changes within each watchlist
- total score and classification changes
- buy/watch/avoid bucket changes
- large component-score moves in quality, growth, valuation, or risk
- newly missing, newly available, or incomplete-data tickers

## Reading Results

Use the scored JSON files as the source of truth for rankings:

- `ticker`
- `total_score`
- `classification`
- `quality_score`
- `growth_score`
- `valuation_score`
- `risk_score`
- `quality_coverage`
- `valuation_coverage`
- `history_coverage`
- raw drivers such as ROIC, margins, revenue growth, debt-to-equity, valuation multiples, and discount-to-median fields

Remember that comparison scores are percentile ranks within each watchlist, not absolute market scores. `SPX` and other index symbols are chart-only and are not scored.

Call out watchlist symbols missing from the scored JSON. Common reasons include missing database rows, unavailable weekly prices, missing shares, or failed comparison-row construction.

## Current Events

Use web research for current-event context because market and company news changes daily. Look back 7 days.

Prefer:

- company investor relations pages and news releases
- SEC filings
- earnings call transcripts
- major financial news
- reputable analyst notes
- macro/index news

Focus stock-specific news on the top candidates in each watchlist, plus any lower-ranked names with notable news. Separate confirmed facts from interpretation, identify rumors or speculation, and avoid unsourced social media unless the source is a high-profile executive or similarly material primary actor.

Include source links in the final answer when current-event claims are used.

## Watchlist Recommendations

Recommend possible new watchlists or additions to existing watchlists when current market context points to relevant themes, sectors, competitors, suppliers, customers, or substitutes not already covered in `watchlists.json`.

Use evidence from:

- current market/news themes from the last 7 days
- sector moves and generated time-series comparison charts
- peer groups around the highest-ranking names
- supply-chain relationships, especially AI infrastructure, semiconductors, power, data centers, payments, banking, and consumer credit
- major earnings, guidance, filings, analyst actions, or macro events

Keep recommendations separate from direct score-based buy/watch/avoid calls because new names may not yet have local data. For each recommendation, include:

- proposed ticker or watchlist theme
- whether it is a new watchlist or an addition to an existing watchlist
- why it belongs
- what evidence supports it, with links when based on web/current-event context
- any caveat, such as missing local data, valuation risk, hype risk, cyclicality, leverage, or dependency on one customer/theme

Do not edit `watchlists.json` unless the user explicitly asks to add the recommendations.

## Buy, Watch, Avoid

Use these default buckets:

- Buy: `total_score >= 80`, equivalent to `High quality candidate`, with acceptable valuation and risk context.
- Watch: `total_score >= 65`, equivalent to `Watchlist quality`, or names with strong quality but expensive valuation, incomplete data, or another caveat that prevents a buy call.
- Avoid: everything else, especially low score, poor quality, poor risk, or insufficient data.

Challenge the scoring model when something looks odd, such as a high score driven by incomplete valuation data, capped multiples, unusual negative debt-to-equity handling, missing tickers, stale fundamentals, or a strong score that conflicts with recent material news.

## Graphs

Reference generated PNG file paths and inspect the charts visually. Give short visual summaries for operational comparisons, valuation comparisons, and time-series daily comparisons when available.

## Rundown Format

Write the final answer as a ranked dashboard summary with a "what changed" and "what to look at next" feel:

1. State that the update was run, include exact local timestamps, and list generated/snapshotted files.
2. Give a brief executive summary.
3. Provide one overall top-candidates list across all watchlists.
4. For each watchlist, identify buy/watch/avoid names, leaders, weak names, incomplete-data names, and top candidates.
5. Explain the main drivers using score components and relevant raw metrics such as ROIC, revenue growth, margins, valuation multiples, debt-to-equity, and discount-to-median.
6. Summarize notable changes versus the prior snapshot, or say no prior snapshot was available.
7. Reference and visually summarize relevant generated graphs.
8. Add current-event context for the market and the relevant stocks, with links.
9. Recommend possible new watchlists or additions to current watchlists based on market context, clearly separated from scored rankings.
10. Mention missing tickers, stale data, coverage caveats, and scoring-model oddities.
11. Close with the names worth deeper research and why.

Avoid presenting the output as investment advice. Phrase conclusions as model/ranking observations based on the local comparison files.
