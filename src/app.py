"""
Matchwise Job Application Screening System.
"""

import streamlit as st

# Configure the page - This must be the first Streamlit command
st.set_page_config(
    page_title="Matchwise",
    page_icon="✓",
    layout="wide"
)

import os
import sys

# Add the current directory to sys.path to ensure imports work
sys.path.append(os.path.dirname(__file__))

# Import the main function from matchwise_app
from matchwise_app import main

# Run the main application function
if __name__ == "__main__":
    main() 