---
name: daily-update
description: Run and summarize the InvestingScripts daily stock-watchlist update workflow. Use when the user asks for a daily update, today's data updates, a watchlist rundown, refreshed comparisons, ranked stock candidates, notable changes or trends, generated comparison charts, deeper market/current-event context tied to the watchlists, or an explanation of the latest `data/*_Comparison.json` outputs in the InvestingScripts repo.
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
8. Inspect the resulting metrics/outputs and generated PNG comparison charts visually and summarize what they show.
9. Research relevant current events from the last 7 days for the market, sectors/themes represented in `watchlists.json`, and top candidates in each watchlist.
10. Identify relevant peer companies/tickers surfaced by that research that are not tracked in any current watchlist, and use them when recommending possible new watchlists or additions to existing watchlists based on market context.
11. Do not commit, delete, or regenerate unrelated `data/` artifacts unless the user explicitly asks.

## Running Updates

Run the update script when the user asks for a daily update or refreshed comparison data.  A daily update may be requested multiple times in a day, given watchlist changes or script changes.

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

After researching market and sector/theme current events, compare any relevant peer tickers mentioned in sources against the union of all symbols in `watchlists.json`. Mention peer companies/tickers that are not tracked in any watchlist yet, and briefly state why they surfaced. Keep these untracked peers separate from scored rankings because they may not have local data.

For follow-up prompts asking for more depth on market context, use the latest completed daily snapshot and generated comparison files unless the user explicitly asks to rerun the update. Re-browse for current market context before answering.

## Market Context Deep Dives

When the user asks for deeper context, produce a synthesis that connects external market conditions to the local model output. Do not provide a generic news roundup. Cover the relevant lenses below, omitting any lens that is not supported by current sources or the watchlist mix:

- macro backdrop: Fed policy, rates, inflation, yields, oil/geopolitics, economic growth, and credit conditions
- market internals: index trend, breadth, leadership, concentration, volatility, sector rotation, and risk appetite
- theme/sector context: semiconductors, software, AI infrastructure and grid, industrials, financials, consumer credit, healthcare, payments, and any newly important theme in `watchlists.json`
- ticker implications: explain how the backdrop helps or hurts the highest-ranked names, borderline names, and obvious laggards
- untracked peers: mention relevant peer tickers surfaced by current research that are absent from every watchlist
- model alignment: state whether the news context reinforces, challenges, or is orthogonal to the score rankings

For each major context point:

- cite a current source link or say the point is an inference from local files
- connect the point to specific watchlists and tickers, not just broad sectors
- distinguish price momentum from the scoring model's quality/growth/valuation/risk components
- mention whether the point is short-term market context or medium-/long-term business context

Prefer primary and high-quality sources for macro facts: Federal Reserve releases, government economic data, Treasury/yield data, company IR/SEC filings, and major financial news. Use analyst notes or market commentary for interpretation, but label them as analyst/commentary views. Do not invent citations, cite inaccessible search snippets as if read directly, or make exact real-time market claims without a source.

When sources disagree or are thin, write the uncertainty plainly. A strong answer can say "the local model says X, while current market context suggests watching Y risk."

## Watchlist Recommendations

Recommend possible new watchlists or additions to existing watchlists when current market context points to relevant themes, sectors, competitors, suppliers, customers, or substitutes not already covered in `watchlists.json`.

Use evidence from:

- current market/news themes from the last 7 days
- sector moves and generated time-series comparison charts
- peer groups around the highest-ranking names
- peer companies/tickers surfaced by current-event research that are not already present in any watchlist
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
8. Add current-event context for the market and the relevant stocks, with links. If the user asks for depth, include a separate market-context section that maps macro/sector themes to watchlists and tickers.
9. Mention relevant peer companies/tickers surfaced by current research that are not tracked in any watchlist yet, clearly separated from scored rankings.
10. Recommend possible new watchlists or additions to current watchlists based on market context, clearly separated from scored rankings.
11. Mention missing tickers, stale data, coverage caveats, and scoring-model oddities.
12. Close with the names worth deeper research and why.

Avoid presenting the output as investment advice. Phrase conclusions as model/ranking observations based on the local comparison files.
