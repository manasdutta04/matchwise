"""
Streamlit web application for the Matchwise job application screening system.
AI-Powered Job Application Screening System with minimal UI and full functionality.
"""

import os
import streamlit as st
import pandas as pd
import numpy as np
import random
import glob
import json
import base64
import re
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
import tempfile
from io import BytesIO
import time

# Create a folder for the database
os.makedirs("data", exist_ok=True)

# Initialize database connection
def get_db_connection():
    """Get a connection to the SQLite database."""
    conn = sqlite3.connect('data/matchwise.db')
    conn.row_factory = sqlite3.Row
    return conn

# Initialize database tables if they don't exist
def init_db():
    """Initialize database tables."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create jobs table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        required_skills TEXT,
        required_experience TEXT,
        required_education TEXT,
        embedding TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create candidates table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS candidates (
        id INTEGER PRIMARY KEY,
        name TEXT,
        cv_filename TEXT NOT NULL UNIQUE,
        cv_path TEXT NOT NULL,
        skills TEXT,
        experience TEXT,
        education TEXT,
        embedding TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create matches table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS matches (
        id INTEGER PRIMARY KEY,
        job_id INTEGER,
        candidate_id INTEGER,
        match_score REAL,
        skills_score REAL,
        experience_score REAL,
        education_score REAL,
        is_shortlisted INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (job_id) REFERENCES jobs (id),
        FOREIGN KEY (candidate_id) REFERENCES candidates (id)
    )
    ''')
    
    # Create interviews table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS interviews (
        id INTEGER PRIMARY KEY,
        match_id INTEGER,
        job_id INTEGER,
        candidate_id INTEGER,
        date TEXT,
        time_slot TEXT,
        format TEXT,
        status TEXT DEFAULT 'Scheduled',
        email_sent INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (match_id) REFERENCES matches (id),
        FOREIGN KEY (job_id) REFERENCES jobs (id),
        FOREIGN KEY (candidate_id) REFERENCES candidates (id)
    )
    ''')
    
    conn.commit()
    conn.close()

# Initialize the database
init_db()

# Agent System Architecture
class JobDescriptionAgent:
    """Agent for parsing and summarizing job descriptions."""
    
    def process_jd(self, title, description):
        """Extract key information from a job description."""
        # Simulate AI processing with regex pattern matching
        
        # Extract skills
        skills_pattern = r"(?i)(?:skills required|required skills|skills|proficiency in|experience with|knowledge of)(?:\s*:\s*|\s+)(.*?)(?:\.|;|$)"
        skills_matches = re.findall(skills_pattern, description)
        skills = []
        for match in skills_matches:
            # Split by commas, and, or other separators
            for skill in re.split(r',|\sand\s|\sor\s', match):
                skill = skill.strip()
                if skill and len(skill) > 2:  # Filter out very short skills
                    skills.append(skill)
        
        # Extract experience
        exp_pattern = r"(?i)(\d+[\+]?(?:\s*-\s*\d+)?\s+years?(?:\s+of)?\s+experience)"
        exp_matches = re.findall(exp_pattern, description)
        experience = exp_matches[0] if exp_matches else "Not specified"
        
        # Extract education
        edu_pattern = r"(?i)(Bachelor's|Master's|PhD|degree|diploma)(\s+in\s+[\w\s]+)?"
        edu_matches = re.findall(edu_pattern, description)
        education = ' '.join([' '.join(filter(None, match)) for match in edu_matches[:1]]) if edu_matches else "Not specified"
        
        return {
            "title": title,
            "description": description,
            "required_skills": skills[:10],  # Limit to top 10 skills
            "required_experience": experience,
            "required_education": education
        }
    
    def save_to_db(self, job_data):
        """Save job data to the database."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if job already exists
        cursor.execute("SELECT id FROM jobs WHERE title = ?", (job_data["title"],))
        existing = cursor.fetchone()
        
        if existing:
            # Update existing job
            cursor.execute("""
            UPDATE jobs 
            SET description = ?, required_skills = ?, required_experience = ?, required_education = ?
            WHERE id = ?
            """, (
                job_data["description"],
                json.dumps(job_data["required_skills"]),
                job_data["required_experience"],
                job_data["required_education"],
                existing["id"]
            ))
            job_id = existing["id"]
        else:
            # Insert new job
            cursor.execute("""
            INSERT INTO jobs (title, description, required_skills, required_experience, required_education)
            VALUES (?, ?, ?, ?, ?)
            """, (
                job_data["title"],
                job_data["description"],
                json.dumps(job_data["required_skills"]),
                job_data["required_experience"],
                job_data["required_education"]
            ))
            job_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        return job_id

