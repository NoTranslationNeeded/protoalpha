from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import sys
from .api import router as api_router

app = FastAPI(title="MTGA Swapper API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api")

# Serve frontend static files
def get_static_dir():
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller bundle
        return os.path.join(sys._MEIPASS, "frontend", "dist")
    # Running in dev mode
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")

static_dir = get_static_dir()
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
else:
    @app.get("/")
    async def root():
        return {"message": "MTGA Swapper API is running (Frontend not found)"}
