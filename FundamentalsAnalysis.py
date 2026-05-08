import json
import pandas as pd
import numpy as np

df_data_income_statement = pd.DataFrame()
report_dates = []
quarterly_total_revenue = []
quarterly_net_income = []

with open('data/SNDK/INCOME_STATEMENT.json') as balance_sheet_json:
    balance_sheet = json.load(balance_sheet_json)

    for quarterly_report in balance_sheet['quarterlyReports']:
        print(quarterly_report['fiscalDateEnding'])
        report_dates.append(quarterly_report['fiscalDateEnding'])
        quarterly_total_revenue.append(quarterly_report['totalRevenue'])
        quarterly_net_income.append(quarterly_report['netIncome'])
    df_data_income_statement['Date'] = report_dates
    df_data_income_statement['TotalRevenue'] = quarterly_total_revenue
    df_data_income_statement['NetIncome'] = quarterly_net_income
    print(df_data_income_statement)

df_data_balance_sheet = pd.DataFrame()
report_dates = []
quarterly_total_equity = []
quarterly_total_debt = []

with open('data/SNDK/BALANCE_SHEET.json') as balance_sheet_json:
    balance_sheet = json.load(balance_sheet_json)

    for quarterly_report in balance_sheet['quarterlyReports']:
        report_dates.append(quarterly_report['fiscalDateEnding'])
        quarterly_total_equity.append(quarterly_report['totalShareholderEquity'])
        quarterly_total_debt.append(quarterly_report['shortLongTermDebtTotal'])
    df_data_balance_sheet['Date'] = report_dates
    df_data_balance_sheet['TotalShareholderEquity'] = quarterly_total_equity
    df_data_balance_sheet['TotalDebt'] = quarterly_total_debt
    print(df_data_balance_sheet)

df_cash_flow = pd.DataFrame()
report_dates = []
quarterly_operating_cash_flow = []
quarterly_capex = []

with open('data/SNDK/CASH_FLOW.json') as cash_flow_json:
    cash_flow = json.load(cash_flow_json)
    
    for quarterly_report in cash_flow['quarterlyReports']:
        report_dates.append(quarterly_report['fiscalDateEnding'])
        quarterly_operating_cash_flow.append(quarterly_report['operatingCashflow'])
        quarterly_capex.append(quarterly_report['capitalExpenditures'])
    df_cash_flow['Date'] = report_dates
    df_cash_flow['OperatingCashFlow'] = quarterly_operating_cash_flow
    df_cash_flow['CapEx'] = quarterly_capex
    print(df_cash_flow)

df_merge1 = pd.merge(df_data_income_statement, df_data_balance_sheet, on='Date')
df_merged = pd.merge(df_merge1, df_cash_flow, on='Date')

df_sorted = df_merged.sort_values(by='Date', ascending=True)
print(df_sorted)