class CVProcessingAgent:
    """Agent for extracting information from CVs."""
    
    def process_cv(self, filename, file_path):
        """Extract key information from a CV."""
        # In a real system, this would use Ollama LLMs to extract data from the CV text
        # Here we'll simulate with random data based on the candidate ID
        
        # Extract candidate ID from filename
        candidate_id = filename.split('.')[0]  # e.g., "C9945" from "C9945.pdf"
        
        # Generate deterministic but varied skills based on the candidate ID
        seed = int(candidate_id[1:]) if candidate_id[1:].isdigit() else hash(candidate_id)
        random.seed(seed)
        
        # Lists of possible skills, degrees, etc.
        all_skills = ["Python", "JavaScript", "React", "Java", "C++", "SQL", "AWS", 
                     "Azure", "Machine Learning", "Data Analysis", "Project Management",
                     "Agile Methodology", "DevOps", "Docker", "Kubernetes", "Team Leadership",
                     "Communication", "Problem Solving", "Critical Thinking", "UI/UX Design"]
        
        degree_types = ["Bachelor's", "Master's", "PhD"]
        degree_fields = ["Computer Science", "Information Technology", "Business Administration", 
                         "Data Science", "Engineering", "Mathematics", "Statistics"]
        
        companies = ["Tech Solutions Inc.", "Data Innovators", "Global Systems", "NextGen Software",
                    "Enterprise Solutions", "Digital Transformers", "Cloud Computing Ltd."]
        
        job_titles = ["Software Engineer", "Data Scientist", "Project Manager", "Product Manager",
                     "DevOps Engineer", "Full Stack Developer", "UX Designer", "System Architect"]
        
        # Generate candidate data
        num_skills = random.randint(4, 10)
        skills = random.sample(all_skills, num_skills)
        
        num_degrees = random.randint(1, 2)
        education = []
        for _ in range(num_degrees):
            degree_type = random.choice(degree_types)
            field = random.choice(degree_fields)
            year = random.randint(2005, 2022)
            university = f"University of {chr(65 + random.randint(0, 25))}{chr(65 + random.randint(0, 25))}"
            education.append({
                "degree": f"{degree_type} in {field}",
                "university": university,
                "year": year
            })
        
        num_jobs = random.randint(1, 3)
        experience = []
        current_year = 2023
        for i in range(num_jobs):
            title = random.choice(job_titles)
            company = random.choice(companies)
            years = random.randint(1, 5)
            end_year = current_year - i
            start_year = end_year - years
            experience.append({
                "title": title,
                "company": company,
                "duration": f"{start_year} - {end_year if i > 0 else 'Present'} ({years} years)"
            })
        
        return {
            "name": f"Candidate {candidate_id}",
            "cv_filename": filename,
            "cv_path": file_path,
            "skills": skills,
            "education": education,
            "experience": experience
        }
    
    def save_to_db(self, cv_data):
        """Save CV data to the database."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if candidate already exists
        cursor.execute("SELECT id FROM candidates WHERE cv_filename = ?", (cv_data["cv_filename"],))
        existing = cursor.fetchone()
        
        if existing:
            # Update existing candidate
            cursor.execute("""
            UPDATE candidates 
            SET name = ?, cv_path = ?, skills = ?, experience = ?, education = ?
            WHERE id = ?
            """, (
                cv_data["name"],
                cv_data["cv_path"],
                json.dumps(cv_data["skills"]),
                json.dumps(cv_data["experience"]),
                json.dumps(cv_data["education"]),
                existing["id"]
            ))
            candidate_id = existing["id"]
        else:
            # Insert new candidate
            cursor.execute("""
            INSERT INTO candidates (name, cv_filename, cv_path, skills, experience, education)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (
                cv_data["name"],
                cv_data["cv_filename"],
                cv_data["cv_path"],
                json.dumps(cv_data["skills"]),
                json.dumps(cv_data["experience"]),
                json.dumps(cv_data["education"])
            ))
            candidate_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        return candidate_id

class MatchingAgent:
    """Agent for matching candidates to jobs."""
    
    def calculate_match(self, job_data, candidate_data):
        """Calculate the match score between a job and a candidate."""
        # Get required skills from job
        job_skills = job_data.get("required_skills", [])
        if isinstance(job_skills, str):
            try:
                job_skills = json.loads(job_skills)
            except:
                job_skills = []
        
        # Get candidate skills
        candidate_skills = candidate_data.get("skills", [])
        if isinstance(candidate_skills, str):
            try:
                candidate_skills = json.loads(candidate_skills)
            except:
                candidate_skills = []
        
        # Calculate skill match (case-insensitive)
        job_skills_lower = [s.lower() for s in job_skills]
        candidate_skills_lower = [s.lower() for s in candidate_skills]
        
        matched_skills = 0
        for skill in job_skills_lower:
            if any(skill in cand_skill.lower() for cand_skill in candidate_skills_lower):
                matched_skills += 1
        
        # Calculate skill score
        skill_score = matched_skills / len(job_skills) if job_skills else 0.5
        
        # Calculate experience match
        exp_score = 0.7 + random.uniform(-0.2, 0.2)  # Simulate experience matching
        
        # Calculate education match
        edu_score = 0.7 + random.uniform(-0.2, 0.2)  # Simulate education matching
        
        # Overall match score - weighted average
        match_score = (skill_score * 0.5) + (exp_score * 0.3) + (edu_score * 0.2)
        
        return {
            "match_score": round(min(0.98, max(0.5, match_score)), 2),
            "skills_score": round(min(0.95, max(0.5, skill_score)), 2),
            "experience_score": round(min(0.95, max(0.5, exp_score)), 2),
            "education_score": round(min(0.95, max(0.5, edu_score)), 2),
            "is_shortlisted": match_score > 0.75  # Auto-shortlist if score > 75%
        }
    
    def save_to_db(self, job_id, candidate_id, match_data):
        """Save match data to the database."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if match already exists
        cursor.execute("SELECT id FROM matches WHERE job_id = ? AND candidate_id = ?", 
                     (job_id, candidate_id))
        existing = cursor.fetchone()
        
        if existing:
            # Update existing match
            cursor.execute("""
            UPDATE matches 
            SET match_score = ?, skills_score = ?, experience_score = ?, 
                education_score = ?, is_shortlisted = ?
            WHERE id = ?
            """, (
                match_data["match_score"],
                match_data["skills_score"],
                match_data["experience_score"],
                match_data["education_score"],
                1 if match_data["is_shortlisted"] else 0,
                existing["id"]
            ))
            match_id = existing["id"]
        else:
            # Insert new match
            cursor.execute("""
            INSERT INTO matches 
                (job_id, candidate_id, match_score, skills_score, experience_score, 
                education_score, is_shortlisted)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                job_id,
                candidate_id,
                match_data["match_score"],
                match_data["skills_score"],
                match_data["experience_score"],
                match_data["education_score"],
                1 if match_data["is_shortlisted"] else 0
            ))
            match_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        return match_id

