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
    df_sorted['Date'] = pd.to_datetime(df_sorted['Date'])

    for column_name in df_sorted:
        if column_name != 'Date':
            df_sorted[column_name] = pd.to_numeric(df_sorted[column_name], errors='coerce').fillna(0)

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
    df_calculated['GrossMargin_Quarterly'] = (df_sorted['TotalRevenue'] - df_sorted['CostOfRevenue']) / df_sorted['TotalRevenue']

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

    # Calculate revenue growth YoY
    df_calculated['RevenueGrowth_YoY'] = df_sorted['TotalRevenue'].pct_change(periods=4)

    # Calculate OCF margin
    df_calculated['OCFMargin'] = df_sorted['OperatingCashFlow'] /df_sorted['TotalRevenue']
    
    # Calculate free cash flow margin
    df_calculated['FCFMargin'] = df_calculated['FreeCashFlow'] / df_sorted['TotalRevenue']

    # TTM metrics
    df_calculated['TTM_TotalRevenue'] = df_sorted['TotalRevenue'].rolling(4).sum()
    df_calculated['TTM_NetIncome'] = df_sorted['NetIncome'].rolling(4).sum()
    df_calculated['TTM_OperatingIncome'] = df_sorted['OperatingIncome'].rolling(4).sum()
    df_calculated['TTM_CapEx'] = df_sorted['CapEx'].rolling(4).sum()
    df_calculated['TTM_NOPAT'] = df_calculated['NOPAT'].rolling(4).sum()
    df_calculated['AverageInvestedCapital'] = df_calculated['InvestedCapital'].rolling(4).mean()
    df_calculated['TTM_ROIC'] = df_calculated['TTM_NOPAT'] / df_calculated['AverageInvestedCapital']
    df_calculated['TTM_FreeCashFlow'] = df_calculated['FreeCashFlow'].rolling(4).sum()
    df_calculated['TTM_GrossMargin'] = ((df_sorted['TotalRevenue'].rolling(4).sum() - df_sorted['CostOfRevenue'].rolling(4).sum()) / 
                                        df_sorted['TotalRevenue'].rolling(4).sum())
    df_calculated['TTM_OperatingCashFlow'] = df_sorted['OperatingCashFlow'].rolling(4).sum()
    df_calculated['TTM_OCFMargin'] = (df_calculated['TTM_OperatingCashFlow'] / 
                                          df_calculated['TTM_TotalRevenue'])
    df_calculated['TTM_FCFMargin'] = (df_calculated['TTM_FreeCashFlow'] /
                                          df_calculated['TTM_TotalRevenue'])
    df_calculated['TTM_OperatingMargin'] = df_calculated['TTM_OperatingIncome'] / df_calculated['TTM_TotalRevenue']
    df_calculated['TTM_NetMargin'] = df_calculated['TTM_NetIncome'] / df_calculated['TTM_TotalRevenue']

    return df_sorted, df_calculated

def main():
    parser = argparse.ArgumentParser(prog='CalculateFundamentals.py', description='Analyze a company\'s fundamentals.')
    parser.add_argument('-t', '--ticker', required=True, help='Stock ticker')

    args = parser.parse_args()
    print("Stock ticker: {}".format(args.ticker))
    df_fundamentals, df_calculated = get_fundamentals(args.ticker)

    df_calculated.to_csv('data/{}/calculated_fundamentals.csv'.format(args.ticker), index=False)

    fig, ax = plt.subplots()
    df_calculated.plot(ax=ax, kind='line', x='Date', y='TTM_ROIC', title='TTM_ROIC', grid=True)
    print(df_calculated.columns.tolist())
    print(df_calculated.tail())
    plt.show()

if __name__ == "__main__":
    main()
