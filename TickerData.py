"""
    Read, update ticker data.
"""

from RequestAndSave import request_json
from DBConnection import get_db_connection
from OperationalMetrics import (get_fundamentals,
                                calculate_fundamentals)
from sqlalchemy import text
from InitDB import (TABLE_COMPANIES_NAME,
                    TABLE_COMPANIES_DICT,
                    TABLE_NAME_FUNDAMENTALS,
                    TABLE_NAME_OPERATIONAL_METRICS,
                    TABLE_NAME_DATA_UPDATES)
from pathlib import Path
import json
import pandas as pd
from datetime import datetime, timezone, timedelta
import time

SAVED_JSON_PATH = 'data/{}/{}.json'

OVERVIEW_FUNCTION_NAME = 'OVERVIEW'
BALANCE_SHEET_FUNCTION_NAME = 'BALANCE_SHEET'
CASH_FLOW_FUNCTION_NAME = 'CASH_FLOW'
INCOME_STATEMENT_FUNCTION_NAME = 'INCOME_STATEMENT'

RECENCY = {
    'companies': 'quarter',
    'fundamentals': 'quarter',
    'operational_metrics': 'quarter',
    'shares_oustanding': 'quarter',
    'prices_weekly': 'week'
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



def get_from_companies(ticker_name, db_connection):
    """
        Get the latest row from 'companies' of the given ticker.
    """
    query_str = "SELECT * FROM {} WHERE ticker = '{}';".format(TABLE_COMPANIES_NAME, ticker_name)
    with db_connection.connect() as connection:
        df_company = pd.read_sql_query(query_str, con=connection)
    return df_company

def add_company(ticker_name, db_connection):
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



def get_from_fundamentals(ticker_name, db_connection):
    """
        Get all rows from 'fundamentals' of the given ticker.
    """
    query_str = "SELECT * FROM {} WHERE ticker = '{}';".format(TABLE_NAME_FUNDAMENTALS, ticker_name)
    with db_connection.connect() as connection:
        df_fundamentals = pd.read_sql_query(query_str, con=connection)
        df_fundamentals['date'] = pd.to_datetime(df_fundamentals['date'])
    return df_fundamentals



def get_from_operational_metrics(ticker_name, db_connection):
    """
        Get all rows from 'operational_metrics' of the given ticker.
    """
    query_str = "SELECT * FROM {} WHERE ticker = '{}';".format(TABLE_NAME_OPERATIONAL_METRICS, ticker_name)
    with db_connection.connect() as connection:
        df_operational_metrics = pd.read_sql_query(query_str, con=connection)
        df_operational_metrics['date'] = pd.to_datetime(df_operational_metrics['date'])
    return df_operational_metrics

def add_fundamentals_and_operational_metrics(ticker_name, db_connection):
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

    df_fundamentals = get_fundamentals(ticker_name)
    df_fundamentals['ticker'] = ticker_name

    operational_metrics = calculate_fundamentals(df_fundamentals)
    operational_metrics['ticker'] = ticker_name

    # Push to the tables
    for table_to_update in [{'df': df_fundamentals,
                             'table_name': TABLE_NAME_FUNDAMENTALS,
                             'append_function': append_fundamentals},
                            {'df': operational_metrics,
                             'table_name': TABLE_NAME_OPERATIONAL_METRICS,
                             'append_function': append_operational_metrics}]:
        check_latest_date = "SELECT MAX (date) FROM {} WHERE ticker=%(ticker_name)s;".format(table_to_update['table_name'])
        df_latest_date = pd.read_sql_query(check_latest_date,
                                            params={"ticker_name": ticker_name},
                                            con=db_connection)
        if df_latest_date['max'].iloc[0] == None:
            pass
        else:
            latest_date = pd.to_datetime(df_latest_date['max']).iloc[0]
            table_to_update['df'] = table_to_update['df'][table_to_update['df']['date'] > latest_date]
        table_to_update['append_function'](ticker_name, table_to_update['df'], db_connection)

    return df_fundamentals, operational_metrics



def append_fundamentals(ticker_name, df_fundamentals, db_connection):
    """
        Insert new rows from df_fundamentals into 'fundamentals'.
    """
    INSERT_STATEMENT = text("INSERT INTO {} (ticker, " \
    "date, " \
    "total_revenue, " \
    "cost_of_revenue, " \
    "operating_income, " \
    "net_income, " \
    "income_before_tax, " \
    "income_tax_expense, " \
    "operating_cash_flow, " \
    "capex, " \
    "total_debt, " \
    "cash, " \
    "shareholder_equity)" \
    "VALUES (:ticker," \
    ":date," \
    ":total_revenue," \
    ":cost_of_revenue," \
    ":operating_income," \
    ":net_income," \
    ":income_before_tax," \
    ":income_tax_expense," \
    ":operating_cash_flow," \
    ":capex," \
    ":total_debt," \
    ":cash," \
    ":shareholder_equity)".format(TABLE_NAME_FUNDAMENTALS))

    with db_connection.begin() as connection:
        for index, row in df_fundamentals.iterrows():
            insert_statement = INSERT_STATEMENT
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



def append_operational_metrics(ticker_name, df_operational_metrics, db_connection):
    """
        Insert new rows from df_operational_metrics into 'operational_metrics'.
    """
    INSERT_STATEMENT = text("INSERT INTO {} (ticker, " \
    "date," \
    "roic," \
    "roe," \
    "debt_to_equity," \
    "nopat," \
    "gross_margin," \
    "operating_margin," \
    "net_margin," \
    "ocf_margin," \
    "fcf_margin," \
    "revenue_growth_yoy," \
    "ttm_roic," \
    "ttm_net_income," \
    "ttm_operating_income," \
    "ttm_fcf," \
    "ttm_operating_margin," \
    "ttm_net_margin," \
    "ttm_fcf_margin," \
    "ttm_ocf_margin)" \
    "VALUES (:ticker," \
    ":date," \
    ":roic," \
    ":roe," \
    ":debt_to_equity," \
    ":nopat," \
    ":gross_margin," \
    ":operating_margin," \
    ":net_margin," \
    ":ocf_margin," \
    ":fcf_margin," \
    ":revenue_growth_yoy," \
    ":ttm_roic," \
    ":ttm_net_income," \
    ":ttm_operating_income," \
    ":ttm_fcf," \
    ":ttm_operating_margin," \
    ":ttm_net_margin," \
    ":ttm_fcf_margin," \
    ":ttm_ocf_margin)".format(TABLE_NAME_OPERATIONAL_METRICS))

    with db_connection.begin() as connection:
        for index, row in df_operational_metrics.iterrows():
            insert_statement = INSERT_STATEMENT
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



def add_update_ticker(ticker_name, db_connection):
    """
        Add and/or update DB data of the given ticker.
    """
    last_update = DataUpdates.get_last_update(ticker_name, TABLE_COMPANIES_NAME, db_connection)
    needs_updated = DataUpdates.check_needs_update(TABLE_COMPANIES_NAME, last_update)
    if(needs_updated == True):
        try:
            add_company(ticker_name, db_connection)
        except FileNotFoundError as e:
            print(e)
    else:
        print('Already have entry in {} for {}.'.format(TABLE_COMPANIES_NAME, ticker_name))
    print(get_from_companies(ticker_name, db_connection))

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
            add_fundamentals_and_operational_metrics(ticker_name,
                                                     db_connection)
        except FileNotFoundError as e:
            print(e)
    else:
        print('Already have entry in {} or {} for {}.'.format(TABLE_NAME_FUNDAMENTALS,
                                                            TABLE_NAME_OPERATIONAL_METRICS,
                                                            ticker_name))

def main():
    ticker_list = [
        'SNDK',
        'CRWD',
        'APH'
        ]
    db_connection = get_db_connection()

    for ticker in ticker_list:
        add_update_ticker(ticker, db_connection)
        print(get_from_fundamentals(ticker, db_connection))
        print(get_from_operational_metrics(ticker, db_connection))

if __name__ == "__main__":
    main()
