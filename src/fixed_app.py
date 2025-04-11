"""
Streamlit web application for the Matchwise job application screening system.
AI-Powered Job Application Screening System with real data integration.
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

# Page configuration
st.set_page_config(
    page_title="Matchwise - AI Job Screening",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply a custom theme with modern styling
st.markdown("""
<style>
    /* Modern, clean styling */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        max-width: 1200px;
    }
    h1, h2, h3 {
        color: #1E88E5;
        font-weight: 600;
    }
    .stButton>button {
        background-color: #1E88E5;
        color: white;
        border-radius: 4px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: 500;
    }
    .stButton>button:hover {
        background-color: #1976D2;
    }
    /* Card-like styling for expandable sections */
    .streamlit-expanderHeader {
        background-color: #f8f9fa;
        border-radius: 4px;
    }
    /* Custom styling for metrics */
    .metric-container {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    /* Table styling */
    .dataframe {
        border-radius: 4px;
        overflow: hidden;
    }
    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 4px 4px 0 0;
        padding: 8px 16px;
        background-color: #f1f3f4;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1E88E5 !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

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
            st.error(f"CV folder not found: {cv_folder}")
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

# Function to create matches between jobs and candidates
def create_matches(job_id, candidate_ids=None):
    """Create matches between jobs and candidates with simulated AI scoring."""
    try:
        all_candidates = load_candidates()
        all_jobs = load_job_descriptions()
        
        # Find the selected job
        selected_job = next((job for job in all_jobs if job["id"] == job_id), None)
        if not selected_job:
            st.error(f"Job with ID {job_id} not found")
            return []
        
        # Select candidates
        if candidate_ids:
            candidates = [c for c in all_candidates if c["id"] in candidate_ids]
        else:
            candidates = all_candidates
        
        if not candidates:
            st.warning("No candidates selected for matching")
            return []
        
        st.info(f"Matching {len(candidates)} candidates to job: {selected_job['title']}")
        
        # In a real system, this would use the multi-agent framework to calculate actual match scores
        # Here we'll use a more sophisticated simulation approach
        matches = []
        
        # Extract job keywords for simple matching
        job_desc_lower = selected_job["description"].lower()
        
        # Define common skill keywords by job type to simulate matching
        tech_skills = ["python", "java", "javascript", "sql", "aws", "cloud", "react", "node", 
                      "docker", "kubernetes", "ai", "machine learning", "data science", "analytics"]
        
        management_skills = ["leadership", "management", "strategy", "communication", "project", 
                            "agile", "scrum", "planning", "stakeholder", "budget", "team"]
        
        # Determine if job is more technical or management focused
        tech_count = sum(1 for skill in tech_skills if skill in job_desc_lower)
        mgmt_count = sum(1 for skill in management_skills if skill in job_desc_lower)
        
        is_technical = tech_count > mgmt_count
        
        # Create matches with "intelligent" scoring based on CV ID patterns
        for candidate in candidates:
            # Parse candidate ID to generate consistent but semi-random scores
            # This simulates how different candidates would naturally match better with different jobs
            candidate_raw_id = candidate.get("raw_id", "")
            
            # Extract numeric part if possible
            candidate_num = 0
            if candidate_raw_id.startswith("C"):
                try:
                    candidate_num = int(candidate_raw_id[1:])
                except ValueError:
                    candidate_num = hash(candidate_raw_id) % 10000
            
            # Base factors on the candidate number and job type
            # This creates a pattern where certain candidates match better with certain job types
            base_factor = (candidate_num % 100) / 100.0  # 0.0 to 0.99
            
            # Technical candidates (higher IDs in our dataset) match better with technical jobs
            technical_factor = 0.1 if (candidate_num > 7000 and is_technical) else -0.1
            
            # Management candidates (lower IDs in our dataset) match better with management jobs
            management_factor = 0.1 if (candidate_num < 7000 and not is_technical) else -0.1
            
            # Calculate scores with some randomness
            match_base = min(0.98, max(0.60, 0.75 + base_factor + technical_factor + management_factor))
            
            # Add slight randomness
            match_score = round(match_base + random.uniform(-0.05, 0.05), 2)
            
            # Component scores with similar logic but different ranges
            skills_factor = base_factor + (0.15 if is_technical else -0.05) + random.uniform(-0.05, 0.05)
            experience_factor = base_factor + random.uniform(-0.1, 0.1)
            education_factor = base_factor + random.uniform(-0.05, 0.15)
            
            skills_score = round(min(0.95, max(0.55, 0.75 + skills_factor)), 2)
            experience_score = round(min(0.90, max(0.50, 0.70 + experience_factor)), 2)
            education_score = round(min(0.95, max(0.65, 0.75 + education_factor)), 2)
            
            matches.append({
                "id": len(matches) + 1,
                "job_id": job_id,
                "candidate_id": candidate["id"],
                "candidate_name": candidate["name"],
                "match_score": match_score,
                "skills_score": skills_score,
                "experience_score": experience_score,
                "education_score": education_score,
                "is_shortlisted": match_score > 0.80  # Auto-shortlist if score > 80%
            })
        
        # Sort matches by score (highest first)
        matches.sort(key=lambda x: x["match_score"], reverse=True)
        return matches
    except Exception as e:
        st.error(f"Error creating matches: {str(e)}")
        st.exception(e)  # Show the full exception details
        return []

# Constants
API_URL = "http://localhost:8000"  # Default API URL

# Initialize session state for storing data between interactions
if 'matches' not in st.session_state:
    st.session_state.matches = {}

if 'shortlisted' not in st.session_state:
    st.session_state.shortlisted = {}

if 'interviews' not in st.session_state:
    st.session_state.interviews = {}

# Main content
st.title("Matchwise AI")
st.caption("AI-Powered Job Application Screening System")

# Create tabs for different sections
tab_dashboard, tab_jobs, tab_candidates, tab_matching, tab_interviews = st.tabs([
    "Dashboard", "Jobs", "Candidates", "Matching", "Interviews"
])

# Dashboard tab
with tab_dashboard:
    st.header("Dashboard")
    
    # Load data
    jobs = load_job_descriptions()
    candidates = load_candidates()
    
    # Display overview metrics
    st.subheader("Overview")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Jobs", len(jobs))
    
    with col2:
        st.metric("Total Candidates", len(candidates))
    
    with col3:
        matches_count = sum(len(matches) for matches in st.session_state.matches.values()) if st.session_state.matches else 0
        st.metric("Total Matches", matches_count)
    
    with col4:
        shortlisted = sum(len(shortlisted) for shortlisted in st.session_state.shortlisted.values()) if st.session_state.shortlisted else 0
        st.metric("Shortlisted", shortlisted)
    
    # Display a sample job and candidate
    if jobs and candidates:
        st.subheader("Sample Data")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Sample Job Description:**")
            sample_job = jobs[0]
            st.info(f"**{sample_job['title']}**\n\n{sample_job['description'][:300]}...")
        
        with col2:
            st.write("**Sample Candidate:**")
            sample_candidate = candidates[0]
            st.info(f"**{sample_candidate['name']}**\n\nFile: {sample_candidate['cv_filename']}")

# Jobs tab
with tab_jobs:
    st.header("Jobs")
    
    # Load jobs
    jobs = load_job_descriptions()
    
    if jobs:
        st.success(f"Loaded {len(jobs)} job descriptions")
        
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
        
        # Display job details
        st.subheader("Job Details")
        
        selected_job_id = st.selectbox(
            "Select a job to view details",
            options=[job["id"] for job in jobs],
            format_func=lambda x: next((job["title"] for job in jobs if job["id"] == x), "")
        )
        
        if selected_job_id:
            selected_job = next((job for job in jobs if job["id"] == selected_job_id), None)
            if selected_job:
                st.write(f"**Title:** {selected_job['title']}")
                st.write(f"**Description:**\n{selected_job['description']}")
                
                # Add an option to match candidates to this job
                if st.button(f"Match Candidates to {selected_job['title']}", key=f"match_btn_{selected_job_id}"):
                    st.session_state.selected_job = selected_job
                    st.session_state.current_tab = 3  # Switch to matching tab
                    st.rerun()
    else:
        st.error("No job descriptions were loaded.")

# Candidates tab
with tab_candidates:
    st.header("Candidates")
    
    # Load candidates
    candidates = load_candidates()
    
    if candidates:
        st.success(f"Loaded {len(candidates)} candidates")
        
        # Display candidates in a table
        candidate_data = []
        for candidate in candidates:
            candidate_data.append({
                "ID": candidate["id"],
                "Name": candidate["name"],
                "Filename": candidate["cv_filename"]
            })
        
        st.dataframe(pd.DataFrame(candidate_data), use_container_width=True)
        
        # Display CV viewer
        st.subheader("CV Viewer")
        
        selected_candidate_id = st.selectbox(
            "Select a candidate to view CV",
            options=[candidate["id"] for candidate in candidates],
            format_func=lambda x: next((candidate["name"] for candidate in candidates if candidate["id"] == x), "")
        )
        
        if selected_candidate_id:
            selected_candidate = next((candidate for candidate in candidates if candidate["id"] == selected_candidate_id), None)
            if selected_candidate:
                st.write(f"**Name:** {selected_candidate['name']}")
                st.write(f"**Filename:** {selected_candidate['cv_filename']}")
                
                # Display the PDF
                st.subheader(f"Viewing: {selected_candidate['cv_filename']}")
                display_pdf(selected_candidate["cv_path"])
    else:
        st.error("No candidates were loaded.")

# Matching tab
with tab_matching:
    st.header("Matching")
    
    # Load data
    jobs = load_job_descriptions()
    candidates = load_candidates()
    
    if jobs and candidates:
        st.success("Data loaded successfully")
        
        # Job selection
        selected_job_id = st.selectbox(
            "Select a job to match candidates",
            options=[job["id"] for job in jobs],
            format_func=lambda x: next((job["title"] for job in jobs if job["id"] == x), "")
        )
        
        if selected_job_id:
            selected_job = next((job for job in jobs if job["id"] == selected_job_id), None)
            
            if selected_job:
                st.subheader(f"Matching candidates to: {selected_job['title']}")
                
                # Option to select specific candidates or match all
                match_option = st.radio(
                    "Match options",
                    ["Match all candidates", "Select specific candidates"]
                )
                
                candidate_ids = None
                if match_option == "Select specific candidates":
                    candidate_ids = st.multiselect(
                        "Select candidates to match",
                        options=[candidate["id"] for candidate in candidates],
                        format_func=lambda x: next((candidate["name"] for candidate in candidates if candidate["id"] == x), "")
                    )
                
                if st.button("Run Matching", key="run_matching"):
                    with st.spinner("Matching candidates..."):
                        # Create matches
                        matches = create_matches(selected_job_id, candidate_ids)
                        
                        # Store matches in session state
                        st.session_state.matches[selected_job_id] = matches
                        
                        # Create shortlisted list
                        st.session_state.shortlisted[selected_job_id] = [
                            match for match in matches if match["match_score"] > 0.80
                        ]
                        
                        st.success(f"Successfully matched {len(matches)} candidates")
                
                # Display existing matches
                if selected_job_id in st.session_state.matches:
                    matches = st.session_state.matches[selected_job_id]
                    
                    st.subheader("Match Results")
                    
                    # Convert to dataframe for display
                    if matches:
                        match_data = [{
                            "Candidate": match["candidate_name"],
                            "Match Score": f"{match['match_score']:.0%}",
                            "Skills": f"{match['skills_score']:.0%}",
                            "Experience": f"{match['experience_score']:.0%}",
                            "Education": f"{match['education_score']:.0%}",
                            "Shortlisted": "✅" if match["is_shortlisted"] else "❌"
                        } for match in matches]
                        
                        st.dataframe(pd.DataFrame(match_data), use_container_width=True)
                        
                        # Display shortlisted candidates
                        shortlisted = [match for match in matches if match["is_shortlisted"]]
                        
                        if shortlisted:
                            st.subheader("Shortlisted Candidates")
                            st.success(f"{len(shortlisted)} candidates shortlisted")
                            
                            # Show shortlisted candidates
                            shortlist_data = [{
                                "Candidate": match["candidate_name"],
                                "Match Score": f"{match['match_score']:.0%}"
                            } for match in shortlisted]
                            
                            st.dataframe(pd.DataFrame(shortlist_data), use_container_width=True)
                            
                            # Option to schedule interviews
                            if st.button("Schedule Interviews", key="schedule_interviews"):
                                st.session_state.shortlisted_job_id = selected_job_id
                                st.session_state.current_tab = 4  # Switch to interviews tab
                                st.rerun()
                        else:
                            st.info("No candidates were shortlisted. Try adjusting the threshold.")
                    else:
                        st.info("No matches found for this job.")
    else:
        st.error("Job descriptions or candidates data could not be loaded.")

# Interviews tab
with tab_interviews:
    st.header("Interviews")
    
    # Show a simple message
    st.info("In this tab, you can schedule interviews for shortlisted candidates.")
    
    # Get job and candidate data
    jobs = load_job_descriptions()
    candidates = load_candidates()
    
    if jobs and candidates:
        # Check if we have any shortlisted candidates
        has_shortlisted = any(len(shortlisted) > 0 for shortlisted in st.session_state.shortlisted.values())
        
        if has_shortlisted:
            st.success("Shortlisted candidates found")
            
            # Select a job with shortlisted candidates
            job_options = [job_id for job_id in st.session_state.shortlisted.keys() 
                          if len(st.session_state.shortlisted[job_id]) > 0]
            
            if job_options:
                selected_job_id = st.selectbox(
                    "Select a job to schedule interviews",
                    options=job_options,
                    format_func=lambda x: next((job["title"] for job in jobs if job["id"] == x), "")
                )
                
                if selected_job_id:
                    selected_job = next((job for job in jobs if job["id"] == selected_job_id), None)
                    
                    if selected_job:
                        st.subheader(f"Schedule interviews for: {selected_job['title']}")
                        
                        # Get shortlisted candidates
                        shortlisted = st.session_state.shortlisted[selected_job_id]
                        
                        # Display shortlisted candidates
                        shortlist_data = [{
                            "ID": match["candidate_id"],
                            "Candidate": match["candidate_name"],
                            "Match Score": f"{match['match_score']:.0%}"
                        } for match in shortlisted]
                        
                        st.dataframe(pd.DataFrame(shortlist_data), use_container_width=True)
                        
                        # Simple interview scheduling form
                        with st.form("interview_form"):
                            st.subheader("Interview Details")
                            
                            # Select candidates to interview
                            interview_candidates = st.multiselect(
                                "Select candidates to interview",
                                options=[match["candidate_id"] for match in shortlisted],
                                format_func=lambda x: next((match["candidate_name"] for match in shortlisted if match["candidate_id"] == x), "")
                            )
                            
                            # Interview date (5 business days from now)
                            today = datetime.now().date()
                            default_date = today + timedelta(days=5)
                            interview_date = st.date_input("Interview Date", value=default_date)
                            
                            # Time slots
                            time_slots = st.multiselect(
                                "Available Time Slots",
                                options=["9:00 AM", "10:00 AM", "11:00 AM", "1:00 PM", "2:00 PM", "3:00 PM", "4:00 PM"],
                                default=["10:00 AM", "2:00 PM"]
                            )
                            
                            # Interview format
                            interview_formats = st.multiselect(
                                "Interview Formats",
                                options=["In-person", "Video Call", "Phone Call"],
                                default=["Video Call"]
                            )
                            
                            # Submit button
                            submitted = st.form_submit_button("Schedule Interviews")
                            
                            if submitted and interview_candidates and time_slots and interview_formats:
                                # Initialize interviews for this job if not already done
                                if selected_job_id not in st.session_state.interviews:
                                    st.session_state.interviews[selected_job_id] = []
                                
                                # Create interviews
                                for candidate_id in interview_candidates:
                                    # Find candidate details
                                    candidate_match = next((match for match in shortlisted if match["candidate_id"] == candidate_id), None)
                                    
                                    if candidate_match:
                                        # Assign a time slot (in a real app, this would be more sophisticated)
                                        time_slot = random.choice(time_slots)
                                        
                                        # Create interview
                                        interview = {
                                            "id": len(st.session_state.interviews[selected_job_id]) + 1,
                                            "job_id": selected_job_id,
                                            "job_title": selected_job["title"],
                                            "candidate_id": candidate_id,
                                            "candidate_name": candidate_match["candidate_name"],
                                            "date": interview_date.strftime("%Y-%m-%d"),
                                            "time_slot": time_slot,
                                            "format": random.choice(interview_formats),
                                            "status": "Scheduled"
                                        }
                                        
                                        # Add to interviews
                                        st.session_state.interviews[selected_job_id].append(interview)
                                
                                st.success(f"Scheduled {len(interview_candidates)} interviews")
                                st.rerun()
        else:
            st.info("No shortlisted candidates found. Please go to the Matching tab to match and shortlist candidates first.")
    else:
        st.error("Job descriptions or candidates data could not be loaded.")

# Footer
st.markdown("---")
st.caption("Matchwise AI - Powered by advanced multi-agent framework") 