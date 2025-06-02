import sqlite3
from database import DatabaseManager
import json

import sqlite3
from database import DatabaseManager

class DataPersistence:
    def __init__(self):
        self.db = DatabaseManager()
        self.init_persistence_tables()
    
    def init_persistence_tables(self):
        """Initialize data persistence tables"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # User portfolio holdings (persistent)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_portfolio_holdings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    symbol TEXT NOT NULL,
                    shares REAL NOT NULL,
                    avg_cost REAL NOT NULL,
                    total_cost REAL NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    UNIQUE(user_id, symbol)
                )
            """)
            
            # User portfolio transactions (persistent)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_portfolio_transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    symbol TEXT NOT NULL,
                    action TEXT NOT NULL,
                    shares REAL NOT NULL,
                    price REAL NOT NULL,
                    total REAL NOT NULL,
                    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            # User watchlists (persistent)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_watchlists (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    symbol TEXT NOT NULL,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    UNIQUE(user_id, symbol)
                )
            """)
            
            # User price alerts (persistent)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_price_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    symbol TEXT NOT NULL,
                    alert_type TEXT NOT NULL,
                    target_price REAL NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    triggered_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            conn.commit()
    
    def save_portfolio_holding(self, user_id, symbol, shares, avg_cost, total_cost):
        """Save portfolio holding to database"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO user_portfolio_holdings 
                (user_id, symbol, shares, avg_cost, total_cost, updated_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (user_id, symbol, shares, avg_cost, total_cost))
            conn.commit()
    
    def get_user_portfolio(self, user_id):
        """Get user's portfolio from database"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT symbol, shares, avg_cost, total_cost
                FROM user_portfolio_holdings
                WHERE user_id = ?
            """, (user_id,))
            return cursor.fetchall()
    
    def add_portfolio_transaction(self, user_id, symbol, action, shares, price, total):
        """Add portfolio transaction to database"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO user_portfolio_transactions 
                (user_id, symbol, action, shares, price, total)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, symbol, action, shares, price, total))
            conn.commit()
    
    def get_user_transactions(self, user_id):
        """Get user's transaction history"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT symbol, action, shares, price, total, transaction_date
                FROM user_portfolio_transactions
                WHERE user_id = ?
                ORDER BY transaction_date DESC
            """, (user_id,))
            return cursor.fetchall()
    
    def save_watchlist_item(self, user_id, symbol):
        """Add symbol to user's watchlist"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO user_watchlists (user_id, symbol)
                    VALUES (?, ?)
                """, (user_id, symbol))
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            return False
    
    def get_user_watchlist(self, user_id):
        """Get user's watchlist"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT symbol FROM user_watchlists 
                WHERE user_id = ?
                ORDER BY added_at DESC
            """, (user_id,))
            return [row['symbol'] for row in cursor.fetchall()]
    
    def remove_watchlist_item(self, user_id, symbol):
        """Remove symbol from user's watchlist"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM user_watchlists 
                WHERE user_id = ? AND symbol = ?
            """, (user_id, symbol))
            conn.commit()
    
    def save_price_alert(self, user_id, symbol, alert_type, target_price):
        """Save price alert"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO user_price_alerts (user_id, symbol, alert_type, target_price)
                VALUES (?, ?, ?, ?)
            """, (user_id, symbol, alert_type, target_price))
            conn.commit()
    
    def get_user_alerts(self, user_id, active_only=True):
        """Get user's price alerts"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM user_price_alerts WHERE user_id = ?"
            params = [user_id]
            
            if active_only:
                query += " AND is_active = 1"
            
            cursor.execute(query, params)
            return cursor.fetchall()

# Global instance
data_persistence = DataPersistence()