"""
    Compare multiple companies.
"""
from OperationalMetrics import get_latest_operational_metrics
from ValuationMetrics import get_latest_valuation
from TickerData import TableOperationalMetrics, TableValuationMetrics, add_update_ticker
from TimeSeriesDaily import get_time_series_daily_adjusted
from DBConnection import get_db_connection
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
from datetime import datetime, timedelta
import json

OPERATIONAL_TIME_FRAME_WEEKS = 52*6
VALUATION_TIME_FRAME_WEEKS = 52*2
OPERATIONAL_AVG_YEARS = 3
VALUATION_MEDIAN_YEARS = 2
MIN_HISTORY_OBSERVATIONS = 4

time_frames = {'ttm_roic': OPERATIONAL_TIME_FRAME_WEEKS,
               'revenue_growth_yoy': OPERATIONAL_TIME_FRAME_WEEKS,
               'ttm_operating_margin': OPERATIONAL_TIME_FRAME_WEEKS,
               'ttm_fcf_margin': OPERATIONAL_TIME_FRAME_WEEKS,
               'pe_ttm': VALUATION_TIME_FRAME_WEEKS,
               'ev_ebit': VALUATION_TIME_FRAME_WEEKS,
               'ev_fcf': VALUATION_TIME_FRAME_WEEKS}

operational_graphs = [{'x': 'date',
                       'y': 'ttm_roic',
                       'type': 'line',
                       'percentFormat': True,
                       'grid': True,
                       'table': 'operational_metrics'},
                      {'x': 'date',
                       'y': 'revenue_growth_yoy',
                       'type': 'line',
                       'percentFormat': True,
                       'grid': True,
                       'table': 'operational_metrics'},
                      {'x': 'date',
                       'y': 'ttm_operating_margin',
                       'type': 'line',
                       'percentFormat': True,
                       'grid': True,
                       'table': 'operational_metrics'},
                      {'x': 'date',
                       'y': 'ttm_fcf_margin',
                       'type': 'line',
                       'percentFormat': True,
                       'grid': True,
                       'table': 'operational_metrics'}
                      ]

valuation_graphs = [{'x': 'date',
                     'y': 'pe_ttm',
                     'type': 'line',
                     'percentFormat': False,
                     'grid': True,
                     'table': 'valuation_metrics'},
                    {'x': 'date',
                     'y': 'ev_ebit',
                     'type': 'line',
                     'percentFormat': False,
                     'grid': True,
                     'table': 'valuation_metrics'},
                    {'x': 'date',
                     'y': 'ev_fcf',
                     'type': 'line',
                     'percentFormat': False,
                     'grid': True,
                     'table': 'valuation_metrics'},
                    {'x': 'ev_ebit',
                     'y': 'ttm_roic',
                     'type': 'scatter',
                     'percentFormat': False,
                     'grid': True,
                     'table': 'ev_ebit_ttm_roic'}
                    ]

time_series_graphs = [{'x': 'date',
                       'y': 'close_change_perc',
                       'type': 'line',
                       'percentFormat': True,
                       'grid': True,
                       'table': 'time_series_daily_adj'}
                      ]

operational_figure = {'graphs': operational_graphs, 'title': 'Operational Comparisons', 'rows': 2, 'cols': 2}
valuation_figure = {'graphs': valuation_graphs, 'title': 'Valuation Comparisons', 'rows': 2, 'cols': 2}
time_series_figure = {'graphs': time_series_graphs, 'title': 'Time Series Daily Comparisons', 'rows': 2, 'cols': 2}

QUALITY_WEIGHTS = pd.Series({
    'ttm_roic_perc_rank': 0.45,
    'ttm_operating_margin_perc_rank': 0.2,
    'ttm_fcf_margin_perc_rank': 0.15,
    'quality_consistency_perc_rank': 0.2
})

GROWTH_WEIGHTS = pd.Series({
    'revenue_growth_yoy_perc_rank': 0.6,
    'revenue_growth_yoy_3yr_avg_perc_rank': 0.4
})

VALUATION_WEIGHTS = pd.Series({
    'pe_ttm_perc_rank': 0.2333,
    'ev_ebit_perc_rank': 0.2333,
    'ev_fcf_perc_rank': 0.2333,
    'pe_ttm_discount_perc_rank': 0.1,
    'ev_ebit_discount_perc_rank': 0.1,
    'ev_fcf_discount_perc_rank': 0.1
})

RISK_WEIGHTS = pd.Series({
    'debt_to_equity_perc_rank': 0.5,
    'ttm_fcf_margin_perc_rank': 0.3,
    'ttm_operating_margin_perc_rank': 0.2
})

TOTAL_SCORE_WEIGHTS = {
    'quality_score': 0.4,
    'growth_score': 0.2,
    'valuation_score': 0.2,
    'risk_score': 0.2
}