class InterviewAgent:
    """Agent for scheduling interviews and generating email templates."""
    
    def schedule_interview(self, match_id, job_id, candidate_id, date, time_slot, format):
        """Schedule an interview."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if interview already exists
        cursor.execute("""
        SELECT id FROM interviews 
        WHERE match_id = ? AND job_id = ? AND candidate_id = ?
        """, (match_id, job_id, candidate_id))
        existing = cursor.fetchone()
        
        if existing:
            # Update existing interview
            cursor.execute("""
            UPDATE interviews 
            SET date = ?, time_slot = ?, format = ?, status = 'Scheduled'
            WHERE id = ?
            """, (date, time_slot, format, existing["id"]))
            interview_id = existing["id"]
        else:
            # Insert new interview
            cursor.execute("""
            INSERT INTO interviews (match_id, job_id, candidate_id, date, time_slot, format)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (match_id, job_id, candidate_id, date, time_slot, format))
            interview_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        return interview_id
    
    def generate_email(self, job_title, candidate_name, date, time, format, company="Matchwise"):
        """Generate an interview invitation email."""
        # In a real system, this would use LLMs via Ollama
        # Here we'll use a template
        
        email_template = f"""
Subject: Interview Invitation for {job_title} position at {company}

Dear {candidate_name},

I hope this email finds you well. We appreciate your interest in the {job_title} position at {company}.

After carefully reviewing your application, we are pleased to invite you for an interview. Your qualifications and experience match what we're looking for in this role.

Interview Details:
- Position: {job_title}
- Date: {date}
- Time: {time}
- Format: {format}

{self._get_format_instructions(format)}

Please confirm your availability for this interview by replying to this email. If you need to reschedule, please provide alternative dates and times that work for you.

If you have any questions before the interview, feel free to reach out to us.

We look forward to speaking with you and learning more about your experience and skills.

Best regards,

Recruitment Team
{company}
        """
        
        return email_template
    
    def _get_format_instructions(self, format):
        """Get specific instructions based on interview format."""
        if format.lower() == "video call":
            return "You will receive a separate email with a link to join the video call closer to the interview date."
        elif format.lower() == "phone call":
            return "Our recruiter will call you at the phone number provided in your application."
        else:  # In-person
            return "Please arrive 10 minutes early. The interview will take place at our main office. Details about the location and parking will be sent in a follow-up email."

# Initialize agents
jd_agent = JobDescriptionAgent()
cv_agent = CVProcessingAgent()
matching_agent = MatchingAgent()
interview_agent = InterviewAgent() 

# Utility Functions for Data Management

# Function to load real job descriptions
def load_job_descriptions():
    """Load real job descriptions from the CSV file and process through the JD agent."""
    # First check if we already have jobs in the database
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM jobs")
    count = cursor.fetchone()["count"]
    
    # If we already have jobs, just fetch them from DB
    if count > 0:
        cursor.execute("""
        SELECT id, title, description, required_skills, required_experience, required_education
        FROM jobs
        """)
        jobs = []
        for row in cursor.fetchall():
            job = dict(row)
            # Parse JSON strings
            if job["required_skills"]:
                try:
                    job["required_skills"] = json.loads(job["required_skills"])
                except:
                    job["required_skills"] = []
            else:
                job["required_skills"] = []
            jobs.append(job)
        
        conn.close()
        return jobs
    
    # If no jobs in DB, load from CSV and process
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
                        conn.close()
                        return []
                    continue
                except Exception as e:
                    st.error(f"Error reading CSV with {encoding} encoding: {e}")
                    continue
            
            # Process jobs through the JD agent
            jobs = []
            for i, row in df.iterrows():
                # Handle missing columns gracefully
                title = row.get("Job Title", f"Job {i+1}")
                description = row.get("Job Description", "No description available")
                
                # Process through agent to extract skills, experience, education
                job_data = jd_agent.process_jd(title, description)
                
                # Save to database
                job_id = jd_agent.save_to_db(job_data)
                
                # Add ID to job data
                job_data["id"] = job_id
                jobs.append(job_data)
            
            conn.close()
            st.success(f"Processed and loaded {len(jobs)} job descriptions")
            return jobs
        else:
            st.error(f"Job description file not found: {jd_path}")
            conn.close()
            return []
    except Exception as e:
        st.error(f"Error loading job descriptions: {str(e)}")
        conn.close()
        return []

