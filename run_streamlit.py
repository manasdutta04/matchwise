"""
Quick start script for the Matchwise Streamlit web interface.
"""

import os
import sys
import subprocess

def main():
    print("Starting the Matchwise web interface with Streamlit...")
    
    # Use Python's module system to run streamlit
    try:
        # Try to run using python -m streamlit
        subprocess.run([sys.executable, "-m", "streamlit", "run", "src/app.py"])
    except Exception as e:
        print(f"Error running Streamlit: {e}")
        print("Please make sure streamlit is installed with: pip install streamlit")

if __name__ == "__main__":
    main() 