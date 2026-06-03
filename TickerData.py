"""
    Read, update ticker data.
"""

from RequestAndSave import request_json
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
from datetime import datetime, timezone, timedelta
import time
import argparse

SAVED_JSON_PATH = 'data/{}/{}.json'

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
    def add_data_update(ticker_name, table_name, db_connection):
        CHECK_ENTRY = "SELECT * FROM data_updates WHERE ticker=%(ticker_name)s AND dataset=%(table_name)s"

        with db_connection.begin() as connection:
            df_check = pd.read_sql_query(CHECK_ENTRY, params={"ticker_name": ticker_name, "table_name": table_name}, con=connection)
            if len(df_check):
                # Update the entry
                UPDATE_ENTRY = text("UPDATE {} SET last_updated = :new_last_updated WHERE ticker = :ticker AND dataset = :dataset_name".format(TABLE_NAME_DATA_UPDATES))
                connection.execute(UPDATE_ENTRY, {'new_last_updated': datetime.now(timezone.utc),
                                                'ticker': ticker_name,
                                                'dataset_name': table_name})
                print('Updated {} for {} and {}.'.format(TABLE_NAME_DATA_UPDATES, ticker_name, table_name))
            else:
                # Add a new entry
                ADD_ENTRY = text("INSERT INTO {} (ticker, dataset, last_updated)" \
                "VALUES (:ticker_name, :dataset_name, :last_updated)".format(TABLE_NAME_DATA_UPDATES))
                connection.execute(ADD_ENTRY, {'ticker_name': ticker_name,
                                            'dataset_name': table_name,
                                            'last_updated': datetime.now(timezone.utc)})
                print('Added {} for {} and {}.'.format(TABLE_NAME_DATA_UPDATES, ticker_name, table_name))

    @staticmethod
    def get_last_update(ticker_name, table_name, db_connection):
        CHECK_ENTRY = "SELECT last_updated FROM data_updates WHERE ticker=%(ticker_name)s AND dataset=%(table_name)s"

        df_check = pd.DataFrame()
        with db_connection.begin() as connection:
            df_check = pd.read_sql_query(CHECK_ENTRY, params={"ticker_name": ticker_name, "table_name": table_name}, con=connection)
        try:
            last_updated = pd.to_datetime(df_check['last_updated'].iloc[0], utc=True)
        except:
            last_updated = None
        return last_updated

    @staticmethod
    def check_needs_update(table_name, last_update_datetime):
        recency = RECENCY[table_name]
        needs_update = True
        if last_update_datetime != None:
            datetime_delta = datetime.now(timezone.utc) - last_update_datetime
            needs_update = False
            if recency == 'quarter':
                needs_update = True if datetime_delta >= timedelta(days=90) else False
            elif recency == 'week':
                needs_update = True if datetime_delta > timedelta(days=7) else False
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
        overview_json = request_json(OVERVIEW_FUNCTION_NAME, ticker_name)

        if 'Symbol' in overview_json:
            Path('data/{}'.format(ticker_name)).mkdir(exist_ok=True)
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

            df_overview[list(TABLE_COMPANIES_DICT)].to_sql(name=TABLE_COMPANIES_NAME,
                                                            con=db_connection,
                                                            if_exists='append',
                                                            index=False)
            DataUpdates.add_data_update(ticker_name, TABLE_COMPANIES_NAME, db_connection)
            print('Added row for {} to table {}.'.format(ticker_name, TABLE_COMPANIES_NAME))

        return df_overview[list(TABLE_COMPANIES_DICT)]

