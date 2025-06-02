import streamlit as st
import pandas as pd
from datetime import datetime
from auth import init_auth, get_current_user, require_auth
from database import DatabaseManager
import streamlit.components.v1 as components

st.set_page_config(page_title="Barcode Scanner", page_icon="📱", layout="wide")

# Load custom CSS
with open('static/css/style.css', 'r') as f:
    css = f.read()
st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)

# Initialize authentication
init_auth()

class BarcodeManager:
    def __init__(self):
        self.db = DatabaseManager()
    
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
        """Find product by SKU as fallback"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.*, pc.name as category_name
                FROM products p
                LEFT JOIN product_categories pc ON p.category_id = pc.id
                WHERE p.sku = ?
            """, (sku,))
            return cursor.fetchone()

@require_auth
def main():
    user = get_current_user()
    barcode_manager = BarcodeManager()
    
    st.title("📱 Barcode Scanner & Quick Operations")
    st.markdown(f"Scan barcodes for instant product operations, **{user['username']}**")
    
    # Barcode scanner interface
    st.subheader("🔍 Barcode Scanner")
    
    # Camera-based scanner (requires webcam access)
    scanner_html = """
    <div id="scanner-container">
        <video id="preview" style="width: 100%; max-width: 400px; border: 2px solid #3b82f6; border-radius: 8px;"></video>
        <div id="scanner-controls" style="margin-top: 10px;">
            <button id="start-scan" onclick="startScanner()" style="background: #3b82f6; color: white; border: none; padding: 10px 20px; border-radius: 5px; margin-right: 10px;">Start Scanner</button>
            <button id="stop-scan" onclick="stopScanner()" style="background: #ef4444; color: white; border: none; padding: 10px 20px; border-radius: 5px;">Stop Scanner</button>
        </div>
        <div id="result" style="margin-top: 10px; font-weight: bold;"></div>
    </div>
    
    <script src="https://unpkg.com/@zxing/library@latest/umd/index.min.js"></script>
    <script>
        let codeReader = null;
        let scanning = false;
        
        function startScanner() {
            if (scanning) return;
            
            codeReader = new ZXing.BrowserBarcodeReader();
            scanning = true;
            
            codeReader.decodeFromVideoDevice(undefined, 'preview', (result, err) => {
                if (result) {
                    document.getElementById('result').innerHTML = 'Barcode detected: ' + result.text;
                    window.parent.postMessage({type: 'barcode', data: result.text}, '*');
                    stopScanner();
                }
                if (err && !(err instanceof ZXing.NotFoundException)) {
                    console.error(err);
                }
            });
        }
        
        function stopScanner() {
            if (codeReader) {
                codeReader.reset();
                scanning = false;
            }
        }
    </script>
    """
    
    # Display scanner interface
    with st.expander("📷 Camera Barcode Scanner", expanded=True):
        st.markdown("**Note:** Camera access required for barcode scanning")
        components.html(scanner_html, height=500)
        
        # Manual barcode input as fallback
        st.markdown("---")
        st.subheader("Manual Barcode Entry")
        manual_barcode = st.text_input("Enter Barcode/SKU", placeholder="Scan or type barcode/SKU")
        
        if st.button("Search Product") and manual_barcode:
            # Search by barcode first, then by SKU
            product = barcode_manager.find_product_by_barcode(manual_barcode)
            if not product:
                product = barcode_manager.find_product_by_sku(manual_barcode)
            
            if product:
                st.session_state.scanned_product = product
                st.success(f"Product found: {product['name']}")
                st.rerun()
            else:
                st.error("Product not found. Check barcode/SKU or add product to inventory first.")
    
    # Product details and operations
    if 'scanned_product' in st.session_state:
        product = st.session_state.scanned_product
        
        st.subheader(f"📦 Product: {product['name']}")
        
        # Product information display
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("SKU", product['sku'])
            st.metric("Current Stock", product['current_stock'])
        
        with col2:
            st.metric("Cost Price", f"${product['cost_price']:.2f}")
            st.metric("Selling Price", f"${product['selling_price']:.2f}")
        
        with col3:
            st.metric("Category", product['category_name'] or 'Uncategorized')
            st.metric("Location", product['location'] or 'Not specified')
        
        # Quick operations
        st.subheader("⚡ Quick Operations")
        
        operation_tabs = st.tabs(["📦 Stock Update", "💰 Quick Sale", "📋 Product Info"])
        
        with operation_tabs[0]:
            # Stock update
            st.write("**Update Stock Levels**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                operation_type = st.selectbox(
                    "Operation Type",
                    ["Stock In", "Stock Out", "Adjustment", "Damage/Loss"]
                )
                
                quantity = st.number_input("Quantity", min_value=1, value=1)
            
            with col2:
                reference = st.text_input("Reference Number")
                notes = st.text_area("Notes")
            
            if st.button("Update Stock"):
                try:
                    # Map operation types to database values
                    operation_mapping = {
                        "Stock In": "purchase",
                        "Stock Out": "sale", 
                        "Adjustment": "adjustment_in",
                        "Damage/Loss": "damage"
                    }
                    
                    movement_type = operation_mapping[operation_type]
                    
                    # Update stock using business utils
                    from utils.business_utils import business_utils
                    
                    business_utils.update_stock(
                        product['id'], quantity, movement_type,
                        reference, notes, user['id']
                    )
                    
                    st.success(f"Stock updated: {operation_type} of {quantity} units")
                    
                    # Refresh product data
                    updated_product = barcode_manager.find_product_by_barcode(product['barcode'])
                    if updated_product:
                        st.session_state.scanned_product = updated_product
                    
                    st.rerun()
                
                except Exception as e:
                    st.error(f"Error updating stock: {str(e)}")
        
        with operation_tabs[1]:
            # Quick sale
            st.write("**Process Quick Sale**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                sale_quantity = st.number_input("Sale Quantity", min_value=1, value=1, max_value=product['current_stock'])
                unit_price = st.number_input("Unit Price", value=float(product['selling_price']), step=0.01)
            
            with col2:
                discount = st.number_input("Discount Amount", value=0.0, step=0.01)
                payment_method = st.selectbox("Payment Method", ["Cash", "Card", "Digital"])
            
            total_amount = (sale_quantity * unit_price) - discount
            st.metric("Total Amount", f"${total_amount:.2f}")
            
            if st.button("Process Sale"):
                if sale_quantity <= product['current_stock']:
                    try:
                        # Record sale transaction
                        transaction_id = f"QS{datetime.now().strftime('%Y%m%d%H%M%S')}"
                        
                        with barcode_manager.db.get_connection() as conn:
                            cursor = conn.cursor()
                            
                            # Insert sale transaction
                            cursor.execute("""
                                INSERT INTO sales_transactions 
                                (transaction_id, total_amount, discount_amount, payment_method, cashier_id)
                                VALUES (?, ?, ?, ?, ?)
                            """, (transaction_id, total_amount, discount, payment_method, user['id']))
                            
                            sale_id = cursor.lastrowid
                            
                            # Insert transaction item
                            cursor.execute("""
                                INSERT INTO sales_transaction_items 
                                (transaction_id, product_id, quantity, unit_price, discount_amount, total_price)
                                VALUES (?, ?, ?, ?, ?, ?)
                            """, (sale_id, product['id'], sale_quantity, unit_price, discount, total_amount))
                            
                            conn.commit()
                        
                        # Update stock
                        from pages.page_08_Inventory_Management import InventoryManager
                        inventory_manager = InventoryManager()
                        inventory_manager.update_stock(
                            product['id'], sale_quantity, 'sale',
                            transaction_id, f"Quick sale via barcode scanner", user['id']
                        )
                        
                        st.success(f"Sale processed! Transaction ID: {transaction_id}")
                        st.balloons()
                        
                        # Refresh product data
                        updated_product = barcode_manager.find_product_by_barcode(product['barcode'])
                        if updated_product:
                            st.session_state.scanned_product = updated_product
                        
                        st.rerun()
                    
                    except Exception as e:
                        st.error(f"Error processing sale: {str(e)}")
                else:
                    st.error(f"Insufficient stock! Available: {product['current_stock']}")
        
        with operation_tabs[2]:
            # Product information
            st.write("**Detailed Product Information**")
            
            info_data = {
                "Field": ["SKU", "Name", "Description", "Category", "Barcode", "Cost Price", 
                         "Selling Price", "Current Stock", "Minimum Stock", "Maximum Stock", 
                         "Location", "Expiry Date"],
                "Value": [
                    product['sku'], product['name'], product['description'] or 'N/A',
                    product['category_name'] or 'Uncategorized', product['barcode'] or 'N/A',
                    f"${product['cost_price']:.2f}", f"${product['selling_price']:.2f}",
                    product['current_stock'], product['minimum_stock'], product['maximum_stock'],
                    product['location'] or 'Not specified', product['expiry_date'] or 'N/A'
                ]
            }
            
            info_df = pd.DataFrame(info_data)
            st.dataframe(info_df, use_container_width=True, hide_index=True)
            
            # Stock history
            st.write("**Recent Stock Movements**")
            
            with barcode_manager.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT sm.*, u.username
                    FROM stock_movements sm
                    LEFT JOIN users u ON sm.user_id = u.id
                    WHERE sm.product_id = ?
                    ORDER BY sm.created_at DESC
                    LIMIT 10
                """, (product['id'],))
                movements = cursor.fetchall()
            
            if movements:
                movements_df = pd.DataFrame(movements)
                st.dataframe(
                    movements_df[['created_at', 'movement_type', 'quantity', 'reference_number', 'username']],
                    use_container_width=True
                )
            else:
                st.info("No stock movements recorded for this product.")
        
        # Clear selection
        if st.button("🔄 Scan Another Product"):
            del st.session_state.scanned_product
            st.rerun()
    
    # Recent scanned products
    if 'recent_scans' not in st.session_state:
        st.session_state.recent_scans = []
    
    if st.session_state.recent_scans:
        st.subheader("📋 Recent Scanned Products")
        
        for i, recent_product in enumerate(st.session_state.recent_scans[-5:]):  # Show last 5
            with st.expander(f"{recent_product['name']} ({recent_product['sku']})"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**Stock:** {recent_product['current_stock']}")
                
                with col2:
                    st.write(f"**Price:** ${recent_product['selling_price']:.2f}")
                
                with col3:
                    if st.button("Scan Again", key=f"rescan_{i}"):
                        st.session_state.scanned_product = recent_product
                        st.rerun()
    
    # Help and tips
    with st.expander("💡 Barcode Scanner Tips"):
        st.markdown("""
        **Using the Barcode Scanner:**
        
        1. **Camera Scanner**: Click "Start Scanner" to use your device camera
        2. **Manual Entry**: Type barcodes or SKUs if camera is unavailable
        3. **Quick Operations**: Perform stock updates and sales directly after scanning
        4. **Mobile Friendly**: Works on smartphones and tablets for mobility
        
        **Best Practices:**
        - Ensure good lighting for camera scanning
        - Hold barcode steady and at appropriate distance
        - Use manual entry as backup method
        - Always verify product details before operations
        
        **Security:** All operations are logged with user authentication for audit trails.
        """)

if __name__ == "__main__":
    main()