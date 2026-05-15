"""
    Request and save data from the AlphaVantage API.
"""
import json
import requests
import subprocess
from pathlib import Path
import time
import argparse

functions = ['CASH_FLOW', 'BALANCE_SHEET', 'INCOME_STATEMENT']

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

    args = parser.parse_args()
    print("Stock ticker: {}".format(args.ticker))
    for function_name in functions:
        print("Requesting {} data...".format(function_name))
        request_and_save_json(function_name, args.ticker)

if __name__ == "__main__":
    main()


