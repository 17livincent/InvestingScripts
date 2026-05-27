'''
    Given data from data/<ticker>/INCOME_STATEMENT.json,
    data/<ticker>/BALANCE_SHEET.json, and data/<ticker>/CASH_FLOW.json,
    calculate DEB, ROE, and FCF.
'''

import json
import pandas as pd
import numpy as np
import argparse
import matplotlib.pyplot as plt

CALCULATED_FUNDAMENTALS_PATH = 'data/{}/calculated_fundamentals.csv'

def compute_ttm(series):
    return series.rolling(4).sum()

def safe_divide(a, b):
    return np.where(b != 0, a / b, np.nan)

def get_fundamentals(ticker):
    df_data_income_statement = pd.DataFrame()

    with open('data/{}/INCOME_STATEMENT.json'.format(ticker)) as income_statement_json:
        income_statement = json.load(income_statement_json)
        df_data_income_statement['date'] = [quarterly_report['fiscalDateEnding'] for
                                            quarterly_report in income_statement['quarterlyReports']]
        df_data_income_statement['total_revenue'] = [quarterly_report['totalRevenue'] for
                                                    quarterly_report in income_statement['quarterlyReports']]
        df_data_income_statement['cost_of_revenue'] = [quarterly_report['costOfRevenue'] for
                                                     quarterly_report in income_statement['quarterlyReports']]
        df_data_income_statement['net_income'] = [quarterly_report['netIncome'] for
                                                 quarterly_report in income_statement['quarterlyReports']]
        df_data_income_statement['operating_income'] = [quarterly_report['operatingIncome'] for
                                                       quarterly_report in income_statement['quarterlyReports']]
        df_data_income_statement['IncomeBeforeTax'] = [quarterly_report['incomeBeforeTax'] for
                                                       quarterly_report in income_statement['quarterlyReports']]
        df_data_income_statement['IncomeTaxExpense'] = [quarterly_report['incomeTaxExpense'] for
                                                        quarterly_report in income_statement['quarterlyReports']]
        df_data_income_statement['EBIT'] = [quarterly_report['ebit'] for
                                            quarterly_report in income_statement['quarterlyReports']]

    df_data_balance_sheet = pd.DataFrame()

    with open('data/{}/BALANCE_SHEET.json'.format(ticker)) as balance_sheet_json:
        balance_sheet = json.load(balance_sheet_json)
        df_data_balance_sheet['date'] = [quarterly_report['fiscalDateEnding'] for
                                         quarterly_report in balance_sheet['quarterlyReports']]
        df_data_balance_sheet['shareholder_equity'] = [quarterly_report['totalShareholderEquity'] for
                                                           quarterly_report in balance_sheet['quarterlyReports']]
        df_data_balance_sheet['total_debt'] = [quarterly_report['shortLongTermDebtTotal'] for
                                              quarterly_report in balance_sheet['quarterlyReports']]
        df_data_balance_sheet['cash'] = [quarterly_report['cashAndCashEquivalentsAtCarryingValue'] for
                                         quarterly_report in balance_sheet['quarterlyReports']]

    df_cash_flow = pd.DataFrame()

    with open('data/{}/CASH_FLOW.json'.format(ticker)) as cash_flow_json:
        cash_flow = json.load(cash_flow_json)
        df_cash_flow['date'] = [quarterly_report['fiscalDateEnding'] for
                                         quarterly_report in cash_flow['quarterlyReports']]
        df_cash_flow['operating_cash_flow'] = [quarterly_report['operatingCashflow'] for
                                         quarterly_report in cash_flow['quarterlyReports']]
        df_cash_flow['capex'] = [quarterly_report['capitalExpenditures'] for
                                         quarterly_report in cash_flow['quarterlyReports']]

    df_merge1 = pd.merge(df_data_income_statement, df_data_balance_sheet, on='date')
    df_merged = pd.merge(df_merge1, df_cash_flow, on='date')

    df_sorted = df_merged.sort_values(by='date', ascending=True)
    df_sorted['date'] = pd.to_datetime(df_sorted['date'])

    for column_name in df_sorted:
        if column_name != 'date':
            df_sorted[column_name] = pd.to_numeric(df_sorted[column_name], errors='coerce').fillna(0)

    return df_sorted

