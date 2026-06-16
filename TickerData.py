"""
    Read, update ticker data.
"""

from RequestAndSave import request_data
from OperationalMetrics import (get_saved_fundamentals,
                                calculate_operational_metrics)
from ValuationMetrics import (get_shares_outstanding,
                              get_timeseries_weekly_adjusted,
                              calculate_valuation_metrics)
from sqlalchemy import text
from InitDB import (TABLE_NAMES,
                    TABLE_COMPANIES_NAME,
                    TABLE_COMPANIES_DICT,
                    TABLE_NAME_FUNDAMENTALS,
                    TABLE_NAME_OPERATIONAL_METRICS,
                    TABLE_NAME_SHARES_OUTSTANDING,
                    TABLE_NAME_PRICES_WEEKLY,
                    TABLE_NAME_VALUATION_METRICS,
                    TABLE_NAME_DATA_UPDATES,
                    INSERT_STATEMENT_FUNDAMENTALS,
                    INSERT_STATEMENT_OPERATIONAL_METRICS,
                    INSERT_STATEMENT_SHARES_OUTSTANDING,
                    INSERT_STATEMENT_PRICES_WEEKLY,
                    INSERT_STATEMENT_VALUATION_METRICS)
from DBConnection import get_db_connection
from pathlib import Path
import json
import pandas as pd
from datetime import datetime, timezone, date
import argparse

SAVED_JSON_PATH = 'data/AlphaVantage/{}/{}.json'

OVERVIEW_FUNCTION_NAME = 'OVERVIEW'
BALANCE_SHEET_FUNCTION_NAME = 'BALANCE_SHEET'
CASH_FLOW_FUNCTION_NAME = 'CASH_FLOW'
INCOME_STATEMENT_FUNCTION_NAME = 'INCOME_STATEMENT'
SHARES_OUTSTANDING_FUNCTION_NAME = 'SHARES_OUTSTANDING'
PRICES_WEEKLY_FUNCTION_NAME = 'TIME_SERIES_WEEKLY_ADJUSTED'

RECENCY = {
    'companies': 'quarter',
    'fundamentals': 'quarter',
    'operational_metrics': 'quarter',
    'shares_outstanding': 'quarter',
    'prices_weekly': 'week',
    'valuation_metrics': 'week'
}

class DataUpdates():
    @staticmethod
    def get_all_last_updates(ticker_name, db_connection):
        query = "SELECT dataset, last_updated FROM data_updates WHERE ticker=%(ticker_name)s"

        with db_connection.connect() as connection:
            df_updates = pd.read_sql_query(query,
                                           params={"ticker_name": ticker_name},
                                           con=connection)

        return {row['dataset']: pd.to_datetime(row['last_updated'], utc=True)
                for _, row in df_updates.iterrows()}

    @staticmethod
    def add_data_update(ticker_name, table_name, db_connection):
        UPSERT_ENTRY = text("INSERT INTO {} (ticker, dataset, last_updated) "
                            "VALUES (:ticker_name, :dataset_name, :last_updated) "
                            "ON CONFLICT (ticker, dataset) DO UPDATE "
                            "SET last_updated = EXCLUDED.last_updated".format(TABLE_NAME_DATA_UPDATES))
        with db_connection.begin() as connection:
            connection.execute(UPSERT_ENTRY, {'ticker_name': ticker_name,
                                              'dataset_name': table_name,
                                              'last_updated': datetime.now(timezone.utc)})
        print('Updated {} for {} and {}.'.format(TABLE_NAME_DATA_UPDATES, ticker_name, table_name))

    @staticmethod
    def get_last_update(ticker_name, table_name, db_connection):
        return DataUpdates.get_all_last_updates(ticker_name, db_connection).get(table_name)

    @staticmethod
    def check_needs_update(table_name, last_update_datetime):
        needs_update = True
        if last_update_datetime == None:
            needs_update = True
        elif last_update_datetime.date() == datetime.now(timezone.utc).date():
            needs_update = False
        else:
            print("{} may be updated, {} vs {}.".format(table_name,
                                                        last_update_datetime,
                                                        datetime.now(timezone.utc).date()))
        return needs_update

    @staticmethod
    def remove_entry(ticker_name, dataset, db_connection):
        DELETE_ENTRY = text("DELETE FROM {} WHERE ticker=:ticker and dataset=:dataset;".format(TABLE_NAME_DATA_UPDATES))

        if dataset in TABLE_NAMES:
            with db_connection.begin() as connection:
                connection.execute(DELETE_ENTRY,
                                   {'ticker': ticker_name,
                                    'dataset': dataset})
            print("Deleted ({},{}) in {}.".format(ticker_name, dataset, TABLE_NAME_DATA_UPDATES))

        else:
            print("Invalid table name: {}".format(dataset))


