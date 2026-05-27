"""
    Read, update ticker data.
"""

from RequestAndSave import request_json
from DBConnection import get_db_connection
from sqlalchemy import text
from InitDB import (TABLE_COMPANIES_NAME,
                    TABLE_COMPANIES_DICT,
                    TABLE_DATA_UPDATES_NAME)
from pathlib import Path
import json
import pandas as pd
from datetime import datetime, timezone

OVERVIEW_FUNCTION_NAME = 'OVERVIEW'
OVERVIEW_PATH = 'data/{}/{}.json'

def add_data_update(ticker_name, table_name, db_connection):
    CHECK_ENTRY = "SELECT * FROM data_updates WHERE ticker=%(ticker_name)s AND dataset=%(table_name)s"
    UPDATE_ENTRY = "UPDATE {}" \
    "SET last_updated={}," \
    "WHERE ticker='{}' AND dataset='{}'".format(TABLE_DATA_UPDATES_NAME,
                                                datetime.now(timezone.utc),
                                                ticker_name, table_name)

    with db_connection.begin() as connection:
        df_check = pd.read_sql_query(CHECK_ENTRY, params={"ticker_name": ticker_name, "table_name": table_name}, con=connection)
        if len(df_check):
            # Update the entry
            UPDATE_ENTRY = text("UPDATE {} SET last_updated = :new_last_updated WHERE ticker = :ticker AND dataset = :dataset_name".format(TABLE_DATA_UPDATES_NAME))
            connection.execute(UPDATE_ENTRY, {'new_last_updated': datetime.now(timezone.utc),
                                              'ticker': ticker_name,
                                              'dataset_name': table_name})
            print('Updated {} for {} and {}.'.format(TABLE_DATA_UPDATES_NAME, ticker_name, table_name))
        else:
            # Add a new entry
            ADD_ENTRY = text("INSERT INTO {} (ticker, dataset, last_updated)" \
            "VALUES (:ticker_name, :dataset_name, :last_updated)".format(TABLE_DATA_UPDATES_NAME))
            connection.execute(ADD_ENTRY, {'ticker_name': ticker_name,
                                           'dataset_name': table_name,
                                           'last_updated': datetime.now(timezone.utc)})
            print('Added {} for {} and {}.'.format(TABLE_DATA_UPDATES_NAME, ticker_name, table_name))

def get_from_companies(ticker_name, db_connection):
    query_str = "SELECT * FROM {} WHERE ticker = '{}';".format(TABLE_COMPANIES_NAME, ticker_name)
    print(query_str)
    with db_connection.connect() as connection:
        df_company = pd.read_sql_query(query_str, con=connection)
    return df_company

def add_company(ticker_name, db_connection):
    overview_path = OVERVIEW_PATH.format(ticker_name, OVERVIEW_FUNCTION_NAME)
    overview_json = request_json(OVERVIEW_FUNCTION_NAME, ticker_name)

    if 'Symbol' in overview_json:
        Path('data/{}'.format(ticker_name)).mkdir(exist_ok=True)
        with open(overview_path, 'w') as export_json_file:
            json.dump(overview_json, export_json_file, indent=4)
    else:
        print('WARNING: Import of {} failed.  Pulling from saved file if exists.'.format(OVERVIEW_FUNCTION_NAME))

    try:
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
            add_data_update(ticker_name, TABLE_COMPANIES_NAME, db_connection)
            print('Added row for {} to table {}.'.format(ticker_name, TABLE_COMPANIES_NAME))
    except FileNotFoundError:
        print('ERROR: Could not read{}.', overview_path)
    return df_overview[list(TABLE_COMPANIES_DICT)]

db_connection = get_db_connection()
df_company_row = get_from_companies('SNDK', db_connection)
if(len(df_company_row) == 0):
    df_company_row = add_company('SNDK', db_connection)
else:
    print('Already have entry in {} for {}.'.format('companies', 'SNDK'))
print(df_company_row)
