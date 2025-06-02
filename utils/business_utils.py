import sqlite3
from datetime import datetime, timedelta
import json
from database import DatabaseManager

class BusinessUtils:
    def __init__(self):
        self.db = DatabaseManager()
    
    def init_business_tables(self):
        """Initialize all business-related tables"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Product categories
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS product_categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Products/Inventory
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sku TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    category_id INTEGER,
                    barcode TEXT,
                    cost_price REAL NOT NULL,
                    selling_price REAL NOT NULL,
                    current_stock INTEGER DEFAULT 0,
                    minimum_stock INTEGER DEFAULT 10,
                    maximum_stock INTEGER DEFAULT 1000,
                    location TEXT,
                    expiry_date DATE,
                    supplier_id INTEGER,
                    image_url TEXT,
                    custom_attributes TEXT DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (category_id) REFERENCES product_categories (id),
                    FOREIGN KEY (supplier_id) REFERENCES suppliers (id)
                )
            """)
            
            # Suppliers
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS suppliers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    contact_person TEXT,
                    email TEXT,
                    phone TEXT,
                    address TEXT,
                    rating REAL DEFAULT 0,
                    payment_terms TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Sales transactions
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sales_transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transaction_id TEXT UNIQUE NOT NULL,
                    customer_id INTEGER,
                    total_amount REAL NOT NULL,
                    discount_amount REAL DEFAULT 0,
                    tax_amount REAL DEFAULT 0,
                    payment_method TEXT,
                    status TEXT DEFAULT 'completed',
                    sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    cashier_id INTEGER,
                    notes TEXT,
                    FOREIGN KEY (customer_id) REFERENCES customers (id),
                    FOREIGN KEY (cashier_id) REFERENCES users (id)
                )
            """)
            
            # Customers
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS customers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_code TEXT UNIQUE,
                    name TEXT NOT NULL,
                    email TEXT,
                    phone TEXT,
                    address TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_purchase_date TIMESTAMP
                )
            """)
            
            # Stock movements
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS stock_movements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER NOT NULL,
                    movement_type TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    reference_number TEXT,
                    notes TEXT,
                    user_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_id) REFERENCES products (id),
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            conn.commit()
    
    def update_stock(self, product_id, quantity, movement_type, reference_number=None, notes=None, user_id=None):
        """Update product stock and record movement"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Update product stock
            if movement_type in ['purchase', 'adjustment_in', 'return']:
                cursor.execute("""
                    UPDATE products SET current_stock = current_stock + ?, 
                    updated_at = CURRENT_TIMESTAMP WHERE id = ?
                """, (quantity, product_id))
            else:  # sale, adjustment_out, damage
                cursor.execute("""
                    UPDATE products SET current_stock = current_stock - ?, 
                    updated_at = CURRENT_TIMESTAMP WHERE id = ?
                """, (quantity, product_id))
            
            # Record stock movement
            cursor.execute("""
                INSERT INTO stock_movements (product_id, movement_type, quantity, 
                                           reference_number, notes, user_id)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (product_id, movement_type, quantity, reference_number, notes, user_id))
            
            conn.commit()
    
    def get_low_stock_products(self):
        """Get products with low stock"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.*, pc.name as category_name
                FROM products p
                LEFT JOIN product_categories pc ON p.category_id = pc.id
                WHERE p.current_stock <= p.minimum_stock
                ORDER BY (p.current_stock - p.minimum_stock) ASC
            """)
            return cursor.fetchall()
    
    def find_product_by_barcode(self, barcode):
        """Find product by barcode"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.*, pc.name as category_name
                FROM products p
                LEFT JOIN product_categories pc ON p.category_id = pc.id
                WHERE p.barcode = ?
            """, (barcode,))
            return cursor.fetchone()
    
    def find_product_by_sku(self, sku):
        """Find product by SKU"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.*, pc.name as category_name
                FROM products p
                LEFT JOIN product_categories pc ON p.category_id = pc.id
                WHERE p.sku = ?
            """, (sku,))
            return cursor.fetchone()

# Initialize business tables on import
business_utils = BusinessUtils()
business_utils.init_business_tables()