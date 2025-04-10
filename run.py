"""
Quick start script for the Matchwise application.
"""

import uvicorn
from src.database.db import init_db

def main():
    # Initialize the database first
    print("Initializing database...")
    init_db()
    
    # Start the FastAPI server
    print("Starting the Matchwise API server...")
    uvicorn.run(
        "src.main:app", 
        host="0.0.0.0",
        port=8000,
        reload=True
    )

if __name__ == "__main__":
    main() 