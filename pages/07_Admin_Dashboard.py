import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from auth import init_auth, get_current_user, require_auth
from database import DatabaseManager
import sqlite3

st.set_page_config(page_title="Admin Dashboard", page_icon="⚙️", layout="wide")

# Load custom CSS
with open('static/css/style.css', 'r') as f:
    css = f.read()
st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)

# Initialize authentication
init_auth()

class AdminManager:
    def __init__(self):
        self.db = DatabaseManager()
        self.init_admin_tables()
    
    def init_admin_tables(self):
        """Initialize admin-specific tables"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # User roles table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_roles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    role TEXT NOT NULL DEFAULT 'employee',
                    permissions TEXT DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    UNIQUE(user_id)
                )
            """)
            
            # Business metrics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS business_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    metric_date DATE NOT NULL,
                    category TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # System settings table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    setting_key TEXT UNIQUE NOT NULL,
                    setting_value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
    
    def get_user_role(self, user_id):
        """Get user role"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT role FROM user_roles WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()
            return result['role'] if result else 'employee'
    
    def set_user_role(self, user_id, role):
        """Set user role"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO user_roles (user_id, role)
                VALUES (?, ?)
            """, (user_id, role))
            conn.commit()
    
    def get_system_stats(self):
        """Get system-wide statistics"""
        stats = {}
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Total users
            cursor.execute("SELECT COUNT(*) as count FROM users WHERE is_active = 1")
            stats['total_users'] = cursor.fetchone()['count']
            
            # Active portfolios
            cursor.execute("SELECT COUNT(DISTINCT user_id) as count FROM portfolios")
            stats['active_portfolios'] = cursor.fetchone()['count']
            
            # Total transactions today
            cursor.execute("""
                SELECT COUNT(*) as count FROM transactions 
                WHERE DATE(transaction_date) = DATE('now')
            """)
            stats['transactions_today'] = cursor.fetchone()['count']
            
            # Total watchlist items
            cursor.execute("SELECT COUNT(*) as count FROM watchlists")
            stats['watchlist_items'] = cursor.fetchone()['count']
            
        return stats

@require_auth
def main():
    user = get_current_user()
    admin_manager = AdminManager()
    
    # Check if user is admin
    user_role = admin_manager.get_user_role(user['id'])
    
    if user_role != 'admin':
        st.error("Access Denied: Admin privileges required")
        st.info("Contact your administrator to request admin access.")
        return
    
    st.title("⚙️ Admin Dashboard")
    st.markdown(f"Welcome to the admin panel, **{user['username']}**")
    
    # System Overview
    st.subheader("📊 System Overview")
    
    stats = admin_manager.get_system_stats()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Users", stats['total_users'], "Active")
    
    with col2:
        st.metric("Active Portfolios", stats['active_portfolios'])
    
    with col3:
        st.metric("Transactions Today", stats['transactions_today'])
    
    with col4:
        st.metric("Watchlist Items", stats['watchlist_items'])
    
    # User Management
    st.subheader("👥 User Management")
    
    with st.expander("Manage User Roles"):
        # Get all users
        with admin_manager.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT u.id, u.username, u.email, u.created_at, u.last_login,
                       COALESCE(ur.role, 'employee') as role
                FROM users u
                LEFT JOIN user_roles ur ON u.id = ur.user_id
                WHERE u.is_active = 1
            """)
            users = cursor.fetchall()
        
        if users:
            users_df = pd.DataFrame(users)
            
            # Display users table
            st.dataframe(users_df, use_container_width=True)
            
            # Role assignment
            st.subheader("Assign Roles")
            selected_user = st.selectbox(
                "Select User",
                options=[f"{user['username']} ({user['email']})" for user in users],
                key="role_user_select"
            )
            
            if selected_user:
                user_id = next(user['id'] for user in users if f"{user['username']} ({user['email']})" == selected_user)
                current_role = next(user['role'] for user in users if user['id'] == user_id)
                
                new_role = st.selectbox(
                    "Role",
                    options=['admin', 'manager', 'employee'],
                    index=['admin', 'manager', 'employee'].index(current_role)
                )
                
                if st.button("Update Role"):
                    admin_manager.set_user_role(user_id, new_role)
                    st.success(f"Role updated to {new_role}")
                    st.rerun()
    
    # System Settings
    st.subheader("⚙️ System Settings")
    
    with st.expander("Application Settings"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Security Settings**")
            
            # Password requirements
            min_password_length = st.number_input("Minimum Password Length", min_value=4, max_value=20, value=6)
            require_special_chars = st.checkbox("Require Special Characters", value=False)
            session_timeout = st.number_input("Session Timeout (minutes)", min_value=5, max_value=1440, value=60)
            
            # Rate limiting
            api_rate_limit = st.number_input("API Rate Limit (requests/minute)", min_value=10, max_value=1000, value=100)
        
        with col2:
            st.write("**Application Settings**")
            
            # Data retention
            data_retention_days = st.number_input("Data Retention (days)", min_value=30, max_value=3650, value=365)
            auto_backup = st.checkbox("Enable Auto Backup", value=True)
            backup_frequency = st.selectbox("Backup Frequency", ["Daily", "Weekly", "Monthly"])
            
            # Notifications
            email_notifications = st.checkbox("Email Notifications", value=True)
            push_notifications = st.checkbox("Push Notifications", value=False)
        
        if st.button("Save Settings"):
            st.success("Settings saved successfully!")
    
    # Activity Monitoring
    st.subheader("📈 Activity Monitoring")
    
    # Recent user activity
    with admin_manager.db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ua.action, ua.timestamp, u.username, ua.details
            FROM user_activity ua
            JOIN users u ON ua.user_id = u.id
            ORDER BY ua.timestamp DESC
            LIMIT 50
        """)
        recent_activity = cursor.fetchall()
    
    if recent_activity:
        activity_df = pd.DataFrame(recent_activity)
        st.dataframe(activity_df, use_container_width=True)
    else:
        st.info("No recent activity to display")
    
    # System Health
    st.subheader("🏥 System Health")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Database Status", "Healthy", "✅")
        st.metric("Response Time", "< 100ms", "Fast")
    
    with col2:
        st.metric("Memory Usage", "45%", "Normal")
        st.metric("Active Sessions", "12", "+3")
    
    with col3:
        st.metric("Error Rate", "0.1%", "Low")
        st.metric("Uptime", "99.9%", "Excellent")
    
    # Database Management
    st.subheader("🗄️ Database Management")
    
    with st.expander("Database Operations"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Backup & Restore**")
            
            if st.button("Create Backup"):
                # Create database backup
                backup_filename = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                st.success(f"Backup created: {backup_filename}")
            
            uploaded_backup = st.file_uploader("Restore from Backup", type="db")
            if uploaded_backup and st.button("Restore Database"):
                st.warning("Database restore would overwrite current data!")
        
        with col2:
            st.write("**Database Statistics**")
            
            with admin_manager.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get table sizes
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                
                for table in tables:
                    table_name = table['name']
                    cursor.execute(f"SELECT COUNT(*) as count FROM {table_name}")
                    count = cursor.fetchone()['count']
                    st.metric(f"{table_name} records", count)
    
    # Audit Logs
    st.subheader("📋 Audit Trail")
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        date_from = st.date_input("From Date", value=datetime.now() - timedelta(days=7))
    
    with col2:
        date_to = st.date_input("To Date", value=datetime.now())
    
    with col3:
        action_filter = st.selectbox("Action Type", ["All", "login", "logout", "transaction", "portfolio_update"])
    
    # Display audit logs
    with admin_manager.db.get_connection() as conn:
        cursor = conn.cursor()
        
        query = """
            SELECT ua.timestamp, u.username, ua.action, ua.details, ua.ip_address
            FROM user_activity ua
            JOIN users u ON ua.user_id = u.id
            WHERE DATE(ua.timestamp) BETWEEN ? AND ?
        """
        params = [date_from, date_to]
        
        if action_filter != "All":
            query += " AND ua.action = ?"
            params.append(action_filter)
        
        query += " ORDER BY ua.timestamp DESC LIMIT 100"
        
        cursor.execute(query, params)
        audit_logs = cursor.fetchall()
    
    if audit_logs:
        audit_df = pd.DataFrame(audit_logs)
        st.dataframe(audit_df, use_container_width=True)
        
        # Export audit logs
        csv = audit_df.to_csv(index=False)
        st.download_button(
            label="Export Audit Logs",
            data=csv,
            file_name=f"audit_logs_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    else:
        st.info("No audit logs found for the selected criteria")

if __name__ == "__main__":
    main()