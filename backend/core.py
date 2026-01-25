import os
import time
import glob
import shutil
import re
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

class GSResearchDownloader:
    def __init__(self, download_dir="downloads", log_callback=None):
        self.base_url = "https://publishing.gs.com/"
        self.download_dir = os.path.abspath(download_dir)
        self.log_callback = log_callback
        
        # --- SELECTORS (Updated based on user's Adobe Inc. report HTML) ---
        self.SEARCH_BOX_SELECTOR = "div[data-cy='gs-uitk-header__search__search-input'] input"
        self.MODEL_SECTION_SELECTOR = "react-company-model-v2[data-title='DOWNLOAD MODEL']"
        self.REPORT_LINK_SELECTOR = "a[href*='/content/research/en/reports/']"
        # --------------------------------------------------------------------------

        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)

        # Configure Chrome options
        self.options = webdriver.ChromeOptions()
        prefs = {
            "download.default_directory": self.download_dir,
            "download.prompt_for_download": False,
            "directory_upgrade": True,
            "safebrowsing.enabled": True,
            "plugins.always_open_pdf_externally": True
        }
        self.options.add_experimental_option("prefs", prefs)
        
        # Headless mode for Streamlit Cloud / Linux
        # Use simple heuristic: if os.name != 'nt' (Windows) assume headless, or check for specific env vars
        # Streamlit Cloud usually runs on Linux
        if os.name != 'nt' or os.environ.get("HEADLESS_MODE") == "true":
            self.options.add_argument("--headless=new")
            self.options.add_argument("--no-sandbox")
            self.options.add_argument("--disable-dev-shm-usage")
            self.options.add_argument("--disable-gpu")
            self.options.add_argument("--window-size=1920,1080")
        
        # Initialize driver
        try:
            # 尝试自动安装并启动
            self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.options)
        except Exception:
            # 如果自动安装失败（常见于 Streamlit Cloud），尝试使用默认系统路径
            try:
                self.driver = webdriver.Chrome(options=self.options)
            except Exception as e:
                # 再次失败，抛出更清晰的错误信息
                raise RuntimeError(f"Failed to initialize Chrome Driver. Error: {e}")
        
        self.wait = WebDriverWait(self.driver, 20)

    def log(self, message):
        if self.log_callback:
            self.log_callback(message)
        else:
            print(message)

    def login_init(self):
        """
        Navigates to the login page.
        """
        self.log(f"Opening {self.base_url}...")
        self.driver.get(self.base_url)
        return "Please log in manually in the browser."

    def search_company(self, company_ticker):
        """
        Searches for a company by ticker or name.
        """
        self.log(f"Searching for company: {company_ticker}")
        try:
            # Wait for the search box to be present
            search_box = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, self.SEARCH_BOX_SELECTOR)))
            
            # Click to focus (sometimes needed)
            try:
                search_box.click()
            except:
                pass

            # Clear existing text and enter new search term
            search_box.clear()
            search_box.send_keys(company_ticker)
            time.sleep(2) # Wait for UI to react/dropdown
            search_box.send_keys(Keys.RETURN)
            
            self.log("Search submitted. Waiting for navigation...")
            time.sleep(5) # Wait for page load

            # Check if we are already on the dashboard (Model section exists)
            if self._is_on_company_page():
                self.log("Successfully navigated to company page.")
                return

            # If not, we might be on a search results page.
            # Try to find a link that matches the company name
            self.log("Not on company page yet. Checking for search results...")
            try:
                # Look for links containing the company name (case insensitive)
                # First try exact ticker match in brackets often seen in results e.g. "Company Name (TICKER)"
                # Then try loose match
                
                # XPath to find <a> tags that contain the ticker text
                # We'll use a slightly more robust strategy: find ANY link that has the ticker in its text
                
                found_link = None
                
                # Strategy 1: Look for exact ticker text
                try:
                    # Case-insensitive contains
                    xpath = f"//a[contains(translate(text(), 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), '{company_ticker.upper()}')]"
                    links = self.driver.find_elements(By.XPATH, xpath)
                    if links:
                        found_link = links[0]
                except:
                    pass
                
                # Strategy 2: If no link found, maybe it's the first result in a list?
                # Sometimes the search jumps directly to a "Search Results" list where the first item is the company
                if not found_link:
                     # Try to find the first result item's link
                     try:
                         first_result = self.driver.find_element(By.CSS_SELECTOR, "div[data-testid='search-item-content'] a")
                         found_link = first_result
                         self.log("Fallback: Selecting first search result link.")
                     except:
                         pass

                if found_link:
                    self.log(f"Found potential result link: {found_link.text}")
                    found_link.click()
                    
                    # Wait again for navigation
                    time.sleep(5)
                    if self._is_on_company_page():
                        self.log("Clicked result and navigated to company page.")
                    else:
                        self.log("Clicked link but still not detecting company page elements.")
                else:
                    self.log("Could not find a specific link for this ticker. Assuming we are on the correct page or results list.")
                    
            except Exception as e:
                self.log(f"Could not auto-select a company from results: {e}")
                self.log("Please manually click the correct company if multiple results appear.")

        except Exception as e:
            self.log(f"Error searching for company: {e}")
            self.log(f"Please check if selector '{self.SEARCH_BOX_SELECTOR}' is correct.")

    def _is_on_company_page(self):
        """Checks if the current page has company dashboard elements."""
        try:
            return len(self.driver.find_elements(By.CSS_SELECTOR, self.MODEL_SECTION_SELECTOR)) > 0
        except:
            return False

    def download_reports(self, company_name, min_pages=1, primary_only=True, days_filter=None, models_only=False):
        """
        Identifies and downloads models and reports.
        days_filter: int, optional. If set, only download reports from the last N days.
        models_only: bool, optional. If True, only download the model and skip reports.
        """
        self.log(f"Attempting to find {'models only' if models_only else 'reports and models'} for {company_name}...")
        
        # Create a specific directory for this company
        company_dir = os.path.join(self.download_dir, company_name)
        if not os.path.exists(company_dir):
            os.makedirs(company_dir)

        # 1. Handle Primary Tab
        if primary_only:
            self._ensure_primary_tab()
                
        # 2. Download Model
        try:
            model_section = self.driver.find_elements(By.CSS_SELECTOR, self.MODEL_SECTION_SELECTOR)
            if model_section:
                self.log("Found Model section.")
                # Look for the download button/link inside
                download_btn = model_section[0].find_element(By.CSS_SELECTOR, "a") # The link wraps the button
                if download_btn:
                    self.log("Downloading Model...")
                    self._click_and_download(download_btn, company_dir, f"{company_name}_Model")
            else:
                self.log("No Model section found.")
        except Exception as e:
            self.log(f"Error downloading model: {e}")
            
        if models_only:
            self.log("Models only mode enabled. Skipping reports download.")
            return
    
        # 3. Download Reports
        try:
            # 3.1 Click "View More" if available to see all reports
            try:
                # Selector based on user HTML: <span ...>View More</span> inside an <a> tag
                view_more_links = self.driver.find_elements(By.XPATH, "//span[contains(text(), 'View More')]")
                for vm in view_more_links:
                    try:
                        # Click the parent <a> or the span itself
                        parent = vm.find_element(By.XPATH, "./..")
                        self.log("Found 'View More' link, clicking to expand...")
                        parent.click()
                        time.sleep(5) # Wait for search page load
                        break
                    except:
                        pass
            except Exception as e:
                self.log(f"No 'View More' link found or error clicking it: {e}")

            # 3.2 Loop through pages
            page_num = 1
            processed_count = 0
            
            while True:
                self.log(f"Processing Page {page_num}...")
                
                # Explicit wait for report items to load (especially after pagination)
                try:
                    # Wait up to 10 seconds for either grid items or table rows to appear
                    WebDriverWait(self.driver, 10).until(
                        lambda d: len(d.find_elements(By.CSS_SELECTOR, "div[data-testid='search-item-content']")) > 0 or \
                                  len(d.find_elements(By.CLASS_NAME, "SearchResults__colCopy")) > 0
                    )
                except:
                    # If timeout, we just proceed to check (it might be empty really, or already loaded)
                    pass

                # Initialize lists and mode
                report_items = []
                mode = "unknown"
                
                # Strategy 1: Grid View (Standard)
                grid_items = self.driver.find_elements(By.CSS_SELECTOR, "div[data-testid='search-item-content']")
                if grid_items:
                    # self.log(f"Found {len(grid_items)} reports in Grid View.")
                    report_items = grid_items
                    mode = "grid"
                else:
                    # Strategy 2: Table View (Search Results Page)
                    # Find all rows that have the copy column
                    # We look for tr that contains .SearchResults__colCopy
                    table_rows = self.driver.find_elements(By.CSS_SELECTOR, "tr")
                    for row in table_rows:
                        if row.find_elements(By.CLASS_NAME, "SearchResults__colCopy"):
                            report_items.append(row)
                    
                    if report_items:
                        # self.log(f"Found {len(report_items)} reports in Table View.")
                        mode = "table"
                
                if not report_items:
                    self.log("No report items found in either Grid or Table view on this page.")
                    # Double check if we are maybe just loading slowly?
                    # If page > 1 and no items found, maybe we reached end or error?
                    if page_num > 1:
                         self.log("Warning: Pagination occurred but no items found on new page.")

                for i, container in enumerate(report_items):
                    if processed_count >= 1000: # Global limit increased
                        break
                        
                    try:
                        url = ""
                        title = ""
                        page_count = 0
                        container_text = container.text # For prefix check
                        report_date = None
                        
                        if mode == "grid":
                            # Extract Link and Title (Grid)
                            link_el = container.find_element(By.CSS_SELECTOR, "a")
                            url = link_el.get_attribute("href")
                            title = link_el.text
                            
                            # Extract Metadata (Page Count)
                            try:
                                metadata_el = container.find_element(By.CSS_SELECTOR, "div[data-testid='search-item-metadata']")
                                metadata_text = metadata_el.text
                                pg_match = re.search(r'(\d+)\s*(pg|pp|pages)', metadata_text, re.IGNORECASE)
                                if pg_match:
                                    page_count = int(pg_match.group(1))
                            except:
                                pass
                                
                        elif mode == "table":
                            # Extract Link and Title (Table)
                            # Look inside .SearchResults__colCopy
                            col_copy = container.find_element(By.CLASS_NAME, "SearchResults__colCopy")
                            link_el = col_copy.find_element(By.TAG_NAME, "a")
                            url = link_el.get_attribute("href")
                            title = link_el.text
                            
                            # Extract Page Count (Table)
                            try:
                                col_pages = container.find_element(By.CLASS_NAME, "SearchResults__colPages")
                                pg_text = col_pages.text.strip() # e.g. "9"
                                if pg_text.isdigit():
                                    page_count = int(pg_text)
                            except:
                                pass

                            # Extract Date (Table)
                            try:
                                date_el = container.find_element(By.CSS_SELECTOR, ".SearchResults__colDate .SearchResults__hiddenEl")
                                ts = int(date_el.get_attribute("textContent").strip())
                                # timestamp is milliseconds
                                report_date = datetime.fromtimestamp(ts / 1000)
                            except Exception as e:
                                # self.log(f"Could not extract date: {e}")
                                pass

                        if not url or "/content/research/en/reports/" not in url:
                            continue
                            
                        # Check Page Count Filter
                        if page_count < min_pages:
                            # self.log(f"Skipping report '{title[:30]}...' ({page_count} pages < {min_pages})")
                            continue

                        # Check Date Filter
                        if days_filter and report_date:
                            cutoff_date = datetime.now() - timedelta(days=days_filter)
                            if report_date < cutoff_date:
                                self.log(f"Skipping report '{title[:30]}...' (Date {report_date.date()} older than {days_filter} days)")
                                continue

                        # Check Duplicate (File Existence)
                        # Create a safe version of the title to match against existing filenames
                        # We used to take only first 30 chars, but let's be more robust
                        # We'll check if the "safe_title" part is contained in any existing filename
                        safe_title = "".join([c for c in title if c.isalnum() or c in " -_"]).strip()
                        # Truncate to a reasonable length for filename matching (avoid OS limits but keep enough uniqueness)
                        match_pattern = safe_title[:50] 
                        
                        existing_files = os.listdir(company_dir)
                        is_duplicate = False
                        
                        # Check 1: Filename match (Loose)
                        for f in existing_files:
                            if match_pattern in f and f.endswith(".pdf"):
                                is_duplicate = True
                                break
                        
                        if is_duplicate:
                            self.log(f"Skipping report '{title[:40]}...' (Already exists in folder)")
                            continue

                        # Determine Prefix (Rating Change / Initiation)
                        prefix = ""
                        if "Initiation" in title or "Initiation" in container_text:
                            prefix = "A_Initiation_"
                        elif "Rating Change" in title or "Rating Change" in container_text:
                                prefix = "A_Rating_"
                        
                        full_prefix = f"{prefix}{company_name}_Report_{processed_count+1}"
                        
                        self.log(f"Processing Report {processed_count+1}: {title[:50]}... ({page_count}pg)")
                        self._download_report_pdf(url, title, company_dir, full_prefix, processed_count+1)
                        processed_count += 1
                        
                    except Exception as e:
                        # self.log(f"Error processing report item {i}: {e}")
                        continue
                        
                # 3.3 Check for Next Page
                try:
                    # Selector based on user HTML: <a data-cy="gs-uitk-pagination__nav-link-next" ...>
                    next_btn = None
                    try:
                        # Capture the first item of the current page to wait for staleness later
                        first_item_on_current_page = report_items[0] if report_items else None

                        # Use the specific data-cy attribute found in HTML
                        # Also keep fallback to aria-label and common classes
                        next_selectors = [
                            "a[data-cy='gs-uitk-pagination__nav-link-next']", 
                            "a[aria-label='Goto next page']",
                            "a[aria-label='Next page']",
                            "a.SearchResults__paginationNext",
                            ".SearchResults__paginationNext",
                            "//a[contains(text(), 'Next')]",
                            "//a[contains(text(), '>')]",
                            "//a[contains(text(), '›')]",
                            "//span[contains(text(), 'Next')]/parent::a",
                            "//span[contains(text(), '>')]/parent::a"
                        ]
                        
                        for sel in next_selectors:
                            try:
                                if sel.startswith("//"):
                                    els = self.driver.find_elements(By.XPATH, sel)
                                else:
                                    els = self.driver.find_elements(By.CSS_SELECTOR, sel)
                                
                                if els:
                                    # Check visibility and state
                                    # Iterate to find the first visible one
                                    for el in els:
                                        if el.is_displayed() and el.get_attribute("aria-disabled") != "true" and "disabled" not in (el.get_attribute("class") or ""):
                                            next_btn = el
                                            self.log(f"Found 'Next' button using selector: {sel}")
                                            break
                                    if next_btn:
                                        break
                            except:
                                pass
                                
                        if next_btn:
                            self.log("Found 'Next' button. Moving to next page...")
                            # Scroll to ensure it's in view
                            self.driver.execute_script("arguments[0].scrollIntoView(true);", next_btn)
                            time.sleep(1)
                            
                            # Try standard click first
                            try:
                                next_btn.click()
                            except Exception:
                                self.log("Standard click failed, attempting JS click...")
                                self.driver.execute_script("arguments[0].click();", next_btn)
                                
                            # Wait for the page to actually reload/change
                            self.log("Waiting for page content to update...")
                            if first_item_on_current_page:
                                try:
                                    # Wait until the old item is attached to DOM (stale)
                                    WebDriverWait(self.driver, 15).until(
                                        EC.staleness_of(first_item_on_current_page)
                                    )
                                    self.log("Page update detected (old elements went stale).")
                                except:
                                    self.log("Warning: Timed out waiting for page update (staleness).")
                            
                            time.sleep(5) # Extra buffer for new elements to render
                            page_num += 1
                        else:
                            self.log("No 'Next' button found or it is disabled/hidden. Finished all pages.")
                            break
                            
                    except Exception as e:
                        self.log(f"Error finding next button: {e}")
                        break
                        
                except Exception as e:
                    self.log(f"Error checking next page: {e}")
                    break
            
        except Exception as e:
            self.log(f"Error processing reports: {e}")

    def _ensure_primary_tab(self):
        """
        Attempts to click the 'Primary' tab if available and not active.
        """
        try:
            # Look for the Primary tab
            # Selector based on HTML: <li ...><a ...>Primary</a></li>
            # XPath is easiest for text match
            primary_tab = self.driver.find_elements(By.XPATH, "//a[contains(text(), 'Primary')]")
            
            if primary_tab:
                el = primary_tab[0]
                # Check if active
                classes = el.get_attribute("class")
                if "active" not in classes:
                    self.log("Switching to 'Primary' tab...")
                    el.click()
                    time.sleep(3) # Wait for reload
                else:
                    self.log("'Primary' tab is already active.")
            else:
                self.log("'Primary' tab not found. Continuing with current view.")
        except Exception as e:
            self.log(f"Error switching tabs: {e}")

    def _click_and_download(self, element, target_dir, file_prefix):
        """
        Helper to click an element and handle the download file.
        """
        try:
            before_files = set(os.listdir(self.download_dir))
            element.click()
            self.wait_and_organize_download(before_files, target_dir, file_prefix)
        except Exception as e:
            self.log(f"Failed to download via click: {e}")

    def _download_report_pdf(self, report_url, report_title, target_dir, file_prefix, index):
        """
        Navigates to report page and attempts to download PDF.
        file_prefix: The prefix string passed from caller (e.g. "0291HK_Report_1")
        """
        original_window = self.driver.current_window_handle
        
        try:
            # Open in new tab
            self.driver.execute_script("window.open(arguments[0]);", report_url)
            self.driver.switch_to.window(self.driver.window_handles[-1])
            
            # Wait for load
            time.sleep(3)
            
            # Try to find PDF button
            # Common patterns: link ending in .pdf, or button with text "PDF" or "Download"
            pdf_selectors = [
                "a[href$='.pdf']",
                "a[aria-label*='PDF']",
                "button[aria-label*='PDF']",
                "//a[contains(text(), 'PDF')]",
                "//button[contains(text(), 'PDF')]"
            ]
            
            found = False
            for selector in pdf_selectors:
                try:
                    if selector.startswith("//"):
                        element = self.driver.find_element(By.XPATH, selector)
                    else:
                        element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    
                    if element:
                        self.log(f"Found PDF link on report page.")
                        # Use same safe_title logic as in check loop to ensure consistency
                        safe_title = "".join([c for c in report_title if c.isalnum() or c in " -_"]).strip()
                        # Limit to prevent OS path length issues but ensure it covers the match_pattern length
                        safe_title_filename = safe_title[:100] 
                        
                        # Fix: Avoid double prefixing. The caller already passes "Company_Report_X"
                        # We just append the title.
                        final_filename_prefix = f"{file_prefix}_{safe_title_filename}"
                        
                        self._click_and_download(element, target_dir, final_filename_prefix)
                        found = True
                        break
                except:
                    continue
            
            if not found:
                self.log(f"No PDF link found for report: {report_title}")
                
        except Exception as e:
            self.log(f"Error accessing report page: {e}")
        finally:
            # Close tab and switch back
            try:
                if len(self.driver.window_handles) > 1:
                    self.driver.close()
                self.driver.switch_to.window(original_window)
            except:
                pass

    def wait_and_organize_download(self, before_files, target_dir, new_name_prefix, timeout=30):
        """
        Waits for a new file to appear in the download directory, then moves and renames it.
        """
        end_time = time.time() + timeout
        new_file = None
        
        self.log("Waiting for download to start...")
        while time.time() < end_time:
            current_files = set(os.listdir(self.download_dir))
            new_files = current_files - before_files
            
            # Filter out temporary/hidden files if necessary, but keep crdownload for tracking
            valid_new_files = [f for f in new_files if not f.endswith('.tmp')]
            
            if valid_new_files:
                # Find the one that is likely the download (e.g. crdownload or final file)
                # If there are multiple, pick the one that is .crdownload or has just appeared
                for f in valid_new_files:
                     new_file = os.path.join(self.download_dir, f)
                     break
                if new_file:
                    break
            
            time.sleep(1)
            
        if not new_file:
            self.log("Timeout: No new file detected.")
            return

        self.log(f"Detected new file: {os.path.basename(new_file)}")

        # If it's a partial download, wait for it to finish
        wait_start = time.time()
        max_download_time = 300  # 5 minutes max wait
        
        while time.time() - wait_start < max_download_time:
            # Check if the file we are tracking still exists
            if not os.path.exists(new_file):
                # The .crdownload file disappeared. It was likely renamed to the final name.
                # Scan directory for any new file that is NOT .crdownload
                current_files = set(os.listdir(self.download_dir))
                final_candidates = current_files - before_files
                
                found_final = False
                for f in final_candidates:
                    if not f.endswith(".crdownload") and not f.endswith(".tmp"):
                        new_file = os.path.join(self.download_dir, f)
                        found_final = True
                        break
                
                if found_final:
                    self.log(f"Download finished. Identified final file: {os.path.basename(new_file)}")
                    break
                else:
                    # If the file is gone and we can't find a replacement, it might have been deleted or moved.
                    # We'll wait a brief moment and check again, but if it persists, we break to avoid infinite loop.
                    time.sleep(1)
                    current_files = set(os.listdir(self.download_dir))
                    if not any(f for f in (current_files - before_files) if not f.endswith('.crdownload')):
                         self.log("Warning: Temporary file disappeared but no final file found yet. Retrying detection...")
                         continue

            # If the file exists, check if it still has a temporary extension
            if not (new_file.endswith(".crdownload") or new_file.endswith(".tmp")):
                self.log("File extension indicates download complete.")
                break
                
            time.sleep(1)
            
        # Double check if file exists after loop
        if not os.path.exists(new_file):
             # Try to find any new file that is not in before_files
             current_files = set(os.listdir(self.download_dir))
             final_new_files = current_files - before_files
             if final_new_files:
                 new_file = os.path.join(self.download_dir, list(final_new_files)[0])
             else:
                 self.log("Error: Downloaded file lost.")
                 return

        filename = os.path.basename(new_file)
        extension = os.path.splitext(filename)[1]
        
        # Sanitize new name
        safe_name = "".join([c for c in new_name_prefix if c.isalpha() or c.isdigit() or c==' ' or c=='_']).strip()
        new_filename = f"{safe_name}{extension}"
        
        target_path = os.path.join(target_dir, new_filename)
        
        try:
            # Handle overwrite
            if os.path.exists(target_path):
                base, ext = os.path.splitext(target_path)
                target_path = f"{base}_{int(time.time())}{ext}"
                
            shutil.move(new_file, target_path)
            self.log(f"Moved and renamed to: {target_path}")
        except Exception as e:
            self.log(f"Error moving file: {e}")

    def check_watchlist_updates(self, watchlist_manager):
        """
        Checks for updates for all tickers in the watchlist.
        """
        watchlist = watchlist_manager.get_watchlist()
        self.log(f"Checking updates for watchlist: {watchlist}")
        
        for ticker in watchlist:
            self.search_company(ticker)
            self.download_reports(ticker, min_pages=1, primary_only=False, days_filter=30)

    def close(self):
        if self.driver:
            self.log("Closing browser...")
            self.driver.quit()
            self.driver = None
