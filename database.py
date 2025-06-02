import os
import bcrypt
import sqlite3
from datetime import datetime
import json
from contextlib import contextmanager

class DatabaseManager:
    def __init__(self, db_path="stock_app.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    settings TEXT DEFAULT '{}',
                    is_active BOOLEAN DEFAULT 1
                )
            """)
            
            # User portfolios
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS portfolios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    symbol TEXT NOT NULL,
                    shares REAL NOT NULL,
                    avg_cost REAL NOT NULL,
                    total_cost REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    UNIQUE(user_id, symbol)
                )
            """)
            
            # User transactions
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
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
            
            # User watchlists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS watchlists (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    symbol TEXT NOT NULL,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    UNIQUE(user_id, symbol)
                )
            """)
            
            # Price alerts
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS price_alerts (
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
            
            # User activity log
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_activity (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    action TEXT NOT NULL,
                    details TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            conn.commit()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def hash_password(self, password):
        """Hash password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def verify_password(self, password, hashed):
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def create_user(self, username, email, password):
        """Create a new user"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                password_hash = self.hash_password(password)
                
                cursor.execute("""
                    INSERT INTO users (username, email, password_hash)
                    VALUES (?, ?, ?)
                """, (username, email, password_hash))
                
                conn.commit()
                return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None
    
    def authenticate_user(self, username, password):
        """Authenticate user login"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, username, email, password_hash, settings
                FROM users 
                WHERE (username = ? OR email = ?) AND is_active = 1
            """, (username, username))
            
            user = cursor.fetchone()
            if user and self.verify_password(password, user['password_hash']):
                # Update last login
                cursor.execute("""
                    UPDATE users SET last_login = CURRENT_TIMESTAMP 
                    WHERE id = ?
                """, (user['id'],))
                conn.commit()
                
                return {
                    'id': user['id'],
                    'username': user['username'],
                    'email': user['email'],
                    'settings': json.loads(user['settings'] or '{}')
                }
        return None
    
    def log_activity(self, user_id, action, details=None, ip_address=None, user_agent=None):
        """Log user activity"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO user_activity (user_id, action, details, ip_address, user_agent)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, action, details, ip_address, user_agent))
            conn.commit()
    
    def update_user_settings(self, user_id, settings):
        """Update user settings"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE users SET settings = ? WHERE id = ?
            """, (json.dumps(settings), user_id))
            conn.commit()
    
    def get_user_portfolio(self, user_id):
        """Get user's portfolio"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT symbol, shares, avg_cost, total_cost
                FROM portfolios 
                WHERE user_id = ?
            """, (user_id,))
            return cursor.fetchall()
    
    def update_portfolio(self, user_id, symbol, shares, avg_cost, total_cost):
        """Update or insert portfolio holding"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO portfolios 
                (user_id, symbol, shares, avg_cost, total_cost, updated_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (user_id, symbol, shares, avg_cost, total_cost))
            conn.commit()
    
    def add_transaction(self, user_id, symbol, action, shares, price, total):
        """Add a transaction record"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO transactions 
                (user_id, symbol, action, shares, price, total)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, symbol, action, shares, price, total))
            conn.commit()
    
    def get_user_transactions(self, user_id):
        """Get user's transaction history"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT symbol, action, shares, price, total, transaction_date
                FROM transactions 
                WHERE user_id = ?
                ORDER BY transaction_date DESC
            """, (user_id,))
            return cursor.fetchall()
    
    def get_user_watchlist(self, user_id):
        """Get user's watchlist"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT symbol, added_at FROM watchlists 
                WHERE user_id = ?
                ORDER BY added_at DESC
            """, (user_id,))
            return [row['symbol'] for row in cursor.fetchall()]
    
    def add_to_watchlist(self, user_id, symbol):
        """Add symbol to user's watchlist"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO watchlists (user_id, symbol)
                    VALUES (?, ?)
                """, (user_id, symbol))
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            return False
    
    def remove_from_watchlist(self, user_id, symbol):
        """Remove symbol from user's watchlist"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM watchlists 
                WHERE user_id = ? AND symbol = ?
            """, (user_id, symbol))
            conn.commit()