class TableCompanies():
    def get_from(ticker_name, db_connection):
        """
            Get the latest row from 'companies' of the given ticker.
        """
        query_str = "SELECT * FROM {} WHERE ticker = '{}';".format(TABLE_COMPANIES_NAME, ticker_name)
        with db_connection.connect() as connection:
            df_company = pd.read_sql_query(query_str, con=connection)
        return df_company

    def add(ticker_name, db_connection):
        """
            Pull the OVERVIEW from AlphaVantage, save it to a local JSON,
            and push it to the 'companies' table.
        """
        overview_path = SAVED_JSON_PATH.format(ticker_name, OVERVIEW_FUNCTION_NAME)
        overview_json = request_data(OVERVIEW_FUNCTION_NAME, ticker_name)
        # time.sleep(1)

        if 'Symbol' in overview_json:
            Path('data/AlphaVantage/{}'.format(ticker_name)).mkdir(exist_ok=True)
            with open(overview_path, 'w') as export_json_file:
                json.dump(overview_json, export_json_file, indent=4)
        else:
            print('WARNING: Import of {} failed.  {}.  Pulling from saved file if exists.'.format(OVERVIEW_FUNCTION_NAME, overview_json))

        with open(overview_path, 'r') as overview_file_json:
            overview_json = json.load(overview_file_json)
            df_overview = pd.DataFrame([overview_json])
            df_overview.rename(columns={
                'Symbol': 'ticker',
                'Name': 'company_name',
                'Sector': 'sector',
                'Industry': 'industry',
                'Exchange': 'exchange',
                'Country': 'country',
                'MarketCapitalization': 'market_cap_latest'
            }, inplace=True)
            df_overview['market_cap_latest'] = df_overview['market_cap_latest'].astype(float)

            UPSERT_ENTRY = text("INSERT INTO {} (ticker, " \
                                "company_name, " \
                                "sector, " \
                                "industry," \
                                "exchange," \
                                "country," \
                                "market_cap_latest) "
                                "VALUES (:ticker, " \
                                ":company_name, " \
                                ":sector," \
                                ":industry," \
                                ":exchange," \
                                ":country," \
                                ":market_cap_latest) "
                                "ON CONFLICT (ticker) DO UPDATE "
                                "SET " \
                                "company_name = EXCLUDED.company_name, " \
                                "sector = EXCLUDED.sector, " \
                                "industry = EXCLUDED.industry, " \
                                "exchange = EXCLUDED.exchange, " \
                                "country = EXCLUDED.country, " \
                                "market_cap_latest = EXCLUDED.market_cap_latest".format(TABLE_COMPANIES_NAME))
            with db_connection.begin() as connection:
                connection.execute(UPSERT_ENTRY, {'ticker': overview_json['Symbol'],
                                                  'company_name': overview_json['Name'],
                                                  'sector': overview_json['Sector'],
                                                  'industry': overview_json['Industry'],
                                                  'exchange': overview_json['Exchange'],
                                                  'country': overview_json['Country'],
                                                  'market_cap_latest': float(overview_json['MarketCapitalization'])})

            DataUpdates.add_data_update(ticker_name, TABLE_COMPANIES_NAME, db_connection)
            print('Added row for {} to table {}.'.format(ticker_name, TABLE_COMPANIES_NAME))

        return df_overview[list(TABLE_COMPANIES_DICT)]

