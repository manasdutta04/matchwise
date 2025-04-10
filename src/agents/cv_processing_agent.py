"""
CV Processing Agent module.
This agent extracts key data from CVs, such as education, work experience, skills, and other relevant information.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class CVProcessingAgent:
    """
    Agent for processing and extracting information from CVs.
    """
    
    def __init__(self, pdf_parser=None, text_processor=None, embedding_processor=None, llm_client=None):
        """
        Initialize the CV processing agent.
        
        Args:
            pdf_parser: Parser for extracting text from PDF files
            text_processor: Processor for analyzing CV text
            embedding_processor: Processor for generating embeddings
            llm_client: Client for LLM interactions
        """
        self.pdf_parser = pdf_parser
        self.text_processor = text_processor
        self.embedding_processor = embedding_processor
        self.llm_client = llm_client
    
    def process_cv(self, cv_path: str) -> Dict[str, Any]:
        """
        Process a CV file to extract key information.
        
        Args:
            cv_path: Path to the CV file
            
        Returns:
            Dictionary with structured CV information
        """
        logger.info(f"Processing CV: {cv_path}")
        cv_filename = Path(cv_path).name
        
        # Extract text from CV
        cv_text = ""
        if self.pdf_parser:
            cv_text = self.pdf_parser.extract_text_from_pdf(cv_path)
        
        if not cv_text:
            logger.error(f"Failed to extract text from CV: {cv_path}")
            return {"cv_filename": cv_filename, "error": "Failed to extract text"}
        
        # Process CV text
        cv_data = {}
        if self.text_processor:
            cv_data = self.text_processor.analyze_cv(cv_text)
        else:
            # Basic fallback if no text processor
            cv_data = {
                "cv_filename": cv_filename,
                "full_text": cv_text,
                "contact_info": {},
                "skills": [],
                "education": [],
                "experience": []
            }
        
        # Add CV filename
        cv_data["cv_filename"] = cv_filename
        
        # Generate embedding if processor available
        if self.embedding_processor:
            try:
                embedding = self.embedding_processor.embed_cv(cv_data)
                cv_data["embedding"] = embedding
            except Exception as e:
                logger.error(f"Error generating embedding for CV: {e}")
        
        return cv_data
    
    def process_cv_with_llm(self, cv_path: str) -> Dict[str, Any]:
        """
        Process a CV using LLM for enhanced extraction.
        
        Args:
            cv_path: Path to the CV file
            
        Returns:
            Dictionary with structured CV information
        """
        if not self.llm_client:
            logger.warning("LLM client not available, falling back to basic processing")
            return self.process_cv(cv_path)
        
        # First extract text from CV
        cv_text = ""
        cv_filename = Path(cv_path).name
        
        if self.pdf_parser:
            cv_text = self.pdf_parser.extract_text_from_pdf(cv_path)
        
        if not cv_text:
            logger.error(f"Failed to extract text from CV: {cv_path}")
            return {"cv_filename": cv_filename, "error": "Failed to extract text"}
        
        try:
            # Extract contact information first
            contact_info = {}
            if self.text_processor:
                contact_info = self.text_processor.extract_contact_info(cv_text)
            
            # Create LLM prompt for detailed extraction
            prompt = f"""
            You are an expert at analyzing resumes/CVs. Extract the following information from this CV text:
            
            1. Technical skills and technologies
            2. Education details (degree, institution, year)
            3. Work experience (title, company, duration, description)
            
            Format your response as a JSON object with these keys:
            - skills: array of strings (technical skills only)
            - education: array of objects with "degree", "institution", and "year" fields
            - experience: array of objects with "title", "company", "duration", and "description" fields
            
            CV Text:
            {cv_text}
            """
            
            response = self.llm_client.complete(prompt)
            
            try:
                # Parse LLM response as JSON
                parsed_data = json.loads(response)
                
                # Add contact info and original text
                parsed_data["contact_info"] = contact_info
                parsed_data["full_text"] = cv_text
                parsed_data["cv_filename"] = cv_filename
                
                # Generate embedding if processor available
                if self.embedding_processor:
                    try:
                        embedding = self.embedding_processor.embed_cv(parsed_data)
                        parsed_data["embedding"] = embedding
                    except Exception as e:
                        logger.error(f"Error generating embedding for CV: {e}")
                
                return parsed_data
            except json.JSONDecodeError:
                logger.error("Failed to parse LLM response as JSON")
                # Fall back to basic processing with text processor
                if self.text_processor:
                    cv_data = self.text_processor.analyze_cv(cv_text)
                    cv_data["cv_filename"] = cv_filename
                    return cv_data
                else:
                    return {
                        "cv_filename": cv_filename,
                        "full_text": cv_text,
                        "contact_info": contact_info,
                        "skills": [],
                        "education": [],
                        "experience": []
                    }
                
        except Exception as e:
            logger.error(f"Error using LLM for CV processing: {e}")
            # Fall back to basic processing
            return self.process_cv(cv_path)
    
    def batch_process_directory(self, directory_path: str) -> Dict[str, Dict[str, Any]]:
        """
        Process all CVs in a directory.
        
        Args:
            directory_path: Path to directory containing CV files
            
        Returns:
            Dictionary mapping filenames to structured CV data
        """
        results = {}
        directory = Path(directory_path)
        
        # Process each PDF file
        for pdf_file in directory.glob("*.pdf"):
            filename = pdf_file.name
            logger.info(f"Processing {filename}...")
            
            # Process CV with LLM if available, otherwise use basic processing
            if self.llm_client:
                cv_data = self.process_cv_with_llm(str(pdf_file))
            else:
                cv_data = self.process_cv(str(pdf_file))
            
            results[filename] = cv_data
        
        logger.info(f"Processed {len(results)} CVs")
        return results
    
    def summarize_cv(self, cv_data: Dict[str, Any]) -> str:
        """
        Generate a human-readable summary of the CV.
        
        Args:
            cv_data: Dictionary with structured CV information
            
        Returns:
            String with a human-readable CV summary
        """
        contact_info = cv_data.get("contact_info", {})
        skills = cv_data.get("skills", [])
        education = cv_data.get("education", [])
        experience = cv_data.get("experience", [])
        
        name = contact_info.get("name", "Unknown Candidate")
        
        summary = f"CV Summary: {name}\n\n"
        
        # Add contact information
        summary += "Contact Information:\n"
        for key, value in contact_info.items():
            if value and key != "name":  # Skip name as it's already in the title
                summary += f"- {key.title()}: {value}\n"
        summary += "\n"
        
        # Add skills section
        if skills:
            summary += "Skills:\n"
            for skill in skills[:10]:  # Limit to top 10 for conciseness
                summary += f"- {skill}\n"
            if len(skills) > 10:
                summary += f"- ...and {len(skills) - 10} more\n"
            summary += "\n"
        
        # Add education section
        if education:
            summary += "Education:\n"
            for edu in education:
                degree = edu.get("degree", "")
                institution = edu.get("institution", "")
                year = edu.get("year", "")
                
                edu_str = ""
                if degree:
                    edu_str += degree
                if institution:
                    edu_str += f" from {institution}"
                if year:
                    edu_str += f" ({year})"
                
                summary += f"- {edu_str}\n"
            summary += "\n"
        
        # Add experience section
        if experience:
            summary += "Experience:\n"
            for exp in experience:
                title = exp.get("title", "")
                company = exp.get("company", "")
                duration = exp.get("duration", "")
                description = exp.get("description", "")
                
                exp_str = ""
                if title:
                    exp_str += title
                if company:
                    exp_str += f" at {company}"
                if duration:
                    exp_str += f" ({duration})"
                
                summary += f"- {exp_str}\n"
                if description:
                    # Include first 100 characters of description with ellipsis if needed
                    desc_summary = description[:100] + ("..." if len(description) > 100 else "")
                    summary += f"  {desc_summary}\n"
            summary += "\n"
        
        return summary


# For testing purposes
if __name__ == "__main__":
    # Import required modules for testing
    try:
        from ..utils.pdf_parser import PDFParser
        pdf_parser = PDFParser()
    except ImportError:
        # When running as a script, paths are different
        import sys
        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
        from utils.pdf_parser import PDFParser
        pdf_parser = PDFParser()
    
    # Create a mock LLM client for testing
    class MockLLMClient:
        def complete(self, prompt):
            # Return a mock response with CV data
            return """
            {
                "skills": ["Python", "JavaScript", "Machine Learning", "Data Analysis", "SQL", "AWS"],
                "education": [
                    {"degree": "MS in Computer Science", "institution": "Example University", "year": "2018-2020"},
                    {"degree": "BS in Mathematics", "institution": "Another University", "year": "2014-2018"}
                ],
                "experience": [
                    {
                        "title": "Senior Data Scientist",
                        "company": "Example Corp",
                        "duration": "2020-present",
                        "description": "Developed machine learning models for predictive analytics and customer segmentation."
                    },
                    {
                        "title": "Software Engineer",
                        "company": "Tech Startup",
                        "duration": "2018-2020",
                        "description": "Built web applications using React and Node.js. Implemented database solutions with PostgreSQL."
                    }
                ]
            }
            """
    
    # Create an agent instance with mock components
    agent = CVProcessingAgent(pdf_parser=pdf_parser, llm_client=MockLLMClient())
    
    # Test with a CV file if available
    test_file = "AI-Powered Job Application Screening System/CVs1/C9945.pdf"
    if os.path.exists(test_file):
        cv_data = agent.process_cv_with_llm(test_file)
        
        # Generate summary
        summary = agent.summarize_cv(cv_data)
        
        # Print results
        print("CV Data:")
        print(json.dumps({k: v for k, v in cv_data.items() if k != "full_text"}, indent=2))  # Exclude full text for brevity
        print("\nCV Summary:")
        print(summary)
    else:
        print(f"Test file not found: {test_file}") 