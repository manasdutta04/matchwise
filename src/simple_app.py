"""
Simplified Streamlit app for the Matchwise job application screening system.
This version focuses on correctly loading data from the dataset.
"""

import os
import streamlit as st
import pandas as pd
import random
import glob
import json
import base64
from pathlib import Path
from datetime import datetime, timedelta
import tempfile
import time

# Function to load real job descriptions
def load_job_descriptions():
    """Load real job descriptions from the CSV file."""
    try:
        jd_path = "AI-Powered Job Application Screening System/job_description.csv"
        if os.path.exists(jd_path):
            # Try different encodings, as many CSV files use different encodings
            encodings_to_try = ['latin-1', 'cp1252', 'ISO-8859-1', 'utf-8-sig', 'utf-8']
            
            for encoding in encodings_to_try:
                try:
                    df = pd.read_csv(jd_path, encoding=encoding)
                    st.success(f"Successfully loaded job descriptions using {encoding} encoding")
                    break
                except UnicodeDecodeError:
                    if encoding == encodings_to_try[-1]:
                        st.error(f"Failed to decode file with any of the attempted encodings")
                        return []
                    continue
                except Exception as e:
                    st.error(f"Error reading CSV with {encoding} encoding: {e}")
                    continue
            
            jobs = []
            for i, row in df.iterrows():
                # Handle missing columns gracefully
                title = row.get("Job Title", f"Job {i+1}")
                description = row.get("Job Description", "No description available")
                
                jobs.append({
                    "id": i + 1,
                    "title": title,
                    "description": description
                })
            
            st.success(f"Loaded {len(jobs)} job descriptions")
            return jobs
        else:
            st.error(f"Job description file not found: {jd_path}")
            return []
    except Exception as e:
        st.error(f"Error loading job descriptions: {str(e)}")
        return []

# Function to load real CV files
def load_candidates():
    """Load real CV files from the dataset folder."""
    try:
        cv_folder = "AI-Powered Job Application Screening System/CVs1"
        if os.path.exists(cv_folder):
            st.success(f"Found CV folder: {cv_folder}")
            candidates = []
            cv_files = glob.glob(f"{cv_folder}/*.pdf")
            
            if not cv_files:
                st.warning(f"No PDF files found in {cv_folder}. Checking subdirectories...")
                # Try looking in subdirectories
                cv_files = glob.glob(f"{cv_folder}/**/*.pdf", recursive=True)
            
            if not cv_files:
                st.error(f"No PDF files found in {cv_folder} or its subdirectories")
                return []
            
            st.success(f"Found {len(cv_files)} CV files")
            
            for i, cv_file in enumerate(cv_files):
                # Extract filename
                filename = os.path.basename(cv_file)
                candidate_id = filename.split('.')[0]  # Extract ID from filename (e.g., "C9945" from "C9945.pdf")
                
                # Basic candidate info
                candidates.append({
                    "id": i + 1,
                    "name": f"Candidate {candidate_id}",
                    "cv_filename": filename,
                    "cv_path": cv_file,
                    "raw_id": candidate_id
                })
            
            return candidates
        else:
            # Try alternative paths
            alt_paths = [
                "AI-Powered Job Application Screening System/CVs",
                "AI-Powered Job Application Screening System/CV",
                "AI-Powered Job Application Screening System/Resumes",
                "CVs1",
                "CVs"
            ]
            
            for path in alt_paths:
                if os.path.exists(path):
                    st.success(f"Found alternative CV folder: {path}")
                    cv_files = glob.glob(f"{path}/*.pdf")
                    
                    if cv_files:
                        candidates = []
                        for i, cv_file in enumerate(cv_files):
                            filename = os.path.basename(cv_file)
                            candidate_id = filename.split('.')[0]
                            
                            candidates.append({
                                "id": i + 1,
                                "name": f"Candidate {candidate_id}",
                                "cv_filename": filename,
                                "cv_path": cv_file,
                                "raw_id": candidate_id
                            })
                        
                        st.success(f"Loaded {len(candidates)} candidates from alternative path")
                        return candidates
            
            # If we get here, we couldn't find any CVs in any location
            st.error(f"CV folder not found in any expected locations")
            return []
            
    except Exception as e:
        st.error(f"Error loading candidates: {str(e)}")
        st.exception(e)  # This will show the full traceback
        return []