class TableFundamentals():
    def get_from(ticker_name, db_connection, minimum_date:datetime = None):
        """
            Get all rows from 'fundamentals' of the given ticker.
        """
        query_str = "SELECT * FROM {} WHERE ticker = '{}'".format(TABLE_NAME_FUNDAMENTALS, ticker_name)

        if minimum_date != None:
            min_date_str = minimum_date.strftime("%Y-%m-%d")
            query_str += " AND (date >= '{}' OR date = " \
                         "(SELECT MAX(date) FROM {} WHERE ticker = '{}' AND date < '{}'))".format(min_date_str,
                                                                                                   TABLE_NAME_FUNDAMENTALS,
                                                                                                   ticker_name,
                                                                                                   min_date_str)

        with db_connection.connect() as connection:
            df_fundamentals = pd.read_sql_query(query_str, con=connection)
            df_fundamentals['date'] = pd.to_datetime(df_fundamentals['date'])
            df_fundamentals = df_fundamentals.sort_values('date')
        return df_fundamentals

    def append(ticker_name, df_fundamentals, db_connection):
        """
            Insert new rows from df_fundamentals into 'fundamentals'.
        """
        if df_fundamentals.empty:
            print('No new rows for {} and {}.'.format(TABLE_NAME_FUNDAMENTALS, ticker_name))
        else:
            data_dicts = df_fundamentals[['ticker',
                                          'date',
                                          'total_revenue',
                                          'cost_of_revenue',
                                          'operating_income',
                                          'net_income',
                                          'income_before_tax',
                                          'income_tax_expense',
                                          'operating_cash_flow',
                                          'capex',
                                          'total_debt',
                                          'cash',
                                          'shareholder_equity']].to_dict(orient='records')
            insert_statement = INSERT_STATEMENT_FUNDAMENTALS
            with db_connection.begin() as connection:
                connection.execute(insert_statement, data_dicts)
                print('Added {} for {}.'.format(TABLE_NAME_FUNDAMENTALS, ticker_name))
        DataUpdates.add_data_update(ticker_name, TABLE_NAME_FUNDAMENTALS, db_connection)

    def update(ticker_name, db_connection, minimum_date:datetime = None):
        """
            Pull BALANCE_SHEET, CASH_FLOW, and INCOME_STATMENT from AlphaVantage.
            Write them to local JSON files and push the new dataframe rows
            to the 'fundamentals' and 'operational_metrics' tables.
        """
        FUNCTIONS_TO_UPDATE = [BALANCE_SHEET_FUNCTION_NAME,
                            CASH_FLOW_FUNCTION_NAME,
                            INCOME_STATEMENT_FUNCTION_NAME]
        for function_name in FUNCTIONS_TO_UPDATE:
            function_path = SAVED_JSON_PATH.format(ticker_name, function_name)
            function_json = request_data(function_name, ticker_name)
            # time.sleep(1)
            if 'symbol' in function_json:
                Path('data/AlphaVantage/{}'.format(ticker_name)).mkdir(exist_ok=True)
                with open(function_path, 'w') as export_json_file:
                    json.dump(function_json, export_json_file, indent=4)
            else:
                print('WARNING: Import of {} failed.  {}\r\n.  ' \
                'Pulling from saved file if exists.'.format(function_name, function_json))

        df_fundamentals = get_saved_fundamentals(ticker_name)
        df_fundamentals['ticker'] = ticker_name

        check_latest_date = "SELECT MAX (date) FROM {} WHERE ticker=%(ticker_name)s;".format(TABLE_NAME_FUNDAMENTALS)
        df_latest_date = pd.read_sql_query(check_latest_date,
                                            params={"ticker_name": ticker_name},
                                            con=db_connection)
        if df_latest_date['max'].iloc[0] == None:
            df_fundamentals = df_fundamentals[df_fundamentals['date'] >= minimum_date]
        else:
            latest_date = pd.to_datetime(df_latest_date['max']).iloc[0]
            df_fundamentals = df_fundamentals[df_fundamentals['date'] > latest_date]
        TableFundamentals.append(ticker_name, df_fundamentals, db_connection)

        return df_fundamentals