# Function to load real CV files
def load_candidates():
    """Load real CV files from the dataset folder and process through the CV agent."""
    # First check if we already have candidates in the database
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM candidates")
    count = cursor.fetchone()["count"]
    
    # If we already have candidates, just fetch them from DB
    if count > 0:
        cursor.execute("""
        SELECT id, name, cv_filename, cv_path, skills, experience, education
        FROM candidates
        """)
        candidates = []
        for row in cursor.fetchall():
            candidate = dict(row)
            # Parse JSON strings
            if candidate["skills"]:
                try:
                    candidate["skills"] = json.loads(candidate["skills"])
                except:
                    candidate["skills"] = []
            else:
                candidate["skills"] = []
                
            if candidate["experience"]:
                try:
                    candidate["experience"] = json.loads(candidate["experience"])
                except:
                    candidate["experience"] = []
            else:
                candidate["experience"] = []
                
            if candidate["education"]:
                try:
                    candidate["education"] = json.loads(candidate["education"])
                except:
                    candidate["education"] = []
            else:
                candidate["education"] = []
                
            candidates.append(candidate)
        
        conn.close()
        return candidates
    
    # If no candidates in DB, load from PDFs and process
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
                conn.close()
                return []
            
            st.success(f"Found {len(cv_files)} CV files")
            
            # Create a progress bar
            progress = st.progress(0)
            
            for i, cv_file in enumerate(cv_files):
                # Extract filename
                filename = os.path.basename(cv_file)
                
                # Process through agent to extract skills, experience, education
                cv_data = cv_agent.process_cv(filename, cv_file)
                
                # Save to database
                candidate_id = cv_agent.save_to_db(cv_data)
                
                # Add ID to candidate data
                cv_data["id"] = candidate_id
                candidates.append(cv_data)
                
                # Update progress
                progress.progress((i + 1) / len(cv_files))
            
            # Remove progress bar
            progress.empty()
            
            conn.close()
            st.success(f"Processed and loaded {len(candidates)} candidates")
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
                        progress = st.progress(0)
                        
                        for i, cv_file in enumerate(cv_files):
                            filename = os.path.basename(cv_file)
                            
                            # Process through agent
                            cv_data = cv_agent.process_cv(filename, cv_file)
                            
                            # Save to database
                            candidate_id = cv_agent.save_to_db(cv_data)
                            
                            # Add ID to candidate data
                            cv_data["id"] = candidate_id
                            candidates.append(cv_data)
                            
                            # Update progress
                            progress.progress((i + 1) / len(cv_files))
                        
                        # Remove progress bar
                        progress.empty()
                        
                        conn.close()
                        st.success(f"Processed and loaded {len(candidates)} candidates from alternative path")
                        return candidates
            
            # If we get here, we couldn't find any CVs in any location
            st.error(f"CV folder not found in any expected locations")
            conn.close()
            return []
            
    except Exception as e:
        st.error(f"Error loading candidates: {str(e)}")
        st.exception(e)  # This will show the full traceback
        conn.close()
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
    """Create matches between a job and candidates using the Matching Agent."""
    # Get connection
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Fetch job data
    cursor.execute("""
    SELECT id, title, description, required_skills, required_experience, required_education
    FROM jobs WHERE id = ?
    """, (job_id,))
    job = cursor.fetchone()
    
    if not job:
        st.error(f"Job with ID {job_id} not found")
        conn.close()
        return []
    
    # Convert row to dict
    job_data = dict(job)
    
    # Parse required skills
    if job_data["required_skills"]:
        try:
            job_data["required_skills"] = json.loads(job_data["required_skills"])
        except:
            job_data["required_skills"] = []
    else:
        job_data["required_skills"] = []
    
    # Determine which candidates to match
    if candidate_ids:
        # Match only specified candidates
        candidate_query = f"SELECT id, name, cv_filename, cv_path, skills, experience, education FROM candidates WHERE id IN ({','.join(['?'] * len(candidate_ids))})"
        cursor.execute(candidate_query, candidate_ids)
    else:
        # Match all candidates
        cursor.execute("SELECT id, name, cv_filename, cv_path, skills, experience, education FROM candidates")
    
    candidates = cursor.fetchall()
    matches = []
    
    # Create a progress bar
    progress = st.progress(0)
    
    # Process each candidate with the matching agent
    for i, candidate in enumerate(candidates):
        candidate_data = dict(candidate)
        
        # Parse JSON fields
        for field in ["skills", "experience", "education"]:
            if candidate_data[field]:
                try:
                    candidate_data[field] = json.loads(candidate_data[field])
                except:
                    candidate_data[field] = []
            else:
                candidate_data[field] = []
        
        # Calculate match using the matching agent
        match_result = matching_agent.calculate_match(job_data, candidate_data)
        
        # Add job and candidate info to match result
        match_result["job_id"] = job_id
        match_result["job_title"] = job_data["title"]
        match_result["candidate_id"] = candidate_data["id"]
        match_result["candidate_name"] = candidate_data["name"]
        
        # Save match to database
        match_id = matching_agent.save_to_db(job_id, candidate_data["id"], match_result)
        match_result["id"] = match_id
        
        matches.append(match_result)
        
        # Update progress
        progress.progress((i + 1) / len(candidates))
    
    # Remove progress bar
    progress.empty()
    
    # Sort matches by score, descending
    matches.sort(key=lambda x: x["match_score"], reverse=True)
    
    conn.close()
    return matches

