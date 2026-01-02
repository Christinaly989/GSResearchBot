import streamlit as st
import sys
import os

# Add backend to path so we can import core
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

try:
    from core import GSResearchDownloader
except ImportError:
    # Fallback if running from backend dir or other structure issues
    sys.path.append(os.path.abspath("backend"))
    from core import GSResearchDownloader

st.set_page_config(page_title="GS Research Bot", layout="wide")

st.title("GS Research Automation")
st.markdown("Use this tool to automate downloading models and reports from GS Publishing.")

# --- Session State Management ---
if "logs" not in st.session_state:
    st.session_state.logs = []

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

# --- Main Area ---
st.header("2. Research Execution")

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

# --- Log History ---
st.markdown("---")
with st.expander("View Full Session Log History"):
    for log in st.session_state.logs:
        st.text(log)