class TableOperationalMetrics():
    def get_from(ticker_name, db_connection, minimum_date:datetime = None):
        """
            Get all rows from 'operational_metrics' of the given ticker.
        """
        query_str = "SELECT * FROM {} WHERE ticker = '{}'".format(TABLE_NAME_OPERATIONAL_METRICS, ticker_name)

        if minimum_date != None:
            min_date_str = minimum_date.strftime("%Y-%m-%d")
            query_str += " AND (date >= '{}' OR date = " \
                         "(SELECT MAX(date) FROM {} WHERE ticker = '{}' AND date < '{}'))".format(min_date_str,
                                                                                                   TABLE_NAME_OPERATIONAL_METRICS,
                                                                                                   ticker_name,
                                                                                                   min_date_str)

        with db_connection.connect() as connection:
            df_operational_metrics = pd.read_sql_query(query_str, con=connection)
            df_operational_metrics['date'] = pd.to_datetime(df_operational_metrics['date'])
            df_operational_metrics = df_operational_metrics.sort_values('date')
        return df_operational_metrics

    def append(ticker_name, df_operational_metrics, db_connection):
        """
            Insert new rows from df_operational_metrics into 'operational_metrics'.
        """
        if df_operational_metrics.empty:
            print('No new rows for {} and {}.'.format(TABLE_NAME_OPERATIONAL_METRICS, ticker_name))
        else:
            data_dicts = df_operational_metrics[['ticker',
                                                'date',
                                                'roic',
                                                'roe',
                                                'debt_to_equity',
                                                'nopat',
                                                'gross_margin',
                                                'operating_margin',
                                                'net_margin',
                                                'ocf_margin',
                                                'fcf_margin',
                                                'revenue_growth_yoy',
                                                'ttm_roic',
                                                'ttm_net_income',
                                                'ttm_operating_income',
                                                'ttm_fcf',
                                                'ttm_operating_margin',
                                                'ttm_net_margin',
                                                'ttm_fcf_margin',
                                                'ttm_ocf_margin']].to_dict(orient='records')
            insert_statement = INSERT_STATEMENT_OPERATIONAL_METRICS
            with db_connection.begin() as connection:
                connection.execute(insert_statement, data_dicts)
                print('Added {} for {}.'.format(TABLE_NAME_OPERATIONAL_METRICS, ticker_name))
        DataUpdates.add_data_update(ticker_name, TABLE_NAME_OPERATIONAL_METRICS, db_connection)

    def update(ticker_name, db_connection):
        """
            Update 'operational_metrics' table from the latest 'fundamentals' table.
        """
        df_fundamentals = TableFundamentals.get_from(ticker_name, db_connection)

        operational_metrics = calculate_operational_metrics(df_fundamentals)
        operational_metrics['ticker'] = ticker_name

        # Push to the tables
        DELETE_ALL = text("DELETE FROM {} WHERE ticker=:ticker".format(TABLE_NAME_OPERATIONAL_METRICS,
                                                                       ticker_name))
        with db_connection.begin() as connection:
            connection.execute(DELETE_ALL,
                               {'ticker': ticker_name})
        TableOperationalMetrics.append(ticker_name, operational_metrics, db_connection)

        return operational_metrics

class TableSharesOutstanding():
    def get_from(ticker_name, db_connection, minimum_date:datetime = None):
        """
            Get all rows from 'shares_outstanding' of the given ticker.
        """
        query_str = "SELECT * FROM {} WHERE ticker = '{}'".format(TABLE_NAME_SHARES_OUTSTANDING, ticker_name)

        if minimum_date != None:
            min_date_str = minimum_date.strftime("%Y-%m-%d")
            query_str += " AND (date >= '{}' OR date = " \
                         "(SELECT MAX(date) FROM {} WHERE ticker = '{}' AND date < '{}'))".format(min_date_str,
                                                                                                   TABLE_NAME_SHARES_OUTSTANDING,
                                                                                                   ticker_name,
                                                                                                   min_date_str)

        with db_connection.connect() as connection:
            df_shares_outstanding = pd.read_sql_query(query_str, con=connection)
            df_shares_outstanding['date'] = pd.to_datetime(df_shares_outstanding['date'])
        return df_shares_outstanding

    def append(ticker_name, df_shares_outstanding, db_connection):
        """
            Insert new rows from df_shares_outstanding into 'shares_outstanding'.
        """
        if df_shares_outstanding.empty:
            print('No new rows for {} and {}.'.format(TABLE_NAME_SHARES_OUTSTANDING, ticker_name))
        else:
            df_shares_outstanding_copy = df_shares_outstanding.copy()
            df_shares_outstanding_copy['ticker'] = ticker_name
            data_dicts = df_shares_outstanding_copy[['ticker',
                                                     'date',
                                                     'basic_shares',
                                                     'diluted_shares']].to_dict(orient='records')
            insert_statement = INSERT_STATEMENT_SHARES_OUTSTANDING
            with db_connection.begin() as connection:
                connection.execute(insert_statement, data_dicts)
        DataUpdates.add_data_update(ticker_name, TABLE_NAME_SHARES_OUTSTANDING, db_connection)

    def update(ticker_name, db_connection, minimum_date:datetime = None):
        """
            Pull SHARES_OUTSTANDING from AlphaVantage.
            Write them to a local JSON file and push the new dataframe rows to 'shares_outstanding'.
        """
        function_path = SAVED_JSON_PATH.format(ticker_name, SHARES_OUTSTANDING_FUNCTION_NAME)
        function_json = request_data(SHARES_OUTSTANDING_FUNCTION_NAME, ticker_name)
        # time.sleep(1)
        if 'symbol' in function_json:
            Path('data/AlphaVantage/{}'.format(ticker_name)).mkdir(exist_ok=True)
            with open(function_path, 'w') as export_json_file:
                json.dump(function_json, export_json_file, indent=4)
        else:
            print('WARNING: Import of {} failed.  {}\r\n.  ' \
            'Pulling from saved file if exists.'.format(SHARES_OUTSTANDING_FUNCTION_NAME, function_json))

        df_shares_outstanding = get_shares_outstanding(ticker_name)
        check_latest_date = "SELECT MAX (date) FROM {} WHERE ticker=%(ticker_name)s;".format(TABLE_NAME_SHARES_OUTSTANDING)
        df_latest_date = pd.read_sql_query(check_latest_date,
                                            params={"ticker_name": ticker_name},
                                            con=db_connection)
        if df_latest_date['max'].iloc[0] == None:
            df_shares_outstanding = df_shares_outstanding[df_shares_outstanding['date'] >= minimum_date]
        else:
            latest_date = pd.to_datetime(df_latest_date['max']).iloc[0]
            df_shares_outstanding = df_shares_outstanding[df_shares_outstanding['date'] > latest_date]
        TableSharesOutstanding.append(ticker_name, df_shares_outstanding, db_connection)

        return df_shares_outstanding

