import streamlit as st
import sys
import os

# Add backend to path so we can import core
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

try:
    from core import GSResearchDownloader
    from watchlist_manager import WatchlistManager
    from auth import AuthManager
except ImportError:
    # Fallback if running from backend dir or other structure issues
    sys.path.append(os.path.abspath("backend"))
    from core import GSResearchDownloader
    from watchlist_manager import WatchlistManager
    from auth import AuthManager

st.set_page_config(page_title="GS Research Bot", layout="wide")

# --- Auth Init ---
if "auth_manager" not in st.session_state:
    st.session_state.auth_manager = AuthManager()

# --- Login System ---
if "user" not in st.session_state:
    st.session_state.user = None

if not st.session_state.user:
    st.title("GS Research Bot - Access Control")
    
    auth_tab1, auth_tab2 = st.tabs(["Login", "Register"])
    
    with auth_tab1:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")
            if submitted:
                if st.session_state.auth_manager.login_user(username, password):
                    st.session_state.user = username
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid username or password")
                    
    with auth_tab2:
        with st.form("register_form"):
            new_user = st.text_input("New Username")
            new_pass = st.text_input("New Password", type="password")
            reg_submitted = st.form_submit_button("Register")
            if reg_submitted:
                success, msg = st.session_state.auth_manager.register_user(new_user, new_pass)
                if success:
                    st.success(msg + " Please switch to Login tab.")
                else:
                    st.error(msg)
                    
    st.stop()

# --- Main App ---
st.sidebar.write(f"User: **{st.session_state.user}**")

# Show Storage Status
if st.session_state.auth_manager.use_supabase:
    st.sidebar.success("☁️ Cloud Storage (Supabase)")
else:
    st.sidebar.warning("📂 Local Storage (JSON/SQLite)")

if st.sidebar.button("Logout"):
    st.session_state.user = None
    # Clear user-specific data
    if "watchlist_manager" in st.session_state:
        del st.session_state["watchlist_manager"]
    if "custom_download_path" in st.session_state:
        del st.session_state["custom_download_path"]
    st.rerun()

st.title("GS Research Automation")
st.markdown("Use this tool to automate downloading models and reports from GS Publishing.")

# --- Session State Management ---
if "logs" not in st.session_state:
    st.session_state.logs = []
    
if "watchlist_manager" not in st.session_state:
    # Initialize with current logged-in user to load their specific file
    st.session_state.watchlist_manager = WatchlistManager(username=st.session_state.user)

# Load User Settings
if "custom_download_path" not in st.session_state:
    saved_path = st.session_state.auth_manager.get_download_path(st.session_state.user)
    st.session_state.custom_download_path = saved_path if saved_path else "downloads"

def stream_log(msg):
    """Callback function to handle logs from the downloader."""
    st.session_state.logs.append(msg)
    # This writes to the current location in the Streamlit app
    st.code(f"{msg}", language="text")

if "downloader" not in st.session_state:
    # Initialize the downloader with our callback and custom path
    st.session_state.downloader = GSResearchDownloader(
        download_dir=st.session_state.custom_download_path,
        log_callback=stream_log
    )

downloader = st.session_state.downloader

# --- Sidebar Controls ---
st.sidebar.header("1. Initialization")
if st.sidebar.button("Launch Browser"):
    try:
        if downloader.driver is None:
            # Re-init if closed
            st.session_state.downloader = GSResearchDownloader(
                download_dir=st.session_state.custom_download_path,
                log_callback=stream_log
            )
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
tab1, tab2, tab3 = st.tabs(["Research Execution", "Watchlist & Account", "Batch Models"])

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

with tab3:
    st.header("Batch Model Download")
    st.write("Download ONLY financial models for multiple companies (skips reports).")
    
    model_tickers = st.text_input("Enter Company Tickers for Models (comma-separated):", "Apple, Tesla", key="model_tickers")
    
    if st.button("Download Models Only"):
        if not downloader.driver:
            st.error("🚨 Browser is not running. Please click 'Launch Browser' in the sidebar first.")
        else:
            st.subheader("Model Download Logs")
            
            companies = [c.strip() for c in model_tickers.split(",") if c.strip()]
            
            progress_bar = st.progress(0)
            
            for i, company in enumerate(companies):
                st.markdown(f"**Processing Model for: {company}**")
                
                downloader.search_company(company)
                # Pass models_only=True
                downloader.download_reports(company, min_pages=1, primary_only=True, models_only=True)
                
                progress_bar.progress((i + 1) / len(companies))
                
            st.success("✅ Batch model download complete!")

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

    st.markdown("---")
    st.subheader("Settings")
    current_path = st.session_state.custom_download_path
    new_path = st.text_input("Local Download Path", value=current_path)
    if st.button("Save Path"):
        if new_path and new_path != current_path:
            # Update DB
            if st.session_state.auth_manager.set_download_path(st.session_state.user, new_path):
                st.session_state.custom_download_path = new_path
                st.success("Download path saved! Please restart the browser (Close -> Launch) to apply changes.")
            else:
                st.error("Failed to save path.")

# --- Log History ---
st.markdown("---")
with st.expander("View Full Session Log History"):
    for log in st.session_state.logs:
        st.text(log)
