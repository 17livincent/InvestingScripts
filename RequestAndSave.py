"""
    Request and save data from the AlphaVantage API.
"""
import json
import requests
import subprocess
from pathlib import Path
import time
import argparse
from OperationalMetrics import get_and_save_fundamentals

functions = [
    'CASH_FLOW',
    'BALANCE_SHEET',
    'INCOME_STATEMENT',
    'TIME_SERIES_WEEKLY_ADJUSTED',
    'SHARES_OUTSTANDING'
    ]

def request_and_save_json(function, symbol):
    '''
        Get data from AlphaVantage with the given function and symbol.
        Saves to a JSON file in data/.
    '''
    result = subprocess.run(['pass', 'show', 'Keys/AlphaVantage'], capture_output=True, text=True)
    key = result.stdout

    url = 'https://www.alphavantage.co/query?function={}&symbol={}&apikey={}'.format(function, symbol, key)
    r = requests.get(url)
    data = r.json()

    if data:
        Path('data/{}'.format(symbol)).mkdir(exist_ok=True)
        with open('data/{}/{}.json'.format(symbol, function), 'w') as export_json_file:
            json.dump(data, export_json_file, indent=4)

def main():
    parser = argparse.ArgumentParser(prog='RequestAndSave.py', description='Get data from AlphaVantage.')
    parser.add_argument('-t', '--ticker', required=True, help='Stock ticker')
    parser.add_argument('-a', '--get-all', required=False, default=False, help='Pull, save, and overwrite all data.  Otherwise, leave the existing files alone.')

    args = parser.parse_args()
    print("Stock ticker: {}".format(args.ticker))
    for function_name in functions:
        if (args.get_all == False) and (Path('data/{}/{}.json'.format(args.ticker, function_name)).exists()):
            continue
        print("Requesting {} data...".format(function_name))
        time.sleep(1)
        request_and_save_json(function_name, args.ticker)

    get_and_save_fundamentals(args.ticker)

if __name__ == "__main__":
    main()
