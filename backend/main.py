"""
Main FastAPI application for Code Review Agent with Learning Memory.
"""
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv
import uvicorn

from backend.api.review import review_router
from backend.api.feedback import feedback_router
from backend.api.stats import stats_router

# Load environment variables
load_dotenv()

app = FastAPI(title="Code Review Agent", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(review_router, prefix="/api", tags=["review"])
app.include_router(feedback_router, prefix="/api", tags=["feedback"])
app.include_router(stats_router, prefix="/api", tags=["stats"])

# Serve frontend static files
frontend_path = project_root / "frontend"
if frontend_path.exists():
    # Mount static files (CSS, JS)
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")
    
    # Serve CSS and JS files directly
    @app.get("/styles.css")
    async def get_css():
        css_file = frontend_path / "styles.css"
        if css_file.exists():
            return FileResponse(str(css_file), media_type="text/css")
        raise HTTPException(status_code=404)
    
    @app.get("/app.js")
    async def get_js():
        js_file = frontend_path / "app.js"
        if js_file.exists():
            return FileResponse(str(js_file), media_type="application/javascript")
        raise HTTPException(status_code=404)

@app.get("/")
async def read_root():
    """Serve the main frontend page."""
    frontend_file = frontend_path / "index.html"
    if frontend_file.exists():
        return FileResponse(str(frontend_file))
    return {"message": "Code Review Agent API", "docs": "/docs"}

if __name__ == "__main__":
    port = int(os.getenv("API_PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

