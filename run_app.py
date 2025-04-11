#!/usr/bin/env python
"""
Run script for the Matchwise Job Application Screening System.
This script launches the Streamlit web interface.
"""

import os
import sys
import subprocess
import importlib.util
import re

def check_dependency(package_name):
    """Check if a Python package is installed."""
    return importlib.util.find_spec(package_name) is not None

def check_streamlit_config():
    """Check if Streamlit configuration is set up properly."""
    # Path to the application files
    app_path = os.path.join("src", "app.py")
    matchwise_app_path = os.path.join("src", "matchwise_app.py")
    
    if not os.path.exists(app_path) or not os.path.exists(matchwise_app_path):
        return True  # Skip check if files don't exist
    
    # Count set_page_config calls
    count = 0
    
    # Check app.py
    with open(app_path, 'r') as f:
        app_content = f.read()
        if 'set_page_config' in app_content:
            count += 1
    
    # Check matchwise_app.py
    with open(matchwise_app_path, 'r') as f:
        matchwise_content = f.read()
        if 'set_page_config' in matchwise_content:
            count += 1
    
    return count == 1  # Should have exactly one set_page_config call

def main():
    """
    Start the Matchwise application with Streamlit.
    """
    # Check essential dependencies
    missing_deps = []
    for package in ["streamlit", "pandas", "numpy", "PyPDF2"]:
        if not check_dependency(package):
            missing_deps.append(package)
    
    if missing_deps:
        print("Error: Missing required dependencies:")
        for dep in missing_deps:
            print(f"  - {dep}")
        print("\nPlease install the missing dependencies with:")
        print(f"pip install {' '.join(missing_deps)}")
        sys.exit(1)
    
    # Check Streamlit config
    if not check_streamlit_config():
        print("Warning: Multiple st.set_page_config() calls detected in the codebase.")
        print("This may cause errors when running the application.")
        print("Ensure only one file (typically app.py) calls set_page_config() and it's the first Streamlit command.")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)
    
    print("\n" + "="*60)
    print("Starting Matchwise Job Application Screening System...")
    print("="*60)
    
    # Path to the application
    app_path = os.path.join("src", "app.py")
    
    # Check if the file exists
    if not os.path.exists(app_path):
        print(f"Error: Application file not found at {app_path}")
        sys.exit(1)
    
    # Create data directory if it doesn't exist
    data_dir = os.path.join("src", "data")
    if not os.path.exists(data_dir):
        print(f"Creating data directory at {data_dir}")
        os.makedirs(data_dir, exist_ok=True)
    
    # Run the Streamlit application
    try:
        print("Launching Streamlit interface...")
        print("The application will be available at http://localhost:8501")
        print("Press Ctrl+C to stop the application")
        print("="*60 + "\n")
        
        subprocess.run([sys.executable, "-m", "streamlit", "run", app_path])
    except KeyboardInterrupt:
        print("\nApplication stopped by user.")
    except Exception as e:
        print(f"\nError running Streamlit: {e}")
        print("Please make sure streamlit is installed with: pip install streamlit")
        sys.exit(1)

if __name__ == "__main__":
    main() 