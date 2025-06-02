import streamlit as st
from database import DatabaseManager

def init_auth():
    """Initialize authentication system"""
    if 'db' not in st.session_state:
        st.session_state.db = DatabaseManager()
    
    # Check for saved login in browser
    if 'user' not in st.session_state:
        saved_user = st.query_params.get('saved_session')
        if saved_user:
            try:
                import json
                user_data = json.loads(saved_user)
                st.session_state.user = user_data
                st.session_state.authenticated = True
            except:
                st.session_state.user = None
                st.session_state.authenticated = False
        else:
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
                        
                        # Save login to browser storage
                        import json
                        user_json = json.dumps(user)
                        st.query_params['saved_session'] = user_json
                        
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

def get_current_user():
    """Get current authenticated user"""
    return st.session_state.user if st.session_state.authenticated else None