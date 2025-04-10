"""
API routes for the job matching system.
Provides RESTful endpoints for managing jobs, candidates, and matches.
"""

import os
import json
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import date

# Import database models and connection utilities
from ..database.db import get_db
from ..database.models import JobDescription, Candidate, Match, InterviewSchedule

# Import agent modules for processing
from ..agents.job_description_agent import JobDescriptionAgent
from ..agents.cv_processing_agent import CVProcessingAgent
from ..agents.matching_agent import MatchingAgent
from ..agents.scheduler_agent import SchedulerAgent

# Import utilities
from ..utils.pdf_parser import PDFParser
from ..utils.text_processor import TextProcessor

# Import models for embeddings and scoring
from ..models.embedding import EmbeddingProcessor
from ..models.scoring import MatchScorer

# Create router
from fastapi import APIRouter
router = APIRouter()

# Initialize components
pdf_parser = PDFParser()
text_processor = TextProcessor()
embedding_processor = EmbeddingProcessor()
match_scorer = MatchScorer(embedding_processor=embedding_processor)

# Initialize agents
job_agent = JobDescriptionAgent(text_processor=text_processor, embedding_processor=embedding_processor)
cv_agent = CVProcessingAgent(pdf_parser=pdf_parser, text_processor=text_processor, embedding_processor=embedding_processor)
matching_agent = MatchingAgent(scorer=match_scorer)
scheduler_agent = SchedulerAgent()


# Data Models for API
class JobDescriptionCreate(BaseModel):
    title: str
    description: str


class JobDescriptionResponse(BaseModel):
    id: int
    title: str
    required_skills: Optional[str] = None
    required_experience: Optional[str] = None
    required_education: Optional[str] = None


class CandidateResponse(BaseModel):
    id: int
    cv_filename: str
    name: Optional[str] = None
    email: Optional[str] = None
    skills: Optional[str] = None


class MatchResponse(BaseModel):
    id: int
    job_id: int
    candidate_id: int
    match_score: float
    skills_score: Optional[float] = None
    experience_score: Optional[float] = None
    education_score: Optional[float] = None
    is_shortlisted: bool


class InterviewScheduleCreate(BaseModel):
    interview_date: date
    interview_slots: List[str]
    interview_formats: List[str]


class InterviewScheduleResponse(BaseModel):
    id: int
    match_id: int
    scheduled_date: date
    status: str
    email_sent: bool


# API Routes
@router.get("/", response_model=Dict[str, str])
async def root():
    """API root endpoint."""
    return {"message": "Welcome to the Job Matching API"}


# Job Description Routes
@router.post("/jobs", response_model=JobDescriptionResponse)
async def create_job(job_data: JobDescriptionCreate, db: Session = Depends(get_db)):
    """Create a new job description."""
    
    # Process job description using the job agent
    processed_job = job_agent.process_job_description(job_data.title, job_data.description)
    
    # Create database record
    db_job = JobDescription(
        title=processed_job["title"],
        description=processed_job["description"],
        required_skills=json.dumps(processed_job.get("required_skills", [])),
        required_experience=processed_job.get("required_experience", ""),
        required_education=processed_job.get("required_education", ""),
        job_responsibilities=json.dumps(processed_job.get("responsibilities", [])),
        embedding=processed_job.get("embedding", "")
    )
    
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    
    return db_job


@router.get("/jobs", response_model=List[JobDescriptionResponse])
async def get_jobs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all job descriptions."""
    jobs = db.query(JobDescription).offset(skip).limit(limit).all()
    return jobs


@router.get("/jobs/{job_id}", response_model=JobDescriptionResponse)
async def get_job(job_id: int, db: Session = Depends(get_db)):
    """Get a specific job description."""
    job = db.query(JobDescription).filter(JobDescription.id == job_id).first()
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


# Candidate Routes
@router.post("/candidates", response_model=CandidateResponse)
async def create_candidate(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload and process a new candidate CV."""
    # Save uploaded file temporarily
    temp_file_path = f"temp_{file.filename}"
    try:
        with open(temp_file_path, "wb") as buffer:
            buffer.write(await file.read())
        
        # Process CV using the CV agent
        processed_cv = cv_agent.process_cv(temp_file_path)
        
        # Extract key information
        contact_info = processed_cv.get("contact_info", {})
        
        # Create database record
        db_candidate = Candidate(
            cv_filename=processed_cv["cv_filename"],
            full_text=processed_cv.get("full_text", ""),
            name=contact_info.get("name", ""),
            email=contact_info.get("email", ""),
            phone=contact_info.get("phone", ""),
            skills=json.dumps(processed_cv.get("skills", [])),
            experience=json.dumps(processed_cv.get("experience", [])),
            education=json.dumps(processed_cv.get("education", [])),
            embedding=processed_cv.get("embedding", "")
        )
        
        db.add(db_candidate)
        db.commit()
        db.refresh(db_candidate)
        
        return db_candidate
        
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)