def create_graph_figures(title, figure_def, df_comparison, df_data):
    graphs = figure_def['graphs']
    num_rows = figure_def['rows']
    num_cols = figure_def['cols']

    top_ttm_roic = df_comparison.iloc[0]['ticker']
    fig, ax = plt.subplots(num_rows, num_cols, figsize=(18, 12))

    for graph_num, graph_x_y in enumerate(graphs):
        row, col = divmod(graph_num, num_cols)
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
        if graph_x_y['grid'] == True:
            ax[row,col].grid(True, alpha=0.3)
        if graph_x_y['percentFormat'] == True:
            ax[row,col].yaxis.set_major_formatter(PercentFormatter(1.0))

    fig.suptitle(title, fontsize=24)
    fig.tight_layout()
    fig.savefig('data/{}.png'.format(title))
    plt.close(fig)

def post_process_valuation_metrics(df_data):
    try:
        df_data['ev_fcf'] = df_data['ev_fcf'].clip(upper=200)
    except KeyError as e:
        pass

def post_process_time_series_daily_adj(df_time_series_daily_adj):
    # Turn the 'close' column into a percent difference of the intial value.
    initial_close_value = df_time_series_daily_adj.iloc[0]['close']
    df_time_series_daily_adj['close_change_perc'] = (df_time_series_daily_adj['close'] - initial_close_value) / df_time_series_daily_adj['close']

def get_unique_tickers_in_watchlist_array(watchlists_json):
    all_tickers = []
    for watchlist_tickers in [watchlists_json[watchlist_name] for watchlist_name in watchlists_json]:
        all_tickers.extend(watchlist_tickers)
    all_tickers.sort()
    all_tickers = list(set(all_tickers))

    return all_tickers

def get_recent_window(df_data, years):
    df_recent_window = df_data.iloc[0:0]

    if not df_data.empty and 'date' in df_data.columns:
        df_data = df_data.copy()
        df_data['date'] = pd.to_datetime(df_data['date'])
        latest_date = df_data['date'].max()
        start_date = latest_date - pd.DateOffset(years=years)
        df_recent_window = df_data.loc[df_data['date'] >= start_date]

    return df_recent_window

def get_metric_summary(df_data, metric, years, aggregate):
    metric_summary = pd.NA

    if metric in df_data.columns:
        df_window = get_recent_window(df_data, years)
        metric_values = pd.to_numeric(df_window[metric], errors='coerce').dropna()

        if len(metric_values) >= MIN_HISTORY_OBSERVATIONS:
            metric_summary = getattr(metric_values, aggregate)()

    return metric_summary

def get_trailing_average_metrics(df_operational_metrics, df_valuation_metrics):
    return {
        'ttm_roic_3yr_avg': get_metric_summary(df_operational_metrics, 'ttm_roic', OPERATIONAL_AVG_YEARS, 'mean'),
        'ttm_roic_3yr_std': get_metric_summary(df_operational_metrics, 'ttm_roic', OPERATIONAL_AVG_YEARS, 'std'),
        'revenue_growth_yoy_3yr_avg': get_metric_summary(df_operational_metrics, 'revenue_growth_yoy', OPERATIONAL_AVG_YEARS, 'mean'),
        'ttm_operating_margin_3yr_avg': get_metric_summary(df_operational_metrics, 'ttm_operating_margin', OPERATIONAL_AVG_YEARS, 'mean'),
        'ttm_fcf_margin_3yr_avg': get_metric_summary(df_operational_metrics, 'ttm_fcf_margin', OPERATIONAL_AVG_YEARS, 'mean'),
        'pe_ttm_2yr_median': get_metric_summary(df_valuation_metrics, 'pe_ttm', VALUATION_MEDIAN_YEARS, 'median'),
        'ev_ebit_2yr_median': get_metric_summary(df_valuation_metrics, 'ev_ebit', VALUATION_MEDIAN_YEARS, 'median'),
        'ev_fcf_2yr_median': get_metric_summary(df_valuation_metrics, 'ev_fcf', VALUATION_MEDIAN_YEARS, 'median')
    }

def get_weighted_score(df_score_components, weights):
    weighted_component_sum = df_score_components.mul(weights, axis=1).sum(axis=1, skipna=True)
    available_weight_sum = df_score_components.notna().mul(weights, axis=1).sum(axis=1)

    return weighted_component_sum / available_weight_sum

def get_discount_to_median(current_values, median_values):
    current_values = pd.to_numeric(current_values, errors='coerce')
    median_values = pd.to_numeric(median_values, errors='coerce')

    return (current_values / median_values).where((current_values > 0) & (median_values > 0))

def get_component_coverage(df_score_components):
    return df_score_components.notna().sum(axis=1) / len(df_score_components.columns)