# Function to get matches for a job
def get_matches(job_id):
    """Get existing matches for a job from the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Join with jobs and candidates to get names
    cursor.execute("""
    SELECT m.id, m.job_id, m.candidate_id, m.match_score, m.skills_score, 
           m.experience_score, m.education_score, m.is_shortlisted,
           j.title as job_title, c.name as candidate_name
    FROM matches m
    JOIN jobs j ON m.job_id = j.id
    JOIN candidates c ON m.candidate_id = c.id
    WHERE m.job_id = ?
    ORDER BY m.match_score DESC
    """, (job_id,))
    
    matches = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return matches

# Function to get shortlisted candidates
def get_shortlisted(job_id):
    """Get shortlisted candidates for a job."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT m.id, m.job_id, m.candidate_id, m.match_score, m.skills_score, 
           m.experience_score, m.education_score, m.is_shortlisted,
           j.title as job_title, c.name as candidate_name
    FROM matches m
    JOIN jobs j ON m.job_id = j.id
    JOIN candidates c ON m.candidate_id = c.id
    WHERE m.job_id = ? AND m.is_shortlisted = 1
    ORDER BY m.match_score DESC
    """, (job_id,))
    
    shortlisted = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return shortlisted

# Function to update shortlist status
def update_shortlist(match_id, is_shortlisted):
    """Update the shortlist status of a match."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
    UPDATE matches
    SET is_shortlisted = ?
    WHERE id = ?
    """, (1 if is_shortlisted else 0, match_id))
    
    conn.commit()
    conn.close()

# Function to schedule an interview
def schedule_interview(match_id, date, time_slot, format):
    """Schedule an interview for a match using the Interview Agent."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get match data
    cursor.execute("""
    SELECT job_id, candidate_id FROM matches WHERE id = ?
    """, (match_id,))
    match = cursor.fetchone()
    
    if not match:
        st.error(f"Match with ID {match_id} not found")
        conn.close()
        return None
    
    # Schedule interview using the agent
    interview_id = interview_agent.schedule_interview(
        match_id, match["job_id"], match["candidate_id"], date, time_slot, format
    )
    
    conn.close()
    return interview_id

# Function to get interviews
def get_interviews(job_id=None):
    """Get interviews, optionally filtered by job."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if job_id:
        # Get interviews for specific job
        cursor.execute("""
        SELECT i.id, i.match_id, i.job_id, i.candidate_id, i.date, i.time_slot, i.format, i.status,
               j.title as job_title, c.name as candidate_name
        FROM interviews i
        JOIN jobs j ON i.job_id = j.id
        JOIN candidates c ON i.candidate_id = c.id
        WHERE i.job_id = ?
        ORDER BY i.date, i.time_slot
        """, (job_id,))
    else:
        # Get all interviews
        cursor.execute("""
        SELECT i.id, i.match_id, i.job_id, i.candidate_id, i.date, i.time_slot, i.format, i.status,
               j.title as job_title, c.name as candidate_name
        FROM interviews i
        JOIN jobs j ON i.job_id = j.id
        JOIN candidates c ON i.candidate_id = c.id
        ORDER BY i.date, i.time_slot
        """)
    
    interviews = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return interviews

# Function to generate interview email
def generate_interview_email(interview_id):
    """Generate an interview email using the Interview Agent."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get interview data with job and candidate details
    cursor.execute("""
    SELECT i.id, i.date, i.time_slot, i.format, 
           j.title as job_title, c.name as candidate_name
    FROM interviews i
    JOIN jobs j ON i.job_id = j.id
    JOIN candidates c ON i.candidate_id = c.id
    WHERE i.id = ?
    """, (interview_id,))
    
    interview = cursor.fetchone()
    if not interview:
        st.error(f"Interview with ID {interview_id} not found")
        conn.close()
        return None
    
    # Generate email using the interview agent
    email = interview_agent.generate_email(
        interview["job_title"],
        interview["candidate_name"],
        interview["date"],
        interview["time_slot"],
        interview["format"]
    )
    
    conn.close()
    return email 

