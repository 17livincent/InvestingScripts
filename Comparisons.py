"""
    Compare multiple companies.
"""
from OperationalMetrics import get_latest_operational_metrics
from ValuationMetrics import get_latest_valuation
from TickerData import TableOperationalMetrics, TableValuationMetrics, add_update_ticker
from DBConnection import get_db_connection
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
from datetime import datetime, timedelta
import json

FIGURE_ROWS = 2
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

operational_graphs = [{'x': 'date', 'y': 'ttm_roic', 'type': 'line', 'percentFormat': True, 'table': 'operational_metrics'},
                      {'x': 'date', 'y': 'revenue_growth_yoy', 'type': 'line', 'percentFormat': True, 'table': 'operational_metrics'},
                      {'x': 'date', 'y': 'ttm_operating_margin', 'type': 'line', 'percentFormat': True, 'table': 'operational_metrics'},
                      {'x': 'date', 'y': 'ttm_fcf_margin', 'type': 'line', 'percentFormat': True, 'table': 'operational_metrics'}
                      ]

valuation_graphs = [{'x': 'date', 'y': 'pe_ttm', 'type': 'line', 'percentFormat': False, 'table': 'valuation_metrics'},
                    {'x': 'date', 'y': 'ev_ebit', 'type': 'line', 'percentFormat': False, 'table': 'valuation_metrics'},
                    {'x': 'date', 'y': 'ev_fcf', 'type': 'line', 'percentFormat': False, 'table': 'valuation_metrics'},
                    {'x': 'ev_ebit', 'y': 'ttm_roic', 'type': 'scatter', 'percentFormat': False, 'table': 'ev_ebit_ttm_roic'}
                    ]

operational_figure = {'graphs': operational_graphs, 'title': 'Operational Comparisons'}
valuation_figure = {'graphs': valuation_graphs, 'title': 'Valuation Comparisons'}

def create_graph_figures(title, graphs, df_comparison, df_data):
    now = pd.to_datetime(datetime.now())

    top_ttm_roic = df_comparison.iloc[0]['ticker']

    fig, ax = plt.subplots(FIGURE_ROWS, FIGURE_COLS, figsize=(18, 12))

    for graph_num, graph_x_y in enumerate(graphs):
        row, col = divmod(graph_num, FIGURE_COLS)
        ax[row,col].set_title('{} to {}'.format(graph_x_y['y'], graph_x_y['x']))

        for ticker_name in df_data:
            ticker_calculated = df_data[ticker_name][graph_x_y['table']]

            try:
                if graph_x_y['type'] == 'line':
                    ax[row,col].plot(ticker_calculated[graph_x_y['x']],
                                    ticker_calculated[graph_x_y['y']],
                                    label=ticker_name,
                                    linewidth=(3 if ticker_name == top_ttm_roic else 1.5))
                elif graph_x_y['type'] == 'scatter':
                    ax[row,col].scatter(ticker_calculated[graph_x_y['x']],
                                        ticker_calculated[graph_x_y['y']],
                                        label=ticker_name)
                    ax[row,col].annotate(ticker_name,
                                            (ticker_calculated[graph_x_y['x']].iloc[0],
                                            ticker_calculated[graph_x_y['y']].iloc[0]))
            except KeyError as e:
                print("WARNING key {} missing from {} for {}.".format(graph_x_y['y'], ticker_calculated.columns, ticker_name))
                print(e)

        ax[row,col].set_xlabel(graph_x_y['x'])
        ax[row,col].set_ylabel(graph_x_y['y'])
        ax[row,col].legend(loc='center left', fontsize=8, bbox_to_anchor=(1, 0.5))
        ax[row,col].grid(True, alpha=0.3)
        if graph_x_y['percentFormat'] == True:
            ax[row,col].yaxis.set_major_formatter(PercentFormatter(1.0))

    fig.suptitle(title, fontsize=24)
    fig.tight_layout()
    fig.savefig('data/{}.png'.format(title))

