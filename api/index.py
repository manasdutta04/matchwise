"""
Vercel serverless function entry point for the Matchwise API.
"""
import os
import sys

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set environment type
os.environ["ENVIRONMENT"] = "production"
os.environ["APP_TYPE"] = "api"

# Import the FastAPI app
from src.main import app

# Vercel uses the 'app' object directly
# This is a standard ASGI application