def calculate_fundamentals(df_fundmentals):
    df_calculated = pd.DataFrame()
    df_calculated['date'] = df_fundmentals['date']

    # Calculate debt-to-equity
    df_calculated['debt_to_equity'] = safe_divide(df_fundmentals['total_debt'], df_fundmentals['shareholder_equity'])

    # Calculate return-on-equity
    df_calculated['roe'] = safe_divide(df_fundmentals['net_income'], df_fundmentals['shareholder_equity'])

    # Calculate gross margin
    df_calculated['gross_margin'] = (df_fundmentals['total_revenue'] - df_fundmentals['cost_of_revenue']) / df_fundmentals['total_revenue']

    # Calculate operating margin
    df_calculated['operating_margin'] = df_fundmentals['operating_income'] / df_fundmentals['total_revenue']

    # Calculate net margin
    df_calculated['net_margin'] = df_fundmentals['net_income'] / df_fundmentals['total_revenue']

    # Calculate effective tax rate
    df_calculated['effective_tax_rate'] = (df_fundmentals['IncomeTaxExpense'] / df_fundmentals['IncomeBeforeTax']).clip(lower=0, upper=0.35)
    # Calculate ROIC
    df_calculated['invested_capital'] = df_fundmentals['total_debt'] + df_fundmentals['shareholder_equity'] - df_fundmentals['cash']
    df_calculated['invested_capital'] = df_calculated['invested_capital'].where(df_calculated['invested_capital'] > 0)
    df_calculated['nopat'] = df_fundmentals['operating_income'] * (1 - df_calculated['effective_tax_rate'])
    df_calculated['roic'] = df_calculated['nopat'] / df_calculated['invested_capital']

    # Calculate revenue growth YoY
    df_calculated['revenue_growth_yoy'] = df_fundmentals['total_revenue'].pct_change(periods=4)

    # Calculate OCF margin
    df_calculated['ocf_margin'] = df_fundmentals['operating_cash_flow'] / df_fundmentals['total_revenue']

    # Calculate free cash flow margin
    fcf = df_fundmentals['operating_cash_flow'] - df_fundmentals['capex']
    df_calculated['fcf_margin'] = fcf / df_fundmentals['total_revenue']

    # TTM metrics
    ttm_total_revenue = compute_ttm(df_fundmentals['total_revenue'])
    ttm_net_income = compute_ttm(df_fundmentals['net_income'])
    ttm_operating_income = compute_ttm(df_fundmentals['operating_income'])
    ttm_fcf = compute_ttm(fcf)
    ttm_ocf = compute_ttm(df_fundmentals['operating_cash_flow'])

    # Store TTM totals for use in valuation calculations
    df_calculated['ttm_net_income'] = ttm_net_income
    df_calculated['ttm_operating_income'] = ttm_operating_income
    df_calculated['ttm_fcf'] = ttm_fcf
    df_calculated['ttm_total_revenue'] = ttm_total_revenue

    df_calculated['ttm_operating_margin'] = ttm_operating_income / ttm_total_revenue
    df_calculated['ttm_net_margin'] = ttm_net_income / ttm_total_revenue
    df_calculated['ttm_fcf_margin'] = ttm_fcf / ttm_total_revenue
    df_calculated['ttm_ocf_margin'] = ttm_ocf / ttm_total_revenue

    # TTM ROIC
    ttm_nopat = compute_ttm(df_calculated['nopat'])
    df_calculated['average_invested_capital'] = df_calculated['invested_capital'].rolling(4).mean()
    df_calculated['ttm_roic'] = ttm_nopat / df_calculated['average_invested_capital']

    return df_calculated

def get_latest_metrics(df_calculated, ticker):
    latest = df_calculated.iloc[-1]
    return {
        'ticker': ticker,
        'ttm_roic': latest['ttm_roic'],
        'ttm_operating_margin': latest['ttm_operating_margin'],
        'ttm_net_margin': latest['ttm_net_margin'],
        'ttm_ocf_margin': latest['ttm_ocf_margin'],
        'revenue_growth_yoy': latest['revenue_growth_yoy'],
        'debt_to_equity': latest['debt_to_equity']
    }

def get_and_save_fundamentals(ticker):
    df_calculated = get_fundamentals(ticker)
    print("Saving to CSV: {}".format(ticker))
    df_calculated.to_csv(CALCULATED_FUNDAMENTALS_PATH.format(ticker), index=False)
    return df_calculated

def read_saved_fundamentals(ticker):
    df_fundamentals = pd.read_csv(CALCULATED_FUNDAMENTALS_PATH.format(ticker))
    df_fundamentals['date'] = pd.to_datetime(df_fundamentals['date'])
    return df_fundamentals

def main():
    parser = argparse.ArgumentParser(prog='CalculateFundamentals.py', description='Analyze a company\'s fundamentals.')
    parser.add_argument('-t', '--ticker', required=True, help='Stock ticker')

    args = parser.parse_args()
    print("Stock ticker: {}".format(args.ticker))
    df_calculated = get_and_save_fundamentals(args.ticker)
    print(df_calculated.columns)

if __name__ == "__main__":
    main()