# Main application
def main():
    """Main function to run the Streamlit app with minimal UI."""
    # Initialize session state variables
    if 'page' not in st.session_state:
        st.session_state.page = 'jobs'
    
    if 'job_to_match' not in st.session_state:
        st.session_state.job_to_match = None
    
    if 'selected_job_id' not in st.session_state:
        st.session_state.selected_job_id = None
    
    if 'selected_candidate_id' not in st.session_state:
        st.session_state.selected_candidate_id = None
    
    if 'shortlisted' not in st.session_state:
        st.session_state.shortlisted = {}
    
    # Minimal sidebar
    with st.sidebar:
        st.title("Matchwise")
        st.markdown("AI-Powered Job Screening")
        
        # Simple navigation
        st.subheader("Navigation")
        selected = st.radio(
            "Select a page:",
            ["Jobs", "Candidates", "Matching", "Interviews"]
        )
        st.session_state.page = selected.lower()
        
        # Add a divider
        st.divider()
        
        # Display workflow steps
        st.markdown("""
        ### Workflow Steps
        1. Browse job descriptions
        2. Browse candidate CVs
        3. Match candidates to jobs
        4. Shortlist candidates
        5. Schedule interviews
        """)
    
    # Header
    st.title(f"Matchwise - {st.session_state.page.capitalize()}")
    
    # Main content area
    if st.session_state.page == 'jobs':
        render_jobs_page()
    elif st.session_state.page == 'candidates':
        render_candidates_page()
    elif st.session_state.page == 'matching':
        render_matching_page()
    elif st.session_state.page == 'interviews':
        render_interviews_page()
    
    # Footer
    st.divider()
    st.caption("© 2025 Matchwise | A craft of Manas Dutta")

def render_jobs_page():
    """Render the jobs page."""
    # Load jobs
    jobs = load_job_descriptions()
    
    if not jobs:
        st.warning("No job descriptions loaded. Please check the data folder.")
        return
    
    # Create tabs for different views
    tab1, tab2 = st.tabs(["Job List", "Job Details"])
    
    with tab1:
        st.subheader("Available Jobs")
        
        # Display job list in a table
        job_df = pd.DataFrame([
            {
                "ID": job["id"],
                "Title": job["title"],
                "Experience": job.get("required_experience", "Not specified"),
                "Education": job.get("required_education", "Not specified"),
                "Skills": len(job.get("required_skills", [])),
            } for job in jobs
        ])
        
        st.dataframe(job_df, use_container_width=True)
        
        # Select a job to view
        job_id = st.selectbox(
            "Select a job to view details",
            options=[job["id"] for job in jobs],
            format_func=lambda x: next((job["title"] for job in jobs if job["id"] == x), f"Job {x}"),
            key="job_selector"
        )
        
        st.session_state.selected_job_id = job_id
        
        # Match button
        if st.button("Match Candidates", key="match_btn"):
            st.session_state.job_to_match = job_id
            st.session_state.page = "matching"
            st.rerun()
    
    with tab2:
        if st.session_state.selected_job_id:
            # Find selected job
            selected_job = next((job for job in jobs if job["id"] == st.session_state.selected_job_id), None)
            
            if selected_job:
                st.subheader(selected_job["title"])
                
                # Basic job information
                st.markdown("### Job Description")
                st.write(selected_job["description"])
                
                # Requirements
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### Required Skills")
                    if "required_skills" in selected_job and selected_job["required_skills"]:
                        for skill in selected_job["required_skills"]:
                            st.write(f"- {skill}")
                    else:
                        st.info("No specific skills listed")
                
                with col2:
                    st.markdown("### Requirements")
                    st.write(f"**Experience:** {selected_job.get('required_experience', 'Not specified')}")
                    st.write(f"**Education:** {selected_job.get('required_education', 'Not specified')}")
            else:
                st.warning("Job not found")
        else:
            st.info("Please select a job from the list")

