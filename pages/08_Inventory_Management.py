import streamlit as st
from auth import init_auth, get_current_user, require_auth

st.set_page_config(page_title="Inventory Management", page_icon="📦", layout="wide")

# Load custom CSS
with open('static/css/style.css', 'r') as f:
    css = f.read()
st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)

# Initialize authentication
init_auth()

@require_auth
def main():
    user = get_current_user()

    st.title("📦 Inventory Management")
    st.info("This section has been removed from the application.")
    st.markdown("Please use the other available features in the navigation menu.")

if __name__ == "__main__":
    main()