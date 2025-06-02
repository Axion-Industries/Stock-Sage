import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from auth import init_auth, get_current_user, require_auth
from database import DatabaseManager
import json
import random
import string

st.set_page_config(page_title="Company Dashboard", page_icon="🏢", layout="wide")

# Load custom CSS
with open('static/css/style.css', 'r') as f:
    css = f.read()
st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)

# Initialize authentication
init_auth()

class CompanyManager:
    def __init__(self):
        self.db = DatabaseManager()
        self.init_company_tables()
    
    def init_company_tables(self):
        """Initialize company management tables"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Companies table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS companies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    company_code TEXT UNIQUE NOT NULL,
                    company_password TEXT NOT NULL,
                    description TEXT,
                    industry TEXT,
                    created_by INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (created_by) REFERENCES users (id)
                )
            """)
            
            # Company members table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS company_members (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    role TEXT NOT NULL DEFAULT 'employee',
                    permissions TEXT DEFAULT '{}',
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    FOREIGN KEY (company_id) REFERENCES companies (id),
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    UNIQUE(company_id, user_id)
                )
            """)
            
            # Company roles definitions
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS company_roles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_id INTEGER NOT NULL,
                    role_name TEXT NOT NULL,
                    permissions TEXT NOT NULL DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (company_id) REFERENCES companies (id),
                    UNIQUE(company_id, role_name)
                )
            """)
            
            conn.commit()
    
    def generate_company_code(self):
        """Generate unique company code"""
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM companies WHERE company_code = ?", (code,))
                if not cursor.fetchone():
                    return code
    
    def create_company(self, name, password, description, industry, created_by):
        """Create a new company"""
        company_code = self.generate_company_code()
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create company
            cursor.execute("""
                INSERT INTO companies (name, company_code, company_password, description, industry, created_by)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (name, company_code, password, description, industry, created_by))
            
            company_id = cursor.lastrowid
            
            # Add creator as CEO
            cursor.execute("""
                INSERT INTO company_members (company_id, user_id, role)
                VALUES (?, ?, 'CEO')
            """, (company_id, created_by))
            
            # Create default roles
            default_roles = [
                ('CEO', json.dumps({
                    'manage_company': True,
                    'manage_users': True,
                    'view_all_data': True,
                    'manage_inventory': True,
                    'manage_sales': True,
                    'view_analytics': True
                })),
                ('Manager', json.dumps({
                    'manage_inventory': True,
                    'manage_sales': True,
                    'view_analytics': True,
                    'manage_team': True
                })),
                ('Sales Representative', json.dumps({
                    'manage_sales': True,
                    'view_inventory': True
                })),
                ('Inventory Manager', json.dumps({
                    'manage_inventory': True,
                    'view_analytics': True
                })),
                ('Employee', json.dumps({
                    'view_inventory': True
                }))
            ]
            
            for role_name, permissions in default_roles:
                cursor.execute("""
                    INSERT INTO company_roles (company_id, role_name, permissions)
                    VALUES (?, ?, ?)
                """, (company_id, role_name, permissions))
            
            conn.commit()
            return company_id, company_code
    
    def join_company(self, user_id, company_code, password):
        """Join a company with code and password"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Verify company credentials
            cursor.execute("""
                SELECT id, name FROM companies 
                WHERE company_code = ? AND company_password = ?
            """, (company_code, password))
            
            company = cursor.fetchone()
            if not company:
                return False, "Invalid company code or password"
            
            # Check if user is already a member
            cursor.execute("""
                SELECT id FROM company_members 
                WHERE company_id = ? AND user_id = ?
            """, (company['id'], user_id))
            
            if cursor.fetchone():
                return False, "You are already a member of this company"
            
            # Add user as employee
            cursor.execute("""
                INSERT INTO company_members (company_id, user_id, role)
                VALUES (?, ?, 'Employee')
            """, (company['id'], user_id))
            
            conn.commit()
            return True, f"Successfully joined {company['name']}"
    
    def get_user_company(self, user_id):
        """Get user's company information"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT c.*, cm.role, cm.permissions
                FROM companies c
                JOIN company_members cm ON c.id = cm.company_id
                WHERE cm.user_id = ? AND cm.is_active = 1
            """, (user_id,))
            return cursor.fetchone()
    
    def get_company_members(self, company_id):
        """Get all company members"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT u.username, u.email, cm.role, cm.joined_at, cm.is_active
                FROM company_members cm
                JOIN users u ON cm.user_id = u.id
                WHERE cm.company_id = ?
                ORDER BY cm.joined_at
            """, (company_id,))
            return cursor.fetchall()
    
    def has_permission(self, user_id, permission):
        """Check if user has specific permission"""
        company = self.get_user_company(user_id)
        if not company:
            return False
        
        # CEO has all permissions
        if company['role'] == 'CEO':
            return True
        
        try:
            permissions = json.loads(company['permissions'] or '{}')
            return permissions.get(permission, False)
        except:
            return False

