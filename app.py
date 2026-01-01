import streamlit as st
import sys
import os

# Add backend to path so we can import core
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

try:
    from core import GSResearchDownloader
    from watchlist_manager import WatchlistManager
except ImportError:
    # Fallback if running from backend dir or other structure issues
    sys.path.append(os.path.abspath("backend"))
    from core import GSResearchDownloader
    from watchlist_manager import WatchlistManager

st.set_page_config(page_title="GS Research Bot", layout="wide")

# --- Login System ---
if "user" not in st.session_state:
    st.session_state.user = None

if not st.session_state.user:
    st.title("GS Research Bot - Login")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        if submitted:
            if username and password: # Simple validation
                st.session_state.user = username
                st.rerun()
            else:
                st.error("Please enter username and password")
    st.stop()

# --- Main App ---
st.sidebar.write(f"User: **{st.session_state.user}**")
if st.sidebar.button("Logout"):
    st.session_state.user = None
    st.rerun()

st.title("GS Research Automation")
st.markdown("Use this tool to automate downloading models and reports from GS Publishing.")

# --- Session State Management ---
if "logs" not in st.session_state:
    st.session_state.logs = []
    
if "watchlist_manager" not in st.session_state:
    st.session_state.watchlist_manager = WatchlistManager()

def stream_log(msg):
    """Callback function to handle logs from the downloader."""
    st.session_state.logs.append(msg)
    # This writes to the current location in the Streamlit app
    st.code(f"{msg}", language="text")

if "downloader" not in st.session_state:
    # Initialize the downloader with our callback
    st.session_state.downloader = GSResearchDownloader(log_callback=stream_log)

downloader = st.session_state.downloader

# --- Sidebar Controls ---
st.sidebar.header("1. Initialization")
if st.sidebar.button("Launch Browser"):
    try:
        if downloader.driver is None:
            # Re-init if closed
            st.session_state.downloader = GSResearchDownloader(log_callback=stream_log)
            downloader = st.session_state.downloader
            
        msg = downloader.login_init()
        st.sidebar.success("Browser Launched!")
        st.sidebar.info(msg)
    except Exception as e:
        st.sidebar.error(f"Error: {e}")

st.sidebar.markdown("---")
st.sidebar.header("3. Cleanup")
if st.sidebar.button("Close Browser"):
    downloader.close()
    st.sidebar.success("Browser closed.")

# --- Tabs ---
tab1, tab2 = st.tabs(["Research Execution", "Watchlist & Account"])

with tab1:
    st.header("Research Execution")
    
    tickers = st.text_input("Enter Company Tickers (comma-separated):", "Apple, Tesla")
    
    col1, col2 = st.columns(2)
    with col1:
        min_pages = st.number_input("Minimum Pages per Report:", min_value=1, value=1, step=1)
    with col2:
        primary_only = st.checkbox("Download 'Primary' Reports Only", value=True)
    
    if st.button("Start Research"):
        if not downloader.driver:
            st.error("🚨 Browser is not running. Please click 'Launch Browser' in the sidebar first.")
        else:
            st.subheader("Live Execution Logs")
            
            companies = [c.strip() for c in tickers.split(",") if c.strip()]
            
            progress_bar = st.progress(0)
            
            for i, company in enumerate(companies):
                st.markdown(f"**Processing: {company}**")
                
                # The downloader methods will call stream_log(), which calls st.code()
                # These logs will appear right here in the flow
                downloader.search_company(company)
                downloader.download_reports(company, min_pages=min_pages, primary_only=primary_only)
                
                progress_bar.progress((i + 1) / len(companies))
                
            st.success("✅ Batch processing complete!")

with tab2:
    st.header("Watchlist Management")
    wm = st.session_state.watchlist_manager
    watchlist = wm.get_watchlist()
    
    # Display Watchlist
    st.subheader("My Watchlist")
    if watchlist:
        st.write(watchlist)
    else:
        st.info("Watchlist is empty.")
        
    # Add Ticker
    with st.form("add_ticker_form"):
        new_ticker = st.text_input("Add New Ticker")
        add_submitted = st.form_submit_button("Add Ticker")
        if add_submitted and new_ticker:
            if wm.add_ticker(new_ticker):
                st.success(f"Added {new_ticker}")
                st.rerun()
            else:
                st.warning("Ticker already exists or invalid.")

    # Remove Ticker
    if watchlist:
        with st.form("remove_ticker_form"):
            rem_ticker = st.selectbox("Select Ticker to Remove", watchlist)
            rem_submitted = st.form_submit_button("Remove Ticker")
            if rem_submitted:
                if wm.remove_ticker(rem_ticker):
                    st.success(f"Removed {rem_ticker}")
                    st.rerun()

    st.markdown("---")
    st.subheader("Auto-Update")
    st.write("Check for reports updated in the last 30 days for all watchlist companies.")
    
    if st.button("Check Watchlist Updates"):
        if not downloader.driver:
            st.error("🚨 Browser is not running. Please click 'Launch Browser' in the sidebar first.")
        else:
            st.subheader("Update Logs")
            downloader.check_watchlist_updates(wm)
            st.success("✅ Watchlist update check complete!")

# --- Log History ---
st.markdown("---")
with st.expander("View Full Session Log History"):
    for log in st.session_state.logs:
        st.text(log)