def render_candidates_page():
    """Render the candidates page."""
    # Load candidates
    candidates = load_candidates()
    
    if not candidates:
        st.warning("No candidates loaded. Please check the data folder.")
        return
    
    # Create tabs for different views
    tab1, tab2 = st.tabs(["Candidate List", "Candidate Details"])
    
    with tab1:
        st.subheader("Available Candidates")
        
        # Display candidate list in a table
        candidate_df = pd.DataFrame([
            {
                "ID": candidate["id"],
                "Name": candidate["name"],
                "Filename": candidate["cv_filename"],
                "Skills": len(candidate.get("skills", [])),
            } for candidate in candidates
        ])
        
        st.dataframe(candidate_df, use_container_width=True)
        
        # Select a candidate to view
        candidate_id = st.selectbox(
            "Select a candidate to view details",
            options=[candidate["id"] for candidate in candidates],
            format_func=lambda x: next((candidate["name"] for candidate in candidates if candidate["id"] == x), f"Candidate {x}"),
            key="candidate_selector"
        )
        
        st.session_state.selected_candidate_id = candidate_id
    
    with tab2:
        if st.session_state.selected_candidate_id:
            # Find selected candidate
            selected_candidate = next((candidate for candidate in candidates if candidate["id"] == st.session_state.selected_candidate_id), None)
            
            if selected_candidate:
                st.subheader(selected_candidate["name"])
                
                # Left column for details, right column for CV
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    # Skills
                    st.markdown("### Skills")
                    if "skills" in selected_candidate and selected_candidate["skills"]:
                        for skill in selected_candidate["skills"]:
                            st.write(f"- {skill}")
                    else:
                        st.info("No skills extracted from CV")
                    
                    # Experience
                    st.markdown("### Experience")
                    if "experience" in selected_candidate and selected_candidate["experience"]:
                        for exp in selected_candidate["experience"]:
                            st.write(f"**{exp.get('title')}** at {exp.get('company')}")
                            st.write(f"{exp.get('duration')}")
                            st.write("---")
                    else:
                        st.info("No experience extracted from CV")
                    
                    # Education
                    st.markdown("### Education")
                    if "education" in selected_candidate and selected_candidate["education"]:
                        for edu in selected_candidate["education"]:
                            st.write(f"**{edu.get('degree')}**")
                            st.write(f"{edu.get('university')}, {edu.get('year')}")
                            st.write("---")
                    else:
                        st.info("No education extracted from CV")
                
                with col2:
                    # Display CV
                    st.markdown("### CV Preview")
                    if "cv_path" in selected_candidate and selected_candidate["cv_path"]:
                        display_pdf(selected_candidate["cv_path"])
                    else:
                        st.error("CV path not found")
            else:
                st.warning("Candidate not found")
        else:
            st.info("Please select a candidate from the list")

def render_matching_page():
    """Render the matching page."""
    # Check if we're matching a specific job
    if st.session_state.job_to_match:
        job_id = st.session_state.job_to_match
        
        # Get job details
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT title FROM jobs WHERE id = ?", (job_id,))
        job = cursor.fetchone()
        conn.close()
        
        if not job:
            st.error(f"Job with ID {job_id} not found")
            return
        
        job_title = job["title"]
        
        st.subheader(f"Matching Candidates for: {job_title}")
        
        # Check if we already have matches
        matches = get_matches(job_id)
        
        if not matches:
            # No matches yet, run matching
            if st.button("Run Matching Algorithm"):
                with st.spinner("Matching candidates to job..."):
                    matches = create_matches(job_id)
                st.success(f"Successfully matched {len(matches)} candidates")
                # Force rerun to display results
                st.rerun()
        else:
            # Show tabs for all matches and shortlisted
            tab1, tab2 = st.tabs(["All Matches", "Shortlisted"])
            
            with tab1:
                st.markdown(f"### All Matches ({len(matches)})")
                
                # Display matches in a table
                match_df = pd.DataFrame([
                    {
                        "ID": match["id"],
                        "Candidate": match["candidate_name"],
                        "Match Score": f"{match['match_score']:.0%}",
                        "Skills": f"{match['skills_score']:.0%}",
                        "Experience": f"{match['experience_score']:.0%}",
                        "Education": f"{match['education_score']:.0%}",
                        "Shortlisted": "Yes" if match["is_shortlisted"] else "No"
                    } for match in matches
                ])
                
                st.dataframe(match_df, use_container_width=True)
                
                # Select a match to view/shortlist
                match_id = st.selectbox(
                    "Select a match to view",
                    options=[match["id"] for match in matches],
                    format_func=lambda x: next((f"{match['candidate_name']} ({match['match_score']:.0%})" 
                                              for match in matches if match["id"] == x), f"Match {x}")
                )
                
                if match_id:
                    selected_match = next((match for match in matches if match["id"] == match_id), None)
                    if selected_match:
                        # Display match details
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("Overall Match", f"{selected_match['match_score']:.0%}")
                        
                        with col2:
                            st.metric("Skills Match", f"{selected_match['skills_score']:.0%}")
                        
                        with col3:
                            st.metric("Experience Match", f"{selected_match['experience_score']:.0%}")
                        
                        # Shortlist button
                        shortlist_label = "Remove from Shortlist" if selected_match["is_shortlisted"] else "Add to Shortlist"
                        if st.button(shortlist_label):
                            update_shortlist(match_id, not selected_match["is_shortlisted"])
                            st.success(f"Candidate {shortlist_label.lower()}ed successfully")
                            st.rerun()
            
            with tab2:
                # Get shortlisted candidates
                shortlisted = get_shortlisted(job_id)
                
                if shortlisted:
                    st.markdown(f"### Shortlisted Candidates ({len(shortlisted)})")
                    
                    # Display shortlisted candidates
                    shortlist_df = pd.DataFrame([
                        {
                            "ID": match["id"],
                            "Candidate": match["candidate_name"],
                            "Match Score": f"{match['match_score']:.0%}"
                        } for match in shortlisted
                    ])
                    
                    st.dataframe(shortlist_df, use_container_width=True)
                    
                    # Schedule interviews button
                    if st.button("Schedule Interviews"):
                        st.session_state.scheduling_job_id = job_id
                        st.session_state.page = "interviews"
                        st.rerun()
                else:
                    st.info("No candidates have been shortlisted yet.")
        
        # Clear match button
        if st.button("Back"):
            st.session_state.job_to_match = None
            st.rerun()
    
    else:
        # Job selection interface
        st.subheader("Select a Job for Matching")
        
        # Load jobs
        jobs = load_job_descriptions()
        
        if not jobs:
            st.warning("No job descriptions loaded. Please go to the Jobs page first.")
            return
        
        # Display job selection
        job_id = st.selectbox(
            "Select a job to match with candidates",
            options=[job["id"] for job in jobs],
            format_func=lambda x: next((job["title"] for job in jobs if job["id"] == x), f"Job {x}")
        )
        
        if st.button("Start Matching"):
            st.session_state.job_to_match = job_id
            st.rerun()

