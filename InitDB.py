"""
    Initialize the tables of the database.
"""

from sqlalchemy import text
from DBConnection import get_db_engine

'''
Tables:
    - fundamentals          --> from raw AlphaVantage JSON
    - operational_metrics   --> calculated from fundamentals
    - prices_weekly         --> from raw AlphaVantage JSON
    - shares_outstanding    --> from raw AlphaVantage JSON
    - valuation_metrics     --> calculated from all raw tables
    - companies             --> data of recorded companies/tickers
    - report_dates          --> next earnings report date
    - data_updates          --> records of when the last ticker*table update was made
'''

TABLE_COMPANIES_NAME = 'companies'
TABLE_NAME_FUNDAMENTALS = 'fundamentals'
TABLE_NAME_OPERATIONAL_METRICS = 'operational_metrics'
TABLE_NAME_SHARES_OUTSTANDING = 'shares_outstanding'
TABLE_NAME_PRICES_WEEKLY = 'prices_weekly'
TABLE_NAME_DATA_UPDATES = 'data_updates'
TABLE_NAME_VALUATION_METRICS = 'valuation_metrics'
TABLE_NAME_REPORT_DATES = 'report_dates'

TABLE_NAMES = [TABLE_COMPANIES_NAME,
               TABLE_NAME_FUNDAMENTALS,
               TABLE_NAME_OPERATIONAL_METRICS,
               TABLE_NAME_SHARES_OUTSTANDING,
               TABLE_NAME_PRICES_WEEKLY,
               TABLE_NAME_VALUATION_METRICS
               ]

TABLE_COMPANIES_DICT = {
    'ticker': '',
    'company_name': '',
    'sector': '',
    'industry': '',
    'exchange': '',
    'country': '',
    'market_cap_latest': ''
}

TABLES = [
"""
CREATE TABLE IF NOT EXISTS fundamentals (
    ticker TEXT NOT NULL,
    date DATE NOT NULL,

    total_revenue DOUBLE PRECISION,
    cost_of_revenue DOUBLE PRECISION,
    operating_income DOUBLE PRECISION,
    net_income DOUBLE PRECISION,
    income_before_tax DOUBLE PRECISION,
    income_tax_expense DOUBLE PRECISION,

    operating_cash_flow DOUBLE PRECISION,
    capex DOUBLE PRECISION,

    total_debt DOUBLE PRECISION,
    cash DOUBLE PRECISION,
    shareholder_equity DOUBLE PRECISION,

    PRIMARY KEY (ticker, date)
);
""",
"""
CREATE TABLE IF NOT EXISTS operational_metrics (
    ticker TEXT NOT NULL,
    date DATE NOT NULL,

    roic DOUBLE PRECISION,
    roe DOUBLE PRECISION,
    debt_to_equity DOUBLE PRECISION,
    nopat DOUBLE PRECISION,

    gross_margin DOUBLE PRECISION,
    operating_margin DOUBLE PRECISION,
    net_margin DOUBLE PRECISION,
    ocf_margin DOUBLE PRECISION,
    fcf_margin DOUBLE PRECISION,

    revenue_growth_yoy DOUBLE PRECISION,

    ttm_roic DOUBLE PRECISION,
    ttm_net_income DOUBLE PRECISION,
    ttm_operating_income DOUBLE PRECISION,
    ttm_fcf DOUBLE PRECISION,
    ttm_operating_margin DOUBLE PRECISION,
    ttm_net_margin DOUBLE PRECISION,
    ttm_fcf_margin DOUBLE PRECISION,
    ttm_ocf_margin DOUBLE PRECISION,

    PRIMARY KEY (ticker, date)
);
""",
"""
CREATE TABLE IF NOT EXISTS prices_weekly (
    ticker TEXT NOT NULL,
    date DATE NOT NULL,

    adjusted_close DOUBLE PRECISION,
    volume BIGINT,

    PRIMARY KEY (ticker, date)
);
""",
"""
CREATE TABLE IF NOT EXISTS shares_outstanding (
    ticker TEXT NOT NULL,
    date DATE NOT NULL,

    basic_shares BIGINT,
    diluted_shares BIGINT,

    PRIMARY KEY (ticker, date)
);
""",
"""
CREATE TABLE IF NOT EXISTS valuation_metrics (
    ticker TEXT NOT NULL,
    date DATE NOT NULL,

    market_cap DOUBLE PRECISION,
    enterprise_value DOUBLE PRECISION,

    pe_ttm DOUBLE PRECISION,
    pfcf DOUBLE PRECISION,

    ev_ebit DOUBLE PRECISION,
    ev_fcf DOUBLE PRECISION,
    ev_nopat DOUBLE PRECISION,

    PRIMARY KEY (ticker, date)
);
""",
"""
CREATE TABLE IF NOT EXISTS companies (
    ticker TEXT PRIMARY KEY,

    company_name TEXT,
    sector TEXT,
    industry TEXT,

    exchange TEXT,
    country TEXT,

    market_cap_latest DOUBLE PRECISION
);
""",
"""
CREATE TABLE IF NOT EXISTS data_updates (
    ticker TEXT NOT NULL,
    dataset TEXT NOT NULL,
    last_updated TIMESTAMP,

    PRIMARY KEY (ticker, dataset)
);
""",
"""
CREATE TABLE IF NOT EXISTS report_dates (
    ticker TEXT NOT NULL,
    report_date DATE NULL
)
"""
]

