# GS Research Bot

[English](#english) | [中文说明](#chinese)

<a id="chinese"></a>
## 📖 中文说明

**GS Research Bot** 是一个强大的自动化工具，旨在简化从高盛发布门户下载研究报告和财务模型的过程。它基于 **Python**、**Selenium** 和 **Streamlit** 构建，提供了一个用户友好的界面来高效管理研究任务。

### 🚀 功能特点

*   **批量下载**：自动搜索并下载多家公司的报告/模型。
*   **深度搜索**：支持自动点击“View More”展开更多结果，并具备智能翻页功能，确保下载*所有*可用报告，而不仅仅是第一页。
*   **智能更新**：
    *   **关注列表管理**：保存你关注的股票代码（如 AAPL, TSLA）。
    *   **增量更新**：一键检查并仅下载过去 30 天内发布的新报告。
    *   **去重检测**：自动跳过已下载的文件，节省时间和带宽。
*   **仅模型模式**：专门的功能，用于批量下载多家公司的财务模型（Excel），跳过报告处理以提高速度。
*   **双视图支持**：完美支持网格视图（Grid View）和列表视图（Table View）的搜索结果。

### 🛠️ 安装指南

#### 前置要求
*   Python 3.8+
*   Google Chrome (用于本地运行)

#### 设置步骤
1.  **克隆仓库**：
    ```bash
    git clone <repository-url>
    cd GSResearch
    ```

2.  **安装依赖**：
    ```bash
    pip install -r requirements.txt
    ```

### 🖥️ 使用说明

1.  **启动应用**：
    ```bash
    streamlit run app.py
    ```

2.  **工作流程**：

    #### 第一步：启动与登录
    *   点击侧边栏的 **"Launch Browser"**（启动浏览器）。
    *   Chrome 窗口将会打开。请在该窗口中**手动登录**你的 GS Publishing 账号。

    #### 第二步：选择任务

    **选项 A：完整研报下载 (标签页: "Research Execution")**
    *   **适用场景**：新公司调研或深度分析。
    *   输入股票代码（逗号分隔，例如 `Apple, Tesla`）。
    *   设置 **Minimum Pages**（最小页数，例如 1）以过滤简短的笔记。
    *   点击 **"Start Research"**。
    *   *执行动作*：下载最新的财务模型 + 所有历史报告（含自动翻页）。

    **选项 B：管理与自动更新 (标签页: "Watchlist & Account")**
    *   **适用场景**：日常/每周维护。
    *   **管理**：在持久化的关注列表（Watchlist）中添加或移除公司。
    *   **更新**：点击 **"Check Watchlist Updates"**。
    *   *执行动作*：检查关注列表中所有公司在**过去 30 天**内发布的新报告（跳过已存在的文件）。

    **选项 C：仅批量下载模型 (标签页: "Batch Models")**
    *   **适用场景**：快速获取多家公司的 Excel 模型，无需等待报告下载。
    *   输入股票代码（逗号分隔）。
    *   点击 **"Download Models Only"**。
    *   *执行动作*：跳过所有报告，仅下载财务模型文件。

3.  **输出结果**：
    *   所有文件将下载到 `downloads/` 文件夹，按公司名称分类（例如 `downloads/Apple/`）。

### ⚠️ 注意事项
本工具仅供教育和提高生产力使用。请确保遵守目标网站的服务条款。

---

<a id="english"></a>
## 📖 English Documentation

**GS Research Bot** is a powerful automation tool designed to streamline the process of downloading research reports and financial models from the GS Publishing portal. Built with **Python**, **Selenium**, and **Streamlit**, it provides a user-friendly interface to manage research tasks efficiently.

### 🚀 Features

*   **Batch Downloading**: Automatically search for and download reports/models for multiple companies.
*   **Deep Search**: Handles "View More" expansion and intelligent pagination to download *all* available reports, not just the first page.
*   **Smart Updates**:
    *   **Watchlist Management**: Save your favorite tickers (e.g., AAPL, TSLA).
    *   **Incremental Update**: One-click check to download only new reports from the last 30 days.
    *   **Duplicate Detection**: Skips files that have already been downloaded to save time and bandwidth.
*   **Model-Only Mode**: Dedicated feature to batch download *only* financial models for multiple companies, skipping report processing for speed.
*   **Dual-View Support**: Works seamlessly with both Grid View and Table View search results.

### 🛠️ Installation

#### Prerequisites
*   Python 3.8+
*   Google Chrome (for local running)

#### Setup
1.  **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd GSResearch
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

### 🖥️ Usage

1.  **Start the Application**:
    ```bash
    streamlit run app.py
    ```

2.  **Workflow**:

    #### Step 1: Launch & Login
    *   Click **"Launch Browser"** in the sidebar.
    *   A Chrome window will open. **Manually log in** to your GS Publishing account in this window.

    #### Step 2: Choose Your Task

    **Option A: Full Research (Tab: "Research Execution")**
    *   Best for: New companies or deep dives.
    *   Enter tickers (comma-separated, e.g., `Apple, Tesla`).
    *   Set **Minimum Pages** (e.g., 1) to filter short notes.
    *   Click **"Start Research"**.
    *   *Action*: Downloads the latest model + ALL reports (paginated).

    **Option B: Manage & Auto-Update (Tab: "Watchlist & Account")**
    *   Best for: Daily/Weekly maintenance.
    *   **Manage**: Add or remove companies from your persistent Watchlist.
    *   **Update**: Click **"Check Watchlist Updates"**.
    *   *Action*: Checks all watchlist companies for reports released in the **last 30 days** that are not yet in your folder.

    **Option C: Batch Models Only (Tab: "Batch Models")**
    *   Best for: Quickly grabbing Excel models for many companies without waiting for reports.
    *   Enter tickers (comma-separated).
    *   Click **"Download Models Only"**.
    *   *Action*: Skips all reports and downloads only the financial model file.

3.  **Output**:
    *   All files are downloaded to the `downloads/` folder, organized by company name (e.g., `downloads/Apple/`).

### 📂 Project Structure

*   **`app.py`**: Main application entry point (Streamlit UI).
*   **`backend/core.py`**: Core automation logic (Selenium driver, navigation, scraping).
*   **`backend/watchlist_manager.py`**: Logic for managing the JSON-based watchlist.
*   **`watchlist.json`**: Local storage for user's watchlist (created automatically).
*   **`downloads/`**: Default directory for downloaded PDFs and Excel models.

### ⚠️ Note
This tool is for educational and productivity purposes. Please ensure you comply with the terms of service of the target website.
