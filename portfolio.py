
import sqlite3
from datetime import datetime

class Portfolio:
    def __init__(self):
        self.conn = sqlite3.connect('portfolio.db')
        self.create_tables()
        
    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY,
            symbol TEXT NOT NULL,
            operation TEXT NOT NULL,
            price REAL NOT NULL,
            quantity INTEGER NOT NULL,
            date TEXT NOT NULL
        )''')
        self.conn.commit()
        
    def add_transaction(self, symbol, operation, price, quantity, date=None):
        cursor = self.conn.cursor()
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
        INSERT INTO transactions (symbol, operation, price, quantity, date)
        VALUES (?, ?, ?, ?, ?)
        ''', (symbol.upper(), operation, price, quantity, date))
        self.conn.commit()
        
    def get_portfolio(self):
        cursor = self.conn.cursor()
        cursor.execute('''
        WITH PortfolioSummary AS (
            SELECT 
                symbol,
                SUM(CASE WHEN operation='BUY' THEN quantity ELSE -quantity END) as total_quantity,
                SUM(CASE WHEN operation='BUY' THEN price*quantity ELSE -price*quantity END) as total_cost,
                MAX(date) as last_transaction_date
            FROM transactions
            GROUP BY symbol
            HAVING total_quantity > 0
        )
        SELECT 
            symbol,
            total_quantity,
            ABS(total_cost) as total_cost,
            last_transaction_date,
            ABS(total_cost/total_quantity) as avg_cost
        FROM PortfolioSummary
        ORDER BY last_transaction_date DESC
        ''')
        return cursor.fetchall()
        
    def get_transactions(self, symbol=None):
        cursor = self.conn.cursor()
        if symbol:
            cursor.execute('SELECT * FROM transactions WHERE symbol=? ORDER BY date DESC', (symbol.upper(),))
        else:
            cursor.execute('SELECT * FROM transactions ORDER BY date DESC')
        return cursor.fetchall()

    def get_portfolio_summary(self):
        """Portföy özet bilgilerini döndürür"""
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT 
            COUNT(DISTINCT symbol) as total_stocks,
            SUM(CASE WHEN operation='BUY' THEN price*quantity ELSE -price*quantity END) as total_investment,
            SUM(CASE WHEN operation='BUY' THEN quantity ELSE -quantity END) as total_shares
        FROM transactions
        ''')
        return cursor.fetchone()
