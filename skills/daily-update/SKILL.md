---
name: daily-update
description: Run and summarize the InvestingScripts daily stock-watchlist update workflow. Use when the user asks for a daily update, today's data updates, a watchlist rundown, refreshed comparisons, ranked stock candidates, notable changes or trends, generated comparison charts, deeper market/current-event context tied to the watchlists, or an explanation of the latest `data/*_Comparison.json` outputs.
---

# Daily Update

Use this skill for daily watchlist updates and report-style summaries from the latest InvestingScripts comparison outputs.

## Update Run

- `uv run Comparsions.py`.  Include `--skip_update` or `--watchlist` if the user requests.
- Describe the log prints from the script as they occur.

## Snapshot And Trends

After a successful fresh update, create the daily snapshot with:

- copies of comparison JSON files
- `watchlists.json`
- useful generated PNGs
- `metadata.json` containing run timestamp, command, generated JSON/PNG names, and prior snapshot used

For changes, compare against the most recent prior snapshot before today, looking back up to 14 days. Note clearly when no prior snapshot is available.

Trend notes should focus on rank, `total_score`, classification, component-score moves, bucket changes, and newly missing/available/incomplete tickers.

## Reading Outputs

Use scored JSON as ranking source of truth. Key fields include `ticker`, `total_score`, `classification`, component scores, coverage fields, ROIC, margins, revenue growth, debt-to-equity, valuation multiples, and discount-to-median fields.

Call out watchlist symbols missing from scored JSON. Common causes are missing DB rows, unavailable weekly prices, missing shares, or failed comparison-row construction.

Challenge odd model output, including strong scores driven by incomplete valuation data, capped multiples, unusual negative debt-to-equity handling, stale fundamentals, or material news that conflicts with the local score.

## Current Context

When current context is requested or useful, browse for the last 7 days and cite sources. Focus on:

- market, macro, sector, and theme context represented in `watchlists.json`
- top candidates in each watchlist
- lower-ranked names with material news
- peer companies or tickers surfaced by research but absent from all watchlists

Keep untracked peers separate from scored rankings because they may not have local data.

For deep dives, connect external context to local model output by watchlist and ticker. Distinguish price momentum from quality/growth/valuation/risk scores, and label short-term market context versus medium-/long-term business context.

## Recommendations

Recommend watchlist additions or new watchlist themes only when current context points to relevant competitors, suppliers, customers, substitutes, or sector themes not already covered.

For each recommendation, include ticker/theme, add-vs-new-watchlist, why it belongs, supporting evidence, and caveats such as missing local data, valuation risk, hype risk, cyclicality, leverage, or customer/theme concentration.

## Report Shape

Daily rundowns should include:

1. Fresh/cached status, exact local timestamps, and generated/snapshotted files.
2. Brief executive summary.
3. Overall top candidates across watchlists.
4. Per-watchlist buy/watch/avoid style rundown, leaders, weak names, incomplete-data names, and drivers.
5. Notable changes versus prior snapshot.
6. Visual summary of relevant generated charts.
7. Current-event context with links when used.
8. Untracked peers and watchlist recommendations, separate from scored rankings.
9. Missing tickers, stale-data caveats, coverage caveats, and model oddities.

Phrase conclusions as model/ranking observations, not investment advice.
