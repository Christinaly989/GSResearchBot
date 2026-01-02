# GS Research Bot

**GS Research Bot** is a powerful automation tool designed to streamline the process of downloading research reports and financial models from the GS Publishing portal. Built with **Python**, **Selenium**, and **Streamlit**, it provides a user-friendly interface to manage research tasks efficiently.

## 🚀 Features

*   **Batch Downloading**: Automatically search for and download reports/models for multiple companies.
*   **Deep Search**: Handles "View More" expansion and intelligent pagination to download *all* available reports, not just the first page.
*   **Smart Updates**:
    *   **Watchlist Management**: Save your favorite tickers (e.g., AAPL, TSLA).
    *   **Incremental Update**: One-click check to download only new reports from the last 30 days.
    *   **Duplicate Detection**: Skips files that have already been downloaded to save time and bandwidth.
*   **Dual-View Support**: Works seamlessly with both Grid View and Table View search results.
*   **Cloud Ready**: Optimized for deployment on Streamlit Cloud with automatic Headless mode detection.

## 🛠️ Installation

### Prerequisites
*   Python 3.8+
*   Google Chrome (for local running)

### Setup
1.  **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd GSResearch
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## 🖥️ Usage

1.  **Start the Application**:
    ```bash
    streamlit run app.py
    ```

2.  **Workflow**:
    *   **Step 1: Launch**: Click **"Launch Browser"** in the sidebar.
    *   **Step 2: Login**: A browser window will open. Manually log in to your GS Publishing account.
    *   **Step 3: Research**:
        *   **Manual Search**: Go to the **"Research Execution"** tab, enter tickers (comma-separated), and click "Start Research".
        *   **Watchlist**: Go to the **"Watchlist & Account"** tab to manage your stocks. Click **"Check Watchlist Updates"** to auto-fetch recent reports for all saved companies.

3.  **Output**:
    *   All files are downloaded to the `downloads/` folder, organized by company name.

## ☁️ Deployment (Streamlit Cloud)

This project is configured for easy deployment on Streamlit Cloud.

*   **`packages.txt`**: Included to install system-level dependencies (`chromium`, `chromium-driver`).
*   **Headless Mode**: The backend automatically detects the Linux environment and switches Chrome to headless mode (no visible UI), ensuring stability in the cloud.

## 📂 Project Structure

*   **`app.py`**: Main application entry point (Streamlit UI).
*   **`backend/core.py`**: Core automation logic (Selenium driver, navigation, scraping).
*   **`backend/watchlist_manager.py`**: Logic for managing the JSON-based watchlist.
*   **`watchlist.json`**: Local storage for user's watchlist (created automatically).
*   **`downloads/`**: Default directory for downloaded PDFs and Excel models.

## ⚠️ Note
This tool is for educational and productivity purposes. Please ensure you comply with the terms of service of the target website.