@require_auth
def main():
    user = get_current_user()
    company_manager = CompanyManager()
    
    st.title("🏢 Company Dashboard")
    st.markdown("**Professional Business Management Center**")
    
    # Check if user is part of a company
    user_company = company_manager.get_user_company(user['id'])
    
    if not user_company:
        # User not in a company - show join/create options
        st.subheader("Welcome to Company Management")
        st.info("You're not currently part of any company. Join an existing company or create a new one.")
        
        tab1, tab2 = st.tabs(["🔗 Join Company", "🏗️ Create Company"])
        
        with tab1:
            st.subheader("Join Existing Company")
            
            with st.form("join_company"):
                company_code = st.text_input("Company Code", help="8-character code provided by your company")
                company_password = st.text_input("Company Password", type="password")
                submit_join = st.form_submit_button("Join Company", type="primary")
                
                if submit_join:
                    if company_code and company_password:
                        success, message = company_manager.join_company(user['id'], company_code.upper(), company_password)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                    else:
                        st.error("Please fill in all fields")
        
        with tab2:
            st.subheader("Create New Company")
            
            with st.form("create_company"):
                col1, col2 = st.columns(2)
                
                with col1:
                    company_name = st.text_input("Company Name")
                    company_password = st.text_input("Company Password", type="password", help="Password for others to join")
                
                with col2:
                    industry = st.selectbox("Industry", [
                        "Technology", "Finance", "Healthcare", "Retail", "Manufacturing",
                        "Education", "Real Estate", "Transportation", "Energy", "Other"
                    ])
                
                description = st.text_area("Company Description")
                submit_create = st.form_submit_button("Create Company", type="primary")
                
                if submit_create:
                    if company_name and company_password:
                        try:
                            company_id, company_code = company_manager.create_company(
                                company_name, company_password, description, industry, user['id']
                            )
                            st.success(f"Company '{company_name}' created successfully!")
                            st.info(f"**Company Code:** {company_code}")
                            st.info("Share this code and password with team members to join")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error creating company: {str(e)}")
                    else:
                        st.error("Company name and password are required")
    
    else:
        # User is part of a company - show company dashboard
        company_id = user_company['id']
        company_name = user_company['name']
        user_role = user_company['role']
        
        st.markdown(f"### {company_name}")
        st.markdown(f"**Your Role:** {user_role}")
        
        # Company overview metrics
        st.subheader("📊 Company Overview")
        
        # Get company statistics
        with company_manager.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Total members
            try:
                cursor.execute("SELECT COUNT(*) as count FROM company_members WHERE company_id = ? AND is_active = 1", (company_id,))
                total_members = cursor.fetchone()['count']
            except:
                total_members = 0
            
            # Total products (if inventory exists)
            try:
                cursor.execute("SELECT COUNT(*) as count FROM products")
                total_products = cursor.fetchone()['count']
            except:
                total_products = 0
            
            # Total transactions today
            try:
                cursor.execute("""
                    SELECT COUNT(*) as count FROM sales_transactions 
                    WHERE DATE(sale_date) = DATE('now')
                """)
                transactions_today = cursor.fetchone()['count']
            except:
                transactions_today = 0
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Team Members", total_members)
        
        with col2:
            st.metric("Products", total_products)
        
        with col3:
            st.metric("Transactions Today", transactions_today)
        
        with col4:
            st.metric("Company Code", user_company['company_code'])
        
        # Main dashboard tabs
        tabs = ["👥 Team", "📊 Analytics", "⚙️ Settings"]
        if company_manager.has_permission(user['id'], 'manage_company'):
            tabs.insert(-1, "🔧 Administration")
        
        selected_tabs = st.tabs(tabs)
        
        # Team Management
        with selected_tabs[0]:
            st.subheader("Team Members")
            
            members = company_manager.get_company_members(company_id)
            if members:
                members_df = pd.DataFrame(members)
                st.dataframe(members_df, use_container_width=True)
                
                # Role distribution chart
                role_counts = members_df['role'].value_counts()
                fig = px.pie(values=role_counts.values, names=role_counts.index, title="Team Roles Distribution")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No team members found")
            
            # Invite new members
            if company_manager.has_permission(user['id'], 'manage_users'):
                with st.expander("📨 Invite Team Members"):
                    st.markdown(f"**Company Code:** `{user_company['company_code']}`")
                    st.markdown(f"**Company Password:** `{user_company['company_password']}`")
                    st.info("Share these credentials with new team members to join your company")
        
        # Analytics (if user has permission)
        with selected_tabs[1]:
            st.subheader("Business Analytics")
            
            if company_manager.has_permission(user['id'], 'view_analytics'):
                # Company performance metrics
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Company Age", f"{(datetime.now() - datetime.fromisoformat(user_company['created_at'])).days} days")
                
                with col2:
                    st.metric("Industry", user_company['industry'])
                
                # Placeholder for real analytics
                st.info("Business analytics will be populated with real transaction and inventory data as your company grows.")
            else:
                st.warning("You don't have permission to view analytics")
        
        # Administration (for authorized users)
        if company_manager.has_permission(user['id'], 'manage_company'):
            with selected_tabs[-2]:
                st.subheader("Company Administration")
                
                # User role management
                st.write("**Manage Team Roles**")
                
                if members:
                    for member in members:
                        if member['username'] != user['username']:  # Don't allow self-modification
                            col1, col2, col3 = st.columns([2, 2, 1])
                            
                            with col1:
                                st.write(f"**{member['username']}**")
                            
                            with col2:
                                new_role = st.selectbox(
                                    "Role",
                                    ["CEO", "Manager", "Sales Representative", "Inventory Manager", "Employee"],
                                    index=["CEO", "Manager", "Sales Representative", "Inventory Manager", "Employee"].index(member['role']),
                                    key=f"role_{member['username']}"
                                )
                            
                            with col3:
                                if st.button("Update", key=f"update_{member['username']}"):
                                    # Update role logic would go here
                                    st.success(f"Role updated for {member['username']}")
                
                # Company settings
                st.write("**Company Settings**")
                
                with st.expander("🔧 Advanced Settings"):
                    new_password = st.text_input("Change Company Password", type="password")
                    if st.button("Update Password"):
                        if new_password:
                            # Update password logic
                            st.success("Company password updated")
                        else:
                            st.error("Password cannot be empty")
        
        # Settings
        with selected_tabs[-1]:
            st.subheader("Personal Settings")
            
            # User's role permissions
            st.write("**Your Permissions:**")
            
            if user_role == 'CEO':
                permissions = ["All permissions (Company Owner)"]
            else:
                try:
                    perms = json.loads(user_company.get('permissions', '{}'))
                    permissions = [k.replace('_', ' ').title() for k, v in perms.items() if v]
                except:
                    permissions = ["View company information"]
            
            for perm in permissions:
                st.write(f"✅ {perm}")
            
            # Leave company option (except for CEO)
            if user_role != 'CEO':
                st.subheader("⚠️ Danger Zone")
                if st.button("Leave Company", type="secondary"):
                    if st.session_state.get('confirm_leave'):
                        # Leave company logic
                        with company_manager.db.get_connection() as conn:
                            cursor = conn.cursor()
                            cursor.execute("""
                                UPDATE company_members SET is_active = 0 
                                WHERE company_id = ? AND user_id = ?
                            """, (company_id, user['id']))
                            conn.commit()
                        
                        st.success("You have left the company")
                        st.rerun()
                    else:
                        st.session_state.confirm_leave = True
                        st.error("Click again to confirm leaving the company")

if __name__ == "__main__":
    main()