ADD_INDICES = [
"""
CREATE INDEX IF NOT EXISTS idx_fundamentals_ticker
ON fundamentals(ticker);
""",
"""
CREATE INDEX IF NOT EXISTS idx_operational_metrics_ticker
ON operational_metrics(ticker);
""",
"""
CREATE INDEX IF NOT EXISTS idx_valuation_metrics_ticker
ON valuation_metrics(ticker);
""",
"""
CREATE INDEX IF NOT EXISTS idx_prices_weekly_ticker
ON prices_weekly(ticker);
""",
"""
CREATE INDEX IF NOT EXISTS idx_operational_metrics_roic
ON operational_metrics(ttm_roic DESC);
""",
"""
CREATE INDEX IF NOT EXISTS idx_prices_weekly_ticker_date_desc
ON prices_weekly(ticker, date DESC);
""",
"""
CREATE INDEX IF NOT EXISTS idx_valuation_metrics_ticker_date_desc
ON valuation_metrics(ticker, date DESC);
""",
"""
CREATE INDEX IF NOT EXISTS idx_shares_outstanding_ticker_date_desc
ON shares_outstanding(ticker, date DESC);
"""
]

INSERT_STATEMENT_FUNDAMENTALS = text("INSERT INTO {} (ticker, " \
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

INSERT_STATEMENT_OPERATIONAL_METRICS = text("INSERT INTO {} (ticker, " \
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
    ":ttm_ocf_margin) " \
    "ON CONFLICT (ticker, date) DO UPDATE SET " \
    "roic = EXCLUDED.roic," \
    "roe = EXCLUDED.roe," \
    "debt_to_equity = EXCLUDED.debt_to_equity," \
    "nopat = EXCLUDED.nopat," \
    "gross_margin = EXCLUDED.gross_margin," \
    "operating_margin = EXCLUDED.operating_margin," \
    "net_margin = EXCLUDED.net_margin," \
    "ocf_margin = EXCLUDED.ocf_margin," \
    "fcf_margin = EXCLUDED.fcf_margin," \
    "revenue_growth_yoy = EXCLUDED.revenue_growth_yoy," \
    "ttm_roic = EXCLUDED.ttm_roic," \
    "ttm_net_income = EXCLUDED.ttm_net_income," \
    "ttm_operating_income = EXCLUDED.ttm_operating_income," \
    "ttm_fcf = EXCLUDED.ttm_fcf," \
    "ttm_operating_margin = EXCLUDED.ttm_operating_margin," \
    "ttm_net_margin = EXCLUDED.ttm_net_margin," \
    "ttm_fcf_margin = EXCLUDED.ttm_fcf_margin," \
    "ttm_ocf_margin = EXCLUDED.ttm_ocf_margin".format(TABLE_NAME_OPERATIONAL_METRICS))

INSERT_STATEMENT_SHARES_OUTSTANDING = text("INSERT INTO {} (ticker, " \
    "date, " \
    "basic_shares," \
    "diluted_shares)" \
    "VALUES (:ticker," \
    ":date," \
    ":basic_shares," \
    ":diluted_shares)".format(TABLE_NAME_SHARES_OUTSTANDING))

INSERT_STATEMENT_PRICES_WEEKLY = text("INSERT INTO {} (ticker, " \
"date, " \
"adjusted_close, " \
"volume)" \
"VALUES (:ticker," \
":date," \
":adjusted_close," \
":volume)".format(TABLE_NAME_PRICES_WEEKLY))

INSERT_STATEMENT_VALUATION_METRICS = text("INSERT INTO {} (ticker, " \
"date," \
"market_cap," \
"enterprise_value," \
"pe_ttm," \
"pfcf," \
"ev_ebit," \
"ev_fcf," \
"ev_nopat)" \
"VALUES (:ticker," \
":date," \
":market_cap," \
":enterprise_value," \
":pe_ttm," \
":pfcf," \
":ev_ebit," \
":ev_fcf," \
":ev_nopat)".format(TABLE_NAME_VALUATION_METRICS))

def init_db_tables(engine):
    for sql in TABLES:
        try:
            with engine.begin() as conn:
                conn.execute(text(sql))
        except Exception as e:
            print(e)
    for index in ADD_INDICES:
        try:
            with engine.begin() as conn:
                conn.execute(text(index))
        except Exception as e:
            print(e)

    print("Database initialized.")

def main():
    db_engine = get_db_engine()
    init_db_tables(db_engine)

if __name__ == "__main__":
    main()
