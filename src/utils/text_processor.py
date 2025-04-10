"""
Text processor module for parsing and analyzing CV and job description text.
Extracts key information from raw text using NLP techniques and LLM assistance.
"""

import re
import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TextProcessor:
    """Text processor for analyzing CVs and job descriptions."""
    
    def __init__(self, llm_client=None):
        """
        Initialize the text processor with an optional LLM client.
        
        Args:
            llm_client: An optional LLM client for advanced text analysis
        """
        self.llm_client = llm_client
    
    def extract_contact_info(self, text: str) -> Dict[str, str]:
        """
        Extract contact information from CV text.
        
        Args:
            text: Raw CV text
            
        Returns:
            Dictionary with name, email, phone, etc.
        """
        # Initialize results dictionary
        contact_info = {
            "name": "",
            "email": "",
            "phone": "",
            "linkedin": "",
            "location": ""
        }
        
        # Extract email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_matches = re.findall(email_pattern, text)
        if email_matches:
            contact_info["email"] = email_matches[0]
        
        # Extract phone number (various formats)
        phone_patterns = [
            r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',  # 123-456-7890
            r'\b\(\d{3}\)\s*\d{3}[-.\s]?\d{4}\b',  # (123) 456-7890
            r'\b\+\d{1,3}\s*\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b'  # +1 123-456-7890
        ]
        
        for pattern in phone_patterns:
            phone_matches = re.findall(pattern, text)
            if phone_matches:
                contact_info["phone"] = phone_matches[0]
                break
        
        # Extract LinkedIn URL
        linkedin_pattern = r'linkedin\.com/in/[A-Za-z0-9_-]+'
        linkedin_matches = re.findall(linkedin_pattern, text)
        if linkedin_matches:
            contact_info["linkedin"] = "https://www." + linkedin_matches[0]
        
        # If we have an LLM client, use it to extract name and location
        if self.llm_client:
            try:
                prompt = f"""
                Extract the person's full name and location from this CV text. 
                Only return a JSON object with "name" and "location" keys.
                
                CV text first few lines:
                {text[:500]}
                """
                llm_response = self.llm_client.complete(prompt)
                try:
                    llm_data = json.loads(llm_response)
                    if "name" in llm_data:
                        contact_info["name"] = llm_data["name"]
                    if "location" in llm_data:
                        contact_info["location"] = llm_data["location"]
                except Exception as e:
                    logger.error(f"Error parsing LLM response: {e}")
            except Exception as e:
                logger.error(f"Error calling LLM: {e}")
        
        return contact_info
    
    def extract_skills(self, text: str) -> List[str]:
        """
        Extract skills from CV text.
        
        Args:
            text: Raw CV text
            
        Returns:
            List of skills
        """
        # Common skills sections in CVs
        skill_section_patterns = [
            r'(?i)(?:technical\s+)?skills[\s:]+(.+?)(?:\n\n|\n[A-Z])',
            r'(?i)(?:core\s+)?competencies[\s:]+(.+?)(?:\n\n|\n[A-Z])',
            r'(?i)technologies[\s:]+(.+?)(?:\n\n|\n[A-Z])'
        ]
        
        skills = []
        
        # Try to find skills section
        for pattern in skill_section_patterns:
            matches = re.search(pattern, text, re.DOTALL)
            if matches:
                skills_text = matches.group(1)
                # Split by common delimiters
                for delimiter in [',', '•', '·', '|', '/', '\n']:
                    if delimiter in skills_text:
                        skills.extend([s.strip() for s in skills_text.split(delimiter) if s.strip()])
                        break
                if skills:
                    break
        
        # If no skills found with regular expressions and LLM client is available, try LLM
        if not skills and self.llm_client:
            try:
                prompt = f"""
                Extract a list of technical skills, technologies, programming languages, and tools from this CV.
                Return the result as a JSON array of strings, with each string being a single skill.
                
                CV text:
                {text}
                """
                llm_response = self.llm_client.complete(prompt)
                try:
                    skills = json.loads(llm_response)
                except Exception as e:
                    logger.error(f"Error parsing LLM response: {e}")
            except Exception as e:
                logger.error(f"Error calling LLM: {e}")
        
        # Remove duplicates and empty strings
        skills = list(set([s for s in skills if s]))
        
        return skills
    
    def extract_education(self, text: str) -> List[Dict[str, str]]:
        """
        Extract education information from CV text.
        
        Args:
            text: Raw CV text
            
        Returns:
            List of education entries (degree, institution, year)
        """
        education_entries = []
        
        # Look for education section
        education_section_pattern = r'(?i)education(?:al)?(?:\s+background)?[\s:]+(.+?)(?:\n\n\w|\n[A-Z]|$)'
        
        education_section = ""
        education_match = re.search(education_section_pattern, text, re.DOTALL)
        if education_match:
            education_section = education_match.group(1)
        
        # If we have an LLM client, use it to extract structured education info
        if self.llm_client:
            try:
                prompt = f"""
                Extract education information from this CV text. For each education entry, identify the degree, 
                institution, and years (if available).
                
                Return the result as a JSON array of objects, with each object having "degree", "institution", and "year" keys.
                
                Education section:
                {education_section if education_section else text}
                """
                llm_response = self.llm_client.complete(prompt)
                try:
                    education_entries = json.loads(llm_response)
                except Exception as e:
                    logger.error(f"Error parsing LLM response: {e}")
            except Exception as e:
                logger.error(f"Error calling LLM: {e}")
        
        return education_entries
    
    def extract_experience(self, text: str) -> List[Dict[str, str]]:
        """
        Extract work experience from CV text.
        
        Args:
            text: Raw CV text
            
        Returns:
            List of experience entries (title, company, duration, description)
        """
        experience_entries = []
        
        # Look for experience section
        experience_section_pattern = r'(?i)(?:work\s+)?experience[\s:]+(.+?)(?:\n\n\w|\n[A-Z]|$)'
        
        experience_section = ""
        experience_match = re.search(experience_section_pattern, text, re.DOTALL)
        if experience_match:
            experience_section = experience_match.group(1)
        
        # If we have an LLM client, use it to extract structured experience info
        if self.llm_client:
            try:
                prompt = f"""
                Extract work experience information from this CV text. For each position, identify the job title, 
                company name, duration/dates, and a brief description of responsibilities.
                
                Return the result as a JSON array of objects, with each object having "title", "company", 
                "duration", and "description" keys.
                
                Experience section:
                {experience_section if experience_section else text}
                """
                llm_response = self.llm_client.complete(prompt)
                try:
                    experience_entries = json.loads(llm_response)
                except Exception as e:
                    logger.error(f"Error parsing LLM response: {e}")
            except Exception as e:
                logger.error(f"Error calling LLM: {e}")
        
        return experience_entries
    
    def parse_job_description(self, job_text: str, job_title: str = "") -> Dict[str, Any]:
        """
        Parse a job description text into structured components.
        
        Args:
            job_text: The raw job description text
            job_title: Optional job title
            
        Returns:
            Dictionary with structured job information
        """
        # Initialize result dictionary
        job_info = {
            "title": job_title,
            "required_skills": [],
            "preferred_skills": [],
            "required_experience": "",
            "required_education": "",
            "responsibilities": []
        }
        
        # If we have an LLM client, use it to extract structured job info
        if self.llm_client:
            try:
                prompt = f"""
                Parse this job description into its key components.
                
                Return a JSON object with the following keys:
                - required_skills: an array of specific skills required for the job
                - preferred_skills: an array of skills that are preferred but not required
                - required_experience: a string describing the required years and type of experience
                - required_education: a string describing the educational requirements
                - responsibilities: an array of job responsibilities
                
                Job title: {job_title}
                
                Job description:
                {job_text}
                """
                llm_response = self.llm_client.complete(prompt)
                try:
                    parsed_info = json.loads(llm_response)
                    # Update job_info with parsed data
                    for key in parsed_info:
                        if key in job_info:
                            job_info[key] = parsed_info[key]
                except Exception as e:
                    logger.error(f"Error parsing LLM response: {e}")
            except Exception as e:
                logger.error(f"Error calling LLM: {e}")
        else:
            # Fallback to regex-based parsing if no LLM client
            # Extract skills
            skills_section = re.search(r'(?i)(?:technical requirements|skills|qualifications)[\s:]+(.+?)(?:\n\n|\n[A-Z]|$)', job_text, re.DOTALL)
            if skills_section:
                skills_text = skills_section.group(1)
                # Look for bullet points or list items
                skills = re.findall(r'(?:•|\*|\-|\d+\.)\s*([^•\*\-\d\.]+)', skills_text)
                if skills:
                    job_info["required_skills"] = [s.strip() for s in skills if s.strip()]
            
            # Extract responsibilities
            resp_section = re.search(r'(?i)(?:responsibilities|duties|role)[\s:]+(.+?)(?:\n\n|\n[A-Z]|$)', job_text, re.DOTALL)
            if resp_section:
                resp_text = resp_section.group(1)
                # Look for bullet points or list items
                responsibilities = re.findall(r'(?:•|\*|\-|\d+\.)\s*([^•\*\-\d\.]+)', resp_text)
                if responsibilities:
                    job_info["responsibilities"] = [r.strip() for r in responsibilities if r.strip()]
            
            # Extract education requirements
            edu_pattern = r'(?i)(?:education|degree)(?:al)?\s+requirements?[\s:]+([^•\*\-\d\.]+)'
            edu_match = re.search(edu_pattern, job_text)
            if edu_match:
                job_info["required_education"] = edu_match.group(1).strip()
            
            # Extract experience requirements
            exp_pattern = r'(?i)(?:experience)(?:al)?\s+requirements?[\s:]+([^•\*\-\d\.]+)'
            exp_match = re.search(exp_pattern, job_text)
            if exp_match:
                job_info["required_experience"] = exp_match.group(1).strip()
        
        return job_info
    
    def analyze_cv(self, cv_text: str) -> Dict[str, Any]:
        """
        Fully analyze a CV, extracting all relevant information.
        
        Args:
            cv_text: Raw CV text
            
        Returns:
            Dictionary with structured CV information
        """
        cv_info = {
            "contact_info": self.extract_contact_info(cv_text),
            "skills": self.extract_skills(cv_text),
            "education": self.extract_education(cv_text),
            "experience": self.extract_experience(cv_text),
            "full_text": cv_text
        }
        
        return cv_info