class TableFundamentals():
    def get_from(ticker_name, db_connection):
        """
            Get all rows from 'fundamentals' of the given ticker.
        """
        query_str = "SELECT * FROM {} WHERE ticker = '{}';".format(TABLE_NAME_FUNDAMENTALS, ticker_name)
        with db_connection.connect() as connection:
            df_fundamentals = pd.read_sql_query(query_str, con=connection)
            df_fundamentals['date'] = pd.to_datetime(df_fundamentals['date'])
            df_fundamentals = df_fundamentals.sort_values('date')
        return df_fundamentals

    def append(ticker_name, df_fundamentals, db_connection):
        """
            Insert new rows from df_fundamentals into 'fundamentals'.
        """
        with db_connection.begin() as connection:
            for index, row in df_fundamentals.iterrows():
                insert_statement = INSERT_STATEMENT_FUNDAMENTALS
                connection.execute(insert_statement, {
                    'ticker': row['ticker'],
                    'date': row['date'],
                    'total_revenue': float(row['total_revenue']),
                    'cost_of_revenue': float(row['cost_of_revenue']),
                    'operating_income': float(row['operating_income']),
                    'net_income': float(row['net_income']),
                    'income_before_tax': float(row['income_before_tax']),
                    'income_tax_expense': float(row['income_tax_expense']),
                    'operating_cash_flow': float(row['operating_cash_flow']),
                    'capex': float(row['capex']),
                    'total_debt': float(row['total_debt']),
                    'cash': float(row['cash']),
                    'shareholder_equity': float(row['shareholder_equity'])
                })
            print('Added {} for {}.'.format(TABLE_NAME_FUNDAMENTALS, ticker_name))
        DataUpdates.add_data_update(ticker_name, TABLE_NAME_FUNDAMENTALS, db_connection)

    def update(ticker_name, db_connection):
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
            function_json = request_json(function_name, ticker_name)
            time.sleep(1)
            if 'symbol' in function_json:
                Path('data/{}'.format(ticker_name)).mkdir(exist_ok=True)
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
            pass
        else:
            latest_date = pd.to_datetime(df_latest_date['max']).iloc[0]
            df_fundamentals = df_fundamentals[df_fundamentals['date'] > latest_date]
        TableFundamentals.append(ticker_name, df_fundamentals, db_connection)

        return df_fundamentals

