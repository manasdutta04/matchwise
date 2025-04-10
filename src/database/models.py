"""
Database models for the job matching system.
These models define the structure of our database tables.
"""

from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .db import Base


class JobDescription(Base):
    """
    Model for storing job descriptions.
    """
    __tablename__ = "job_descriptions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), index=True)
    description = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Parsed details
    required_skills = Column(Text)
    required_experience = Column(Text)
    required_education = Column(Text)
    job_responsibilities = Column(Text)
    embedding = Column(Text)  # JSON string of embedding vector
    
    # Relationships
    matches = relationship("Match", back_populates="job")


class Candidate(Base):
    """
    Model for storing candidate information.
    """
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    cv_filename = Column(String(255), unique=True, index=True)
    full_text = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Parsed details
    name = Column(String(255))
    email = Column(String(255))
    phone = Column(String(50))
    skills = Column(Text)
    experience = Column(Text)
    education = Column(Text)
    certifications = Column(Text)
    embedding = Column(Text)  # JSON string of embedding vector
    
    # Relationships
    matches = relationship("Match", back_populates="candidate")


class Match(Base):
    """
    Model for storing job-candidate matches and scores.
    """
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("job_descriptions.id"))
    candidate_id = Column(Integer, ForeignKey("candidates.id"))
    match_score = Column(Float)
    skills_score = Column(Float)
    experience_score = Column(Float)
    education_score = Column(Float)
    shortlisted = Column(Boolean, default=False)
    interview_scheduled = Column(Boolean, default=False)
    interview_date = Column(DateTime, nullable=True)
    interview_details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    job = relationship("JobDescription", back_populates="matches")
    candidate = relationship("Candidate", back_populates="matches")


class InterviewSchedule(Base):
    """
    Model for storing interview schedules.
    """
    __tablename__ = "interview_schedules"

    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id"))
    scheduled_date = Column(DateTime)
    email_sent = Column(Boolean, default=False)
    email_content = Column(Text)
    status = Column(String(50), default="pending")  # pending, confirmed, rejected, completed
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now()) 