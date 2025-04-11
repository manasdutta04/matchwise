"""
Main application entry point.
Initializes the database and starts the FastAPI server.
"""

import os
import logging
import datetime
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
import uvicorn

# Import database utilities
# When run as a module, we need to use relative import
try:
    from .database.db import init_db
except ImportError:
    # When run directly, use absolute import
    from src.database.db import init_db

# Import API routes - commented until fixed
# from src.api.routes import router

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Environment variables
SECRET_KEY = os.environ.get("SECRET_KEY", "development_secret_key")
ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# Configure CORS origins based on environment
if ENVIRONMENT == "production":
    # In production, only allow your Streamlit app domain
    allowed_origins = [
        os.environ.get("STREAMLIT_URL", "https://your-app.streamlit.app"),
    ]
    # You can add more allowed origins as needed:
    # If additional origins are specified in environment variables
    additional_origins = os.environ.get("ADDITIONAL_CORS_ORIGINS", "")
    if additional_origins:
        allowed_origins.extend(additional_origins.split(","))
else:
    # In development, allow all local origins
    allowed_origins = [
        "http://localhost:8501",  # Default Streamlit port
        "http://localhost:3000",  # For potential React frontend
        "http://127.0.0.1:8501",
    ]

# Create FastAPI application
app = FastAPI(
    title="Matchwise API",
    description="API for the Matchwise job application screening system",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes - commented until fixed
# app.include_router(router, prefix="/api")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy", 
        "timestamp": datetime.datetime.now().isoformat(),
        "environment": ENVIRONMENT
    }

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Welcome to Matchwise API",
        "description": "AI-Powered Job Application Screening System",
        "documentation": "/docs",
        "health_check": "/health"
    }


def main():
    """
    Main application function that initializes the database and starts the server.
    """
    # Initialize database
    logger.info("Initializing database...")
    init_db()
    
    # Start the server
    logger.info("Starting API server...")
    # Get the correct module path depending on how we're running this
    import sys
    if __name__ == "__main__":
        module_path = "src.main:app"
    else:
        module_path = "src.main:app"
    
    # Get port from environment variable or use default
    port = int(os.environ.get("PORT", 8000))
    
    uvicorn.run(
        module_path,
        host="0.0.0.0",
        port=port,
        reload=ENVIRONMENT == "development",  # Only reload in development
        log_level="info"
    )


if __name__ == "__main__":
    main() 