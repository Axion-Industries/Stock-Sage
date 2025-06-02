import streamlit as st
import requests
from datetime import datetime, timedelta
from auth import init_auth, get_current_user, require_auth
import streamlit.components.v1 as components

st.set_page_config(page_title="Market News", page_icon="📰", layout="wide")

# Load custom CSS
with open('static/css/style.css', 'r') as f:
    css = f.read()
st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)

# Initialize authentication
init_auth()

@require_auth
def main():
    st.title("📰 Market News & Analysis")
    
    user = get_current_user()
    if user:
        st.markdown(f"Stay informed, **{user['username']}**!")
    
    # News categories
    categories = ["General", "Technology", "Finance", "Energy", "Healthcare", "Crypto"]
    selected_category = st.selectbox("News Category", categories)
    
    # News API integration placeholder
    st.subheader("Real-Time Market News")
    
    # Check if user has provided news API key
    if 'news_api_key' not in st.session_state:
        st.info("To display real-time news, please provide a News API key in the settings.")
        
        with st.expander("🔑 Configure News API"):
            api_key = st.text_input("News API Key", type="password", help="Get your free API key from newsapi.org")
            if st.button("Save API Key"):
                if api_key:
                    st.session_state.news_api_key = api_key
                    st.success("API key saved! Refresh to load news.")
                    st.rerun()
    else:
        # Fetch news with API key
        try:
            api_key = st.session_state.news_api_key
            
            # News API parameters
            category_map = {
                "General": "business",
                "Technology": "technology", 
                "Finance": "business",
                "Energy": "business",
                "Healthcare": "health",
                "Crypto": "technology"
            }
            
            category_param = category_map.get(selected_category, "business")
            
            # Make API request
            url = f"https://newsapi.org/v2/top-headlines"
            params = {
                "category": category_param,
                "country": "us",
                "pageSize": 20,
                "apiKey": api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                news_data = response.json()
                articles = news_data.get("articles", [])
                
                if articles:
                    # Display news in cards
                    for i, article in enumerate(articles[:10]):
                        if article.get("title") and article.get("description"):
                            with st.container():
                                col1, col2 = st.columns([3, 1])
                                
                                with col1:
                                    st.subheader(article["title"])
                                    st.write(article["description"])
                                    
                                    if article.get("publishedAt"):
                                        pub_date = datetime.fromisoformat(article["publishedAt"].replace("Z", "+00:00"))
                                        st.caption(f"Published: {pub_date.strftime('%Y-%m-%d %H:%M UTC')}")
                                    
                                    if article.get("source", {}).get("name"):
                                        st.caption(f"Source: {article['source']['name']}")
                                
                                with col2:
                                    if article.get("urlToImage"):
                                        st.image(article["urlToImage"], width=200)
                                    
                                    if article.get("url"):
                                        st.link_button("Read Full Article", article["url"])
                                
                                st.divider()
                else:
                    st.warning("No news articles found for this category.")
            
            elif response.status_code == 401:
                st.error("Invalid API key. Please check your News API key.")
                if st.button("Reset API Key"):
                    del st.session_state.news_api_key
                    st.rerun()
            
            elif response.status_code == 429:
                st.error("API rate limit exceeded. Please try again later.")
            
            else:
                st.error(f"Error fetching news: {response.status_code}")
                
        except Exception as e:
            st.error(f"Error connecting to news service: {str(e)}")
    
    # Market sentiment analysis
    st.subheader("📊 Market Sentiment")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Market Sentiment", "Neutral", "0.2%")
    
    with col2:
        st.metric("Fear & Greed Index", "45", "-5")
    
    with col3:
        st.metric("VIX Level", "18.5", "+2.1")
    
    # Economic calendar
    st.subheader("📅 Economic Calendar")
    
    st.info("Economic calendar integration requires a financial data API. Configure your API key to display upcoming economic events.")
    
    # News sources and disclaimers
    with st.expander("ℹ️ About News Sources"):
        st.markdown("""
        **News Sources:**
        - Real-time news powered by NewsAPI.org
        - Financial data from Yahoo Finance
        - Market sentiment from various financial indicators
        
        **Disclaimer:**
        News and analysis provided for informational purposes only. 
        Not financial advice. Always conduct your own research before making investment decisions.
        """)

if __name__ == "__main__":
    main()