class TablePricesWeekly():
    def get_latest_date(ticker_name, db_connection):
        latest_date = None
        check_latest_date = "SELECT MAX (date) FROM {} WHERE ticker=%(ticker_name)s;".format(TABLE_NAME_PRICES_WEEKLY)
        df_latest_date = pd.read_sql_query(check_latest_date,
                                            params={"ticker_name": ticker_name},
                                            con=db_connection)
        if df_latest_date['max'].iloc[0] != None:
            latest_date = pd.to_datetime(df_latest_date['max'], utc=True).iloc[0]
        return latest_date

    def get_from(ticker_name, db_connection, minimum_date:datetime = None):
        """
            Get all rows from 'prices_weekly' of the given ticker.
        """
        query_str = "SELECT * FROM {} WHERE ticker = '{}'".format(TABLE_NAME_PRICES_WEEKLY, ticker_name)

        if minimum_date != None:
            query_str += " AND date >= '{}'".format(minimum_date.strftime("%Y-%m-%d"))

        with db_connection.connect() as connection:
            df_prices_weekly = pd.read_sql_query(query_str, con=connection)
            df_prices_weekly['date'] = pd.to_datetime(df_prices_weekly['date'])
            df_prices_weekly = df_prices_weekly.sort_values('date')
        return df_prices_weekly

    def append(ticker_name, df_prices_weekly, db_connection):
        """
            Append rows to 'prices_weekly' of the given ticker.
        """
        if df_prices_weekly.empty:
            print('No new rows for {} and {}.'.format(TABLE_NAME_PRICES_WEEKLY, ticker_name))
        else:
            df_prices_weekly = df_prices_weekly.copy()
            df_prices_weekly['ticker'] = ticker_name
            data_dicts = df_prices_weekly[['ticker',
                                           'date',
                                           'adjusted_close',
                                           'volume']].to_dict(orient='records')
            insert_statement = INSERT_STATEMENT_PRICES_WEEKLY
            with db_connection.begin() as connection:
                connection.execute(insert_statement, data_dicts)
        DataUpdates.add_data_update(ticker_name, TABLE_NAME_PRICES_WEEKLY, db_connection)

    def update(ticker_name, db_connection, minimum_date:datetime = None):
        """
            Pull TIMER_SERIES_WEEKLY_ADJUSTED from AlphaVantage.
            Write them to a local JSON file and push the new dataframe rows to 'prices_weekly'.
        """
        function_path = SAVED_JSON_PATH.format(ticker_name, PRICES_WEEKLY_FUNCTION_NAME)
        function_json = request_data(PRICES_WEEKLY_FUNCTION_NAME, ticker_name)
        # time.sleep(1)
        if 'Weekly Adjusted Time Series' in function_json:
            Path('data/AlphaVantage/{}'.format(ticker_name)).mkdir(exist_ok=True)
            with open(function_path, 'w') as export_json_file:
                json.dump(function_json, export_json_file, indent=4)
        else:
            print('WARNING: Import of {} failed.  {}\r\n.  ' \
            'Pulling from saved file if exists.'.format(PRICES_WEEKLY_FUNCTION_NAME, function_json))

        df_prices_weekly = get_timeseries_weekly_adjusted(ticker_name)
        check_latest_date = "SELECT MAX (date) FROM {} WHERE ticker=%(ticker_name)s;".format(TABLE_NAME_PRICES_WEEKLY)
        df_latest_date = pd.read_sql_query(check_latest_date,
                                            params={"ticker_name": ticker_name},
                                            con=db_connection)
        if df_latest_date['max'].iloc[0] == None:
            df_prices_weekly = df_prices_weekly[df_prices_weekly['date'] >= minimum_date]
        else:
            latest_date = pd.to_datetime(df_latest_date['max']).iloc[0]
            df_prices_weekly = df_prices_weekly[df_prices_weekly['date'] > latest_date]
        TablePricesWeekly.append(ticker_name, df_prices_weekly, db_connection)