@router.get("/candidates", response_model=List[CandidateResponse])
async def get_candidates(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all candidates."""
    candidates = db.query(Candidate).offset(skip).limit(limit).all()
    return candidates


@router.get("/candidates/{candidate_id}", response_model=CandidateResponse)
async def get_candidate(candidate_id: int, db: Session = Depends(get_db)):
    """Get a specific candidate."""
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if candidate is None:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidate


# Matching Routes
@router.post("/matches/{job_id}", response_model=List[MatchResponse])
async def create_matches(job_id: int, candidate_ids: List[int] = Query(None), db: Session = Depends(get_db)):
    """Create matches between a job and candidates."""
    # Get job data
    job = db.query(JobDescription).filter(JobDescription.id == job_id).first()
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Prepare job data for matching
    job_data = {
        "id": job.id,
        "title": job.title,
        "description": job.description,
        "required_skills": json.loads(job.required_skills) if job.required_skills else [],
        "required_experience": job.required_experience,
        "required_education": job.required_education, 
        "responsibilities": json.loads(job.job_responsibilities) if job.job_responsibilities else [],
        "embedding": job.embedding
    }
    
    # Get candidates
    query = db.query(Candidate)
    if candidate_ids:
        query = query.filter(Candidate.id.in_(candidate_ids))
    candidates = query.all()
    
    if not candidates:
        raise HTTPException(status_code=404, detail="No candidates found")
    
    # Create matches
    matches = []
    for candidate in candidates:
        # Prepare candidate data for matching
        candidate_data = {
            "id": candidate.id,
            "cv_filename": candidate.cv_filename,
            "contact_info": {
                "name": candidate.name,
                "email": candidate.email,
                "phone": candidate.phone
            },
            "skills": json.loads(candidate.skills) if candidate.skills else [],
            "experience": json.loads(candidate.experience) if candidate.experience else [],
            "education": json.loads(candidate.education) if candidate.education else [],
            "embedding": candidate.embedding
        }
        
        # Match candidate to job
        match_result = matching_agent.match_candidate_to_job(job_data, candidate_data)
        
        # Save match to database
        db_match = Match(
            job_id=job.id,
            candidate_id=candidate.id,
            match_score=match_result.get("total_score", 0),
            skills_score=match_result.get("skills_match", {}).get("score", 0),
            experience_score=match_result.get("experience_match", {}).get("score", 0),
            education_score=match_result.get("education_match", {}).get("score", 0),
            shortlisted=match_result.get("is_shortlisted", False)
        )
        
        db.add(db_match)
        matches.append(db_match)
    
    db.commit()
    
    # Refresh to get IDs
    for match in matches:
        db.refresh(match)
    
    return matches


@router.get("/matches/{job_id}", response_model=List[MatchResponse])
async def get_matches(job_id: int, shortlisted_only: bool = False, db: Session = Depends(get_db)):
    """Get matches for a specific job."""
    query = db.query(Match).filter(Match.job_id == job_id)
    
    if shortlisted_only:
        query = query.filter(Match.shortlisted == True)
    
    matches = query.all()
    return matches


# Interview Scheduling Routes
@router.post("/interviews/{match_id}", response_model=InterviewScheduleResponse)
async def schedule_interview(
    match_id: int, 
    schedule_data: InterviewScheduleCreate, 
    db: Session = Depends(get_db)
):
    """Schedule an interview for a match."""
    # Get match data
    match = db.query(Match).filter(Match.id == match_id).first()
    if match is None:
        raise HTTPException(status_code=404, detail="Match not found")
    
    # Check if match is shortlisted
    if not match.shortlisted:
        raise HTTPException(status_code=400, detail="Cannot schedule interview for non-shortlisted candidate")
    
    # Get job and candidate data
    job = db.query(JobDescription).filter(JobDescription.id == match.job_id).first()
    candidate = db.query(Candidate).filter(Candidate.id == match.candidate_id).first()
    
    if job is None or candidate is None:
        raise HTTPException(status_code=404, detail="Job or candidate not found")
    
    # Prepare data for scheduler
    job_data = {
        "title": job.title,
        "required_skills": json.loads(job.required_skills) if job.required_skills else [],
        "required_experience": job.required_experience,
        "required_education": job.required_education
    }
    
    candidate_data = {
        "cv_filename": candidate.cv_filename,
        "contact_info": {
            "name": candidate.name,
            "email": candidate.email,
            "phone": candidate.phone
        }
    }
    
    match_data = {
        "id": match.id,
        "is_shortlisted": match.shortlisted,
        "total_score": match.match_score
    }
    
    # Schedule interview
    interview_details = scheduler_agent.schedule_interview(
        match_data, 
        candidate_data, 
        job_data,
        interview_date=schedule_data.interview_date,
        interview_slots=schedule_data.interview_slots,
        interview_formats=schedule_data.interview_formats
    )
    
    # Save to database
    db_interview = InterviewSchedule(
        match_id=match.id,
        scheduled_date=schedule_data.interview_date,
        email_sent=interview_details.get("email_sent", False),
        email_content=interview_details.get("email_content", ""),
        status="pending"
    )
    
    db.add(db_interview)
    db.commit()
    db.refresh(db_interview)
    
    # Update match with interview scheduled flag
    match.interview_scheduled = True
    match.interview_date = schedule_data.interview_date
    db.commit()
    
    return db_interview


@router.get("/interviews", response_model=List[InterviewScheduleResponse])
async def get_interviews(status: Optional[str] = None, db: Session = Depends(get_db)):
    """Get all interview schedules."""
    query = db.query(InterviewSchedule)
    
    if status:
        query = query.filter(InterviewSchedule.status == status)
    
    interviews = query.all()
    return interviews 