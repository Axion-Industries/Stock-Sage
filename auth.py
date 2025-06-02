import streamlit as st
from database import DatabaseManager

def init_auth():
    """Initialize authentication system"""
    if 'db' not in st.session_state:
        st.session_state.db = DatabaseManager()
    
    # Check for saved login in browser localStorage
    if 'user' not in st.session_state:
        # Add JavaScript to check localStorage
        import streamlit.components.v1 as components
        
        # Check localStorage for saved session
        check_session_script = """
        <script>
        const savedSession = localStorage.getItem('stock_dashboard_session');
        if (savedSession) {
            const sessionData = JSON.parse(savedSession);
            // Send session data back to Streamlit
            window.parent.postMessage({
                type: 'saved_session',
                data: sessionData
            }, '*');
        } else {
            window.parent.postMessage({
                type: 'no_session'
            }, '*');
        }
        </script>
        """
        components.html(check_session_script, height=0)
        
        # Initialize session state
        st.session_state.user = None
        st.session_state.authenticated = False

def login_page():
    """Display login/register page"""
    st.title("📈 Professional Stock Market Dashboard")
    st.markdown("---")
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        st.subheader("Sign In")
        with st.form("login_form"):
            username = st.text_input("Username or Email")
            password = st.text_input("Password", type="password")
            submit_login = st.form_submit_button("Sign In", type="primary")
            
            if submit_login:
                if username and password:
                    user = st.session_state.db.authenticate_user(username, password)
                    if user:
                        st.session_state.user = user
                        st.session_state.authenticated = True
                        st.session_state.db.log_activity(
                            user['id'], 
                            'login', 
                            'User logged in successfully'
                        )
                        
                        # Save login to browser localStorage
                        import streamlit.components.v1 as components
                        import json
                        user_json = json.dumps(user)
                        save_session_script = f"""
                        <script>
                        localStorage.setItem('stock_dashboard_session', '{user_json}');
                        </script>
                        """
                        components.html(save_session_script, height=0)
                        
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error("Invalid username/email or password")
                else:
                    st.error("Please fill in all fields")
    
    with tab2:
        st.subheader("Create Account")
        with st.form("register_form"):
            new_username = st.text_input("Username", help="Choose a unique username")
            new_email = st.text_input("Email", help="Enter your email address")
            new_password = st.text_input("Password", type="password", help="Choose a secure password")
            confirm_password = st.text_input("Confirm Password", type="password")
            submit_register = st.form_submit_button("Create Account", type="primary")
            
            if submit_register:
                if new_username and new_email and new_password and confirm_password:
                    if new_password == confirm_password:
                        if len(new_password) >= 6:
                            user_id = st.session_state.db.create_user(new_username, new_email, new_password)
                            if user_id:
                                st.success("Account created successfully! Please sign in.")
                            else:
                                st.error("Username or email already exists")
                        else:
                            st.error("Password must be at least 6 characters long")
                    else:
                        st.error("Passwords do not match")
                else:
                    st.error("Please fill in all fields")

def logout():
    """Logout user"""
    if st.session_state.user:
        st.session_state.db.log_activity(
            st.session_state.user['id'], 
            'logout', 
            'User logged out'
        )
    
    # Clear localStorage
    import streamlit.components.v1 as components
    clear_session_script = """
    <script>
    localStorage.removeItem('stock_dashboard_session');
    </script>
    """
    components.html(clear_session_script, height=0)
    
    st.session_state.user = None
    st.session_state.authenticated = False
    st.rerun()

def require_auth(func):
    """Decorator to require authentication"""
    def wrapper(*args, **kwargs):
        if not st.session_state.authenticated:
            login_page()
            return None
        return func(*args, **kwargs)
    return wrapper

def restore_session_from_storage(user_data):
    """Restore session from localStorage data"""
    try:
        if user_data and isinstance(user_data, dict):
            # Verify user still exists in database
            db = st.session_state.db
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE id = ? AND is_active = 1", (user_data['id'],))
                current_user = cursor.fetchone()
                
                if current_user:
                    st.session_state.user = dict(current_user)
                    st.session_state.authenticated = True
                    return True
    except Exception as e:
        pass
    
    return False

def get_current_user():
    """Get current authenticated user"""
    return st.session_state.user if st.session_state.authenticated else None