class TableValuationMetrics():
    def get_latest_date(ticker_name, db_connection):
        latest_date = None
        check_latest_date = "SELECT MAX (date) FROM {} WHERE ticker=%(ticker_name)s;".format(TABLE_NAME_VALUATION_METRICS)
        df_latest_date = pd.read_sql_query(check_latest_date,
                                            params={"ticker_name": ticker_name},
                                            con=db_connection)
        if df_latest_date['max'].iloc[0] != None:
            latest_date = pd.to_datetime(df_latest_date['max'], utc=True).iloc[0]
        return latest_date

    def get_from(ticker_name, db_connection, minimum_date:datetime = None):
        """
            Get all rows from 'valuation_metrics' of the given ticker.
        """
        query_str = "SELECT * FROM {} WHERE ticker = '{}'".format(TABLE_NAME_VALUATION_METRICS, ticker_name)

        if minimum_date != None:
            query_str += " AND date >= '{}'".format(minimum_date.strftime("%Y-%m-%d"))

        with db_connection.connect() as connection:
            df_valuation_metrics = pd.read_sql_query(query_str, con=connection)
            df_valuation_metrics['date'] = pd.to_datetime(df_valuation_metrics['date'])
            df_valuation_metrics = df_valuation_metrics.sort_values('date')
        return df_valuation_metrics

    def append(ticker_name, df_valuation_metrics, db_connection):
        """
            Append rows to 'valuation_metrics' of the given ticker.
        """
        if df_valuation_metrics.empty:
            print('No new rows for {} and {}.'.format(TABLE_NAME_VALUATION_METRICS, ticker_name))
        else:
            df_valuation_metrics = df_valuation_metrics.copy()
            df_valuation_metrics['ticker'] = ticker_name
            data_dicts = df_valuation_metrics[['ticker',
                                               'date',
                                               'market_cap',
                                               'enterprise_value',
                                               'pe_ttm',
                                               'pfcf',
                                               'ev_ebit',
                                               'ev_fcf',
                                               'ev_nopat']].to_dict(orient='records')
            insert_statement = INSERT_STATEMENT_VALUATION_METRICS
            with db_connection.begin() as connection:
                connection.execute(insert_statement, data_dicts)
                print('Added {} for {}.'.format(TABLE_NAME_VALUATION_METRICS, ticker_name))
        DataUpdates.add_data_update(ticker_name, TABLE_NAME_VALUATION_METRICS, db_connection)

    def update(ticker_name, db_connection):
        """
            Read from 'fundamentals', 'operational_metrics', 'prices_weekly', and 'shares_outstanding'.
            Update 'valuation_metrics' rows of the ticker.
        """
        latest_date = TableValuationMetrics.get_latest_date(ticker_name, db_connection)
        minimum_date = None

        if latest_date != None:
            minimum_date = latest_date.replace(tzinfo=None)

        df_fundamentals = TableFundamentals.get_from(ticker_name, db_connection, minimum_date)
        df_operational_metrics = TableOperationalMetrics.get_from(ticker_name, db_connection, minimum_date)
        df_prices_weekly = TablePricesWeekly.get_from(ticker_name, db_connection, minimum_date)
        df_shares_outstanding = TableSharesOutstanding.get_from(ticker_name, db_connection, minimum_date)
        df_operational_metrics = pd.merge(df_fundamentals, df_operational_metrics, on='date')
        df_valuation_metrics = calculate_valuation_metrics(df_operational_metrics,
                                                           df_prices_weekly,
                                                           df_shares_outstanding)
        if latest_date != None:
            df_valuation_metrics = df_valuation_metrics[df_valuation_metrics['date'] > minimum_date]
        TableValuationMetrics.append(ticker_name, df_valuation_metrics, db_connection)