def get_score_classification(row):
    minimum_coverage = min(row['quality_coverage'], row['valuation_coverage'], row['history_coverage'])
    classification = 'Low rank'

    if minimum_coverage < 0.6:
        classification = 'Incomplete data'
    elif row['total_score'] >= 80:
        classification = 'High quality candidate'
    elif row['total_score'] >= 65:
        classification = 'Watchlist quality'
    elif row['total_score'] >= 50:
        classification = 'Mixed'

    return classification

def get_scores(df_watchlist_comparison):
    df_watchlist_comparison_clean = df_watchlist_comparison.copy()

    df_watchlist_comparison_clean['debt_to_equity'] = df_watchlist_comparison_clean['debt_to_equity'].where(df_watchlist_comparison_clean['debt_to_equity'] >= 0, 5).clip(upper=5)

    df_quality_score_components = pd.DataFrame()
    df_quality_score_components['ttm_roic_perc_rank'] = df_watchlist_comparison_clean['ttm_roic'].rank(pct=True) * 100
    df_quality_score_components['ttm_operating_margin_perc_rank'] = df_watchlist_comparison_clean['ttm_operating_margin'].rank(pct=True) * 100
    df_quality_score_components['ttm_fcf_margin_perc_rank'] = df_watchlist_comparison_clean['ttm_fcf_margin'].rank(pct=True) * 100
    df_quality_score_components['quality_consistency_perc_rank'] = (df_watchlist_comparison_clean['ttm_roic_3yr_avg'] -
                                                                    df_watchlist_comparison_clean['ttm_roic_3yr_std']).rank(pct=True) * 100

    df_watchlist_comparison_clean['quality_score'] = get_weighted_score(df_quality_score_components, QUALITY_WEIGHTS)
    df_watchlist_comparison_clean['quality_coverage'] = get_component_coverage(df_quality_score_components)

    df_growth_score_components = pd.DataFrame()
    df_growth_score_components['revenue_growth_yoy_perc_rank'] = df_watchlist_comparison_clean['revenue_growth_yoy'].rank(pct=True) * 100
    df_growth_score_components['revenue_growth_yoy_3yr_avg_perc_rank'] = df_watchlist_comparison_clean['revenue_growth_yoy_3yr_avg'].rank(pct=True) * 100

    df_watchlist_comparison_clean['growth_score'] = get_weighted_score(df_growth_score_components, GROWTH_WEIGHTS)

    df_valuation_score_components = pd.DataFrame()
    df_valuation_score_components['pe_ttm_perc_rank'] = df_watchlist_comparison_clean['pe_ttm'].rank(pct=True, ascending=False) * 100
    df_valuation_score_components['ev_ebit_perc_rank'] = df_watchlist_comparison_clean['ev_ebit'].rank(pct=True, ascending=False) * 100
    df_valuation_score_components['ev_fcf_perc_rank'] = df_watchlist_comparison_clean['ev_fcf'].rank(pct=True, ascending=False) * 100
    df_watchlist_comparison_clean['pe_ttm_discount'] = get_discount_to_median(df_watchlist_comparison_clean['pe_ttm'],
                                                                                 df_watchlist_comparison_clean['pe_ttm_2yr_median'])
    df_watchlist_comparison_clean['ev_ebit_discount'] = get_discount_to_median(df_watchlist_comparison_clean['ev_ebit'],
                                                                                df_watchlist_comparison_clean['ev_ebit_2yr_median'])
    df_watchlist_comparison_clean['ev_fcf_discount'] = get_discount_to_median(df_watchlist_comparison_clean['ev_fcf'],
                                                                               df_watchlist_comparison_clean['ev_fcf_2yr_median'])
    df_valuation_score_components['pe_ttm_discount_perc_rank'] = df_watchlist_comparison_clean['pe_ttm_discount'].rank(pct=True, ascending=True) * 100
    df_valuation_score_components['ev_ebit_discount_perc_rank'] = df_watchlist_comparison_clean['ev_ebit_discount'].rank(pct=True, ascending=True) * 100
    df_valuation_score_components['ev_fcf_discount_perc_rank'] = df_watchlist_comparison_clean['ev_fcf_discount'].rank(pct=True, ascending=True) * 100

    df_watchlist_comparison_clean['valuation_score'] = get_weighted_score(df_valuation_score_components, VALUATION_WEIGHTS)
    df_watchlist_comparison_clean['valuation_coverage'] = get_component_coverage(df_valuation_score_components)

    df_risk_score_components = pd.DataFrame()
    df_risk_score_components['debt_to_equity_perc_rank'] = (df_watchlist_comparison_clean['debt_to_equity']
                                                            .rank(pct=True, ascending=False)
                                                            .mul(100))
    df_risk_score_components['ttm_fcf_margin_perc_rank'] = df_watchlist_comparison_clean['ttm_fcf_margin'].rank(pct=True).mul(100)
    df_risk_score_components['ttm_operating_margin_perc_rank'] = df_watchlist_comparison_clean['ttm_operating_margin'].rank(pct=True).mul(100)

    df_watchlist_comparison_clean['risk_score'] = get_weighted_score(df_risk_score_components, RISK_WEIGHTS)
    df_watchlist_comparison_clean['history_coverage'] = get_component_coverage(
        df_watchlist_comparison_clean[['ttm_roic_3yr_avg',
                                       'ttm_roic_3yr_std',
                                       'revenue_growth_yoy_3yr_avg',
                                       'ttm_operating_margin_3yr_avg',
                                       'ttm_fcf_margin_3yr_avg',
                                       'pe_ttm_2yr_median',
                                       'ev_ebit_2yr_median',
                                       'ev_fcf_2yr_median']]
    )

    score_columns = ['quality_score', 'growth_score', 'valuation_score', 'risk_score']
    df_watchlist_comparison_clean[score_columns] = df_watchlist_comparison_clean[score_columns].fillna(0)

    df_watchlist_comparison_clean['total_score'] = (TOTAL_SCORE_WEIGHTS['quality_score'] * df_watchlist_comparison_clean['quality_score'] +
                                              TOTAL_SCORE_WEIGHTS['growth_score'] * df_watchlist_comparison_clean['growth_score'] +
                                              TOTAL_SCORE_WEIGHTS['valuation_score'] * df_watchlist_comparison_clean['valuation_score'] +
                                              TOTAL_SCORE_WEIGHTS['risk_score'] * df_watchlist_comparison_clean['risk_score'])

    df_watchlist_comparison_clean['classification'] = df_watchlist_comparison_clean.apply(get_score_classification, axis=1)

    df_watchlist_comparison_clean = df_watchlist_comparison_clean.sort_values(by='total_score', ascending=False)
    print(df_watchlist_comparison_clean[['ticker',
                                         'quality_score',
                                         'growth_score',
                                         'valuation_score',
                                         'risk_score',
                                         'total_score',
                                         'quality_coverage',
                                         'valuation_coverage',
                                         'history_coverage',
                                         'classification']].to_string())

    return df_watchlist_comparison_clean

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

                df_time_series_daily_adjusted = get_time_series_daily_adjusted(ticker,
                                                                               datetime.now() - timedelta(weeks=VALUATION_TIME_FRAME_WEEKS))

                # Some post-processing
                post_process_valuation_metrics(df_valuation_metrics)
                post_process_time_series_daily_adj(df_time_series_daily_adjusted)

                comparison_dict = get_latest_operational_metrics(df_operational_metrics, ticker)
                comparison_dict.update(get_latest_valuation(df_valuation_metrics, ticker))
                comparison_dict.update(get_trailing_average_metrics(df_operational_metrics, df_valuation_metrics))

                comparison_rows.append(comparison_dict)
                ev_ebit_ttm_roic = pd.DataFrame([comparison_dict])

                df_calculated_all[ticker] = {'operational_metrics': df_operational_metrics,
                                             'valuation_metrics': df_valuation_metrics,
                                             'ev_ebit_ttm_roic': ev_ebit_ttm_roic,
                                             'time_series_daily_adj': df_time_series_daily_adjusted}

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

                if watchlist_tickers:
                    df_watchlist_comparison = df_comparison.loc[df_comparison['ticker'].isin(watchlist_tickers)]

                    if not df_watchlist_comparison.empty:
                        watchlist_calculated = {key: df_calculated_all[key] for key in watchlists_json[watchlist_name] if key in df_calculated_all}
                        # plt.style.use('dark_background')

                        create_graph_figures('{} {}'.format(watchlist_name, operational_figure['title']),
                                             operational_figure,
                                             df_watchlist_comparison,
                                             watchlist_calculated)
                        create_graph_figures('{} {}'.format(watchlist_name, valuation_figure['title']),
                                            valuation_figure,
                                            df_watchlist_comparison,
                                            watchlist_calculated)
                        create_graph_figures('{} {}'.format(watchlist_name, time_series_figure['title']),
                                             time_series_figure,
                                             df_watchlist_comparison,
                                             watchlist_calculated)

                        print('\r\n\r\n{} : {}'.format(watchlist_name, watchlist_tickers))
                        print('Rank by greatest {}:'.format('ttm_roic'))
                        print(df_watchlist_comparison.to_string())

                        df_watchlist_comparison = get_scores(df_watchlist_comparison)

                        df_watchlist_comparison.to_json('data/{}_Comparison.json'.format(watchlist_name), orient='records', indent=4)

if __name__ == "__main__":
    main()
