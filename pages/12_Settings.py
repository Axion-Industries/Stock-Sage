import streamlit as st
import json
from datetime import datetime
from auth import init_auth, get_current_user, require_auth
from database import DatabaseManager
import streamlit.components.v1 as components

st.set_page_config(page_title="Settings", page_icon="⚙️", layout="wide")

# Load custom CSS
with open('static/css/style.css', 'r') as f:
    css = f.read()
st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)

# Initialize authentication
init_auth()

class SettingsManager:
    def __init__(self):
        self.db = DatabaseManager()
        self.init_settings_tables()
    
    def init_settings_tables(self):
        """Initialize settings tables"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # User preferences
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_preferences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    preference_key TEXT NOT NULL,
                    preference_value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    UNIQUE(user_id, preference_key)
                )
            """)
            
            # System notifications
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    message TEXT NOT NULL,
                    type TEXT DEFAULT 'info',
                    is_read BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            conn.commit()
    
    def get_user_preference(self, user_id, key, default_value=None):
        """Get user preference"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT preference_value FROM user_preferences 
                WHERE user_id = ? AND preference_key = ?
            """, (user_id, key))
            result = cursor.fetchone()
            return result['preference_value'] if result else default_value
    
    def set_user_preference(self, user_id, key, value):
        """Set user preference"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO user_preferences (user_id, preference_key, preference_value, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """, (user_id, key, str(value)))
            conn.commit()
    
    def get_notifications(self, user_id, unread_only=False):
        """Get user notifications"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM notifications WHERE user_id = ?"
            params = [user_id]
            
            if unread_only:
                query += " AND is_read = 0"
            
            query += " ORDER BY created_at DESC LIMIT 20"
            
            cursor.execute(query, params)
            return cursor.fetchall()

@require_auth
def main():
    user = get_current_user()
    settings_manager = SettingsManager()
    
    st.title("⚙️ Settings & Preferences")
    st.markdown("**Customize your experience and manage your account**")
    
    # Settings navigation
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🎨 Appearance", "🔔 Notifications", "👤 Account", "🔐 Security", "📊 Data", "🔧 Advanced"
    ])
    
    with tab1:
        # Appearance Settings
        st.subheader("Appearance & Theme")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Theme Selection")
            
            current_theme = settings_manager.get_user_preference(user['id'], 'theme', 'light')
            
            theme_options = {
                "Light": "light",
                "Dark": "dark",
                "Dark Green": "dark-green",
                "Professional Blue": "professional-blue",
                "Custom": "custom"
            }
            
            selected_theme = st.selectbox(
                "Choose Theme",
                options=list(theme_options.keys()),
                index=list(theme_options.values()).index(current_theme) if current_theme in theme_options.values() else 0
            )
            
            # Visual Effects
            st.markdown("### Visual Effects")
            
            grid_effect = st.toggle(
                "Grid Background Animation",
                value=settings_manager.get_user_preference(user['id'], 'grid_effect', 'true') == 'true'
            )
            
            mouse_glow = st.toggle(
                "Mouse Glow Effect",
                value=settings_manager.get_user_preference(user['id'], 'mouse_glow', 'true') == 'true'
            )
            
            animations = st.toggle(
                "UI Animations",
                value=settings_manager.get_user_preference(user['id'], 'animations', 'true') == 'true'
            )
            
            # Apply theme button
            if st.button("Apply Theme Changes", type="primary"):
                theme_value = theme_options[selected_theme]
                
                # Save preferences
                settings_manager.set_user_preference(user['id'], 'theme', theme_value)
                settings_manager.set_user_preference(user['id'], 'grid_effect', str(grid_effect).lower())
                settings_manager.set_user_preference(user['id'], 'mouse_glow', str(mouse_glow).lower())
                settings_manager.set_user_preference(user['id'], 'animations', str(animations).lower())
                
                # Apply via JavaScript with proper CSS injection
                components.html(f"""
                <script>
                // Remove existing theme classes
                document.body.className = document.body.className.replace(/theme-\\w+/g, '');
                
                // Apply new theme
                if ('{theme_value}' === 'dark') {{
                    document.body.classList.add('theme-dark');
                    document.body.style.backgroundColor = '#0E1117';
                    document.body.style.color = '#FAFAFA';
                }} else if ('{theme_value}' === 'dark-green') {{
                    document.body.classList.add('theme-dark-green');
                    document.body.style.backgroundColor = '#0F2027';
                    document.body.style.backgroundImage = 'linear-gradient(135deg, #0F2027, #203A43, #2C5364)';
                    document.body.style.color = '#FAFAFA';
                }} else if ('{theme_value}' === 'professional-blue') {{
                    document.body.classList.add('theme-professional-blue');
                    document.body.style.backgroundColor = '#1e3a8a';
                    document.body.style.backgroundImage = 'linear-gradient(135deg, #1e3a8a, #3b82f6)';
                    document.body.style.color = 'white';
                }} else {{
                    document.body.style.backgroundColor = '';
                    document.body.style.backgroundImage = '';
                    document.body.style.color = '';
                }}
                
                // Apply to all Streamlit elements
                const elements = document.querySelectorAll('.stApp, .main, .block-container');
                elements.forEach(el => {{
                    if ('{theme_value}' !== 'light') {{
                        el.style.backgroundColor = 'transparent';
                    }}
                }});
                
                // Store in localStorage
                localStorage.setItem('user_theme', '{theme_value}');
                localStorage.setItem('grid_effect', '{str(grid_effect).lower()}');
                localStorage.setItem('mouse_glow', '{str(mouse_glow).lower()}');
                localStorage.setItem('animations', '{str(animations).lower()}');
                
                // Force Streamlit to re-render
                setTimeout(() => {{
                    const event = new CustomEvent('themeChanged', {{
                        detail: {{ theme: '{theme_value}' }}
                    }});
                    window.dispatchEvent(event);
                }}, 100);
                </script>
                """, height=0)
                
                st.success("Theme applied successfully! Changes will be visible across all pages.")
        
        with col2:
            st.markdown("### Custom Background")
            
            if selected_theme == "Custom":
                uploaded_bg = st.file_uploader(
                    "Upload Background Image",
                    type=['png', 'jpg', 'jpeg', 'gif'],
                    help="Upload a custom background image for your dashboard"
                )
                
                if uploaded_bg:
                    # Convert to base64 and apply
                    import base64
                    bg_data = base64.b64encode(uploaded_bg.read()).decode()
                    bg_url = f"data:image/{uploaded_bg.type.split('/')[1]};base64,{bg_data}"
                    
                    components.html(f"""
                    <script>
                    document.body.style.backgroundImage = 'url({bg_url})';
                    document.body.style.backgroundSize = 'cover';
                    document.body.style.backgroundAttachment = 'fixed';
                    localStorage.setItem('custom_background', '{bg_url}');
                    </script>
                    """, height=0)
                    
                    st.success("Custom background applied!")
            
            st.markdown("### Display Options")
            
            sidebar_collapsed = st.toggle(
                "Collapsed Sidebar by Default",
                value=settings_manager.get_user_preference(user['id'], 'sidebar_collapsed', 'false') == 'true'
            )
            
            wide_mode = st.toggle(
                "Wide Layout Mode",
                value=settings_manager.get_user_preference(user['id'], 'wide_mode', 'true') == 'true'
            )
            
            if st.button("Save Display Settings"):
                settings_manager.set_user_preference(user['id'], 'sidebar_collapsed', str(sidebar_collapsed).lower())
                settings_manager.set_user_preference(user['id'], 'wide_mode', str(wide_mode).lower())
                st.success("Display settings saved!")
    
    with tab2:
        # Notifications Settings
        st.subheader("Notification Preferences")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Notification Types")
            
            email_notifications = st.toggle(
                "Email Notifications",
                value=settings_manager.get_user_preference(user['id'], 'email_notifications', 'true') == 'true'
            )
            
            push_notifications = st.toggle(
                "Browser Push Notifications",
                value=settings_manager.get_user_preference(user['id'], 'push_notifications', 'false') == 'true'
            )
            
            stock_alerts = st.toggle(
                "Stock Price Alerts",
                value=settings_manager.get_user_preference(user['id'], 'stock_alerts', 'true') == 'true'
            )
            
            inventory_alerts = st.toggle(
                "Inventory Alerts",
                value=settings_manager.get_user_preference(user['id'], 'inventory_alerts', 'true') == 'true'
            )
            
            if st.button("Save Notification Settings"):
                settings_manager.set_user_preference(user['id'], 'email_notifications', str(email_notifications).lower())
                settings_manager.set_user_preference(user['id'], 'push_notifications', str(push_notifications).lower())
                settings_manager.set_user_preference(user['id'], 'stock_alerts', str(stock_alerts).lower())
                settings_manager.set_user_preference(user['id'], 'inventory_alerts', str(inventory_alerts).lower())
                st.success("Notification settings saved!")
        
        with col2:
            st.markdown("### Recent Notifications")
            
            notifications = settings_manager.get_notifications(user['id'])
            
            if notifications:
                for notification in notifications:
                    with st.container():
                        if notification['type'] == 'warning':
                            st.warning(f"**{notification['title']}** - {notification['message']}")
                        elif notification['type'] == 'success':
                            st.success(f"**{notification['title']}** - {notification['message']}")
                        elif notification['type'] == 'error':
                            st.error(f"**{notification['title']}** - {notification['message']}")
                        else:
                            st.info(f"**{notification['title']}** - {notification['message']}")
                        
                        st.caption(f"Created: {notification['created_at']}")
            else:
                st.info("No notifications yet")
    
    with tab3:
        # Account Settings
        st.subheader("Account Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Profile Information")
            
            with st.form("profile_form"):
                current_username = user['username']
                current_email = user['email']
                
                new_username = st.text_input("Username", value=current_username)
                new_email = st.text_input("Email", value=current_email)
                
                submit_profile = st.form_submit_button("Update Profile")
                
                if submit_profile:
                    if new_username and new_email:
                        try:
                            with settings_manager.db.get_connection() as conn:
                                cursor = conn.cursor()
                                cursor.execute("""
                                    UPDATE users SET username = ?, email = ? WHERE id = ?
                                """, (new_username, new_email, user['id']))
                                conn.commit()
                            
                            st.success("Profile updated successfully!")
                            # Update session
                            st.session_state.user['username'] = new_username
                            st.session_state.user['email'] = new_email
                            
                        except Exception as e:
                            st.error(f"Error updating profile: {str(e)}")
                    else:
                        st.error("All fields are required")
        
        with col2:
            st.markdown("### Account Statistics")
            
            # Account creation date
            with settings_manager.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT created_at, last_login FROM users WHERE id = ?", (user['id'],))
                user_data = cursor.fetchone()
            
            if user_data:
                created_date = datetime.fromisoformat(user_data['created_at'])
                account_age = (datetime.now() - created_date).days
                
                st.metric("Account Age", f"{account_age} days")
                st.metric("Created", created_date.strftime("%Y-%m-%d"))
                
                if user_data['last_login']:
                    last_login = datetime.fromisoformat(user_data['last_login'])
                    st.metric("Last Login", last_login.strftime("%Y-%m-%d %H:%M"))
    
    with tab4:
        # Security Settings
        st.subheader("Security & Privacy")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Change Password")
            
            with st.form("password_form"):
                current_password = st.text_input("Current Password", type="password")
                new_password = st.text_input("New Password", type="password")
                confirm_password = st.text_input("Confirm New Password", type="password")
                
                submit_password = st.form_submit_button("Change Password")
                
                if submit_password:
                    if current_password and new_password and confirm_password:
                        if new_password == confirm_password:
                            if len(new_password) >= 6:
                                # Verify current password and update
                                if settings_manager.db.verify_password(current_password, user.get('password_hash', '')):
                                    new_hash = settings_manager.db.hash_password(new_password)
                                    
                                    with settings_manager.db.get_connection() as conn:
                                        cursor = conn.cursor()
                                        cursor.execute("""
                                            UPDATE users SET password_hash = ? WHERE id = ?
                                        """, (new_hash, user['id']))
                                        conn.commit()
                                    
                                    st.success("Password changed successfully!")
                                else:
                                    st.error("Current password is incorrect")
                            else:
                                st.error("New password must be at least 6 characters")
                        else:
                            st.error("Passwords do not match")
                    else:
                        st.error("All fields are required")
        
        with col2:
            st.markdown("### Security Settings")
            
            two_factor = st.toggle(
                "Two-Factor Authentication",
                value=settings_manager.get_user_preference(user['id'], 'two_factor', 'false') == 'true',
                help="Enable 2FA for enhanced security"
            )
            
            login_notifications = st.toggle(
                "Login Notifications",
                value=settings_manager.get_user_preference(user['id'], 'login_notifications', 'true') == 'true',
                help="Get notified of new login attempts"
            )
            
            if st.button("Save Security Settings"):
                settings_manager.set_user_preference(user['id'], 'two_factor', str(two_factor).lower())
                settings_manager.set_user_preference(user['id'], 'login_notifications', str(login_notifications).lower())
                st.success("Security settings saved!")
    
    with tab5:
        # Data Management
        st.subheader("Data Management")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Export Data")
            
            if st.button("Export Portfolio Data"):
                # Export portfolio
                from utils.portfolio_manager import PortfolioManager
                portfolio_manager = PortfolioManager()
                portfolio_json = portfolio_manager.export_portfolio()
                
                st.download_button(
                    label="Download Portfolio JSON",
                    data=portfolio_json,
                    file_name=f"portfolio_export_{datetime.now().strftime('%Y%m%d')}.json",
                    mime="application/json"
                )
            
            if st.button("Export User Data"):
                # Export user data
                user_data = {
                    'username': user['username'],
                    'email': user['email'],
                    'export_date': datetime.now().isoformat()
                }
                
                st.download_button(
                    label="Download User Data JSON",
                    data=json.dumps(user_data, indent=2),
                    file_name=f"user_data_export_{datetime.now().strftime('%Y%m%d')}.json",
                    mime="application/json"
                )
        
        with col2:
            st.markdown("### Import Data")
            
            uploaded_portfolio = st.file_uploader("Import Portfolio Data", type="json")
            if uploaded_portfolio:
                try:
                    portfolio_data = json.loads(uploaded_portfolio.read())
                    if st.button("Import Portfolio"):
                        from utils.portfolio_manager import PortfolioManager
                        portfolio_manager = PortfolioManager()
                        if portfolio_manager.import_portfolio(json.dumps(portfolio_data)):
                            st.success("Portfolio imported successfully!")
                        else:
                            st.error("Error importing portfolio")
                except Exception as e:
                    st.error(f"Invalid portfolio file: {str(e)}")
    
    with tab6:
        # Advanced Settings
        st.subheader("Advanced Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### API Configuration")
            
            # News API Key
            news_api_key = st.text_input(
                "News API Key",
                type="password",
                value="***" if 'news_api_key' in st.session_state else "",
                help="Required for market news features"
            )
            
            if st.button("Save API Keys"):
                if news_api_key and news_api_key != "***":
                    st.session_state.news_api_key = news_api_key
                    st.success("API keys saved!")
            
            st.markdown("### Developer Options")
            
            debug_mode = st.toggle(
                "Debug Mode",
                value=settings_manager.get_user_preference(user['id'], 'debug_mode', 'false') == 'true'
            )
            
            if st.button("Save Developer Settings"):
                settings_manager.set_user_preference(user['id'], 'debug_mode', str(debug_mode).lower())
                st.success("Developer settings saved!")
        
        with col2:
            st.markdown("### Reset Options")
            
            st.warning("⚠️ These actions cannot be undone!")
            
            if st.button("Reset All Preferences"):
                if st.session_state.get('confirm_reset_prefs'):
                    with settings_manager.db.get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM user_preferences WHERE user_id = ?", (user['id'],))
                        conn.commit()
                    
                    st.success("All preferences reset to defaults!")
                    st.session_state.confirm_reset_prefs = False
                    st.rerun()
                else:
                    st.session_state.confirm_reset_prefs = True
                    st.error("Click again to confirm reset")
            
            if st.button("Delete Account", type="secondary"):
                st.error("Account deletion requires administrator approval. Contact support.")

if __name__ == "__main__":
    main()