def add_update_ticker(ticker_name, db_connection, minimum_date:datetime = None):
    """
        Add and/or update DB data of the given ticker.
    """
    need_to_update_valuation_metrics = False
    last_updates = DataUpdates.get_all_last_updates(ticker_name, db_connection)

    last_update = last_updates.get(TABLE_COMPANIES_NAME)
    needs_updated = DataUpdates.check_needs_update(TABLE_COMPANIES_NAME, last_update)
    if(needs_updated == True):
        try:
            TableCompanies.add(ticker_name, db_connection)
        except FileNotFoundError as e:
            print(e)
    else:
        print('Already have entry in {} for {}.'.format(TABLE_COMPANIES_NAME, ticker_name))

    last_updated_fundamentals = last_updates.get(TABLE_NAME_FUNDAMENTALS)
    last_update_operational_metrics = last_updates.get(TABLE_NAME_OPERATIONAL_METRICS)
    if((DataUpdates.check_needs_update(TABLE_NAME_FUNDAMENTALS,
                                       last_updated_fundamentals) == True) or
    (DataUpdates.check_needs_update(TABLE_NAME_OPERATIONAL_METRICS,
                                    last_update_operational_metrics) == True)):
        try:
            TableFundamentals.update(ticker_name, db_connection, minimum_date)
            TableOperationalMetrics.update(ticker_name, db_connection)
            need_to_update_valuation_metrics = True
        except FileNotFoundError as e:
            print(e)
    else:
        print('Already have entry in {} or {} for {}.'.format(TABLE_NAME_FUNDAMENTALS,
                                                            TABLE_NAME_OPERATIONAL_METRICS,
                                                            ticker_name))

    last_update = last_updates.get(TABLE_NAME_SHARES_OUTSTANDING)
    needs_updated = DataUpdates.check_needs_update(TABLE_NAME_SHARES_OUTSTANDING, last_update)
    if(needs_updated == True):
        try:
            TableSharesOutstanding.update(ticker_name, db_connection, minimum_date)
            need_to_update_valuation_metrics = True
        except FileNotFoundError as e:
            print(e)
    else:
        print('Already have entry in {} for {}.'.format(TABLE_NAME_SHARES_OUTSTANDING, ticker_name))

    last_update = last_updates.get(TABLE_NAME_PRICES_WEEKLY)
    needs_updated = DataUpdates.check_needs_update(TABLE_NAME_PRICES_WEEKLY, last_update)
    if(needs_updated == True):
        try:
            TablePricesWeekly.update(ticker_name, db_connection, minimum_date)
            need_to_update_valuation_metrics = True
        except FileNotFoundError as e:
            print(e)
    else:
        print('Already have entry in {} for {}.'.format(TABLE_NAME_PRICES_WEEKLY, ticker_name))

    last_update = last_updates.get(TABLE_NAME_VALUATION_METRICS)
    needs_updated = DataUpdates.check_needs_update(TABLE_NAME_VALUATION_METRICS, last_update)
    if (need_to_update_valuation_metrics == True) or (needs_updated == True):
        TableValuationMetrics.update(ticker_name, db_connection)
    else:
        print('Aleady have entries in {} for {}.'.format(TABLE_NAME_VALUATION_METRICS, ticker_name))

def force_update_ticker(ticker_name, table_name, db_connection):
    DataUpdates.remove_entry(ticker_name, table_name, db_connection)
    add_update_ticker(ticker_name, db_connection)

def main():
    parser = argparse.ArgumentParser(prog='TickerData.py', description='Organize ticker data.')
    parser.add_argument('-t', '--ticker', required=True, help='Stock ticker')
    parser.add_argument('-u', '--force_update_table', required=False, default=None, help='Force the update of the given table of a ticker.')

    args = parser.parse_args()
    db_connection = get_db_connection()

    if args.force_update_table:
        force_update_ticker(args.ticker, args.force_update_table, db_connection)

if __name__ == "__main__":
    main()
