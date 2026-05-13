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

def get_fundamentals(ticker):
    df_data_income_statement = pd.DataFrame()

    with open('data/{}/INCOME_STATEMENT.json'.format(ticker)) as income_statement_json:
        income_statement = json.load(income_statement_json)
        df_data_income_statement['Date'] = [quarterly_report['fiscalDateEnding'] for 
                                         quarterly_report in income_statement['quarterlyReports']]
        df_data_income_statement['TotalRevenue'] = [quarterly_report['totalRevenue'] for 
                                         quarterly_report in income_statement['quarterlyReports']]
        df_data_income_statement['CostOfRevenue'] = [quarterly_report['costOfRevenue'] for 
                                         quarterly_report in income_statement['quarterlyReports']]
        df_data_income_statement['NetIncome'] = [quarterly_report['netIncome'] for 
                                         quarterly_report in income_statement['quarterlyReports']]
        df_data_income_statement['OperatingIncome'] = [quarterly_report['operatingIncome'] for 
                                         quarterly_report in income_statement['quarterlyReports']]
        df_data_income_statement['EBIT'] = [quarterly_report['ebit'] for
                                            quarterly_report in income_statement['quarterlyReports']]
        df_data_income_statement['IncomeBeforeTax'] = [quarterly_report['incomeBeforeTax'] for
                                                       quarterly_report in income_statement['quarterlyReports']]
        df_data_income_statement['IncomeTaxExpense'] = [quarterly_report['incomeTaxExpense'] for
                                                        quarterly_report in income_statement['quarterlyReports']]

    df_data_balance_sheet = pd.DataFrame()

    with open('data/{}/BALANCE_SHEET.json'.format(ticker)) as balance_sheet_json:
        balance_sheet = json.load(balance_sheet_json)
        df_data_balance_sheet['Date'] = [quarterly_report['fiscalDateEnding'] for 
                                         quarterly_report in balance_sheet['quarterlyReports']]
        df_data_balance_sheet['TotalShareholderEquity'] = [quarterly_report['totalShareholderEquity'] for 
                                         quarterly_report in balance_sheet['quarterlyReports']]
        df_data_balance_sheet['TotalDebt'] = [quarterly_report['shortLongTermDebtTotal'] for 
                                         quarterly_report in balance_sheet['quarterlyReports']]
        df_data_balance_sheet['Cash'] = [quarterly_report['cashAndCashEquivalentsAtCarryingValue'] for
                                                          quarterly_report in balance_sheet['quarterlyReports']]

    df_cash_flow = pd.DataFrame()

    with open('data/{}/CASH_FLOW.json'.format(ticker)) as cash_flow_json:
        cash_flow = json.load(cash_flow_json)
        df_cash_flow['Date'] = [quarterly_report['fiscalDateEnding'] for 
                                         quarterly_report in cash_flow['quarterlyReports']]
        df_cash_flow['OperatingCashFlow'] = [quarterly_report['operatingCashflow'] for 
                                         quarterly_report in cash_flow['quarterlyReports']]
        df_cash_flow['CapEx'] = [quarterly_report['capitalExpenditures'] for 
                                         quarterly_report in cash_flow['quarterlyReports']]

    df_merge1 = pd.merge(df_data_income_statement, df_data_balance_sheet, on='Date')
    df_merged = pd.merge(df_merge1, df_cash_flow, on='Date')

    df_sorted = df_merged.sort_values(by='Date', ascending=True)

    for column_name in df_sorted:
        if column_name != 'Date':
            df_sorted[column_name] = df_sorted[column_name].replace('None', 0).astype(int)

    df_sorted['TotalShareholderEquity'] = df_sorted['TotalShareholderEquity'].replace('None', 0)
    df_sorted['TotalDebt'] = df_sorted['TotalDebt'].replace('None', 0)

    df_calculated = pd.DataFrame()
    df_calculated['Date'] = df_sorted['Date']
    
    # Calculate debt-to-equity
    df_calculated['DebtToEquity'] = np.where(df_sorted['TotalShareholderEquity'] > 0,
                                             df_sorted['TotalDebt'] / df_sorted['TotalShareholderEquity'],
                                             np.nan)

    # Calculate return-on-equity
    df_calculated['ReturnOnEquity'] = np.where(df_sorted['TotalShareholderEquity'] > 0,
                                               df_sorted['NetIncome'] / df_sorted['TotalShareholderEquity'],
                                               np.nan)

    # Calculate free cash flow
    df_calculated['FreeCashFlow'] = df_sorted['OperatingCashFlow'] - df_sorted['CapEx']

    # Calculate gross margin
    df_calculated['GrossMargin'] = (df_sorted['TotalRevenue'] - df_sorted['CostOfRevenue']) / df_sorted['TotalRevenue']

    # Calculate operating margin
    df_calculated['OperatingMargin'] = df_sorted['OperatingIncome'] / df_sorted['TotalRevenue']

    # Calculate net margin
    df_calculated['NetMargin'] = df_sorted['NetIncome'] / df_sorted['TotalRevenue']

    # Calculate effective tax rate
    df_calculated['EffectiveTaxRate'] = (df_sorted['IncomeTaxExpense'] / df_sorted['IncomeBeforeTax']).clip(lower=0, upper=0.35)
    # Calculate ROIC
    df_calculated['InvestedCapital'] = df_sorted['TotalDebt'] + df_sorted['TotalShareholderEquity'] - df_sorted['Cash']
    df_calculated['InvestedCapital'] = df_calculated['InvestedCapital'].where(df_calculated['InvestedCapital'] > 0)
    df_calculated['NOPAT'] = df_sorted['OperatingIncome'] * (1 - df_calculated['EffectiveTaxRate'])
    df_calculated['ROIC'] = df_calculated['NOPAT'] / df_calculated['InvestedCapital']

    return df_sorted, df_calculated

def main():
    parser = argparse.ArgumentParser(prog='FundamentalsAnalysis.py', description='Analyze a company\'s fundamentals.')
    parser.add_argument('-t', '--ticker', required=True, help='Stock ticker')

    args = parser.parse_args()
    print("Stock ticker: {}".format(args.ticker))
    df_fundamentals, df_calculated = get_fundamentals(args.ticker)
    print(df_calculated['ROIC'])
    print(df_calculated)

    print(df_calculated.loc[df_calculated['ROIC'] == 0])

    fig, ax = plt.subplots(2, 4)
    df_fundamentals.plot(ax=ax[0, 0], kind='line', x='Date', y='TotalRevenue', title='TotalRevenue', grid=True)
    df_calculated.plot(ax=ax[0, 1], kind='line', x='Date', y='DebtToEquity', title='DebtToEquity', grid=True)
    df_calculated.plot(ax=ax[0, 2], kind='line', x='Date', y='ReturnOnEquity', title='ReturnOnEquity', grid=True)
    df_calculated.plot(ax=ax[0, 3], kind='line', x='Date', y='FreeCashFlow', title='FreeCashFlow', grid=True)
    print(df_calculated.columns.tolist())
    plt.show()

if __name__ == "__main__":
    main()
