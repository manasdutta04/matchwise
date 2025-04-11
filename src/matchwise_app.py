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
    
    # Create matches table - make sure to use is_shortlisted consistently
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
        matched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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
        status TEXT DEFAULT 'scheduled',
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (match_id) REFERENCES matches (id),
        FOREIGN KEY (job_id) REFERENCES jobs (id),
        FOREIGN KEY (candidate_id) REFERENCES candidates (id)
    )
    ''')
    
    # Create a directory for data if it doesn't exist
    os.makedirs(os.path.dirname(os.path.abspath(__file__)) + "/data", exist_ok=True)
    
    # Create data directory for uploaded files
    os.makedirs("uploads", exist_ok=True)
    os.makedirs("uploads/CVs", exist_ok=True)
    
    # Commit changes and close connection
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
        
        # Extract experience - improved with additional patterns
        # Try multiple patterns to extract experience requirements
        experience = "Not specified"
        
        # Common patterns for experience
        exp_patterns = [
            r"(?i)(\d+[\+]?(?:\s*-\s*\d+)?\s+years?(?:\s+of)?\s+experience)",  # e.g., "3+ years experience"
            r"(?i)(minimum\s+of\s+\d+[\+]?\s+years?(?:\s+of)?\s+experience)",  # e.g., "minimum of 5 years experience"
            r"(?i)(at\s+least\s+\d+[\+]?\s+years?(?:\s+of)?\s+experience)",    # e.g., "at least 2 years experience"
            r"(?i)(experience\s*:\s*\d+[\+]?\s*-?\s*\d*\s+years?)",            # e.g., "Experience: 3-5 years"
            r"(?i)(experience\s*required\s*:\s*\d+[\+]?\s*-?\s*\d*\s+years?)",  # e.g., "Experience required: 2+ years"
            r"(?i)(\d+[\+]?\s*-?\s*\d*\s+years?(?:\s+of)?\s+.*?experience)"    # e.g., "3-5 years of software development experience"
        ]
        
        # Try each pattern until we find a match
        for pattern in exp_patterns:
            matches = re.findall(pattern, description)
            if matches:
                experience = matches[0]
                break
                
        # If no specific years found but "experience" is mentioned, extract surrounding context
        if experience == "Not specified" and re.search(r"(?i)experience", description):
            # Look for sentences containing "experience"
            exp_sentences = re.findall(r"(?i)([^.]*experience[^.]*\.)", description)
            if exp_sentences:
                # Use the first sentence that mentions experience requirements
                experience = exp_sentences[0].strip()
        
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
        
        # Calculate skills score
        skills_score = 0
        matched_skills = []
        
        if job_skills and len(job_skills) > 0:
            # Find exact and partial matches
            for required_skill in job_skills:
                # Normalize skill names for comparison
                norm_required = required_skill.lower().strip()
                
                # Check for match in candidate skills
                for candidate_skill in candidate_skills:
                    norm_candidate = candidate_skill.lower().strip()
                    
                    # Check for exact or partial match
                    if (norm_required == norm_candidate or
                        norm_required in norm_candidate or
                        norm_candidate in norm_required):
                        matched_skills.append(required_skill)
                        break
            
            # Calculate percentage of required skills matched
            skills_score = (len(matched_skills) / len(job_skills)) * 100
            
            # Add variance based on candidate ID to create more diverse scores
            candidate_id = candidate_data.get("id", 0)
            skills_variance = (candidate_id % 10) / 5  # +/- 2%
            skills_score = min(99, max(35, skills_score + skills_variance))
        else:
            # No required skills specified
            skills_score = 65.0
        
        # Calculate experience score - simplified for demo
        experience_score = 50.0 + (candidate_data.get("id", 0) % 15)  # 50-65%
        
        # Calculate education score - simplified for demo
        education_score = 60.0 + (candidate_data.get("id", 0) % 20)  # 60-80%
        
        # Calculate overall match score (weighted average)
        match_score = (skills_score * 0.6 + experience_score * 0.25 + education_score * 0.15)
        
        return {
            "match_score": round(match_score, 1),
            "skills_score": round(skills_score, 1),
            "experience_score": round(experience_score, 1),
            "education_score": round(education_score, 1),
            "matched_skills": matched_skills,
            "is_shortlisted": False  # Default to not shortlisted - using is_shortlisted instead of shortlisted
        }
    
    def save_to_db(self, job_id, candidate_id, match_data):
        """Save match result to the database."""
        try:
            conn = get_db_connection()
            
            # Check if match already exists
            existing_match = conn.execute(
                "SELECT id FROM matches WHERE job_id = ? AND candidate_id = ?",
                (job_id, candidate_id)
            ).fetchone()
            
            if existing_match:
                # Update existing match
                conn.execute("""
                UPDATE matches SET
                    match_score = ?,
                    skills_score = ?,
                    experience_score = ?,
                    education_score = ?,
                    is_shortlisted = ?
                WHERE job_id = ? AND candidate_id = ?
                """, (
                    match_data["match_score"],
                    match_data["skills_score"],
                    match_data["experience_score"],
                    match_data["education_score"],
                    1 if match_data.get("is_shortlisted", False) else 0,
                    job_id,
                    candidate_id
                ))
                match_id = existing_match["id"]
            else:
                # Insert new match
                cursor = conn.execute("""
                INSERT INTO matches (
                    job_id, candidate_id, match_score,
                    skills_score, experience_score, education_score, is_shortlisted
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    job_id,
                    candidate_id,
                    match_data["match_score"],
                    match_data["skills_score"],
                    match_data["experience_score"],
                    match_data["education_score"],
                    1 if match_data.get("is_shortlisted", False) else 0
                ))
                match_id = cursor.lastrowid
            
            conn.commit()
            conn.close()
            return match_id
            
        except Exception as e:
            print(f"Error saving match: {e}")
            return None

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
            SET date = ?, time_slot = ?, format = ?, status = 'scheduled'
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
    
    # If no jobs in DB, try loading from CSV, or create dummy data
    try:
        jd_path = "AI-Powered Job Application Screening System/job_description.csv"
        
        # Try different possible locations for the file
        possible_paths = [
            "AI-Powered Job Application Screening System/job_description.csv",
            "AI-Powered Job Application Screening System/job_descriptions.csv",
            "AI-Powered Job Application Screening System/jobs.csv",
            "job_description.csv",
            "job_descriptions.csv",
            "jobs.csv"
        ]
        
        # Find the first existing file
        for path in possible_paths:
            if os.path.exists(path):
                jd_path = path
                st.success(f"Found job descriptions at: {path}")
                break
        
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
                        # Fall back to creating dummy data
                        df = None
                    continue
                except Exception as e:
                    st.error(f"Error reading CSV with {encoding} encoding: {e}")
                    df = None
                    break
            
            if df is not None:
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
        
        # If we couldn't load from a file, create dummy job data
        st.warning("No job description file found. Creating sample job data...")
        
        # Create dummy job descriptions
        dummy_jobs = [
            {
                "title": "Software Engineer",
                "description": "We are looking for a talented Software Engineer to join our development team. You will be responsible for developing high-quality applications and services.",
                "required_skills": ["Python", "JavaScript", "React", "SQL", "Git"],
                "required_experience": "3+ years of software development experience",
                "required_education": "Bachelor's degree in Computer Science"
            },
            {
                "title": "Data Scientist",
                "description": "Join our data science team to develop models and algorithms that solve complex business problems using machine learning techniques.",
                "required_skills": ["Python", "Machine Learning", "SQL", "Statistics", "Data Visualization"],
                "required_experience": "2+ years of experience in data science or analytics",
                "required_education": "Master's in Data Science, Statistics, or related field"
            },
            {
                "title": "Product Manager",
                "description": "Lead the development of our product roadmap, gathering and prioritizing requirements, and defining the product vision.",
                "required_skills": ["Product Management", "Agile Methodology", "Market Research", "User Experience", "Communication"],
                "required_experience": "4+ years of product management experience",
                "required_education": "Bachelor's degree in Business, Engineering, or related field"
            }
        ]
        
        # Save the dummy jobs to database
        jobs = []
        for job_data in dummy_jobs:
            job_id = jd_agent.save_to_db(job_data)
            job_data["id"] = job_id
            jobs.append(job_data)
        
        conn.close()
        st.success(f"Created {len(jobs)} sample job descriptions")
        return jobs
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
    
    # If no candidates in DB, try to find CV files or generate sample candidates
    try:
        cv_folder = "AI-Powered Job Application Screening System/CVs1"
        cv_files = []
        
        # Check for CV files in various possible locations
        possible_folders = [
            "AI-Powered Job Application Screening System/CVs1",
            "AI-Powered Job Application Screening System/CVs",
            "AI-Powered Job Application Screening System/CV",
            "AI-Powered Job Application Screening System/Resumes",
            "CVs1",
            "CVs",
            "resumes"
        ]
        
        for folder in possible_folders:
            if os.path.exists(folder):
                st.success(f"Found CV folder: {folder}")
                cv_files = glob.glob(f"{folder}/*.pdf")
                
                if cv_files:
                    cv_folder = folder
                    break
                else:
                    # Try looking in subdirectories
                    cv_files = glob.glob(f"{folder}/**/*.pdf", recursive=True)
                    if cv_files:
                        cv_folder = folder
                        break
        
        # If PDF files found, process them
        if cv_files:
            st.success(f"Found {len(cv_files)} CV files")
            
            # Create a progress bar
            progress = st.progress(0)
            
            # Process the CV files
            candidates = []
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
        
        # If no PDF files found, generate synthetic candidates
        else:
            st.warning("No CV files found. Creating sample candidate data...")
            
            # Generate sample candidates with varied skills and backgrounds
            sample_candidates = [
                {
                    "name": "John Smith",
                    "cv_filename": "john_smith.pdf",
                    "cv_path": "",
                    "skills": ["Python", "JavaScript", "React", "Node.js", "SQL", "MongoDB"],
                    "experience": [
                        {"title": "Senior Developer", "company": "Tech Solutions Inc.", "duration": "2019 - Present (4 years)"},
                        {"title": "Web Developer", "company": "Digital Innovations", "duration": "2015 - 2019 (4 years)"}
                    ],
                    "education": [
                        {"degree": "Master's in Computer Science", "university": "University of Technology", "year": 2015}
                    ]
                },
                {
                    "name": "Sarah Johnson",
                    "cv_filename": "sarah_johnson.pdf",
                    "cv_path": "",
                    "skills": ["Data Analysis", "Python", "R", "Machine Learning", "SQL", "Tableau"],
                    "experience": [
                        {"title": "Data Scientist", "company": "Analytics Pro", "duration": "2018 - Present (5 years)"},
                        {"title": "Data Analyst", "company": "Business Insights", "duration": "2016 - 2018 (2 years)"}
                    ],
                    "education": [
                        {"degree": "PhD in Statistics", "university": "State University", "year": 2016}
                    ]
                },
                {
                    "name": "Michael Chen",
                    "cv_filename": "michael_chen.pdf",
                    "cv_path": "",
                    "skills": ["Product Management", "Agile", "UX Research", "Market Analysis", "SQL", "Jira"],
                    "experience": [
                        {"title": "Product Manager", "company": "Innovation Labs", "duration": "2017 - Present (6 years)"},
                        {"title": "Associate Product Manager", "company": "Tech Startups Inc.", "duration": "2015 - 2017 (2 years)"}
                    ],
                    "education": [
                        {"degree": "MBA", "university": "Business School", "year": 2015},
                        {"degree": "Bachelor's in Computer Engineering", "university": "Tech Institute", "year": 2013}
                    ]
                },
                {
                    "name": "Emily Davis",
                    "cv_filename": "emily_davis.pdf",
                    "cv_path": "",
                    "skills": ["UI/UX Design", "Figma", "Adobe XD", "HTML", "CSS", "JavaScript"],
                    "experience": [
                        {"title": "UX Designer", "company": "Creative Solutions", "duration": "2020 - Present (3 years)"},
                        {"title": "UI Designer", "company": "Digital Agency", "duration": "2017 - 2020 (3 years)"}
                    ],
                    "education": [
                        {"degree": "Bachelor's in Graphic Design", "university": "Art Institute", "year": 2017}
                    ]
                },
                {
                    "name": "Alex Thompson",
                    "cv_filename": "alex_thompson.pdf",
                    "cv_path": "",
                    "skills": ["DevOps", "AWS", "Docker", "Kubernetes", "CI/CD", "Python", "Terraform"],
                    "experience": [
                        {"title": "DevOps Engineer", "company": "Cloud Solutions", "duration": "2019 - Present (4 years)"},
                        {"title": "Systems Administrator", "company": "Tech Infrastructure", "duration": "2016 - 2019 (3 years)"}
                    ],
                    "education": [
                        {"degree": "Bachelor's in Information Technology", "university": "Tech University", "year": 2016}
                    ]
                }
            ]
            
            # Save to database
            candidates = []
            for candidate_data in sample_candidates:
                candidate_id = cv_agent.save_to_db(candidate_data)
                candidate_data["id"] = candidate_id
                candidates.append(candidate_data)
            
            conn.commit()
            conn.close()
            
            st.success(f"Created {len(candidates)} sample candidates")
            return candidates
            
    except Exception as e:
        st.error(f"Error loading candidates: {str(e)}")
        
        # Create fallback candidates if error occurs
        st.warning("Generating fallback candidate data...")
        candidates = []
        
        # Generate 5 fallback candidates
        for i in range(1, 6):
            candidate_id = f"C{9000 + i}"
            candidate = {
                "id": i,
                "name": f"Candidate {candidate_id}",
                "cv_filename": f"{candidate_id}.pdf",
                "cv_path": "",
                "skills": ["Python", "Java", "Communication"],
                "experience": [{"title": "Software Developer", "company": "Tech Inc", "duration": "3 years"}],
                "education": [{"degree": "Bachelor's in CS", "university": "Tech University", "year": 2018}]
            }
            
            # Save to database
            cursor.execute("""
            INSERT INTO candidates (name, cv_filename, cv_path, skills, experience, education)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (
                candidate["name"],
                candidate["cv_filename"],
                candidate["cv_path"],
                json.dumps(candidate["skills"]),
                json.dumps(candidate["experience"]),
                json.dumps(candidate["education"])
            ))
            candidate["id"] = cursor.lastrowid
            candidates.append(candidate)
        
        conn.commit()
        conn.close()
        return candidates

# Function to display PDF (for viewing CVs)
def display_pdf(file_path):
    """Display a PDF file in Streamlit."""
    try:
        # First check if file exists
        if not os.path.exists(file_path):
            # Fallback: Show a placeholder and mock CV preview
            st.warning(f"PDF file not found: {file_path}")
            st.markdown("### Mock CV Preview")
            
            # Display placeholder image
            st.markdown("""
            <div style="text-align: center; padding: 20px; background-color: #f5f5f5; border-radius: 5px;">
                <svg width="100" height="100" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M14 2H6C4.89543 2 4 2.89543 4 4V20C4 21.1046 4.89543 22 6 22H18C19.1046 22 20 21.1046 20 20V8L14 2Z" stroke="#000000" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M14 2V8H20" stroke="#000000" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M12 12C12.5523 12 13 11.5523 13 11C13 10.4477 12.5523 10 12 10C11.4477 10 11 10.4477 11 11C11 11.5523 11.4477 12 12 12Z" stroke="#000000" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M9 18C9 16.3431 10.3431 15 12 15C13.6569 15 15 16.3431 15 18" stroke="#000000" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                <p style="margin-top: 10px;">CV Preview not available</p>
            </div>
            """, unsafe_allow_html=True)
            return False
        
        # Check file size (limit to 10MB to avoid memory issues)
        file_size = os.path.getsize(file_path) / (1024 * 1024)  # Convert to MB
        if file_size > 10:
            st.warning(f"PDF file is large ({file_size:.1f} MB). Loading preview may take time.")
        
        # Try to read and display the PDF
        try:
            with open(file_path, "rb") as f:
                base64_pdf = base64.b64encode(f.read()).decode('utf-8')
            
            pdf_display = f"""
                <iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf"></iframe>
            """
            st.markdown(pdf_display, unsafe_allow_html=True)
            return True
        except Exception as e:
            # If display fails, provide a download button instead
            st.error(f"Could not display PDF: {str(e)}")
            
            # Display placeholder image
            st.markdown("""
            <div style="text-align: center; padding: 20px; background-color: #f5f5f5; border-radius: 5px;">
                <svg width="100" height="100" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M14 2H6C4.89543 2 4 2.89543 4 4V20C4 21.1046 4.89543 22 6 22H18C19.1046 22 20 21.1046 20 20V8L14 2Z" stroke="#000000" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M14 2V8H20" stroke="#000000" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                <p style="margin-top: 10px;">PDF preview not available in browser</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Provide download button
            with open(file_path, "rb") as file:
                filename = os.path.basename(file_path)
                st.download_button(
                    label="Download CV", 
                    data=file,
                    file_name=filename,
                    mime="application/pdf"
                )
            return False
            
    except Exception as e:
        st.error(f"Error with PDF: {str(e)}")
        
        # Show a simple placeholder with CV info instead
        st.markdown("""
        <div style="text-align: center; padding: 20px; background-color: #f5f5f5; border-radius: 5px;">
            <svg width="100" height="100" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M14 2H6C4.89543 2 4 2.89543 4 4V20C4 21.1046 4.89543 22 6 22H18C19.1046 22 20 21.1046 20 20V8L14 2Z" stroke="#000000" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M14 2V8H20" stroke="#000000" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M16 13H8" stroke="#000000" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M16 17H8" stroke="#000000" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M10 9H9H8" stroke="#000000" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <p style="margin-top: 10px;">CV content not available</p>
        </div>
        """, unsafe_allow_html=True)
        
        return False

# Function to create matches between jobs and candidates
def create_matches(job_id, candidate_ids=None):
    """Create matches between a job and candidates."""
    try:
        conn = get_db_connection()
        
        # Get job data
        job_data = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        if not job_data:
            st.error(f"Job with ID {job_id} not found.")
            return
        
        # Convert job data to dictionary
        job_dict = {
            "id": job_data["id"],
            "title": job_data["title"],
            "description": job_data["description"],
            "required_skills": job_data["required_skills"],
            "required_experience": job_data["required_experience"],
            "required_education": job_data["required_education"]
        }
        
        # Get candidates
        if candidate_ids:
            # Get specific candidates
            placeholders = ",".join(["?"] * len(candidate_ids))
            candidates = conn.execute(
                f"SELECT * FROM candidates WHERE id IN ({placeholders})",
                candidate_ids
            ).fetchall()
        else:
            # Get all candidates
            candidates = conn.execute("SELECT * FROM candidates").fetchall()
        
        # Create matches
        matcher = MatchingAgent()
        matches_created = 0
        
        for candidate in candidates:
            # Convert candidate data to dictionary
            candidate_dict = {
                "id": candidate["id"],
                "name": candidate["name"],
                "skills": candidate["skills"],
                "experience": candidate["experience"],
                "education": candidate["education"]
            }
            
            # Calculate match score
            match_data = matcher.calculate_match(job_dict, candidate_dict)
            
            # Auto-shortlist candidates with match scores over 59%
            if match_data["match_score"] > 59:
                match_data["is_shortlisted"] = True
            
            # Save match to database
            matcher.save_to_db(job_id, candidate["id"], match_data)
            matches_created += 1
        
        conn.close()
        
        if matches_created > 0:
            st.success(f"Created {matches_created} matches for job ID {job_id}.")
            st.info("Candidates with match scores over 59% have been automatically shortlisted.")
        else:
            st.warning("No candidates found to match.")
            
    except Exception as e:
        st.error(f"Error creating matches: {e}")

# Function to get matches for a job
def get_matches(job_id):
    """Get matches for a job."""
    try:
        conn = get_db_connection()
        matches = conn.execute(
            "SELECT * FROM matches WHERE job_id = ? ORDER BY match_score DESC", 
            (job_id,)
        ).fetchall()
        conn.close()
        
        # Convert to list of dictionaries
        return [dict(match) for match in matches]
    except Exception as e:
        st.error(f"Error getting matches: {e}")
        return []

# Function to get shortlisted candidates
def get_shortlisted(job_id):
    """Get shortlisted candidates for a job."""
    try:
        conn = get_db_connection()
        shortlisted = conn.execute(
            "SELECT * FROM matches WHERE job_id = ? AND is_shortlisted = 1 ORDER BY match_score DESC", 
            (job_id,)
        ).fetchall()
        conn.close()
        
        # Convert to list of dictionaries
        return [dict(match) for match in shortlisted]
    except Exception as e:
        st.error(f"Error getting shortlisted candidates: {e}")
        return []

# Function to update shortlist status
def update_shortlist(match_id, is_shortlisted):
    """Update shortlist status for a match."""
    try:
        conn = get_db_connection()
        conn.execute(
            "UPDATE matches SET is_shortlisted = ? WHERE id = ?", 
            (1 if is_shortlisted else 0, match_id)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error updating shortlist status: {e}")
        return False

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
    # Initialize database
    init_db()
    
    # Initialize session state variables
    if 'page' not in st.session_state:
        st.session_state.page = 'jobs'
    
    if 'job_to_match' not in st.session_state:
        st.session_state.job_to_match = None
    
    if 'selected_job_id' not in st.session_state:
        st.session_state.selected_job_id = None
    
    if 'selected_candidate_id' not in st.session_state:
        st.session_state.selected_candidate_id = None
    
    if 'scheduling_job_id' not in st.session_state:
        st.session_state.scheduling_job_id = None
    
    # Initialize agents
    global jd_agent, cv_agent, matching_agent, interview_agent
    jd_agent = JobDescriptionAgent()
    cv_agent = CVProcessingAgent()
    matching_agent = MatchingAgent()
    interview_agent = InterviewAgent()
    
    # Page title and sidebar
    st.markdown("# Matchwise - {0}".format(st.session_state.page.title()))
    
    # Sidebar for navigation
    # Instead of showing logo separately, we'll combine it with the title
    st.sidebar.markdown("""
    <div style="display: flex; align-items: center; margin-bottom: 1rem;">
        <h1 style="margin: 0; padding: 0; font-size: 2.2rem;">Matchwise</h1>
        <div style="margin-left: 10px;">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <rect width="24" height="24" rx="12" fill="#1E88E5" />
                <path d="M7 12L10 15L17 8" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.sidebar.caption("AI-Powered Job Screening")
    
    st.sidebar.markdown("---")
    st.sidebar.title("Navigation")
    
    st.sidebar.markdown("Select a page:")
    
    # Radio buttons for navigation
    page = st.sidebar.radio(
        "Select a page:",
        options=["Jobs", "Candidates", "Matching", "Interviews"],
        index=["jobs", "candidates", "matching", "interviews"].index(st.session_state.page),
        label_visibility="collapsed"
    )
    
    # Update session state when page changes
    if page.lower() != st.session_state.page:
        st.session_state.page = page.lower()
        st.rerun()
    
    # Workflow steps in sidebar
    st.sidebar.markdown("---")
    st.sidebar.title("Workflow Steps")
    
    workflow_steps = [
        "1. Browse job descriptions",
        "2. Browse candidate CVs",
        "3. Match candidates to jobs",
        "4. Shortlist candidates",
        "5. Schedule interviews"
    ]
    
    for step in workflow_steps:
        st.sidebar.markdown(step)
    
    # Main content based on selected page
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
    
    # Application notices based on current page
    if st.session_state.page == 'candidates':
        st.info("📄 **Note about CV Display**: In deployed environments, CV files may not be accessible. The application will show candidate information extracted from the database instead of the actual CV file.")
    
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
        
        st.dataframe(job_df, use_container_width=True, hide_index=True)
        
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
            # Store the selected job ID for the matching page
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
                
                # Match button in the details tab too
                if st.button("Match Candidates", key="match_btn_detail"):
                    # Store the selected job ID for the matching page
                    st.session_state.job_to_match = st.session_state.selected_job_id
                    st.session_state.page = "matching"
                    st.rerun()
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
                    # Check if path exists
                    if "cv_path" in selected_candidate and selected_candidate["cv_path"]:
                        # Try to display PDF
                        if not display_pdf(selected_candidate["cv_path"]):
                            # If display failed, show extracted information in a nicer format
                            st.info("Using extracted CV information for preview:")
                            
                            # Create a neat display of candidate info
                            with st.container():
                                st.markdown("""
                                <div style="border: 1px solid #ddd; padding: 15px; border-radius: 5px;">
                                    <h4 style="text-align: center; border-bottom: 1px solid #eee; padding-bottom: 10px;">
                                        Candidate Profile
                                    </h4>
                                """, unsafe_allow_html=True)
                                
                                # Show experience summary
                                if "experience" in selected_candidate and selected_candidate["experience"]:
                                    exp_years = sum([int(exp.get("duration", "").split()[0]) 
                                                  if "duration" in exp and exp.get("duration", "").split() and exp.get("duration", "").split()[0].isdigit() 
                                                  else 0 
                                                  for exp in selected_candidate["experience"]])
                                    st.markdown(f"**Total Experience:** {exp_years}+ years")
                                
                                # Show education summary
                                if "education" in selected_candidate and selected_candidate["education"]:
                                    highest_degree = selected_candidate["education"][0].get("degree", "Not specified")
                                    st.markdown(f"**Highest Degree:** {highest_degree}")
                                
                                # Show top skills
                                if "skills" in selected_candidate and selected_candidate["skills"]:
                                    top_skills = selected_candidate["skills"][:5]
                                    st.markdown("**Top Skills:** " + ", ".join(top_skills))
                                
                                st.markdown("</div>", unsafe_allow_html=True)
                    else:
                        # No CV path available
                        st.error("CV file not found")
                        st.info("Using candidate information from database:")
                        
                        # Display candidate information in a neat card
                        with st.container():
                            st.markdown("""
                            <div style="border: 1px solid #ddd; padding: 15px; border-radius: 5px; background-color: #f9f9f9;">
                                <h4 style="text-align: center; border-bottom: 1px solid #eee; padding-bottom: 10px;">
                                    Candidate Information
                                </h4>
                            """, unsafe_allow_html=True)
                            
                            st.markdown(f"**Name:** {selected_candidate['name']}")
                            
                            if "skills" in selected_candidate and selected_candidate["skills"]:
                                st.markdown("**Skills:** " + ", ".join(selected_candidate["skills"][:5]))
                            
                            st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.warning("Candidate not found")
        else:
            st.info("Please select a candidate from the list")

def render_matching_page():
    """Render the matching page."""
    st.title("Candidate Matching")
    
    # Initialize matching agent
    matching_agent = MatchingAgent()
    
    # Get jobs
    conn = get_db_connection()
    jobs = conn.execute("SELECT id, title FROM jobs").fetchall()
    
    if not jobs:
        st.warning("No jobs found. Please add jobs first.")
        conn.close()
        return
    
    # Job selection - use the job_to_match from session state if available
    job_options = [f"{job['id']} - {job['title']}" for job in jobs]
    
    # Find the index of the job_to_match in job_options if it exists
    default_index = 0
    if 'job_to_match' in st.session_state and st.session_state.job_to_match:
        for i, option in enumerate(job_options):
            job_id = int(option.split(" - ")[0])
            if job_id == st.session_state.job_to_match:
                default_index = i
                break
    
    selected_job = st.selectbox(
        "Select Job", 
        options=job_options,
        index=default_index
    )
    job_id = int(selected_job.split(" - ")[0])
    
    # Clear the job_to_match after using it
    st.session_state.job_to_match = None
    
    # Show job details
    job = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    
    if job:
        with st.expander("Job Details", expanded=False):
            st.subheader(job["title"])
            st.write("**Description:**")
            st.write(job["description"])
            
            # Display required skills
            st.write("**Required Skills:**")
            if job["required_skills"]:
                skills = job["required_skills"]
                if isinstance(skills, str):
                    try:
                        skills = json.loads(skills)
                    except:
                        skills = []
                st.write(", ".join(skills) if skills else "None specified")
            else:
                st.write("None specified")
            
            # Display required experience
            st.write("**Required Experience:**")
            st.write(job["required_experience"] if job["required_experience"] else "Not specified")
            
            # Display required education
            st.write("**Required Education:**")
            st.write(job["required_education"] if job["required_education"] else "Not specified")
    
    # Run the matching algorithm
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("Run Matching Algorithm"):
            with st.spinner("Matching candidates to job..."):
                create_matches(job_id)
                # After creating matches, refresh the page to show results
                st.rerun()
    
    # Check if we have matches for this job
    matches = get_matches(job_id)
    
    if matches:
        # Display matches
        st.subheader("Match Results")
        
        # Show total number of candidates matched
        st.write(f"Found {len(matches)} candidate matches")
        
        # Show the number of auto-shortlisted candidates
        auto_shortlisted = sum(1 for match in matches if match["is_shortlisted"])
        if auto_shortlisted > 0:
            st.info(f"{auto_shortlisted} candidates were automatically shortlisted (score > 59%).")
        
        # Create tabs for all matches and shortlisted
        tab1, tab2 = st.tabs(["All Candidates", "Shortlisted"])
        
        with tab1:
            # All candidates table
            match_data = []
            for match in matches:
                # Get candidate
                candidate = conn.execute("SELECT name FROM candidates WHERE id = ?", 
                                        (match["candidate_id"],)).fetchone()
                match_data.append({
                    "ID": match["id"],
                    "Candidate": candidate["name"],
                    "Match Score": f"{match['match_score']:.1f}%",
                    "Skills": f"{match['skills_score']:.1f}%",
                    "Experience": f"{match['experience_score']:.1f}%",
                    "Education": f"{match['education_score']:.1f}%",
                    "Shortlisted": "✓" if match["is_shortlisted"] else "✗"
                })
            
            # Create DataFrame
            df = pd.DataFrame(match_data)
            
            # Display table with formatting
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Add checkboxes to shortlist/un-shortlist
            st.subheader("Update Shortlist Status")
            
            cols = st.columns(3)
            with cols[0]:
                match_id = st.number_input("Match ID", min_value=1, step=1)
            with cols[1]:
                is_shortlisted = st.checkbox("Shortlisted")
            with cols[2]:
                if st.button("Update"):
                    update_shortlist(match_id, is_shortlisted)
                    st.success(f"Updated match {match_id}")
                    # Rerun to refresh
                    st.rerun()
        
        with tab2:
            # Get shortlisted candidates
            shortlisted = get_shortlisted(job_id)
            
            if shortlisted:
                shortlisted_data = []
                for match in shortlisted:
                    # Get candidate
                    candidate = conn.execute("SELECT name FROM candidates WHERE id = ?", 
                                           (match["candidate_id"],)).fetchone()
                    shortlisted_data.append({
                        "ID": match["id"],
                        "Candidate": candidate["name"],
                        "Match Score": f"{match['match_score']:.1f}%",
                        "Skills": f"{match['skills_score']:.1f}%",
                        "Experience": f"{match['experience_score']:.1f}%",
                        "Education": f"{match['education_score']:.1f}%"
                    })
                
                # Create DataFrame
                df_shortlisted = pd.DataFrame(shortlisted_data)
                
                # Display table
                st.dataframe(df_shortlisted, use_container_width=True, hide_index=True)
                
                # Navigate to interviews
                if st.button("Schedule Interviews"):
                    # Set the job ID for interview scheduling
                    st.session_state.scheduling_job_id = job_id
                    st.session_state.page = "interviews"
                    st.rerun()
            else:
                st.info("No candidates have been shortlisted yet.")
    
    # Clear match button
    if matches and st.button("Clear Matches"):
        conn.execute("DELETE FROM matches WHERE job_id = ?", (job_id,))
        conn.commit()
        st.success("Matches cleared")
        st.rerun()
    
    conn.close()

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
        
        # Fetch candidate names for display
        conn = get_db_connection()
        for match in shortlisted:
            candidate = conn.execute(
                "SELECT name FROM candidates WHERE id = ?", 
                (match["candidate_id"],)
            ).fetchone()
            match["candidate_name"] = candidate["name"] if candidate else f"Candidate {match['candidate_id']}"
        conn.close()
        
        # Create interview scheduling form
        with st.form("interview_form"):
            st.write("### Interview Details")
            
            # Select candidates
            candidates = st.multiselect(
                "Select candidates to interview",
                options=[match["id"] for match in shortlisted],
                format_func=lambda x: next((f"{match['candidate_name']} ({match['match_score']:.1f}%)" 
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
            
            st.dataframe(interview_df, use_container_width=True, hide_index=True)
            
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
                    st.text_area("Email Content", email, height=300, key="email-content")
                    
                    # Add copy button for the email content
                    st.markdown("""
                    <div>
                        <button onclick="navigator.clipboard.writeText(document.getElementById('root').querySelector('textarea').value)">
                            Copy Email
                        </button>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No interviews scheduled yet")
            
            # Go to scheduling
            if st.button("Schedule New Interviews"):
                # Redirect to matching page
                st.session_state.page = "matching"
                st.rerun()

# Run the application
if __name__ == "__main__":
    main() 