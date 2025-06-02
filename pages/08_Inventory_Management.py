import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from auth import init_auth, get_current_user, require_auth
from database import DatabaseManager
import json

st.set_page_config(page_title="Inventory Management", page_icon="📦", layout="wide")

# Load custom CSS
with open('static/css/style.css', 'r') as f:
    css = f.read()
st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)

# Initialize authentication
init_auth()

class InventoryManager:
    def __init__(self):
        self.db = DatabaseManager()
        self.init_inventory_tables()

    def init_inventory_tables(self):
        """Initialize inventory management tables"""
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

            # Purchase orders
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS purchase_orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    po_number TEXT UNIQUE NOT NULL,
                    supplier_id INTEGER NOT NULL,
                    status TEXT DEFAULT 'pending',
                    total_amount REAL DEFAULT 0,
                    order_date DATE NOT NULL,
                    expected_delivery DATE,
                    actual_delivery DATE,
                    notes TEXT,
                    created_by INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (supplier_id) REFERENCES suppliers (id),
                    FOREIGN KEY (created_by) REFERENCES users (id)
                )
            """)

            # Purchase order items
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS purchase_order_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    po_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    quantity INTEGER NOT NULL,
                    unit_price REAL NOT NULL,
                    received_quantity INTEGER DEFAULT 0,
                    FOREIGN KEY (po_id) REFERENCES purchase_orders (id),
                    FOREIGN KEY (product_id) REFERENCES products (id)
                )
            """)

            # Stock alerts
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS stock_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER NOT NULL,
                    alert_type TEXT NOT NULL,
                    threshold_value REAL,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_id) REFERENCES products (id)
                )
            """)

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

    def get_expiring_products(self, days=30):
        """Get products expiring within specified days"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.*, pc.name as category_name
                FROM products p
                LEFT JOIN product_categories pc ON p.category_id = pc.id
                WHERE p.expiry_date IS NOT NULL 
                AND p.expiry_date <= DATE('now', '+{} days')
                ORDER BY p.expiry_date ASC
            """.format(days))
            return cursor.fetchall()

    def add_product(self, product_data):
        """Add new product"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO products (sku, name, description, category_id, barcode, 
                                    cost_price, selling_price, current_stock, minimum_stock, 
                                    maximum_stock, location, expiry_date, supplier_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                product_data['sku'], product_data['name'], product_data['description'],
                product_data['category_id'], product_data['barcode'], product_data['cost_price'],
                product_data['selling_price'], product_data['current_stock'], 
                product_data['minimum_stock'], product_data['maximum_stock'],
                product_data['location'], product_data['expiry_date'], product_data['supplier_id']
            ))
            conn.commit()
            return cursor.lastrowid

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

    def get_inventory_overview(self):
        """Get inventory overview statistics"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()

                # Check if products table exists
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='products'")
                if not cursor.fetchone():
                    return {
                        'total_products': 0,
                        'low_stock_items': 0,
                        'out_of_stock_items': 0,
                        'total_value': 0
                    }

                # Total products
                cursor.execute("SELECT COUNT(*) as count FROM products")
                total_products = cursor.fetchone()['count']

                # Low stock items
                cursor.execute("SELECT COUNT(*) as count FROM products WHERE current_stock <= minimum_stock")
                low_stock_items = cursor.fetchone()['count']

                # Out of stock items
                cursor.execute("SELECT COUNT(*) as count FROM products WHERE current_stock = 0")
                out_of_stock_items = cursor.fetchone()['count']

                # Total inventory value
                cursor.execute("SELECT COALESCE(SUM(current_stock * unit_cost), 0) as total_value FROM products")
                total_value = cursor.fetchone()['total_value']

                return {
                    'total_products': total_products,
                    'low_stock_items': low_stock_items,
                    'out_of_stock_items': out_of_stock_items,
                    'total_value': total_value
                }
        except Exception as e:
            return {
                'total_products': 0,
                'low_stock_items': 0,
                'out_of_stock_items': 0,
                'total_value': 0
            }

@require_auth
def main():
    try:
        user = get_current_user()
        inventory_manager = InventoryManager()

        st.title("📦 Inventory Management")
        st.markdown(f"Comprehensive inventory tracking and management system for **{user['username']}**")
    except Exception as e:
        st.error("Error initializing inventory management. Please try refreshing the page.")
        st.stop()

    # Main navigation tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Dashboard", "📦 Products", "📋 Stock Movements", 
        "🏪 Suppliers", "📝 Purchase Orders", "⚠️ Alerts"
    ])

    with tab1:
        # Inventory Dashboard
        st.subheader("Inventory Overview")

        # Key metrics
        with inventory_manager.db.get_connection() as conn:
            cursor = conn.cursor()

            # Total products
            cursor.execute("SELECT COUNT(*) as count FROM products")
            total_products = cursor.fetchone()['count']

            # Total stock value
            cursor.execute("SELECT SUM(current_stock * cost_price) as value FROM products")
            total_value = cursor.fetchone()['value'] or 0

            # Low stock products
            low_stock = len(inventory_manager.get_low_stock_products())

            # Recent movements
            cursor.execute("""
                SELECT COUNT(*) as count FROM stock_movements 
                WHERE DATE(created_at) = DATE('now')
            """)
            today_movements = cursor.fetchone()['count']

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Products", total_products)

        with col2:
            st.metric("Inventory Value", f"${total_value:,.2f}")

        with col3:
            st.metric("Low Stock Items", low_stock, delta_color="inverse")

        with col4:
            st.metric("Today's Movements", today_movements)

        # Low stock alerts
        st.subheader("🚨 Low Stock Alerts")
        low_stock_products = inventory_manager.get_low_stock_products()

        if low_stock_products:
            low_stock_df = pd.DataFrame(low_stock_products)
            # Check which columns exist before selecting
            available_columns = ['sku', 'name', 'current_stock', 'minimum_stock']
            if 'category_name' in low_stock_df.columns:
                available_columns.append('category_name')

            if not low_stock_df.empty:
                # Check which columns are available
                available_columns = [col for col in ['sku', 'name', 'current_stock', 'minimum_stock'] if col in low_stock_df.columns]

                if available_columns:
                    # Only select available columns that exist
                    display_df = low_stock_df[available_columns]
                    st.dataframe(
                        display_df,
                        use_container_width=True
                    )
                else:
                    # If no expected columns exist, show the dataframe as is
                    st.dataframe(low_stock_df, use_container_width=True)
        else:
            st.success("All products are adequately stocked!")

        # Expiring products
        st.subheader("📅 Expiring Products (Next 30 Days)")
        expiring_products = inventory_manager.get_expiring_products()

        if expiring_products:
            expiring_df = pd.DataFrame(expiring_products)
            # Check available columns
            available_columns = [col for col in ['sku', 'name', 'current_stock', 'expiry_date', 'category_name'] if col in expiring_df.columns]
            
            if available_columns:
                st.dataframe(
                    expiring_df[available_columns],
                    use_container_width=True
                )
            else:
                st.dataframe(expiring_df, use_container_width=True)
        else:
            st.success("No products expiring in the next 30 days!")

    with tab2:
        # Products Management
        st.subheader("Product Management")

        # Add new product form
        with st.expander("➕ Add New Product"):
            col1, col2 = st.columns(2)

            with col1:
                sku = st.text_input("SKU*", help="Unique product identifier")
                name = st.text_input("Product Name*")
                description = st.text_area("Description")

                # Categories
                with inventory_manager.db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT id, name FROM product_categories")
                    categories = cursor.fetchall()

                if categories:
                    category_options = {cat['name']: cat['id'] for cat in categories}
                    selected_category = st.selectbox("Category", options=list(category_options.keys()))
                    category_id = category_options.get(selected_category)
                else:
                    st.info("No categories found. Add categories first.")
                    category_id = None

                barcode = st.text_input("Barcode")

            with col2:
                cost_price = st.number_input("Cost Price*", min_value=0.0, step=0.01)
                selling_price = st.number_input("Selling Price*", min_value=0.0, step=0.01)
                current_stock = st.number_input("Current Stock", min_value=0, value=0)
                minimum_stock = st.number_input("Minimum Stock", min_value=0, value=10)
                maximum_stock = st.number_input("Maximum Stock", min_value=0, value=1000)
                location = st.text_input("Storage Location")
                expiry_date = st.date_input("Expiry Date (Optional)", value=None)

            if st.button("Add Product"):
                if sku and name and cost_price and selling_price:
                    try:
                        # Check if SKU already exists
                        with inventory_manager.db.get_connection() as conn:
                            cursor = conn.cursor()
                            cursor.execute("SELECT COUNT(*) as count FROM products WHERE sku = ?", (sku,))
                            result = cursor.fetchone()
                            existing_sku = result['count'] if result else 0
                        
                        if existing_sku > 0:
                            st.error(f"SKU '{sku}' already exists. Please use a unique SKU.")
                        else:
                            try:
                                product_data = {
                                'sku': sku,
                                'name': name,
                                'description': description,
                                'category_id': category_id,
                                'barcode': barcode,
                                'cost_price': cost_price,
                                'selling_price': selling_price,
                                'current_stock': current_stock,
                                'minimum_stock': minimum_stock,
                                'maximum_stock': maximum_stock,
                                'location': location,
                                'expiry_date': expiry_date,
                                'supplier_id': None
                            }

                            product_id = inventory_manager.add_product(product_data)

                            # Record initial stock if any
                            if current_stock > 0:
                                inventory_manager.update_stock(
                                    product_id, current_stock, 'initial_stock', 
                                    notes="Initial stock entry", user_id=user['id']
                                )

                            st.success(f"Product '{name}' added successfully!")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error adding product: {str(e)}")
                else:
                    st.error("Please fill in all required fields (*)")

        # Product list
        st.subheader("Product Inventory")

        # Search and filters
        col1, col2, col3 = st.columns(3)

        with col1:
            search_term = st.text_input("Search Products", placeholder="Search by name or SKU")

        with col2:
            stock_filter = st.selectbox("Stock Level", ["All", "In Stock", "Low Stock", "Out of Stock"])

        with col3:
            category_filter = st.selectbox("Category", ["All"] + [cat['name'] for cat in categories])

        # Get products with filters
        with inventory_manager.db.get_connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT p.*, pc.name as category_name, s.name as supplier_name
                FROM products p
                LEFT JOIN product_categories pc ON p.category_id = pc.id
                LEFT JOIN suppliers s ON p.supplier_id = s.id
                WHERE 1=1
            """
            params = []

            if search_term:
                query += " AND (p.name LIKE ? OR p.sku LIKE ?)"
                params.extend([f"%{search_term}%", f"%{search_term}%"])

            if stock_filter == "In Stock":
                query += " AND p.current_stock > p.minimum_stock"
            elif stock_filter == "Low Stock":
                query += " AND p.current_stock <= p.minimum_stock AND p.current_stock > 0"
            elif stock_filter == "Out of Stock":
                query += " AND p.current_stock = 0"

            if category_filter != "All":
                query += " AND pc.name = ?"
                params.append(category_filter)

            query += " ORDER BY p.name"

            cursor.execute(query, params)
            products = cursor.fetchall()

        if products:
            products_df = pd.DataFrame(products)

            # Display products table
            display_columns = ['sku', 'name', 'category_name', 'current_stock', 'minimum_stock', 
                             'cost_price', 'selling_price', 'location']

            # Check which columns exist
            available_columns = [col for col in display_columns if col in products_df.columns]
            if available_columns:
                st.dataframe(
                    products_df[available_columns],
                    use_container_width=True
                )
            else:
                st.info("No product data available")
        else:
            st.info("No products found matching the criteria.")

    with tab3:
        # Stock Movements
        st.subheader("Stock Movements")

        # Quick stock adjustment
        with st.expander("🔄 Quick Stock Adjustment"):
            col1, col2, col3 = st.columns(3)

            with col1:
                # Product selection
                with inventory_manager.db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT id, sku, name FROM products ORDER BY name")
                    products = cursor.fetchall()

                if products:
                    product_options = {f"{p['sku']} - {p['name']}": p['id'] for p in products}
                    selected_product = st.selectbox("Select Product", options=list(product_options.keys()))
                    product_id = product_options.get(selected_product)
                else:
                    st.warning("No products available")
                    product_id = None

            with col2:
                movement_type = st.selectbox("Movement Type", 
                    ["purchase", "sale", "adjustment_in", "adjustment_out", "damage", "return"])
                quantity = st.number_input("Quantity", min_value=1, value=1)

            with col3:
                reference_number = st.text_input("Reference Number")
                notes = st.text_area("Notes")

            if st.button("Record Movement") and product_id:
                try:
                    inventory_manager.update_stock(
                        product_id, quantity, movement_type, 
                        reference_number, notes, user['id']
                    )
                    st.success("Stock movement recorded successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error recording movement: {str(e)}")

        # Recent stock movements
        st.subheader("Recent Stock Movements")

        with inventory_manager.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT sm.*, p.sku, p.name as product_name, u.username
                FROM stock_movements sm
                JOIN products p ON sm.product_id = p.id
                LEFT JOIN users u ON sm.user_id = u.id
                ORDER BY sm.created_at DESC
                LIMIT 50
            """)
            movements = cursor.fetchall()

        if movements:
            movements_df = pd.DataFrame(movements)
            # Check which columns exist and only display available ones
            available_columns = []
            for col in ['created_at', 'sku', 'product_name', 'movement_type', 'quantity', 'reference_number', 'username']:
                if col in movements_df.columns:
                    available_columns.append(col)
            
            if available_columns:
                st.dataframe(
                    movements_df[available_columns],
                    use_container_width=True
                )
            else:
                st.dataframe(movements_df, use_container_width=True)
        else:
            st.info("No stock movements recorded yet.")

    with tab4:
        # Suppliers Management
        st.subheader("Supplier Management")

        # Add supplier
        with st.expander("➕ Add New Supplier"):
            col1, col2 = st.columns(2)

            with col1:
                supplier_name = st.text_input("Supplier Name*")
                contact_person = st.text_input("Contact Person")
                email = st.text_input("Email")

            with col2:
                phone = st.text_input("Phone")
                address = st.text_area("Address")
                payment_terms = st.text_input("Payment Terms")

            if st.button("Add Supplier"):
                if supplier_name:
                    try:
                        with inventory_manager.db.get_connection() as conn:
                            cursor = conn.cursor()
                            cursor.execute("""
                                INSERT INTO suppliers (name, contact_person, email, phone, address, payment_terms)
                                VALUES (?, ?, ?, ?, ?, ?)
                            """, (supplier_name, contact_person, email, phone, address, payment_terms))
                            conn.commit()

                        st.success(f"Supplier '{supplier_name}' added successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error adding supplier: {str(e)}")
                else:
                    st.error("Supplier name is required")

        # Suppliers list
        with inventory_manager.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM suppliers ORDER BY name")
            suppliers = cursor.fetchall()

        if suppliers:
            suppliers_df = pd.DataFrame(suppliers)
            st.dataframe(suppliers_df, use_container_width=True)
        else:
            st.info("No suppliers added yet.")

    with tab5:
        # Purchase Orders
        st.subheader("Purchase Order Management")
        st.info("Purchase order functionality requires supplier integration. This feature tracks orders from suppliers.")

        # Create PO placeholder
        with st.expander("➕ Create Purchase Order"):
            st.write("Feature coming soon - Full purchase order management system")

    with tab6:
        # Alerts and Notifications
        st.subheader("Inventory Alerts")

        # Alert configuration
        with st.expander("⚙️ Configure Alerts"):
            alert_types = st.multiselect(
                "Alert Types",
                ["Low Stock", "Out of Stock", "Expiring Products", "Overstock"],
                default=["Low Stock", "Out of Stock"]
            )

            notification_methods = st.multiselect(
                "Notification Methods",
                ["Email", "In-App", "SMS"],
                default=["In-App"]
            )

            if st.button("Save Alert Settings"):
                st.success("Alert settings saved!")

        # Current alerts
        st.subheader("Active Alerts")

        alerts = []

        # Low stock alerts
        low_stock = inventory_manager.get_low_stock_products()
        for product in low_stock:
            alerts.append({
                'type': 'Low Stock',
                'product': f"{product['sku']} - {product['name']}",
                'message': f"Stock level: {product['current_stock']} (Min: {product['minimum_stock']})",
                'severity': 'warning'
            })

        # Expiring products
        expiring = inventory_manager.get_expiring_products()
        for product in expiring:
            alerts.append({
                'type': 'Expiring Soon',
                'product': f"{product['sku']} - {product['name']}",
                'message': f"Expires: {product['expiry_date']}",
                'severity': 'warning'
            })

        if alerts:
            for alert in alerts:
                if alert['severity'] == 'warning':
                    st.warning(f"**{alert['type']}** - {alert['product']}: {alert['message']}")
                else:
                    st.error(f"**{alert['type']}** - {alert['product']}: {alert['message']}")
        else:
            st.success("No active alerts!")

if __name__ == "__main__":
    main()