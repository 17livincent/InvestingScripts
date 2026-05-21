"""
    Initialize the tables of the database.
"""

from sqlalchemy import text
from DBConnection import get_db_connection

engine = get_db_connection()

TABLES = [
"""
CREATE TABLE IF NOT EXISTS fundamentals (
    ticker TEXT NOT NULL,
    date DATE NOT NULL,

    TotalRevenue DOUBLE PRECISION,
    CostOfRevenue DOUBLE PRECISION,
    NetIncome DOUBLE PRECISION,
    OperatingIncome DOUBLE PRECISION,
    IncomeBeforeTax DOUBLE PRECISION,
    IncomeTaxExpense DOUBLE PRECISION,
    EBIT DOUBLE PRECISION,
    TotalShareholderEquity DOUBLE PRECISION,
    TotalDebt DOUBLE PRECISION,
    Cash DOUBLE PRECISION,
    OperatingCashFlow DOUBLE PRECISION,
    CapEx DOUBLE PRECISION,

    PRIMARY KEY (ticker, date)
);
"""
]

with engine.begin() as conn:
    for sql in TABLES:
        conn.execute(text(sql))

print("Database initialized.")
