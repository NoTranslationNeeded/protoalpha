import uvicorn
import webbrowser
import threading
import time
import sys
import os
from backend.main import app

def open_browser():
    time.sleep(2)
    webbrowser.open("http://localhost:8000")

if __name__ == "__main__":
    # Start browser in a separate thread
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Run server
    # workers=1 is important for PyInstaller to avoid multiprocessing issues
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