def render_interviews_page():
    """Render the interviews page."""
    # Check if we're scheduling for a specific job
    if 'scheduling_job_id' in st.session_state and st.session_state.scheduling_job_id:
        job_id = st.session_state.scheduling_job_id
        
        # Get job details
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT title FROM jobs WHERE id = ?", (job_id,))
        job = cursor.fetchone()
        conn.close()
        
        if not job:
            st.error(f"Job with ID {job_id} not found")
            return
        
        job_title = job["title"]
        
        # Get shortlisted candidates
        shortlisted = get_shortlisted(job_id)
        
        if not shortlisted:
            st.warning("No shortlisted candidates found for this job")
            return
        
        st.subheader(f"Schedule Interviews for: {job_title}")
        
        # Create interview scheduling form
        with st.form("interview_form"):
            st.write("### Interview Details")
            
            # Select candidates
            candidates = st.multiselect(
                "Select candidates to interview",
                options=[match["id"] for match in shortlisted],
                format_func=lambda x: next((f"{match['candidate_name']} ({match['match_score']:.0%})" 
                                          for match in shortlisted if match["id"] == x), f"Match {x}")
            )
            
            # Date selection
            today = datetime.now().date()
            default_date = today + timedelta(days=5)
            date = st.date_input("Interview Date", value=default_date)
            
            # Time slots
            time_slots = st.multiselect(
                "Available Time Slots",
                options=["9:00 AM", "10:00 AM", "11:00 AM", "1:00 PM", "2:00 PM", "3:00 PM", "4:00 PM"],
                default=["10:00 AM", "2:00 PM"]
            )
            
            # Format
            format = st.radio(
                "Interview Format",
                options=["Video Call", "Phone Call", "In-person"],
                horizontal=True
            )
            
            # Submit button
            submitted = st.form_submit_button("Schedule Interviews")
            
            if submitted:
                if not candidates:
                    st.error("Please select at least one candidate")
                elif not time_slots:
                    st.error("Please select at least one time slot")
                else:
                    scheduled_count = 0
                    
                    with st.spinner("Scheduling interviews..."):
                        for match_id in candidates:
                            # Select a time slot
                            time_slot = time_slots[scheduled_count % len(time_slots)]
                            
                            # Schedule interview
                            interview_id = schedule_interview(
                                match_id, 
                                date.strftime("%Y-%m-%d"),
                                time_slot,
                                format
                            )
                            
                            if interview_id:
                                scheduled_count += 1
                    
                    if scheduled_count > 0:
                        st.success(f"Successfully scheduled {scheduled_count} interviews")
                        # Clear scheduling state
                        st.session_state.scheduling_job_id = None
                        st.rerun()
                    else:
                        st.error("Failed to schedule interviews")
        
        # Cancel button
        if st.button("Cancel"):
            st.session_state.scheduling_job_id = None
            st.rerun()
    
    else:
        # Show scheduled interviews
        st.subheader("Scheduled Interviews")
        
        # Get all interviews
        interviews = get_interviews()
        
        if interviews:
            # Display interviews in a table
            interview_df = pd.DataFrame([
                {
                    "ID": interview["id"],
                    "Job": interview["job_title"],
                    "Candidate": interview["candidate_name"],
                    "Date": interview["date"],
                    "Time": interview["time_slot"],
                    "Format": interview["format"],
                    "Status": interview["status"]
                } for interview in interviews
            ])
            
            st.dataframe(interview_df, use_container_width=True)
            
            # Select an interview to view email
            interview_id = st.selectbox(
                "Select an interview to generate email",
                options=[interview["id"] for interview in interviews],
                format_func=lambda x: next((f"{interview['candidate_name']} - {interview['job_title']} ({interview['date']})" 
                                          for interview in interviews if interview["id"] == x), f"Interview {x}")
            )
            
            if interview_id:
                # Generate email
                email = generate_interview_email(interview_id)
                
                if email:
                    st.subheader("Interview Invitation Email")
                    st.text_area("Email Content", email, height=300)
                    
                    # Add email copy button (markdown doesn't do anything but is informative)
                    st.markdown("Use the email above to invite the candidate.")
        else:
            st.info("No interviews scheduled yet")
            
            # Go to scheduling
            if st.button("Schedule New Interviews"):
                st.session_state.page = "matching"
                st.rerun()

# Run the application
if __name__ == "__main__":
    main() 