# For testing purposes
if __name__ == "__main__":
    # Mock LLM client for testing
    class MockLLMClient:
        def complete(self, prompt):
            # Simply return a mock JSON response
            if "skills" in prompt.lower():
                return '["Python", "JavaScript", "Machine Learning", "Data Analysis"]'
            elif "education" in prompt.lower():
                return '[{"degree": "BS in Computer Science", "institution": "Example University", "year": "2018"}]'
            elif "experience" in prompt.lower():
                return '[{"title": "Software Engineer", "company": "Example Corp", "duration": "2018-2020", "description": "Developed web applications"}]'
            elif "name" in prompt.lower():
                return '{"name": "John Doe", "location": "New York, NY"}'
            else:
                return '{}'
    
    # Create processor with mock LLM
    processor = TextProcessor(llm_client=MockLLMClient())
    
    # Test with sample text
    sample_text = """
    John Doe
    john.doe@example.com | (123) 456-7890 | linkedin.com/in/johndoe
    New York, NY
    
    SKILLS
    Python, JavaScript, React, Node.js, Machine Learning, AWS, Docker
    
    EDUCATION
    BS in Computer Science, Example University (2014-2018)
    
    EXPERIENCE
    Software Engineer, Example Corp (2018-2020)
    - Developed web applications using React and Node.js
    - Implemented machine learning algorithms for data analysis
    """
    
    # Analyze CV
    result = processor.analyze_cv(sample_text)
    print(json.dumps(result, indent=2)) 