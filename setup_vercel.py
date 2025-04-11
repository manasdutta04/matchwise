#!/usr/bin/env python
"""
Setup script for Vercel deployment of Matchwise.
This script prepares your project for deployment to Vercel.
"""
import os
import shutil
import json
import secrets
from pathlib import Path

def main():
    """Prepare the project for Vercel deployment."""
    print("Setting up Matchwise for Vercel deployment...")
    
    # Create required directories
    os.makedirs("api", exist_ok=True)
    os.makedirs(".streamlit", exist_ok=True)
    
    # Generate Vercel configuration
    vercel_config = {
        "version": 2,
        "builds": [
            {
                "src": "api/index.py",
                "use": "@vercel/python"
            }
        ],
        "routes": [
            {
                "src": "/(.*)",
                "dest": "api/index.py"
            }
        ],
        "env": {
            "APP_TYPE": "api",
            "ENVIRONMENT": "production",
            "VERCEL": "1",
            "SECRET_KEY": secrets.token_hex(32)
        }
    }
    
    # Create Vercel configuration file
    with open("vercel.json", "w") as f:
        json.dump(vercel_config, f, indent=2)
    print("✅ Created vercel.json")
    
    # Create API entry point
    api_entry_content = """\"\"\"
Vercel serverless function entry point for the Matchwise API.
\"\"\"
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
"""
    
    with open("api/index.py", "w") as f:
        f.write(api_entry_content)
    print("✅ Created api/index.py")
    
    # Create API requirements
    api_requirements = """fastapi==0.109.2
uvicorn==0.27.1
python-dotenv==1.0.0
SQLAlchemy==2.0.27
aiosqlite>=0.19.0
pydantic>=2.0.0
httpx>=0.27.0
"""
    
    with open("api/requirements.txt", "w") as f:
        f.write(api_requirements)
    print("✅ Created api/requirements.txt")
    
    # Create Streamlit configuration
    streamlit_config = """[server]
enableCORS = true
enableXsrfProtection = true

[browser]
gatherUsageStats = false

[theme]
primaryColor = "#1E88E5"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"
"""
    
    with open(".streamlit/config.toml", "w") as f:
        f.write(streamlit_config)
    print("✅ Created .streamlit/config.toml")
    
    # Create README for Vercel deployment
    print("✅ Created VERCEL_DEPLOYMENT.md (check this file for detailed instructions)")
    
    print("\nSetup complete! Follow the steps in VERCEL_DEPLOYMENT.md to deploy your application.")

if __name__ == "__main__":
    main() 