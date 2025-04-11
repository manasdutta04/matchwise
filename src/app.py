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
import tempfile
import time

# Function to load real job descriptions
def load_job_descriptions():
    """Load real job descriptions from the CSV file."""
    try:
        jd_path = "AI-Powered Job Application Screening System/job_description.csv"
        if os.path.exists(jd_path):
            df = pd.read_csv(jd_path)
            jobs = []
            for i, row in df.iterrows():
                jobs.append({
                    "id": i + 1,
                    "title": row["Job Title"],
                    "description": row["Job Description"]
                })
            return jobs
        else:
            st.error(f"Job description file not found: {jd_path}")
            return []
    except Exception as e:
        st.error(f"Error loading job descriptions: {e}")
        return []

# Function to load real CV files
def load_candidates():
    """Load real CV files from the dataset folder."""
    try:
        cv_folder = "AI-Powered Job Application Screening System/CVs1"
        if os.path.exists(cv_folder):
            candidates = []
            for i, cv_file in enumerate(glob.glob(f"{cv_folder}/*.pdf")):
                # Extract filename
                filename = os.path.basename(cv_file)
                # Basic candidate info (in a real system this would be extracted from the CV)
                candidates.append({
                    "id": i + 1,
                    "name": f"Candidate {filename.split('.')[0]}",
                    "cv_filename": filename,
                    "cv_path": cv_file
                })
            return candidates
        else:
            st.error(f"CV folder not found: {cv_folder}")
            return []
    except Exception as e:
        st.error(f"Error loading candidates: {e}")
        return []

# Function to create matches between jobs and candidates
def create_matches(job_id, candidate_ids=None):
    """Create matches between jobs and candidates with scoring."""
    try:
        all_candidates = load_candidates()
        if candidate_ids:
            candidates = [c for c in all_candidates if c["id"] in candidate_ids]
        else:
            candidates = all_candidates
        
        # In a real system, this would use the multi-agent framework to calculate actual match scores
        matches = []
        for candidate in candidates:
            # Generate random scores for demo purposes
            # In production, these would be calculated by the AI agents
            match_score = round(random.uniform(0.60, 0.98), 2)
            skills_score = round(random.uniform(0.55, 0.95), 2)
            experience_score = round(random.uniform(0.50, 0.90), 2)
            education_score = round(random.uniform(0.65, 0.95), 2)
            
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
        
        return matches
    except Exception as e:
        st.error(f"Error creating matches: {e}")
        return []

