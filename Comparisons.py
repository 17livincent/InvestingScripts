"""
    Compare multiple companies.
"""
from CalculateFundamentals import read_saved_fundamentals, get_latest_metrics
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
from datetime import datetime, timedelta

tickers = [
    # 'PLTR',
    # 'TEAM',
    'APH',
    'AME',
    # 'ETN',
    # 'F',
    # 'SNDK',
    # 'MU',
    # 'NVDA',
    # 'AVGO',
    # 'META',
    'V',
    'MA',
    'TMUS',
    'VZ'
    ]

graphs = [{'x': 'Date', 'y': 'TTM_ROIC'},
          {'x': 'Date', 'y': 'RevenueGrowth_YoY'},
          {'x': 'Date', 'y': 'TTM_OperatingMargin'},
          {'x': 'Date', 'y': 'TTM_FCFMargin'}]

df_calculated_all = {}
comparison_rows = []

now = pd.to_datetime(datetime.now())

for ticker in tickers:
    df_calculated = pd.DataFrame()
    try:
        df_calculated = read_saved_fundamentals(ticker)
        comparison_rows.append(get_latest_metrics(df_calculated, ticker))
    except FileNotFoundError as e:
        print(e)
        print("WARNING: no data for {}.".format(ticker))
    df_calculated_all[ticker] = df_calculated

df_comparison = pd.DataFrame(comparison_rows)
df_comparison = df_comparison.sort_values(by='TTM_ROIC', ascending=False)
print(df_comparison)

top_ttm_roic = df_comparison.iloc[0]['Ticker']

plt.style.use('dark_background')
fig, ax = plt.subplots(2, 2, figsize=(16, 8))

for ticker in tickers:
    ticker_calculated = df_calculated_all[ticker]
    if not df_calculated_all[ticker].empty:
        since_2020_calculated = ticker_calculated[now - ticker_calculated['Date'] < timedelta(weeks=52*6)]

        for graph_num, graph_x_y in enumerate(graphs):
            row, col = divmod(graph_num, 2)
            # Graph TTM_ROIC over time
            ax[row,col].set_title(graph_x_y['y'])
            ax[row,col].plot(since_2020_calculated[graph_x_y['x']],
                            since_2020_calculated[graph_x_y['y']],
                            label=ticker,
                            linewidth=(3 if ticker == top_ttm_roic else 1.5))
            ax[row,col].legend(loc='center left', bbox_to_anchor=(1, 0.5))
            ax[row,col].grid(True, alpha=0.3)
            ax[row,col].yaxis.set_major_formatter(PercentFormatter(1.0))

fig.suptitle('Comparisons', fontsize=24)
fig.tight_layout()
plt.show()
fig.savefig('data/Comparisons.png')