class TableOperationalMetrics():
    def get_from(ticker_name, db_connection):
        """
            Get all rows from 'operational_metrics' of the given ticker.
        """
        query_str = "SELECT * FROM {} WHERE ticker = '{}';".format(TABLE_NAME_OPERATIONAL_METRICS, ticker_name)
        with db_connection.connect() as connection:
            df_operational_metrics = pd.read_sql_query(query_str, con=connection)
            df_operational_metrics['date'] = pd.to_datetime(df_operational_metrics['date'])
            df_operational_metrics = df_operational_metrics.sort_values('date')
        return df_operational_metrics

    def append(ticker_name, df_operational_metrics, db_connection):
        """
            Insert new rows from df_operational_metrics into 'operational_metrics'.
        """
        with db_connection.begin() as connection:
            for index, row in df_operational_metrics.iterrows():
                insert_statement = INSERT_STATEMENT_OPERATIONAL_METRICS
                connection.execute(insert_statement, {
                    'ticker': row['ticker'],
                    'date': row['date'],
                    'roic': float(row['roic']),
                    'roe': float(row['roe']),
                    'debt_to_equity': float(row['debt_to_equity']),
                    'nopat': float(row['nopat']),
                    'gross_margin': float(row['gross_margin']),
                    'operating_margin': float(row['operating_margin']),
                    'net_margin': float(row['net_margin']),
                    'ocf_margin': float(row['ocf_margin']),
                    'fcf_margin': float(row['fcf_margin']),
                    'revenue_growth_yoy': float(row['revenue_growth_yoy']),
                    'ttm_roic': float(row['ttm_roic']),
                    'ttm_net_income': float(row['ttm_net_income']),
                    'ttm_operating_income': float(row['ttm_operating_income']),
                    'ttm_fcf': float(row['ttm_fcf']),
                    'ttm_operating_margin': float(row['ttm_operating_margin']),
                    'ttm_net_margin': float(row['ttm_net_margin']),
                    'ttm_fcf_margin': float(row['ttm_fcf_margin']),
                    'ttm_ocf_margin': float(row['ttm_ocf_margin'])
                })
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
    def get_from(ticker_name, db_connection):
        """
            Get all rows from 'shares_outstanding' of the given ticker.
        """
        query_str = "SELECT * FROM {} WHERE ticker = '{}';".format(TABLE_NAME_SHARES_OUTSTANDING, ticker_name)
        with db_connection.connect() as connection:
            df_shares_outstanding = pd.read_sql_query(query_str, con=connection)
            df_shares_outstanding['date'] = pd.to_datetime(df_shares_outstanding['date'])
        return df_shares_outstanding

    def append(ticker_name, df_shares_outstanding, db_connection):
        """
            Insert new rows from df_shares_outstanding into 'shares_outstanding'.
        """
        with db_connection.begin() as connection:
            for index, row in df_shares_outstanding.iterrows():
                insert_statement = INSERT_STATEMENT_SHARES_OUTSTANDING
                connection.execute(insert_statement, {
                    'ticker': ticker_name,
                    'date': row['date'],
                    'basic_shares': row['basic_shares'],
                    'diluted_shares': row['diluted_shares']
                })
            print('Added {} for {}.'.format(TABLE_NAME_SHARES_OUTSTANDING, ticker_name))
        DataUpdates.add_data_update(ticker_name, TABLE_NAME_SHARES_OUTSTANDING, db_connection)

    def update(ticker_name, db_connection):
        """
            Pull SHARES_OUTSTANDING from AlphaVantage.
            Write them to a local JSON file and push the new dataframe rows to 'shares_outstanding'.
        """
        function_path = SAVED_JSON_PATH.format(ticker_name, SHARES_OUTSTANDING_FUNCTION_NAME)
        function_json = request_json(SHARES_OUTSTANDING_FUNCTION_NAME, ticker_name)
        time.sleep(1)
        if 'symbol' in function_json:
            Path('data/{}'.format(ticker_name)).mkdir(exist_ok=True)
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
            pass
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

    def get_from(ticker_name, db_connection):
        """
            Get all rows from 'prices_weekly' of the given ticker.
        """
        query_str = "SELECT * FROM {} WHERE ticker = '{}';".format(TABLE_NAME_PRICES_WEEKLY, ticker_name)
        with db_connection.connect() as connection:
            df_prices_weekly = pd.read_sql_query(query_str, con=connection)
            df_prices_weekly['date'] = pd.to_datetime(df_prices_weekly['date'])
            df_prices_weekly = df_prices_weekly.sort_values('date')
        return df_prices_weekly

    def append(ticker_name, df_prices_weekly, db_connection):
        """
            Append rows to 'prices_weekly' of the given ticker.
        """
        with db_connection.begin() as connection:
            for index, row in df_prices_weekly.iterrows():
                insert_statement = INSERT_STATEMENT_PRICES_WEEKLY
                connection.execute(insert_statement, {
                    'ticker': ticker_name,
                    'date': row['date'],
                    'adjusted_close': row['adjusted_close'],
                    'volume': row['volume']
                })
            print('Added {} for {}.'.format(TABLE_NAME_PRICES_WEEKLY, ticker_name))
        DataUpdates.add_data_update(ticker_name, TABLE_NAME_PRICES_WEEKLY, db_connection)

    def update(ticker_name, db_connection):
        """
            Pull TIMER_SERIES_WEEKLY_ADJUSTED from AlphaVantage.
            Write them to a local JSON file and push the new dataframe rows to 'prices_weekly'.
        """
        function_path = SAVED_JSON_PATH.format(ticker_name, PRICES_WEEKLY_FUNCTION_NAME)
        function_json = request_json(PRICES_WEEKLY_FUNCTION_NAME, ticker_name)
        time.sleep(1)
        if 'Weekly Adjusted Time Series' in function_json:
            Path('data/{}'.format(ticker_name)).mkdir(exist_ok=True)
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
            pass
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

    def get_from(ticker_name, db_connection):
        """
            Get all rows from 'valuation_metrics' of the given ticker.
        """
        query_str = "SELECT * FROM {} WHERE ticker = '{}';".format(TABLE_NAME_VALUATION_METRICS, ticker_name)
        with db_connection.connect() as connection:
            df_valuation_metrics = pd.read_sql_query(query_str, con=connection)
            df_valuation_metrics['date'] = pd.to_datetime(df_valuation_metrics['date'])
            df_valuation_metrics = df_valuation_metrics.sort_values('date')
        return df_valuation_metrics

    def append(ticker_name, df_valuation_metrics, db_connection):
        """
            Append rows to 'valuation_metrics' of the given ticker.
        """
        with db_connection.begin() as connection:
            for index, row in df_valuation_metrics.iterrows():
                insert_statement = INSERT_STATEMENT_VALUATION_METRICS
                connection.execute(insert_statement, {
                    'ticker': ticker_name,
                    'date': row['date'],
                    'market_cap': row['market_cap'],
                    'enterprise_value': row['enterprise_value'],
                    'pe_ttm': row['pe_ttm'],
                    'pfcf': row['pfcf'],
                    'ev_ebit': row['ev_ebit'],
                    'ev_fcf': row['ev_fcf'],
                    'ev_nopat': row['ev_nopat']
                })
            print('Added {} for {}.'.format(TABLE_NAME_VALUATION_METRICS, ticker_name))
        DataUpdates.add_data_update(ticker_name, TABLE_NAME_VALUATION_METRICS, db_connection)

    def update(ticker_name, db_connection):
        """
            Read from 'fundamentals', 'operational_metrics', 'prices_weekly', and 'shares_outstanding'.
            Update 'valuation_metrics' rows of the ticker.
        """
        df_fundamentals = TableFundamentals.get_from(ticker_name, db_connection)
        df_operational_metrics = TableOperationalMetrics.get_from(ticker_name, db_connection)
        df_prices_weekly = TablePricesWeekly.get_from(ticker_name, db_connection)
        df_shares_outstanding = TableSharesOutstanding.get_from(ticker_name, db_connection)
        df_operational_metrics = pd.merge(df_fundamentals, df_operational_metrics, on='date')
        df_valuation_metrics = calculate_valuation_metrics(df_operational_metrics,
                                                           df_prices_weekly,
                                                           df_shares_outstanding)
        DELETE_ALL = text("DELETE FROM {} WHERE ticker=:ticker".format(TABLE_NAME_VALUATION_METRICS,
                                                                       ticker_name))
        with db_connection.begin() as connection:
            connection.execute(DELETE_ALL,
                               {'ticker': ticker_name})
        TableValuationMetrics.append(ticker_name, df_valuation_metrics, db_connection)


