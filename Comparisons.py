"""
    Compare multiple companies.
"""
from OperationalMetrics import get_latest_metrics
from ValuationMetrics import get_valuation, get_latest_valuation
from TickerData import get_from_fundamentals, get_from_operational_metrics, add_update_ticker
from DBConnection import get_db_connection
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
from datetime import datetime, timedelta

tickers = [
    # 'PLTR',
    # 'TEAM',
    'APH',
    # 'ETN',
    # 'F',
    'SNDK',
    # 'MU',
    # 'NVDA',
    # 'AVGO',
    # 'META',
    # 'V',
    # 'MA',
    # 'TMUS',
    # 'VZ',
    # 'FDX',
    'CRWD',
    # 'CVX'
    ]

FIGURE_ROWS = 4
FIGURE_COLS = 2
OPERATIONAL_TIME_FRAME_WEEKS = 52*6
VALUATION_TIME_FRAME_WEEKS = 52*2

time_frames = {'ttm_roic': OPERATIONAL_TIME_FRAME_WEEKS,
               'revenue_growth_yoy': OPERATIONAL_TIME_FRAME_WEEKS,
               'ttm_operating_margin': OPERATIONAL_TIME_FRAME_WEEKS,
               'ttm_fcf_margin': OPERATIONAL_TIME_FRAME_WEEKS,
               'pe_ttm': VALUATION_TIME_FRAME_WEEKS,
               'ev_ebit': VALUATION_TIME_FRAME_WEEKS,
               'ev_fcf': VALUATION_TIME_FRAME_WEEKS}

graphs = [{'x': 'date', 'y': 'ttm_roic', 'percentFormat': True},
          {'x': 'date', 'y': 'revenue_growth_yoy', 'percentFormat': True},
          {'x': 'date', 'y': 'ttm_operating_margin', 'percentFormat': True},
          {'x': 'date', 'y': 'ttm_fcf_margin', 'percentFormat': True},
          {'x': 'date', 'y': 'pe_ttm', 'percentFormat': False},
          {'x': 'date', 'y': 'ev_ebit', 'percentFormat': False},
          {'x': 'date', 'y': 'ev_fcf', 'percentFormat': False}]

df_calculated_all = {}
comparison_rows = []

now = pd.to_datetime(datetime.now())
db_connection = get_db_connection()

for ticker in tickers:
    add_update_ticker(ticker, db_connection)

    df_calculated = pd.DataFrame()
    try:
        df_fundamentals = get_from_fundamentals(ticker, db_connection)
        df_calculated = pd.merge(df_fundamentals, get_from_operational_metrics(ticker, db_connection), on='date')
        df_calculated = get_valuation(ticker, df_calculated)

        comparison_dict = get_latest_metrics(df_calculated, ticker)
        comparison_dict.update(get_latest_valuation(df_calculated, ticker))
        comparison_rows.append(comparison_dict)
    except FileNotFoundError as e:
        print(e)
        print("WARNING: no data for {}.".format(ticker))
    except KeyError as e:
        print(e)
        print(ticker)

    df_calculated_all[ticker] = df_calculated

df_comparison = pd.DataFrame(comparison_rows)
df_comparison = df_comparison.sort_values(by='ttm_roic', ascending=False)
print(df_comparison)

top_ttm_roic = df_comparison.iloc[0]['ticker']

plt.style.use('dark_background')
fig, ax = plt.subplots(FIGURE_ROWS, FIGURE_COLS, figsize=(18, 12))

for ticker in tickers:

        for graph_num, graph_x_y in enumerate(graphs):
            ticker_calculated = df_calculated_all[ticker]
            since_calculated = ticker_calculated[now - ticker_calculated['date'] < timedelta(weeks=time_frames[graph_x_y['y']])]

            if not df_calculated_all[ticker].empty:

                row, col = divmod(graph_num, FIGURE_COLS)
                ax[row,col].set_title(graph_x_y['y'])
                try:
                    ax[row,col].plot(since_calculated[graph_x_y['x']],
                                    since_calculated[graph_x_y['y']],
                                    label=ticker,
                                    linewidth=(3 if ticker == top_ttm_roic else 1.5))
                    ax[row,col].legend(loc='center left', fontsize=8, bbox_to_anchor=(1, 0.5))
                except KeyError as e:
                    print("WARNING key {} missing for {}.".format(graph_x_y['y'], ticker))
                ax[row,col].grid(True, alpha=0.3)
                if graph_x_y['percentFormat'] == True:
                    ax[row,col].yaxis.set_major_formatter(PercentFormatter(1.0))

fig.suptitle('Comparisons', fontsize=24)
fig.tight_layout()
fig.savefig('data/Comparisons.png')
