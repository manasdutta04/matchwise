"""
Streamlit web application for the Matchwise job application screening system.
Minimal version for demonstration purposes.
"""

import os
import streamlit as st
import random

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
    page_icon="📝",
    layout="wide"
)

# Apply a custom theme
st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    h1, h2, h3 {
        color: #1E88E5;
    }
    .stButton>button {
        background-color: #1E88E5;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Main content
st.title("Matchwise - AI Job Application Screening")

# Display the API URL (with warning if not connected)
st.info(f"This is a demo using mock data. In production, it would connect to: {API_URL}")

# Create tabs
tab1, tab2, tab3, tab4 = st.tabs(["Dashboard", "Jobs", "Candidates", "Matching"])

with tab1:
    st.header("Dashboard")
    
    # Create a simple layout with mock metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Jobs", len(MOCK_DATA["jobs"]))
    with col2:
        st.metric("Total Candidates", len(MOCK_DATA["candidates"]))
    with col3:
        st.metric("Total Matches", "5")
    with col4:
        st.metric("Shortlisted", "2")
    
    # Add a sample chart using Streamlit's native chart
    st.subheader("Match Score Distribution")
    chart_data = {
        "Software Engineer": random.uniform(0.6, 0.9),
        "Data Scientist": random.uniform(0.7, 0.95),
        "Product Manager": random.uniform(0.5, 0.85)
    }
    st.bar_chart(chart_data)

with tab2:
    st.header("Jobs")
    st.info("Here you can add and manage job descriptions.")
    
    # Display existing mock jobs
    st.subheader("Current Job Listings")
    for job in MOCK_DATA["jobs"]:
        with st.expander(f"{job['title']}"):
            st.write(f"**ID:** {job['id']}")
            st.write(f"**Description:** {job['description']}")
    
    # Simple job form
    st.subheader("Add a New Job")
    with st.form("job_form"):
        job_title = st.text_input("Job Title")
        job_description = st.text_area("Job Description")
        submit_button = st.form_submit_button("Add Job")
        
        if submit_button:
            if job_title and job_description:
                st.success(f"Job '{job_title}' would be added in production!")
            else:
                st.warning("Please fill in all fields")

with tab3:
    st.header("Candidates")
    st.info("Here you can upload and manage candidate CVs.")
    
    # Display existing mock candidates
    st.subheader("Current Candidates")
    for candidate in MOCK_DATA["candidates"]:
        with st.expander(f"{candidate['name']}"):
            st.write(f"**ID:** {candidate['id']}")
            st.write(f"**CV Filename:** {candidate['cv_filename']}")
    
    # Simple upload form
    st.subheader("Upload a CV")
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
    if uploaded_file is not None:
        st.success(f"File '{uploaded_file.name}' would be processed in production!")

with tab4:
    st.header("Matching")
    st.info("Here you can match candidates to jobs.")
    
    # Simple matching form
    st.subheader("Create Matches")
    col1, col2 = st.columns(2)
    with col1:
        job_selection = st.selectbox("Select Job", 
                                    options=[job["id"] for job in MOCK_DATA["jobs"]],
                                    format_func=lambda x: next((job["title"] for job in MOCK_DATA["jobs"] if job["id"] == x), ""))
    with col2:
        candidate_selection = st.multiselect("Select Candidates", 
                                           options=[candidate["id"] for candidate in MOCK_DATA["candidates"]],
                                           format_func=lambda x: next((candidate["name"] for candidate in MOCK_DATA["candidates"] if candidate["id"] == x), ""))
    
    if st.button("Match Candidates"):
        if candidate_selection:
            st.success(f"Created {len(candidate_selection)} matches successfully!")
            
            # Show sample results
            st.subheader("Match Results")
            
            results = []
            for candidate_id in candidate_selection:
                candidate_name = next((candidate["name"] for candidate in MOCK_DATA["candidates"] if candidate["id"] == candidate_id), "Unknown")
                score = round(random.uniform(0.6, 0.98) * 100, 1)
                skill_score = round(random.uniform(0.5, 0.99) * 100, 1)
                exp_score = round(random.uniform(0.6, 0.95) * 100, 1)
                edu_score = round(random.uniform(0.7, 0.97) * 100, 1)
                
                results.append({
                    "Candidate": candidate_name,
                    "Match Score": f"{score}%",
                    "Skills Score": f"{skill_score}%",
                    "Experience Score": f"{exp_score}%",
                    "Education Score": f"{edu_score}%"
                })
            
            st.table(results)
        else:
            st.warning("Please select at least one candidate")

# Footer
st.markdown("---")
st.write("Matchwise Demo - For demonstration purposes only") 