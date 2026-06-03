"""
    Request and save data from the AlphaVantage API.
"""
import json
import requests
import subprocess
from pathlib import Path
import pandas as pd
import time
import argparse

functions = [
    'BALANCE_SHEET',
    'CASH_FLOW',
    'INCOME_STATEMENT',
    'SHARES_OUTSTANDING',
    'TIME_SERIES_WEEKLY_ADJUSTED'
    ]

recency = {
    'BALANCE_SHEET': 'quarter',
    'CASH_FLOW': 'quarter',
    'INCOME_STATEMENT': 'quarter',
    'SHARES_OUTSTANDING': 'quarter',
    'TIME_SERIES_WEEKLY_ADJUSTED': 'week'
}

def request_json(function, symbol):
    result = subprocess.run(['pass', 'show', 'Keys/AlphaVantage'], capture_output=True, text=True)
    key = result.stdout

    url = 'https://www.alphavantage.co/query?function={}&symbol={}&apikey={}'.format(function, symbol, key.strip())
    r = requests.get(url)
    data = r.json()
    return data

def request_and_save_json(function, symbol):
    '''
        Get data from AlphaVantage with the given function and symbol.
        Saves to a JSON file in data/.
    '''
    data = request_json(function, symbol)

    if data and 'Information' not in data:
        Path('data/{}'.format(symbol)).mkdir(exist_ok=True)
        with open('data/{}/{}.json'.format(symbol, function), 'w') as export_json_file:
            json.dump(data, export_json_file, indent=4)
    else:
        print("WARNING: received for {}:\r\n{}".format(function, data))

def get_most_recent_date(function_name, function_json):
    recent_date = None
    if function_name == 'BALANCE_SHEET':
        recent_date = function_json['quarterlyReports'][0]['fiscalDateEnding']
    elif function_name == 'CASH_FLOW':
        recent_date = function_json['quarterlyReports'][0]['fiscalDateEnding']
    elif function_name == 'INCOME_STATEMENT':
        recent_date = function_json['quarterlyReports'][0]['fiscalDateEnding']
    elif function_name == 'SHARES_OUTSTANDING':
        recent_date = function_json['data'][0]['date']
    elif function_name == 'TIME_SERIES_WEEKLY_ADJUSTED':
        recent_date = list(function_json['Weekly Adjusted Time Series'].keys())[0]

    recent_date = pd.to_datetime(recent_date)
    return recent_date
