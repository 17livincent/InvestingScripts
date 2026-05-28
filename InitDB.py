"""
    Initialize the tables of the database.
"""

from sqlalchemy import text
from DBConnection import get_db_connection

engine = get_db_connection()

'''
Tables:
    - fundamentals          --> from raw AlphaVantage JSON
    - operational_metrics   --> calculated from fundamentals
    - prices_weekly         --> from raw AlphaVantage JSON
    - shares_outstanding    --> from raw AlphaVantage JSON
    - valuation_metrics     --> calculated from all raw tables
    - companies
    - data_updates
'''

TABLE_COMPANIES_NAME = 'companies'
TABLE_NAME_FUNDAMENTALS = 'fundamentals'
TABLE_NAME_OPERATIONAL_METRICS = 'operational_metrics'
TABLE_NAME_DATA_UPDATES = 'data_updates'

TABLE_COMPANIES_DICT = {
    'ticker': '',
    'company_name': '',
    'sector': '',
    'industry': '',
    'exchange': '',
    'country': '',
    'market_cap_latest': ''
}

TABLE_DATA_UPDATES_DICT = {
    'ticker': '',
    'dataset': '',
    'last_updated': None
}

TABLES = [
"""
CREATE TABLE fundamentals (
    ticker TEXT NOT NULL,
    date DATE NOT NULL,

    total_revenue DOUBLE PRECISION,
    cost_of_revenue DOUBLE PRECISION,
    operating_income DOUBLE PRECISION,
    net_income DOUBLE PRECISION,
    operating_cash_flow DOUBLE PRECISION,
    capex DOUBLE PRECISION,

    total_debt DOUBLE PRECISION,
    cash DOUBLE PRECISION,
    shareholder_equity DOUBLE PRECISION,

    PRIMARY KEY (ticker, date)
);
""",
"""
CREATE TABLE operational_metrics (
    ticker TEXT NOT NULL,
    date DATE NOT NULL,

    roic DOUBLE PRECISION,
    roe DOUBLE PRECISION,
    debt_to_equity DOUBLE PRECISION,

    gross_margin DOUBLE PRECISION,
    operating_margin DOUBLE PRECISION,
    net_margin DOUBLE PRECISION,

    ocf_margin DOUBLE PRECISION,
    fcf_margin DOUBLE PRECISION,

    revenue_growth_yoy DOUBLE PRECISION,

    ttm_roic DOUBLE PRECISION,
    ttm_operating_margin DOUBLE PRECISION,
    ttm_net_margin DOUBLE PRECISION,
    ttm_fcf_margin DOUBLE PRECISION,

    PRIMARY KEY (ticker, date)
);
""",
"""
CREATE TABLE prices_weekly (
    ticker TEXT NOT NULL,
    date DATE NOT NULL,

    adjusted_close DOUBLE PRECISION,
    volume BIGINT,

    PRIMARY KEY (ticker, date)
);
""",
"""
CREATE TABLE shares_outstanding (
    ticker TEXT NOT NULL,
    date DATE NOT NULL,

    basic_shares BIGINT,
    diluted_shares BIGINT,

    PRIMARY KEY (ticker, date)
);
""",
"""
CREATE TABLE valuation_metrics (
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
CREATE TABLE companies (
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
CREATE TABLE data_updates (
    ticker TEXT NOT NULL,
    dataset TEXT NOT NULL,
    last_updated TIMESTAMP,

    PRIMARY KEY (ticker, dataset)
);
"""
]

ADD_INDICES = [
"""
CREATE INDEX idx_fundamentals_ticker
ON fundamentals(ticker);
""",
"""
CREATE INDEX idx_operational_metrics_ticker
ON operational_metrics(ticker);
""",
"""
CREATE INDEX idx_valuation_metrics_ticker
ON valuation_metrics(ticker);
""",
"""
CREATE INDEX idx_prices_weekly_ticker
ON prices_weekly(ticker);
""",
"""
CREATE INDEX idx_operational_metrics_roic
ON operational_metrics(ttm_roic DESC);
"""
]

def init_db_tables(engine):
    with engine.begin() as conn:
        for sql in TABLES:
            conn.execute(text(sql))

    print("Database initialized.")