def add_update_ticker(ticker_name, db_connection):
    """
        Add and/or update DB data of the given ticker.
    """
    need_to_update_valuation_metrics = False
    last_update = DataUpdates.get_last_update(ticker_name, TABLE_COMPANIES_NAME, db_connection)
    needs_updated = DataUpdates.check_needs_update(TABLE_COMPANIES_NAME, last_update)
    if(needs_updated == True):
        try:
            TableCompanies.add(ticker_name, db_connection)
        except FileNotFoundError as e:
            print(e)
    else:
        print('Already have entry in {} for {}.'.format(TABLE_COMPANIES_NAME, ticker_name))
    print(TableCompanies.get_from(ticker_name, db_connection))

    last_updated_fundamentals = DataUpdates.get_last_update(ticker_name,
                                                            TABLE_NAME_FUNDAMENTALS,
                                                            db_connection)
    last_update_operational_metrics = DataUpdates.get_last_update(ticker_name,
                                                                  TABLE_NAME_OPERATIONAL_METRICS,
                                                                  db_connection)
    if((DataUpdates.check_needs_update(TABLE_NAME_FUNDAMENTALS,
                                       last_updated_fundamentals) == True) or
    (DataUpdates.check_needs_update(TABLE_NAME_OPERATIONAL_METRICS,
                                    last_update_operational_metrics) == True)):
        try:
            TableFundamentals.update(ticker_name, db_connection)
            TableOperationalMetrics.update(ticker_name, db_connection)
            need_to_update_valuation_metrics = True
        except FileNotFoundError as e:
            print(e)
    else:
        print('Already have entry in {} or {} for {}.'.format(TABLE_NAME_FUNDAMENTALS,
                                                            TABLE_NAME_OPERATIONAL_METRICS,
                                                            ticker_name))
    # print(TableFundamentals.get_from(ticker_name, db_connection).to_string())
    # print(TableOperationalMetrics.get_from(ticker_name, db_connection).to_string())

    last_update = DataUpdates.get_last_update(ticker_name, TABLE_NAME_SHARES_OUTSTANDING, db_connection)
    needs_updated = DataUpdates.check_needs_update(TABLE_NAME_SHARES_OUTSTANDING, last_update)
    if(needs_updated == True):
        try:
            TableSharesOutstanding.update(ticker_name, db_connection)
            need_to_update_valuation_metrics = True
        except FileNotFoundError as e:
            print(e)
    else:
        print('Already have entry in {} for {}.'.format(TABLE_NAME_SHARES_OUTSTANDING, ticker_name))
    # print(TableSharesOutstanding.get_from(ticker_name, db_connection))

    last_update = TablePricesWeekly.get_latest_date(ticker_name, db_connection)
    needs_updated = DataUpdates.check_needs_update(TABLE_NAME_PRICES_WEEKLY, last_update)
    if(needs_updated == True):
        try:
            TablePricesWeekly.update(ticker_name, db_connection)
            need_to_update_valuation_metrics = True
        except FileNotFoundError as e:
            print(e)
    else:
        print('Already have entry in {} for {}.'.format(TABLE_NAME_PRICES_WEEKLY, ticker_name))
    # print(TablePricesWeekly.get_from(ticker_name, db_connection))

    last_update = TableValuationMetrics.get_latest_date(ticker_name, db_connection)
    needs_updated = DataUpdates.check_needs_update(TABLE_NAME_VALUATION_METRICS, last_update)
    if (need_to_update_valuation_metrics == True) or (needs_updated == True):
        TableValuationMetrics.update(ticker_name, db_connection)
    else:
        print('Aleady have entries in {} for {}.'.format(TABLE_NAME_VALUATION_METRICS, ticker_name))
    # print(TableValuationMetrics.get_from(ticker_name, db_connection).to_string())

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