# Function to display PDF (for viewing CVs)
def display_pdf(file_path):
    """Display a PDF file in Streamlit."""
    try:
        # First check if file exists
        if not os.path.exists(file_path):
            st.error(f"PDF file not found: {file_path}")
            return False
        
        # Check file size (limit to 10MB to avoid memory issues)
        file_size = os.path.getsize(file_path) / (1024 * 1024)  # Convert to MB
        if file_size > 10:
            st.warning(f"PDF file is large ({file_size:.1f} MB). Loading preview may take time.")
        
        # Try to read and display the PDF
        with open(file_path, "rb") as f:
            base64_pdf = base64.b64encode(f.read()).decode('utf-8')
        
        pdf_display = f"""
            <iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf"></iframe>
        """
        st.markdown(pdf_display, unsafe_allow_html=True)
        return True
    except FileNotFoundError:
        st.error(f"PDF file not found: {file_path}")
        return False
    except Exception as e:
        st.error(f"Error displaying PDF: {str(e)}")
        st.info("PDF preview is not available. You can download the file instead.")
        
        # Try to provide a download option even if display fails
        try:
            with open(file_path, "rb") as file:
                filename = os.path.basename(file_path)
                st.download_button(
                    label="Download PDF", 
                    data=file,
                    file_name=filename,
                    mime="application/pdf"
                )
        except Exception as download_error:
            st.error(f"Unable to provide download option: {str(download_error)}")
        
        return False

# Page configuration
st.set_page_config(
    page_title="Matchwise - Data Loading Test",
    page_icon="📋",  # Fixed icon
    layout="wide"
)

# Main application
st.title("Matchwise - Data Loading Test")
st.info("This simple app verifies that we can correctly load data from the dataset.")

# Create tabs
tab1, tab2, tab3 = st.tabs(["Job Descriptions", "Candidates", "PDF Viewer"])

with tab1:
    st.header("Job Descriptions")
    
    # Load job descriptions
    jobs = load_job_descriptions()
    
    if jobs:
        # Display jobs in a table
        job_data = []
        for job in jobs:
            # Truncate description for display
            desc = job["description"]
            short_desc = desc[:100] + "..." if len(desc) > 100 else desc
            
            job_data.append({
                "ID": job["id"],
                "Title": job["title"],
                "Description": short_desc
            })
        
        st.dataframe(pd.DataFrame(job_data), use_container_width=True)
        
        # Show a sample job in full
        st.subheader("Sample Job Description")
        sample_job = random.choice(jobs)
        st.write(f"**Title:** {sample_job['title']}")
        st.write(f"**Description:**\n{sample_job['description']}")
    else:
        st.error("No job descriptions were loaded.")

with tab2:
    st.header("Candidates")
    
    # Load candidates
    candidates = load_candidates()
    
    if candidates:
        # Display candidates in a table
        candidate_data = []
        for candidate in candidates:
            candidate_data.append({
                "ID": candidate["id"],
                "Name": candidate["name"],
                "Filename": candidate["cv_filename"],
                "Raw ID": candidate["raw_id"]
            })
        
        st.dataframe(pd.DataFrame(candidate_data), use_container_width=True)
        
        # Show a few random candidates
        st.subheader("Sample Candidates")
        sample_candidates = random.sample(
            candidates, 
            min(5, len(candidates))
        )
        
        for candidate in sample_candidates:
            st.write(f"**{candidate['name']}** - File: {candidate['cv_filename']}")
    else:
        st.error("No candidates were loaded.")

with tab3:
    st.header("PDF Viewer Test")
    
    # Load candidates for PDF selection
    candidates = load_candidates()
    
    if candidates:
        # Select a random CV to display
        sample_candidates = random.sample(
            candidates, 
            min(5, len(candidates))
        )
        
        # Create selection
        selected_candidate = st.selectbox(
            "Select a CV to view",
            options=[f"{c['name']} ({c['cv_filename']})" for c in sample_candidates],
            index=0
        )
        
        # Find the selected candidate
        selected_index = [f"{c['name']} ({c['cv_filename']})" for c in sample_candidates].index(selected_candidate)
        candidate = sample_candidates[selected_index]
        
        # Display the PDF
        st.subheader(f"Viewing: {candidate['cv_filename']}")
        display_pdf(candidate["cv_path"])
    else:
        st.error("No PDF files available to display.") 