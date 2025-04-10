"""
Main application entry point.
Initializes the database and starts the FastAPI server.
"""

import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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

# Create FastAPI application
app = FastAPI(
    title="Matchwise API",
    description="API for the Matchwise job application screening system",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this in production to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes - commented until fixed
# app.include_router(router, prefix="/api")

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Welcome to Matchwise API",
        "description": "AI-Powered Job Application Screening System",
        "documentation": "/docs"
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
    
    uvicorn.run(
        module_path,
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )


if __name__ == "__main__":
    main() 