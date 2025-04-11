"""
Production deployment script for the Matchwise application.
This script can run either the FastAPI backend or Streamlit frontend
based on the APP_TYPE environment variable.
"""

import os
import sys
import logging
import uvicorn
import subprocess
from dotenv import load_dotenv
from src.database.db import init_db

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables from .env file if it exists
load_dotenv()

def run_api():
    """Run the FastAPI backend server"""
    logger.info("Initializing database...")
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        sys.exit(1)
    
    # Get port from environment variable or use default
    port = int(os.environ.get("PORT", 8000))
    
    logger.info(f"Starting Matchwise API server on port {port}...")
    
    # Check for workers setting in environment
    workers = int(os.environ.get("API_WORKERS", 4))
    
    try:
        uvicorn.run(
            "src.main:app",
            host="0.0.0.0",
            port=port,
            workers=workers,
            log_level=os.environ.get("LOG_LEVEL", "info")
        )
    except Exception as e:
        logger.error(f"Error starting API server: {e}")
        sys.exit(1)

def run_streamlit():
    """Run the Streamlit frontend"""
    # Get port from environment variable or use default
    port = os.environ.get("PORT", 8501)
    
    logger.info(f"Starting Matchwise Streamlit interface on port {port}...")
    
    # Build command with arguments
    cmd = [
        "streamlit", "run", "src/app.py",
        "--server.port", str(port),
        "--server.address", "0.0.0.0"
    ]
    
    # Add optional server settings if specified
    if os.environ.get("STREAMLIT_SERVER_HEADLESS", "true").lower() == "true":
        cmd.extend(["--server.headless", "true"])
    
    if os.environ.get("STREAMLIT_SERVER_ENABLE_CORS", "false").lower() == "true":
        cmd.extend(["--server.enableCORS", "true"])
    
    try:
        # Use direct subprocess call
        process = subprocess.run(cmd)
        if process.returncode != 0:
            logger.error(f"Streamlit process exited with code {process.returncode}")
            sys.exit(process.returncode)
    except Exception as e:
        logger.error(f"Error running Streamlit: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Determine which component to run based on environment variable
    app_type = os.environ.get("APP_TYPE", "api").lower()
    
    logger.info(f"Starting Matchwise in {app_type} mode")
    
    if app_type == "api":
        run_api()
    elif app_type == "streamlit":
        run_streamlit()
    else:
        logger.error(f"Unknown APP_TYPE: {app_type}. Use 'api' or 'streamlit'.")
        sys.exit(1) 