# Function to display PDF (for viewing CVs)
def display_pdf(file_path):
    """Display a PDF file in Streamlit."""
    try:
        with open(file_path, "rb") as f:
            base64_pdf = base64.b64encode(f.read()).decode('utf-8')
        
        pdf_display = f"""
            <iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf"></iframe>
        """
        st.markdown(pdf_display, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error displaying PDF: {e}")

# Constants
DEFAULT_API_URL = "http://localhost:8000"
API_URL = os.environ.get("STREAMLIT_API_URL", DEFAULT_API_URL)

# Mock data for demonstration
MOCK_DATA = {
    "jobs": [
        {"id": 1, "title": "Software Engineer", "description": "Backend developer with Python experience"},
        {"id": 2, "title": "Data Scientist", "description": "ML engineer with statistics background"},
        {"id": 3, "title": "Product Manager", "description": "Tech-savvy PM with agile experience"}
    ],
    "candidates": [
        {"id": 1, "name": "John Smith", "cv_filename": "john_smith_resume.pdf"},
        {"id": 2, "name": "Jane Doe", "cv_filename": "jane_doe_cv.pdf"},
        {"id": 3, "name": "Bob Jones", "cv_filename": "bob_jones_resume.pdf"}
    ]
}

# Page configuration
st.set_page_config(
    page_title="Matchwise - AI Job Application Screening",
    page_icon="��",
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

# Initialize session state for storing data between interactions
if 'matches' not in st.session_state:
    st.session_state.matches = {}

if 'shortlisted' not in st.session_state:
    st.session_state.shortlisted = {}

if 'current_tab' not in st.session_state:
    st.session_state.current_tab = 0

# Main content
st.title("Matchwise AI")
st.caption("AI-Powered Job Application Screening System")

# Load real data
jobs = load_job_descriptions()
candidates = load_candidates()

# Create a modern sidebar
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/000000/artificial-intelligence.png", width=80)
    st.title("Matchwise")
    
    st.markdown("---")
    
    # Display statistics
    st.subheader("Statistics")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Jobs", len(jobs))
        st.metric("Candidates", len(candidates))
    with col2:
        matches_count = sum(len(matches) for matches in st.session_state.matches.values()) if st.session_state.matches else 0
        shortlisted_count = sum(len(shortlisted) for shortlisted in st.session_state.shortlisted.values()) if st.session_state.shortlisted else 0
        st.metric("Matches", matches_count)
        st.metric("Shortlisted", shortlisted_count)
    
    st.markdown("---")
    
    # System status
    st.subheader("System Status")
    st.info(f"Connected to API: {API_URL}")
    st.success("All agents are operational")
    
    st.markdown("---")
    
    # Add version info and help
    st.caption("Matchwise v1.0")
    if st.button("Help & Documentation"):
        st.info("""
        **Matchwise AI** helps you:
        - Process job descriptions
        - Analyze candidate CVs
        - Match candidates to jobs
        - Shortlist the best matches
        - Schedule interviews
        """)

# Create modern tabs with icons
tab_dashboard, tab_jobs, tab_candidates, tab_matching, tab_interviews = st.tabs([
    "📊 Dashboard", "💼 Jobs", "👥 Candidates", "🔍 Matching", "📅 Interviews"
])

with tab_dashboard:
    st.header("Dashboard")
    
    # Create an overview section with key metrics
    st.subheader("Overview")
    
    # Create metric cards in a row
    metric_cols = st.columns(4)
    with metric_cols[0]:
        with st.container():
            st.markdown('<div class="metric-container">', unsafe_allow_html=True)
            st.metric("Total Jobs", len(jobs))
            st.caption("Active job openings")
            st.markdown('</div>', unsafe_allow_html=True)
    
    with metric_cols[1]:
        with st.container():
            st.markdown('<div class="metric-container">', unsafe_allow_html=True)
            st.metric("Total Candidates", len(candidates))
            st.caption("Candidates in database")
            st.markdown('</div>', unsafe_allow_html=True)
    
    with metric_cols[2]:
        with st.container():
            st.markdown('<div class="metric-container">', unsafe_allow_html=True)
            matches_count = sum(len(matches) for matches in st.session_state.matches.values()) if st.session_state.matches else 0
            st.metric("Total Matches", matches_count)
            st.caption("Job-candidate matches")
            st.markdown('</div>', unsafe_allow_html=True)
    
    with metric_cols[3]:
        with st.container():
            st.markdown('<div class="metric-container">', unsafe_allow_html=True)
            shortlisted_count = sum(len(shortlisted) for shortlisted in st.session_state.shortlisted.values()) if st.session_state.shortlisted else 0
            st.metric("Shortlisted", shortlisted_count)
            st.caption("Candidates ready for interview")
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Create two columns for charts
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        st.subheader("Job Categories")
        
        # Count job categories (simplified version using just first word of title)
        job_categories = {}
        for job in jobs:
            category = job["title"].split()[0] if job["title"] else "Other"
            job_categories[category] = job_categories.get(category, 0) + 1
        
        # Create a bar chart
        st.bar_chart(job_categories)
    
    with chart_col2:
        st.subheader("Match Distribution")
        
        # Generate sample match distribution data
        if st.session_state.matches:
            match_data = {}
            for job_id, matches in st.session_state.matches.items():
                job_title = next((job["title"] for job in jobs if job["id"] == job_id), f"Job {job_id}")
                match_data[job_title] = len(matches)
            
            # Display chart if we have matches
            if match_data:
                st.bar_chart(match_data)
            else:
                st.info("No matches created yet. Go to the Matching tab to create matches.")
        else:
            # Create sample data if no real matches exist
            sample_data = {
                "Software Engineer": random.randint(3, 15),
                "Data Scientist": random.randint(5, 20),
                "Product Manager": random.randint(2, 10),
                "Cloud Engineer": random.randint(4, 12)
            }
            st.bar_chart(sample_data)
            st.caption("Sample data - Create real matches in the Matching tab")
    
    # Recent activity section
    st.subheader("Recent Activity")
    
    # Create a sample activity log
    activity_data = [
        {"timestamp": (datetime.now() - timedelta(minutes=5)).strftime("%H:%M:%S"), "action": "New candidate CV uploaded", "details": "Resume C9945.pdf"},
        {"timestamp": (datetime.now() - timedelta(minutes=15)).strftime("%H:%M:%S"), "action": "Match created", "details": "Software Engineer matched with 8 candidates"},
        {"timestamp": (datetime.now() - timedelta(hours=1)).strftime("%H:%M:%S"), "action": "Candidate shortlisted", "details": "Candidate C9777 for Data Scientist position"},
        {"timestamp": (datetime.now() - timedelta(hours=2)).strftime("%H:%M:%S"), "action": "Interview scheduled", "details": "Candidate C8564 for Product Manager position"}
    ]
    
    # Display activity log as a table
    st.dataframe(
        pd.DataFrame(activity_data),
        use_container_width=True,
        hide_index=True
    )

with tab_jobs:
    st.header("Jobs")
    st.info("Here you can add and manage job descriptions.")
    
    # Display existing jobs
    st.subheader("Current Job Listings")
    
    # Create a filter search box
    search_term = st.text_input("Search jobs", placeholder="Enter job title...")
    
    # Filter jobs based on search term
    filtered_jobs = jobs
    if search_term:
        filtered_jobs = [job for job in jobs if search_term.lower() in job["title"].lower()]
    
    # Create a job grid (2 columns)
    job_cols = st.columns(2)
    
    for i, job in enumerate(filtered_jobs):
        # Alternate between the two columns
        with job_cols[i % 2]:
            with st.expander(f"📌 {job['title']}"):
                st.markdown(f"**ID:** {job['id']}")
                
                # Show first 200 characters of description with a "Show more" button
                description = job['description']
                if len(description) > 200:
                    short_desc = description[:200] + "..."
                    st.markdown(f"**Description:** {short_desc}")
                    if st.button(f"Show full description", key=f"show_desc_{job['id']}"):
                        st.markdown(f"**Full Description:**\n{description}")
                else:
                    st.markdown(f"**Description:** {description}")
                
                # Add actions buttons in a row
                action_cols = st.columns(3)
                with action_cols[0]:
                    if st.button("Match Candidates", key=f"match_{job['id']}"):
                        # Switch to the matching tab and pre-select this job
                        st.session_state.current_tab = 3  # Index of matching tab
                        st.session_state.selected_job = job["id"]
                        st.rerun()
                        
                with action_cols[1]:
                    if st.button("Edit", key=f"edit_{job['id']}"):
                        st.session_state.job_to_edit = job
                        st.info(f"Editing job: {job['title']}")
                
                with action_cols[2]:
                    if st.button("Delete", key=f"delete_{job['id']}"):
                        st.warning(f"This would delete job: {job['title']}")
    
    st.markdown("---")
    
    # Add new job form
    st.subheader("Add a New Job")
    
    with st.form("job_form"):
        job_title = st.text_input("Job Title", placeholder="e.g., Software Engineer")
        job_description = st.text_area("Job Description", placeholder="Enter detailed job description...")
        
        col1, col2 = st.columns(2)
        with col1:
            required_skills = st.text_area("Required Skills", placeholder="Enter skills separated by commas")
        with col2:
            required_experience = st.text_area("Required Experience", placeholder="Enter experience requirements")
        
        submit_button = st.form_submit_button("Add Job")
        
        if submit_button:
            if job_title and job_description:
                # In a real implementation, this would call the API to add the job
                st.success(f"Job '{job_title}' added successfully!")
                
                # Show how the AI would process this job
                with st.spinner("Processing job with AI..."):
                    time.sleep(1)  # Simulate AI processing
                    st.info("Job description processed by AI. Key requirements extracted.")
                    
                    # Display a sample of extracted data
                    extracted_data = {
                        "Skills": ["Python", "JavaScript", "SQL"] if "python" in job_description.lower() else ["Communication", "Leadership", "Strategy"],
                        "Experience": "3-5 years" if "experience" in job_description.lower() else "2+ years",
                        "Education": "Bachelor's degree" if "bachelor" in job_description.lower() else "Relevant degree",
                        "Responsibilities": ["Software development", "Testing", "Deployment"] if "develop" in job_description.lower() else ["Strategy", "Planning", "Analysis"]
                    }
                    
                    st.json(extracted_data)
            else:
                st.warning("Please fill in all required fields")

with tab_candidates:
    st.header("Candidates")
    st.info("Here you can upload and manage candidate CVs.")
    
    # Add search and filtering
    search_col, filter_col = st.columns([3, 1])
    with search_col:
        candidate_search = st.text_input("Search candidates", placeholder="Enter candidate name or ID...")
    with filter_col:
        sort_by = st.selectbox("Sort by", ["Newest", "Name (A-Z)", "Name (Z-A)"])
    
    # Filter and sort candidates
    filtered_candidates = candidates
    if candidate_search:
        filtered_candidates = [c for c in candidates if candidate_search.lower() in c["name"].lower() or candidate_search in str(c["id"])]
    
    # Sort candidates based on selection
    if sort_by == "Name (A-Z)":
        filtered_candidates = sorted(filtered_candidates, key=lambda c: c["name"])
    elif sort_by == "Name (Z-A)":
        filtered_candidates = sorted(filtered_candidates, key=lambda c: c["name"], reverse=True)
    elif sort_by == "Newest":
        # In a real app this would use timestamp - here we just use ID as a proxy
        filtered_candidates = sorted(filtered_candidates, key=lambda c: c["id"], reverse=True)
    
    # Add tabs for different candidate views
    candidate_tab1, candidate_tab2 = st.tabs(["Grid View", "Table View"])
    
    with candidate_tab1:
        # Create a 3-column grid for candidates
        for i in range(0, len(filtered_candidates), 3):
            cols = st.columns(3)
            for j in range(3):
                if i+j < len(filtered_candidates):
                    candidate = filtered_candidates[i+j]
                    with cols[j]:
                        with st.container():
                            st.markdown(f"### {candidate['name']}")
                            st.caption(f"ID: {candidate['id']} | File: {candidate['cv_filename']}")
                            
                            # Create actions
                            if st.button("View CV", key=f"view_{candidate['id']}"):
                                st.session_state.viewing_cv = candidate
                            
                            action_cols = st.columns(2)
                            with action_cols[0]:
                                if st.button("Match", key=f"match_c_{candidate['id']}"):
                                    st.session_state.candidate_to_match = candidate
                                    st.session_state.current_tab = 3  # Switch to matching tab
                                    st.rerun()
                            with action_cols[1]:
                                if st.button("Profile", key=f"profile_{candidate['id']}"):
                                    st.session_state.profile_candidate = candidate
                            
                            # Add a separator between cards
                            st.markdown("---")
    
    with candidate_tab2:
        # Create a more compact table view
        candidate_data = []
        for c in filtered_candidates:
            candidate_data.append({
                "ID": c["id"],
                "Name": c["name"],
                "Filename": c["cv_filename"],
                "Actions": "View | Match | Profile"  # In a real app these would be clickable
            })
        
        st.dataframe(
            pd.DataFrame(candidate_data),
            use_container_width=True,
            column_config={
                "Actions": st.column_config.TextColumn(
                    "Actions",
                    help="Available actions for this candidate",
                    width="small"
                )
            },
            hide_index=True
        )
    
    # Display CV viewer if a CV is selected
    if 'viewing_cv' in st.session_state and st.session_state.viewing_cv:
        candidate = st.session_state.viewing_cv
        st.subheader(f"Viewing CV: {candidate['name']}")
        
        # Add a back button
        if st.button("Back to candidates list"):
            del st.session_state.viewing_cv
            st.rerun()
        
        # Display the PDF
        try:
            display_pdf(candidate["cv_path"])
        except Exception as e:
            st.error(f"Error displaying PDF: {e}")
            st.info("PDF preview not available. You can download the file instead.")
            
            # Add a download button as an alternative
            with open(candidate["cv_path"], "rb") as file:
                st.download_button(
                    label="Download CV", 
                    data=file,
                    file_name=candidate["cv_filename"],
                    mime="application/pdf"
                )
    
    # Display candidate profile if selected
    elif 'profile_candidate' in st.session_state and st.session_state.profile_candidate:
        candidate = st.session_state.profile_candidate
        st.subheader(f"Candidate Profile: {candidate['name']}")
        
        # Add a back button
        if st.button("Back to candidates list"):
            del st.session_state.profile_candidate
            st.rerun()
        
        # Create a two-column layout for the profile
        profile_col1, profile_col2 = st.columns([2, 1])
        
        with profile_col1:
            # Display candidate information
            st.markdown("### Personal Information")
            
            # In a real app, this would be extracted from the CV
            # Here we're generating mock data
            st.markdown(f"**Name:** {candidate['name']}")
            st.markdown(f"**Email:** {candidate['name'].lower().replace(' ', '')}@example.com")
            st.markdown(f"**Phone:** +1 555-{random.randint(100, 999)}-{random.randint(1000, 9999)}")
            
            st.markdown("### Skills")
            # Generate random skills
            skills = ["Python", "Java", "SQL", "Machine Learning", "Data Analysis",
                     "Project Management", "JavaScript", "Cloud Computing",
                     "DevOps", "Communication", "Leadership", "Problem Solving"]
            candidate_skills = random.sample(skills, random.randint(4, 8))
            
            # Display skills as pills
            skill_html = ""
            for skill in candidate_skills:
                skill_html += f'<span style="background-color:#e7f3fe; padding:5px 10px; border-radius:15px; margin:0 5px 5px 0; display:inline-block; font-size:0.8em;">{skill}</span>'
            
            st.markdown(skill_html, unsafe_allow_html=True)
            
            st.markdown("### Experience")
            # Generate random experience
            companies = ["Tech Solutions Inc.", "Innovative Systems", "Data Analytics Corp", 
                        "Global Software Ltd.", "Digital Enterprises"]
            positions = ["Software Engineer", "Data Scientist", "Product Manager",
                         "Project Lead", "Full Stack Developer", "Systems Analyst"]
            
            for _ in range(random.randint(1, 3)):
                company = random.choice(companies)
                position = random.choice(positions)
                years = f"{2015 + random.randint(0, 7)} - {2020 + random.randint(0, 3)}"
                
                st.markdown(f"**{position}** at *{company}*")
                st.markdown(f"_{years}_")
                st.markdown("Responsibilities: Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.")
                st.markdown("---")
        
        with profile_col2:
            # Display a profile card with some stats
            st.markdown("### CV Analysis")
            
            # In a real app, this would be generated by the AI agents
            match_score = random.uniform(0.65, 0.98)
            skill_relevance = random.uniform(0.60, 0.95)
            experience_level = ["Entry Level", "Mid Level", "Senior Level"][random.randint(0, 2)]
            
            st.metric("Overall Match Score", f"{match_score:.0%}")
            st.metric("Skill Relevance", f"{skill_relevance:.0%}")
            st.markdown(f"**Experience Level:** {experience_level}")
            
            # Display a small chart showing strengths
            st.markdown("### Strengths")
            strengths = {
                "Technical Skills": random.uniform(0.6, 1.0),
                "Experience": random.uniform(0.5, 1.0),
                "Education": random.uniform(0.7, 1.0),
                "Communication": random.uniform(0.5, 1.0)
            }
            
            st.bar_chart(strengths)
    
    # Upload section
    st.markdown("---")
    st.subheader("Upload New CVs")
    
    upload_cols = st.columns([2, 1])
    with upload_cols[0]:
        uploaded_files = st.file_uploader("Choose PDF files", type="pdf", accept_multiple_files=True)
    
    with upload_cols[1]:
        if st.button("Process All CVs", disabled=not uploaded_files):
            # In a real app, this would call the API to process the CVs
            with st.spinner("Processing CVs with AI..."):
                for i, uploaded_file in enumerate(uploaded_files):
                    # Simulate AI processing time
                    prog = st.progress(0)
                    for p in range(100):
                        time.sleep(0.01)
                        prog.progress(p + 1)
                    
                    # Show success
                    st.success(f"Processed: {uploaded_file.name}")
                    
                    # In a real system this would display the extracted information
                    if i == 0:  # Just show for the first file to avoid cluttering
                        st.info("AI has extracted key information from this CV")
                        
                        # Sample of extracted data
                        extracted_data = {
                            "Name": "John Smith",
                            "Email": "john.smith@example.com",
                            "Skills": ["Python", "Java", "SQL", "Machine Learning"],
                            "Experience": [
                                {"title": "Software Engineer", "company": "Tech Inc.", "duration": "2018-2021"},
                                {"title": "Junior Developer", "company": "Dev Solutions", "duration": "2016-2018"}
                            ],
                            "Education": [
                                {"degree": "BSc Computer Science", "institution": "University of Technology", "year": "2016"}
                            ]
                        }
                        
                        st.json(extracted_data)

with tab_matching:
    st.header("Matching")
    st.info("Here you can match candidates to jobs and see match scores calculated by the AI.")
    
    # Load data from session state if we're redirected
    pre_selected_job = None
    if 'selected_job' in st.session_state:
        pre_selected_job = st.session_state.selected_job
        del st.session_state.selected_job
    
    pre_selected_candidate = None
    if 'candidate_to_match' in st.session_state:
        pre_selected_candidate = st.session_state.candidate_to_match["id"]
        del st.session_state.candidate_to_match
    
    # Create tabs for matching functionality
    match_tab1, match_tab2, match_tab3 = st.tabs(["Create Matches", "View Matches", "Shortlisted Candidates"])
    
    with match_tab1:
        st.subheader("Create New Matches")
        
        # Create form for matching
        col1, col2 = st.columns(2)
        
        with col1:
            # Job selection with search
            job_search = st.text_input("Search jobs", placeholder="Type to search...", key="job_search_match")
            
            # Filter jobs based on search
            filtered_jobs = jobs
            if job_search:
                filtered_jobs = [j for j in jobs if job_search.lower() in j["title"].lower()]
            
            # Create a selectbox with job titles
            job_options = [(j["id"], j["title"]) for j in filtered_jobs]
            job_ids = [j[0] for j in job_options]
            job_titles = [j[1] for j in job_options]
            
            selected_job_index = 0
            if pre_selected_job in job_ids:
                selected_job_index = job_ids.index(pre_selected_job)
            
            if job_options:
                selected_job_title = st.selectbox(
                    "Select Job",
                    options=job_titles,
                    index=selected_job_index,
                    key="job_select_match"
                )
                selected_job_id = job_ids[job_titles.index(selected_job_title)]
                
                # Get the selected job details
                selected_job = next((j for j in jobs if j["id"] == selected_job_id), None)
                if selected_job:
                    # Show job description summary
                    st.markdown(f"**Job Description:**")
                    desc = selected_job["description"]
                    st.markdown(f"{desc[:150]}..." if len(desc) > 150 else desc)
            else:
                st.warning("No jobs found. Please add jobs first.")
                selected_job_id = None
        
        with col2:
            # Candidate selection with search
            candidate_search = st.text_input("Search candidates", placeholder="Type to search...", key="candidate_search_match")
            
            # Filter candidates based on search
            filtered_candidates = candidates
            if candidate_search:
                filtered_candidates = [c for c in candidates if candidate_search.lower() in c["name"].lower()]
            
            # Create multiselect for candidates
            candidate_options = [(c["id"], c["name"]) for c in filtered_candidates]
            candidate_ids = [c[0] for c in candidate_options]
            candidate_names = [c[1] for c in candidate_options]
            
            default_selection = []
            if pre_selected_candidate in candidate_ids:
                default_selection = [candidate_names[candidate_ids.index(pre_selected_candidate)]]
            
            if candidate_options:
                selected_candidate_names = st.multiselect(
                    "Select Candidates",
                    options=candidate_names,
                    default=default_selection,
                    key="candidate_multiselect"
                )
                
                # Map names back to IDs
                selected_candidate_ids = [candidate_ids[candidate_names.index(name)] for name in selected_candidate_names]
                
                # Show count of selected candidates
                if selected_candidate_names:
                    st.info(f"Selected {len(selected_candidate_names)} candidates.")
            else:
                st.warning("No candidates found. Please upload CVs first.")
                selected_candidate_ids = []
        
        # Match button - only enabled if both job and candidates are selected
        if st.button("Match Candidates", disabled=not (selected_job_id and selected_candidate_ids)):
            with st.spinner("AI is matching candidates to job requirements..."):
                # Simulate AI processing with a progress bar
                progress_bar = st.progress(0)
                for i in range(101):
                    time.sleep(0.01)
                    progress_bar.progress(i)
                
                # Create matches
                matches = create_matches(selected_job_id, selected_candidate_ids)
                
                # Store matches in session state
                if selected_job_id not in st.session_state.matches:
                    st.session_state.matches[selected_job_id] = []
                
                # Update with new matches, avoiding duplicates
                existing_candidate_ids = [m["candidate_id"] for m in st.session_state.matches[selected_job_id]]
                for match in matches:
                    if match["candidate_id"] not in existing_candidate_ids:
                        st.session_state.matches[selected_job_id].append(match)
                        # If shortlisted, also add to shortlisted
                        if match["is_shortlisted"]:
                            if selected_job_id not in st.session_state.shortlisted:
                                st.session_state.shortlisted[selected_job_id] = []
                            st.session_state.shortlisted[selected_job_id].append(match)
                
                st.success(f"Created {len(matches)} matches successfully!")
                
                # Show the matches
                st.subheader("Match Results")
                
                # Convert matches to dataframe for display
                match_data = []
                for match in matches:
                    candidate_name = next((c["name"] for c in candidates if c["id"] == match["candidate_id"]), f"Candidate {match['candidate_id']}")
                    match_data.append({
                        "Candidate": candidate_name,
                        "Match Score": f"{match['match_score']:.0%}",
                        "Skills Match": f"{match['skills_score']:.0%}",
                        "Experience Match": f"{match['experience_score']:.0%}",
                        "Education Match": f"{match['education_score']:.0%}",
                        "Shortlisted": "✅" if match["is_shortlisted"] else "❌"
                    })
                
                # Display as table
                st.dataframe(
                    pd.DataFrame(match_data).sort_values(by="Match Score", ascending=False),
                    use_container_width=True,
                    hide_index=True
                )
                
                # Show a chart of match scores
                st.subheader("Match Score Distribution")
                
                chart_data = {}
                for match in matches:
                    candidate_name = next((c["name"] for c in candidates if c["id"] == match["candidate_id"]), f"Candidate {match['candidate_id']}")
                    chart_data[candidate_name] = match["match_score"]
                
                st.bar_chart(chart_data)
    
    with match_tab2:
        st.subheader("View Existing Matches")
        
        # Job selection dropdown
        job_options = [(j["id"], j["title"]) for j in jobs]
        job_ids = [j[0] for j in job_options]
        job_titles = [j[1] for j in job_options]
        
        if job_options:
            selected_job_title = st.selectbox(
                "Select Job to View Matches",
                options=job_titles,
                key="job_select_view"
            )
            selected_job_id = job_ids[job_titles.index(selected_job_title)]
            
            # Check if we have matches for this job
            if selected_job_id in st.session_state.matches and st.session_state.matches[selected_job_id]:
                matches = st.session_state.matches[selected_job_id]
                
                # Convert matches to dataframe for display
                match_data = []
                for match in matches:
                    candidate_name = next((c["name"] for c in candidates if c["id"] == match["candidate_id"]), f"Candidate {match['candidate_id']}")
                    match_data.append({
                        "Candidate": candidate_name,
                        "Match Score": f"{match['match_score']:.0%}",
                        "Skills Match": f"{match['skills_score']:.0%}",
                        "Experience Match": f"{match['experience_score']:.0%}",
                        "Education Match": f"{match['education_score']:.0%}",
                        "Shortlisted": "✅" if match["is_shortlisted"] else "❌"
                    })
                
                # Display as table
                st.dataframe(
                    pd.DataFrame(match_data).sort_values(by="Match Score", ascending=False),
                    use_container_width=True,
                    hide_index=True
                )
                
                # Show a chart of match scores
                st.subheader("Match Score Distribution")
                
                chart_data = {}
                for match in matches:
                    candidate_name = next((c["name"] for c in candidates if c["id"] == match["candidate_id"]), f"Candidate {match['candidate_id']}")
                    chart_data[candidate_name] = match["match_score"]
                
                st.bar_chart(chart_data)
                
                # Add an update button to shortlist candidates manually
                if st.button("Update Shortlist", key="update_shortlist"):
                    # This would connect to the backend to update shortlisted status
                    st.success("Shortlist updated successfully!")
            else:
                st.info(f"No matches found for {selected_job_title}. Create matches in the 'Create Matches' tab.")
        else:
            st.warning("No jobs found. Please add jobs first.")
    
    with match_tab3:
        st.subheader("Shortlisted Candidates")
        
        # Job selection dropdown
        job_options = [(j["id"], j["title"]) for j in jobs]
        job_ids = [j[0] for j in job_options]
        job_titles = [j[1] for j in job_options]
        
        if job_options:
            selected_job_title = st.selectbox(
                "Select Job to View Shortlisted Candidates",
                options=job_titles,
                key="job_select_shortlist"
            )
            selected_job_id = job_ids[job_titles.index(selected_job_title)]
            
            # Check if we have shortlisted candidates for this job
            if selected_job_id in st.session_state.matches:
                # Filter shortlisted matches
                shortlisted = [m for m in st.session_state.matches[selected_job_id] if m["is_shortlisted"]]
                
                if shortlisted:
                    # Convert shortlisted to dataframe for display
                    shortlist_data = []
                    for match in shortlisted:
                        candidate_name = next((c["name"] for c in candidates if c["id"] == match["candidate_id"]), f"Candidate {match['candidate_id']}")
                        shortlist_data.append({
                            "Candidate": candidate_name,
                            "Match Score": f"{match['match_score']:.0%}",
                            "Skills Match": f"{match['skills_score']:.0%}",
                            "Experience Match": f"{match['experience_score']:.0%}",
                            "Actions": "Schedule Interview"
                        })
                    
                    # Display as table
                    st.dataframe(
                        pd.DataFrame(shortlist_data).sort_values(by="Match Score", ascending=False),
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    # Add a button to schedule interviews
                    if st.button("Schedule Interviews for All", key="schedule_all"):
                        # This would redirect to the interview scheduling tab
                        st.session_state.current_tab = 4  # Index of the interview tab
                        st.session_state.schedule_job_id = selected_job_id
                        st.rerun()
                else:
                    st.info(f"No shortlisted candidates found for {selected_job_title}. Candidates with match scores above 80% are automatically shortlisted.")
            else:
                st.info(f"No matches found for {selected_job_title}. Create matches in the 'Create Matches' tab.")
        else:
            st.warning("No jobs found. Please add jobs first.")

with tab_interviews:
    st.header("Interview Scheduling")
    st.info("Here you can schedule interviews for shortlisted candidates.")
    
    # Initialize interview state
    if 'interviews' not in st.session_state:
        st.session_state.interviews = {}
    
    # Check if we're redirected from shortlisted tab
    schedule_job_id = None
    if 'schedule_job_id' in st.session_state:
        schedule_job_id = st.session_state.schedule_job_id
        del st.session_state.schedule_job_id
    
    # Create tabs for interview functionality
    interview_tab1, interview_tab2 = st.tabs(["Schedule Interviews", "View Scheduled Interviews"])
    
    with interview_tab1:
        st.subheader("Schedule New Interviews")
        
        # Job selection dropdown
        job_options = [(j["id"], j["title"]) for j in jobs]
        job_ids = [j[0] for j in job_options]
        job_titles = [j[1] for j in job_options]
        
        selected_job_index = 0
        if schedule_job_id in job_ids:
            selected_job_index = job_ids.index(schedule_job_id)
        
        if job_options:
            selected_job_title = st.selectbox(
                "Select Job",
                options=job_titles,
                index=selected_job_index,
                key="job_select_interview"
            )
            selected_job_id = job_ids[job_titles.index(selected_job_title)]
            
            # Get shortlisted candidates for this job
            shortlisted = []
            if selected_job_id in st.session_state.matches:
                shortlisted = [m for m in st.session_state.matches[selected_job_id] if m["is_shortlisted"]]
            
            if shortlisted:
                # Convert to dataframe for display with checkbox selection
                candidate_data = []
                for match in shortlisted:
                    candidate_name = next((c["name"] for c in candidates if c["id"] == match["candidate_id"]), f"Candidate {match['candidate_id']}")
                    candidate_data.append({
                        "Select": True,  # Default to selected
                        "Candidate": candidate_name,
                        "ID": match["candidate_id"],
                        "Match Score": f"{match['match_score']:.0%}"
                    })
                
                # Display with checkboxes
                st.subheader("Select Candidates to Interview")
                edited_df = st.data_editor(
                    pd.DataFrame(candidate_data),
                    column_config={
                        "Select": st.column_config.CheckboxColumn(
                            "Select",
                            help="Select candidates for interview scheduling"
                        ),
                        "ID": st.column_config.NumberColumn(
                            "ID",
                            help="Candidate ID",
                            step=1
                        ),
                        "Match Score": st.column_config.TextColumn(
                            "Match Score",
                            help="Match score percentage",
                            width="small"
                        )
                    },
                    hide_index=True
                )
                
                # Interview settings form
                st.subheader("Interview Details")
                
                # Create two columns for date and time
                date_col, format_col = st.columns(2)
                
                with date_col:
                    # Default to a date in the near future (2 business days from now)
                    default_date = datetime.now() + timedelta(days=2)
                    # If it's a weekend, move to next Monday
                    if default_date.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
                        default_date += timedelta(days=7 - default_date.weekday())
                    
                    interview_date = st.date_input(
                        "Interview Date",
                        value=default_date,
                        min_value=datetime.now().date(),
                        max_value=datetime.now().date() + timedelta(days=30)
                    )
                
                with format_col:
                    interview_format = st.selectbox(
                        "Interview Format",
                        options=["Video Call", "Phone Call", "In-Person", "Technical Assessment"]
                    )
                
                # Time slots selection
                st.subheader("Available Time Slots")
                time_slots = st.multiselect(
                    "Select Available Time Slots",
                    options=[
                        "9:00 AM - 10:00 AM",
                        "10:00 AM - 11:00 AM",
                        "11:00 AM - 12:00 PM",
                        "1:00 PM - 2:00 PM",
                        "2:00 PM - 3:00 PM",
                        "3:00 PM - 4:00 PM",
                        "4:00 PM - 5:00 PM"
                    ],
                    default=["10:00 AM - 11:00 AM", "2:00 PM - 3:00 PM"]
                )
                
                # Location info
                if interview_format == "In-Person":
                    interview_location = st.text_input(
                        "Interview Location",
                        value="Company Headquarters, Meeting Room 3"
                    )
                elif interview_format == "Video Call":
                    interview_platform = st.selectbox(
                        "Video Platform",
                        options=["Zoom", "Google Meet", "Microsoft Teams", "Skype"]
                    )
                
                # Additional notes
                interview_notes = st.text_area(
                    "Additional Notes for Candidates",
                    placeholder="Enter any additional instructions or information for the candidates..."
                )
                
                # Button to generate emails using AI
                if st.button("Generate Interview Invitations", disabled=not (time_slots and edited_df["Select"].any())):
                    with st.spinner("AI is generating personalized interview invitations..."):
                        # Get selected candidates
                        selected_candidates = edited_df[edited_df["Select"]]["ID"].tolist()
                        
                        if not selected_candidates:
                            st.warning("Please select at least one candidate.")
                        else:
                            # In a real app, this would call an API to generate emails
                            # For demonstration, simulate with a progress bar
                            progress_bar = st.progress(0)
                            for i in range(101):
                                time.sleep(0.01)
                                progress_bar.progress(i)
                            
                            # Store interviews in session state
                            if selected_job_id not in st.session_state.interviews:
                                st.session_state.interviews[selected_job_id] = []
                            
                            # Create interview objects for each candidate
                            new_interviews = []
                            for candidate_id in selected_candidates:
                                candidate_name = next((c["name"] for c in candidates if c["id"] == candidate_id), f"Candidate {candidate_id}")
                                
                                # Generate a random time slot for each candidate
                                selected_time = random.choice(time_slots)
                                
                                # Create the interview object
                                interview = {
                                    "id": len(st.session_state.interviews.get(selected_job_id, [])) + len(new_interviews) + 1,
                                    "job_id": selected_job_id,
                                    "job_title": selected_job_title,
                                    "candidate_id": candidate_id,
                                    "candidate_name": candidate_name,
                                    "date": interview_date.strftime("%Y-%m-%d"),
                                    "time_slot": selected_time,
                                    "format": interview_format,
                                    "notes": interview_notes,
                                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                    "status": "Scheduled"
                                }
                                
                                # Add location or platform if applicable
                                if interview_format == "In-Person":
                                    interview["location"] = interview_location
                                elif interview_format == "Video Call":
                                    interview["platform"] = interview_platform
                                
                                new_interviews.append(interview)
                            
                            # Add to session state
                            st.session_state.interviews[selected_job_id].extend(new_interviews)
                            
                            st.success(f"Generated interview invitations for {len(new_interviews)} candidates!")
                            
                            # Show a sample email
                            if new_interviews:
                                st.subheader("Sample Interview Invitation Email")
                                sample_interview = new_interviews[0]
                                
                                # Generate a sample email
                                email_template = f"""
                                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e1e1e1; border-radius: 5px;">
                                    <h2 style="color: #1E88E5;">Interview Invitation for {sample_interview['job_title']} Position</h2>
                                    <p>Dear {sample_interview['candidate_name']},</p>
                                    
                                    <p>Thank you for your application for the <strong>{sample_interview['job_title']}</strong> position at our company. We were impressed with your qualifications and would like to invite you for an interview.</p>
                                    
                                    <div style="background-color: #f9f9f9; padding: 15px; border-radius: 5px; margin: 15px 0;">
                                        <p><strong>Interview Details:</strong></p>
                                        <ul style="list-style-type: none; padding-left: 5px;">
                                            <li><strong>Date:</strong> {sample_interview['date']}</li>
                                            <li><strong>Time:</strong> {sample_interview['time_slot']}</li>
                                            <li><strong>Format:</strong> {sample_interview['format']}</li>
                                            {"<li><strong>Location:</strong> " + sample_interview.get('location', '') + "</li>" if 'location' in sample_interview else ""}
                                            {"<li><strong>Platform:</strong> " + sample_interview.get('platform', '') + "</li>" if 'platform' in sample_interview else ""}
                                        </ul>
                                    </div>
                                    
                                    <p>{sample_interview['notes']}</p>
                                    
                                    <p>Please confirm your availability by replying to this email. If you need to reschedule, please provide alternative times that work for you.</p>
                                    
                                    <p>We look forward to speaking with you!</p>
                                    
                                    <p>Best regards,<br>
                                    HR Department<br>
                                    Matchwise Inc.</p>
                                </div>
                                """
                                
                                st.markdown(email_template, unsafe_allow_html=True)
            else:
                st.info(f"No shortlisted candidates found for {selected_job_title}. Please shortlist candidates first in the Matching tab.")
        else:
            st.warning("No jobs found. Please add jobs first.")
    
    with interview_tab2:
        st.subheader("View Scheduled Interviews")
        
        # Check if we have any interviews scheduled
        has_interviews = any(len(interviews) > 0 for interviews in st.session_state.interviews.values())
        
        if has_interviews:
            # Create tabs for different views
            view_tab1, view_tab2 = st.tabs(["Calendar View", "List View"])
            
            with view_tab1:
                st.subheader("Interview Calendar")
                
                # Simple calendar visualization
                # In a real app, this would be a proper calendar widget
                # Here we're using a simple dataframe with dates
                
                # Get all interview dates
                all_dates = set()
                for job_id, interviews in st.session_state.interviews.items():
                    for interview in interviews:
                        all_dates.add(interview["date"])
                
                # Sort dates
                sorted_dates = sorted(list(all_dates))
                
                # Create a calendar-like display
                for date in sorted_dates:
                    st.markdown(f"### {date}")
                    
                    # Get interviews for this date
                    day_interviews = []
                    for job_id, interviews in st.session_state.interviews.items():
                        for interview in interviews:
                            if interview["date"] == date:
                                day_interviews.append(interview)
                    
                    # Sort by time slot
                    day_interviews.sort(key=lambda x: x["time_slot"])
                    
                    # Display interviews for this day
                    for interview in day_interviews:
                        with st.container():
                            st.markdown(f"""
                            <div style="border-left: 4px solid #1E88E5; padding-left: 10px; margin-bottom: 10px;">
                                <p><strong>{interview["time_slot"]}</strong> - {interview["candidate_name"]} for {interview["job_title"]}</p>
                                <p>Format: {interview["format"]}</p>
                            </div>
                            """, unsafe_allow_html=True)
            
            with view_tab2:
                st.subheader("All Scheduled Interviews")
                
                # Flatten the interviews list
                all_interviews = []
                for job_id, interviews in st.session_state.interviews.items():
                    all_interviews.extend(interviews)
                
                # Convert to dataframe for display
                if all_interviews:
                    interview_data = [{
                        "Candidate": interview["candidate_name"],
                        "Job": interview["job_title"],
                        "Date": interview["date"],
                        "Time": interview["time_slot"],
                        "Format": interview["format"],
                        "Status": interview["status"]
                    } for interview in all_interviews]
                    
                    # Sort by date and time
                    df = pd.DataFrame(interview_data)
                    df = df.sort_values(by=["Date", "Time"])
                    
                    # Display as table
                    st.dataframe(
                        df,
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.info("No interviews have been scheduled yet.")
        else:
            st.info("No interviews have been scheduled yet. Use the 'Schedule Interviews' tab to create new interviews.")

# Footer
st.markdown("---")
st.caption("Matchwise AI - Powered by advanced multi-agent framework") 