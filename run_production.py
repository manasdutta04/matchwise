"""
Production deployment script for the Matchwise application.
This script can run either the FastAPI backend or Streamlit frontend
based on the APP_TYPE environment variable.
"""

import os
import sys
import uvicorn
import subprocess
from src.database.db import init_db

def run_api():
    """Run the FastAPI backend server"""
    print("Initializing database...")
    init_db()
    
    # Get port from environment variable or use default
    port = int(os.environ.get("PORT", 8000))
    
    print(f"Starting Matchwise API server on port {port}...")
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=port,
        workers=4  # Multiple workers for production
    )

def run_streamlit():
    """Run the Streamlit frontend"""
    # Get port from environment variable or use default
    port = os.environ.get("PORT", 8501)
    
    print(f"Starting Matchwise Streamlit interface on port {port}...")
    # Use direct subprocess call
    subprocess.run([
        "streamlit", "run", "src/app.py",
        "--server.port", str(port),
        "--server.address", "0.0.0.0"
    ])

if __name__ == "__main__":
    # Determine which component to run based on environment variable
    app_type = os.environ.get("APP_TYPE", "api").lower()
    
    if app_type == "api":
        run_api()
    elif app_type == "streamlit":
        run_streamlit()
    else:
        print(f"Unknown APP_TYPE: {app_type}. Use 'api' or 'streamlit'.")
        sys.exit(1) 