def post_process_df(df_data):
    try:
        df_data['ev_fcf'] = df_data['ev_fcf'].clip(upper=200)
    except KeyError as e:
        pass

def get_unique_tickers_in_watchlist_array(watchlists_json):
    all_tickers = []
    for watchlist_tickers in [watchlists_json[watchlist_name] for watchlist_name in watchlists_json]:
        all_tickers.extend(watchlist_tickers)
    all_tickers.sort()
    all_tickers = list(set(all_tickers))

    return all_tickers

def main():
    db_connection = get_db_connection()

    with open('watchlists.json', 'r') as watchlists_file:
        watchlists_json = json.load(watchlists_file)
        print(watchlists_json)

        all_tickers = get_unique_tickers_in_watchlist_array(watchlists_json)
        print('Unique tickers: {}'.format(all_tickers))

        df_calculated_all = {}
        comparison_rows = []

        for ticker in all_tickers:
            try:
                add_update_ticker(ticker, db_connection)

                df_operational_metrics = TableOperationalMetrics.get_from(ticker,
                                                                          db_connection,
                                                                          datetime.now() - timedelta(weeks=OPERATIONAL_TIME_FRAME_WEEKS))
                df_valuation_metrics = TableValuationMetrics.get_from(ticker,
                                                                      db_connection,
                                                                      datetime.now() - timedelta(weeks=VALUATION_TIME_FRAME_WEEKS))

                # Some post-processing
                post_process_df(df_valuation_metrics)

                comparison_dict = get_latest_operational_metrics(df_operational_metrics, ticker)
                comparison_dict.update(get_latest_valuation(df_valuation_metrics, ticker))

                comparison_dict['ROIC_EV_SCORE'] = comparison_dict['ttm_roic'] / comparison_dict['ev_ebit']
                comparison_rows.append(comparison_dict)
                ev_ebit_ttm_roic = pd.DataFrame([comparison_dict])

                df_calculated_all[ticker] = {'operational_metrics': df_operational_metrics,
                                'valuation_metrics': df_valuation_metrics,
                                'ev_ebit_ttm_roic': ev_ebit_ttm_roic}

            except FileNotFoundError as e:
                print(e)
                print("WARNING: no data for {}.".format(ticker))
            except IndexError as e:
                print(e)
            except KeyError as e:
                print(e)
                print(ticker)

        if comparison_rows:
            df_comparison = pd.DataFrame(comparison_rows)
            df_comparison = df_comparison.sort_values(by='ttm_roic', ascending=False)
            print(watchlists_json)

            for watchlist_name in watchlists_json:
                watchlist_tickers = watchlists_json[watchlist_name]
                print(watchlist_tickers)

                if watchlist_tickers:
                    df_watchlist_comparison = df_comparison.loc[df_comparison['ticker'].isin(watchlist_tickers)]

                    if not df_watchlist_comparison.empty:
                        watchlist_calculated = {key: df_calculated_all[key] for key in watchlists_json[watchlist_name] if key in df_calculated_all}
                        # plt.style.use('dark_background')

                        create_graph_figures('{} {}'.format(watchlist_name, operational_figure['title']),
                                            operational_figure['graphs'],
                                            df_watchlist_comparison,
                                            watchlist_calculated)
                        create_graph_figures('{} {}'.format(watchlist_name, valuation_figure['title']),
                                            valuation_figure['graphs'],
                                            df_watchlist_comparison,
                                            watchlist_calculated)

                        print('\r\n\r\n{}: Rank by greatest {}:'.format(watchlist_name, 'ttm_roic'))
                        print(df_watchlist_comparison.to_string())

                        df_watchlist_comparison = df_watchlist_comparison.sort_values(by='pe_ttm', ascending=True)
                        print('\r\n\r\n{}: Rank by lowest {}:'.format(watchlist_name, 'pe_ttm'))
                        print(df_watchlist_comparison.to_string())

if __name__ == "__main__":
    main()
