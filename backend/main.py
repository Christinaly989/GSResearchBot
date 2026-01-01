from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import threading
import time
import os
from core import GSResearchDownloader

app = FastAPI()

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
class AppState:
    downloader: Optional[GSResearchDownloader] = None
    status: str = "idle" # idle, login_pending, ready, processing, error
    logs: List[str] = []
    
state = AppState()

class InitRequest(BaseModel):
    download_dir: str = "downloads"

class ProcessRequest(BaseModel):
    companies: List[str]

def log(message: str):
    timestamp = time.strftime("%H:%M:%S")
    entry = f"[{timestamp}] {message}"
    print(entry)
    state.logs.append(entry)
    # Keep logs manageable
    if len(state.logs) > 100:
        state.logs = state.logs[-100:]

@app.get("/status")
def get_status():
    return {"status": state.status, "logs": state.logs}

@app.post("/init")
def init_browser(req: InitRequest):
    if state.downloader:
        log("Browser already initialized.")
        return {"message": "Browser already initialized", "status": state.status}
    
    try:
        log("Initializing browser...")
        # Adjust download dir to be absolute relative to where the backend is running
        # Assuming backend is running from backend/ or root, let's make sure it's correct
        # If running from root, "downloads" is fine.
        state.downloader = GSResearchDownloader(req.download_dir, log_callback=log)
        state.status = "login_pending"
        
        msg = state.downloader.login_init()
        log(msg)
        
        return {"message": "Browser initialized. Please log in.", "status": state.status}
    except Exception as e:
        state.status = "error"
        log(f"Error initializing: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/confirm-login")
def confirm_login():
    if not state.downloader:
        raise HTTPException(status_code=400, detail="Browser not initialized")
    
    state.status = "ready"
    log("Login confirmed by user. Ready to process.")
    return {"status": state.status}

def process_companies_task(companies: List[str]):
    if not state.downloader:
        return
    
    state.status = "processing"
    try:
        for company in companies:
            if state.status != "processing": # Allow stopping
                break
            log(f"Processing company: {company}")
            state.downloader.search_company(company)
            state.downloader.download_reports(company)
            log(f"Finished processing {company}")
        
        log("Batch processing complete.")
        state.status = "ready"
    except Exception as e:
        log(f"Error during processing: {str(e)}")
        state.status = "error"

@app.post("/process")
def start_processing(req: ProcessRequest, background_tasks: BackgroundTasks):
    if not state.downloader:
        raise HTTPException(status_code=400, detail="Browser not initialized")
    
    if state.status != "ready":
        # Allow force processing if needed, but warn
        pass

    background_tasks.add_task(process_companies_task, req.companies)
    return {"message": "Processing started", "status": "processing"}

@app.post("/stop")
def stop_browser():
    if state.downloader:
        log("Stopping browser...")
        state.downloader.close()
        state.downloader = None
    state.status = "idle"
    return {"message": "Browser stopped", "status": state.status}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
