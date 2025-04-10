"""
Streamlit web application for the Matchwise job application screening system.
Provides a user-friendly interface for uploading and matching job descriptions and CVs.
"""

import os
import json
import time
import pandas as pd
import streamlit as st
import requests
from datetime import datetime, timedelta
import tempfile
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Any, Optional

# Set page configuration
st.set_page_config(
    page_title="Matchwise - AI Job Application Screening",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Constants
API_URL = "http://localhost:8000/api"  # URL of the FastAPI server


# Helper functions
def load_job_descriptions() -> List[Dict[str, Any]]:
    """Load job descriptions from the API."""
    try:
        response = requests.get(f"{API_URL}/jobs")
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error loading job descriptions: {response.text}")
            return []
    except Exception as e:
        st.error(f"Error connecting to API: {e}")
        return []


def load_candidates() -> List[Dict[str, Any]]:
    """Load candidates from the API."""
    try:
        response = requests.get(f"{API_URL}/candidates")
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error loading candidates: {response.text}")
            return []
    except Exception as e:
        st.error(f"Error connecting to API: {e}")
        return []


def load_matches(job_id: int, shortlisted_only: bool = False) -> List[Dict[str, Any]]:
    """Load matches for a specific job."""
    try:
        response = requests.get(
            f"{API_URL}/matches/{job_id}",
            params={"shortlisted_only": shortlisted_only}
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error loading matches: {response.text}")
            return []
    except Exception as e:
        st.error(f"Error connecting to API: {e}")
        return []


def create_job(title: str, description: str) -> Optional[Dict[str, Any]]:
    """Create a new job description."""
    try:
        response = requests.post(
            f"{API_URL}/jobs",
            json={"title": title, "description": description}
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error creating job: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error connecting to API: {e}")
        return None


def upload_cv(file) -> Optional[Dict[str, Any]]:
    """Upload a CV file."""
    try:
        files = {"file": (file.name, file, "application/pdf")}
        response = requests.post(f"{API_URL}/candidates", files=files)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error uploading CV: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error connecting to API: {e}")
        return None


def create_matches(job_id: int, candidate_ids: List[int] = None) -> List[Dict[str, Any]]:
    """Create matches between a job and candidates."""
    try:
        params = {}
        if candidate_ids:
            params["candidate_ids"] = candidate_ids
        
        response = requests.post(f"{API_URL}/matches/{job_id}", params=params)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error creating matches: {response.text}")
            return []
    except Exception as e:
        st.error(f"Error connecting to API: {e}")
        return []


def schedule_interview(match_id: int, interview_date, interview_slots, interview_formats) -> Optional[Dict[str, Any]]:
    """Schedule an interview for a match."""
    try:
        data = {
            "interview_date": interview_date.strftime("%Y-%m-%d"),
            "interview_slots": interview_slots,
            "interview_formats": interview_formats
        }
        response = requests.post(f"{API_URL}/interviews/{match_id}", json=data)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error scheduling interview: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error connecting to API: {e}")
        return None


# UI Components
def render_sidebar():
    """Render the sidebar with navigation."""
    st.sidebar.title("Matchwise")
    st.sidebar.subheader("AI Job Application Screening")
    
    page = st.sidebar.radio(
        "Navigation",
        ["Dashboard", "Jobs", "Candidates", "Matching", "Interviews"]
    )
    
    st.sidebar.markdown("---")
    st.sidebar.info(
        "Matchwise is an AI-powered job application screening system that "
        "helps you match candidates to job descriptions using advanced NLP techniques."
    )
    
    return page


def render_dashboard():
    """Render the dashboard with key metrics."""
    st.title("Dashboard")
    
    # Load data
    jobs = load_job_descriptions()
    candidates = load_candidates()
    
    # Create metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Jobs", len(jobs))
    
    with col2:
        st.metric("Total Candidates", len(candidates))
    
    with col3:
        # Calculate shortlisted candidates
        shortlisted_count = 0
        for job in jobs:
            matches = load_matches(job["id"], shortlisted_only=True)
            shortlisted_count += len(matches)
        
        st.metric("Shortlisted Candidates", shortlisted_count)
    
    with col4:
        # Calculate average matches per job
        total_matches = 0
        for job in jobs:
            matches = load_matches(job["id"])
            total_matches += len(matches)
        
        avg_matches = total_matches / len(jobs) if jobs else 0
        st.metric("Avg. Matches per Job", f"{avg_matches:.1f}")
    
    # Create charts
    st.subheader("Recent Activity")
    
    # Convert data for charts
    if jobs:
        # Sample chart: Job matches distribution
        job_data = []
        for job in jobs:
            matches = load_matches(job["id"])
            job_data.append({
                "Job Title": job["title"],
                "Total Candidates": len(matches),
                "Shortlisted": len([m for m in matches if m["is_shortlisted"]])
            })
        
        job_df = pd.DataFrame(job_data)
        
        if not job_df.empty:
            fig = px.bar(
                job_df,
                x="Job Title",
                y=["Total Candidates", "Shortlisted"],
                barmode="group",
                title="Candidates per Job",
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No jobs found. Add some jobs to see the dashboard.")


def render_jobs_page():
    """Render the jobs management page."""
    st.title("Job Descriptions")
    
    # Create tabs for view and create
    tab1, tab2 = st.tabs(["View Jobs", "Add New Job"])
    
    with tab1:
        jobs = load_job_descriptions()
        
        if jobs:
            for job in jobs:
                with st.expander(f"{job['title']}"):
                    # Display job details
                    st.write("**Required Skills:**", job.get("required_skills", ""))
                    st.write("**Required Experience:**", job.get("required_experience", ""))
                    st.write("**Required Education:**", job.get("required_education", ""))
                    
                    # Add action buttons
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"View Matches for {job['title']}", key=f"view_matches_{job['id']}"):
                            st.session_state["current_page"] = "Matching"
                            st.session_state["selected_job_id"] = job["id"]
                            st.experimental_rerun()
        else:
            st.info("No jobs found. Add a new job below.")
    
    with tab2:
        st.subheader("Add a New Job")
        
        # Create form for adding new job
        with st.form("add_job_form"):
            job_title = st.text_input("Job Title")
            job_description = st.text_area("Job Description", height=300)
            
            submitted = st.form_submit_button("Add Job")
            
            if submitted and job_title and job_description:
                with st.spinner("Processing job description..."):
                    job = create_job(job_title, job_description)
                    if job:
                        st.success(f"Job '{job_title}' added successfully!")
                        time.sleep(1)
                        st.experimental_rerun()


def render_candidates_page():
    """Render the candidates management page."""
    st.title("Candidates")
    
    # Create tabs for view and upload
    tab1, tab2 = st.tabs(["View Candidates", "Upload CVs"])
    
    with tab1:
        candidates = load_candidates()
        
        if candidates:
            for candidate in candidates:
                with st.expander(f"{candidate.get('name', 'Unknown')} ({candidate['cv_filename']})"):
                    # Display candidate details
                    st.write("**Email:**", candidate.get("email", "Not available"))
                    
                    # Try to parse skills JSON if available
                    if candidate.get("skills"):
                        try:
                            skills = json.loads(candidate["skills"])
                            st.write("**Skills:**", ", ".join(skills))
                        except:
                            st.write("**Skills:**", candidate["skills"])
        else:
            st.info("No candidates found. Upload CVs below.")
    
    with tab2:
        st.subheader("Upload CVs")
        
        # Create form for uploading CVs
        uploaded_files = st.file_uploader(
            "Upload candidate CVs (PDF)",
            type=["pdf"],
            accept_multiple_files=True
        )
        
        if uploaded_files:
            if st.button("Process CVs"):
                for file in uploaded_files:
                    with st.spinner(f"Processing {file.name}..."):
                        # Save file to temp directory
                        candidate = upload_cv(file)
                        if candidate:
                            st.success(f"CV '{file.name}' processed successfully!")
                
                time.sleep(1)
                st.experimental_rerun()


def render_matching_page():
    """Render the matching page."""
    st.title("Match Candidates to Jobs")
    
    # Load jobs and candidates
    jobs = load_job_descriptions()
    candidates = load_candidates()
    
    if not jobs or not candidates:
        st.warning("You need at least one job and one candidate to perform matching.")
        return
    
    # Select job
    job_options = {job["id"]: job["title"] for job in jobs}
    
    # Check if we have a selected job from another page
    selected_job_id = None
    if "selected_job_id" in st.session_state:
        selected_job_id = st.session_state["selected_job_id"]
        # Clear it after use
        del st.session_state["selected_job_id"]
    
    selected_job_id = st.selectbox(
        "Select Job",
        options=list(job_options.keys()),
        format_func=lambda x: job_options[x],
        index=0 if selected_job_id is None else list(job_options.keys()).index(selected_job_id)
    )
    
    if selected_job_id:
        # Load existing matches
        existing_matches = load_matches(selected_job_id)
        
        # Display existing matches if any
        if existing_matches:
            st.subheader("Existing Matches")
            
            # Convert to dataframe for easier display
            matches_data = []
            for match in existing_matches:
                # Find candidate
                candidate = next((c for c in candidates if c["id"] == match["candidate_id"]), None)
                if candidate:
                    matches_data.append({
                        "Match ID": match["id"],
                        "Candidate ID": candidate["id"],
                        "Candidate Name": candidate.get("name", "Unknown"),
                        "CV Filename": candidate.get("cv_filename", ""),
                        "Match Score": f"{match['match_score'] * 100:.1f}%",
                        "Skills Score": f"{match.get('skills_score', 0) * 100:.1f}%",
                        "Experience Score": f"{match.get('experience_score', 0) * 100:.1f}%",
                        "Education Score": f"{match.get('education_score', 0) * 100:.1f}%",
                        "Shortlisted": "✅" if match["is_shortlisted"] else "❌",
                        "Raw Score": match["match_score"]  # For sorting
                    })
            
            if matches_data:
                # Create dataframe and display
                df = pd.DataFrame(matches_data)
                df = df.sort_values("Raw Score", ascending=False).drop("Raw Score", axis=1)
                
                # Display as table
                st.dataframe(df, use_container_width=True)
                
                # Create visualization
                fig = px.bar(
                    df,
                    x="Candidate Name",
                    y=["Match Score", "Skills Score", "Experience Score", "Education Score"],
                    title="Match Scores",
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Schedule interview button for shortlisted candidates
                shortlisted = [m for m in existing_matches if m["is_shortlisted"]]
                if shortlisted:
                    if st.button("Schedule Interviews for Shortlisted Candidates"):
                        st.session_state["current_page"] = "Interviews"
                        st.session_state["selected_job_id"] = selected_job_id
                        st.experimental_rerun()
        
        # Option to create new matches
        st.subheader("Create New Matches")
        
        # Select candidates to match
        candidate_options = {c["id"]: f"{c.get('name', 'Unknown')} ({c['cv_filename']})" for c in candidates}
        
        # Exclude candidates that already have matches
        if existing_matches:
            matched_candidate_ids = [m["candidate_id"] for m in existing_matches]
            unmatched_candidate_options = {k: v for k, v in candidate_options.items() if k not in matched_candidate_ids}
            
            if unmatched_candidate_options:
                selected_candidate_ids = st.multiselect(
                    "Select Candidates to Match",
                    options=list(unmatched_candidate_options.keys()),
                    format_func=lambda x: unmatched_candidate_options[x]
                )
                
                match_all = st.checkbox("Match All Unmatched Candidates")
                
                if st.button("Create Matches"):
                    with st.spinner("Creating matches..."):
                        # If match all is selected, use all unmatched candidates
                        if match_all:
                            new_matches = create_matches(selected_job_id)
                        else:
                            if selected_candidate_ids:
                                new_matches = create_matches(selected_job_id, selected_candidate_ids)
                            else:
                                st.warning("Please select at least one candidate.")
                                return
                        
                        if new_matches:
                            st.success(f"Created {len(new_matches)} new matches!")
                            time.sleep(1)
                            st.experimental_rerun()
            else:
                st.info("All candidates have already been matched to this job.")
        else:
            match_all = st.checkbox("Match All Candidates", value=True)
            
            if match_all:
                # Just create matches for all candidates
                if st.button("Create Matches"):
                    with st.spinner("Creating matches..."):
                        new_matches = create_matches(selected_job_id)
                        if new_matches:
                            st.success(f"Created {len(new_matches)} new matches!")
                            time.sleep(1)
                            st.experimental_rerun()
            else:
                # Let user select specific candidates
                selected_candidate_ids = st.multiselect(
                    "Select Candidates to Match",
                    options=list(candidate_options.keys()),
                    format_func=lambda x: candidate_options[x]
                )
                
                if st.button("Create Matches"):
                    with st.spinner("Creating matches..."):
                        if selected_candidate_ids:
                            new_matches = create_matches(selected_job_id, selected_candidate_ids)
                            if new_matches:
                                st.success(f"Created {len(new_matches)} new matches!")
                                time.sleep(1)
                                st.experimental_rerun()
                        else:
                            st.warning("Please select at least one candidate.")


def render_interviews_page():
    """Render the interviews scheduling page."""
    st.title("Interview Scheduling")
    
    # Load jobs
    jobs = load_job_descriptions()
    
    if not jobs:
        st.warning("You need at least one job to schedule interviews.")
        return
    
    # Select job
    job_options = {job["id"]: job["title"] for job in jobs}
    
    # Check if we have a selected job from another page
    selected_job_id = None
    if "selected_job_id" in st.session_state:
        selected_job_id = st.session_state["selected_job_id"]
        # Clear it after use
        del st.session_state["selected_job_id"]
    
    selected_job_id = st.selectbox(
        "Select Job",
        options=list(job_options.keys()),
        format_func=lambda x: job_options[x],
        index=0 if selected_job_id is None else list(job_options.keys()).index(selected_job_id)
    )
    
    if selected_job_id:
        # Load shortlisted candidates
        matches = load_matches(selected_job_id, shortlisted_only=True)
        candidates = load_candidates()
        
        if not matches:
            st.info("No shortlisted candidates found for this job.")
            return
        
        # Display shortlisted candidates
        st.subheader("Shortlisted Candidates")
        
        # Create candidate lookup
        candidate_lookup = {c["id"]: c for c in candidates}
        
        # Display each candidate and schedule interview
        for match in matches:
            candidate = candidate_lookup.get(match["candidate_id"])
            if not candidate:
                continue
            
            with st.expander(f"{candidate.get('name', 'Unknown')} - Match Score: {match['match_score']*100:.1f}%"):
                # Display interview scheduling form
                st.write("**Schedule an Interview**")
                
                # Date picker
                today = datetime.now().date()
                min_date = today + timedelta(days=1)  # Must be at least tomorrow
                interview_date = st.date_input(
                    "Interview Date",
                    min_value=min_date,
                    value=min_date + timedelta(days=5)  # Default to 5 days from now
                )
                
                # Time slots
                default_slots = [
                    "10:00 AM - 11:00 AM",
                    "2:00 PM - 3:00 PM",
                    "4:00 PM - 5:00 PM"
                ]
                
                interview_slots = st.multiselect(
                    "Available Time Slots",
                    options=default_slots,
                    default=default_slots
                )
                
                # Interview formats
                default_formats = ["Video call", "Phone call", "In-person"]
                interview_formats = st.multiselect(
                    "Available Interview Formats",
                    options=default_formats,
                    default=default_formats
                )
                
                if st.button(f"Schedule Interview for {candidate.get('name', 'Candidate')}", key=f"schedule_{match['id']}"):
                    if interview_slots and interview_formats:
                        with st.spinner("Scheduling interview..."):
                            interview = schedule_interview(
                                match["id"],
                                interview_date,
                                interview_slots,
                                interview_formats
                            )
                            
                            if interview:
                                st.success("Interview scheduled successfully!")
                    else:
                        st.warning("Please select at least one time slot and interview format.")


# Main App
def main():
    """Main application function."""
    # Check if current_page exists in session state
    if "current_page" not in st.session_state:
        st.session_state["current_page"] = "Dashboard"
    
    # Render sidebar and get selected page
    selected_page = render_sidebar()
    
    # Update the current page in session state if changed by user
    if selected_page != st.session_state["current_page"]:
        st.session_state["current_page"] = selected_page
    
    # Render the selected page
    if st.session_state["current_page"] == "Dashboard":
        render_dashboard()
    elif st.session_state["current_page"] == "Jobs":
        render_jobs_page()
    elif st.session_state["current_page"] == "Candidates":
        render_candidates_page()
    elif st.session_state["current_page"] == "Matching":
        render_matching_page()
    elif st.session_state["current_page"] == "Interviews":
        render_interviews_page()


if __name__ == "__main__":
    main() 