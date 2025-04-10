"""
Job Description Agent module.
This agent reads and summarizes key elements from job descriptions.
"""

import json
import logging
from typing import Dict, List, Any, Optional

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class JobDescriptionAgent:
    """
    Agent for analyzing and summarizing job descriptions.
    """
    
    def __init__(self, llm_client=None, text_processor=None, embedding_processor=None):
        """
        Initialize the job description agent.
        
        Args:
            llm_client: Client for LLM interactions
            text_processor: Text processor for parsing job descriptions
            embedding_processor: Processor for generating embeddings
        """
        self.llm_client = llm_client
        self.text_processor = text_processor
        self.embedding_processor = embedding_processor
    
    def process_job_description(self, title: str, description: str) -> Dict[str, Any]:
        """
        Process a job description to extract key information.
        
        Args:
            title: Job title
            description: Full job description text
            
        Returns:
            Dictionary with structured job information
        """
        logger.info(f"Processing job description for: {title}")
        
        # Parse job description using text processor
        if self.text_processor:
            job_data = self.text_processor.parse_job_description(description, title)
        else:
            # Fallback to basic parsing if no text processor
            job_data = self._basic_parse_job_description(title, description)
        
        # Generate embedding if processor available
        if self.embedding_processor:
            try:
                embedding = self.embedding_processor.embed_job_description(job_data)
                job_data["embedding"] = embedding
            except Exception as e:
                logger.error(f"Error generating embedding for job description: {e}")
        
        return job_data
    
    def process_job_description_with_llm(self, title: str, description: str) -> Dict[str, Any]:
        """
        Process a job description using LLM for enhanced extraction.
        
        Args:
            title: Job title
            description: Full job description text
            
        Returns:
            Dictionary with structured job information
        """
        if not self.llm_client:
            logger.warning("LLM client not available, falling back to basic processing")
            return self.process_job_description(title, description)
        
        try:
            prompt = f"""
            You are an expert recruiter. Analyze this job description and extract the following information:
            
            1. Required skills (technical and soft skills)
            2. Required experience (years and type)
            3. Required education (degree level and field)
            4. Key responsibilities
            
            Format your response as a JSON object with these keys:
            - required_skills: array of strings
            - preferred_skills: array of strings
            - required_experience: string
            - required_education: string
            - responsibilities: array of strings
            
            Job Title: {title}
            
            Job Description:
            {description}
            """
            
            response = self.llm_client.complete(prompt)
            
            try:
                # Parse LLM response as JSON
                parsed_data = json.loads(response)
                
                # Add title and original description
                parsed_data["title"] = title
                parsed_data["description"] = description
                
                # Generate embedding if processor available
                if self.embedding_processor:
                    try:
                        embedding = self.embedding_processor.embed_job_description(parsed_data)
                        parsed_data["embedding"] = embedding
                    except Exception as e:
                        logger.error(f"Error generating embedding for job description: {e}")
                
                return parsed_data
            except json.JSONDecodeError:
                logger.error("Failed to parse LLM response as JSON")
                # Fall back to basic processing
                return self.process_job_description(title, description)
                
        except Exception as e:
            logger.error(f"Error using LLM for job description processing: {e}")
            return self.process_job_description(title, description)
    
    def summarize_job_description(self, job_data: Dict[str, Any]) -> str:
        """
        Generate a human-readable summary of the job.
        
        Args:
            job_data: Dictionary with structured job information
            
        Returns:
            String with a human-readable job summary
        """
        title = job_data.get("title", "Unknown Position")
        required_skills = job_data.get("required_skills", [])
        preferred_skills = job_data.get("preferred_skills", [])
        required_experience = job_data.get("required_experience", "")
        required_education = job_data.get("required_education", "")
        responsibilities = job_data.get("responsibilities", [])
        
        summary = f"Job Summary: {title}\n\n"
        
        # Add responsibilities section
        if responsibilities:
            summary += "Key Responsibilities:\n"
            for resp in responsibilities[:5]:  # Limit to top 5 for conciseness
                summary += f"- {resp}\n"
            summary += "\n"
        
        # Add required skills section
        if required_skills:
            summary += "Required Skills:\n"
            for skill in required_skills:
                summary += f"- {skill}\n"
            summary += "\n"
        
        # Add preferred skills section
        if preferred_skills:
            summary += "Preferred Skills:\n"
            for skill in preferred_skills:
                summary += f"- {skill}\n"
            summary += "\n"
        
        # Add required experience
        if required_experience:
            summary += f"Required Experience: {required_experience}\n\n"
        
        # Add required education
        if required_education:
            summary += f"Required Education: {required_education}\n\n"
        
        return summary
    
    def _basic_parse_job_description(self, title: str, description: str) -> Dict[str, Any]:
        """
        Basic job description parsing without advanced NLP.
        
        Args:
            title: Job title
            description: Full job description text
            
        Returns:
            Dictionary with basic structured job information
        """
        import re
        
        # Initialize result dictionary
        job_data = {
            "title": title,
            "description": description,
            "required_skills": [],
            "preferred_skills": [],
            "required_experience": "",
            "required_education": "",
            "responsibilities": []
        }
        
        # Extract required experience using regex patterns
        experience_patterns = [
            r'(?i)(\d+\+?\s*years?.*?experience.*?)[\.\n]',
            r'(?i)(experience.*?\d+\+?\s*years?)[\.\n]'
        ]
        
        for pattern in experience_patterns:
            match = re.search(pattern, description)
            if match:
                job_data["required_experience"] = match.group(1).strip()
                break
        
        # Extract education requirements
        education_patterns = [
            r'(?i)(Bachelor\'s|Master\'s|PhD|degree|diploma).*?(\w+\s+\w+|\w+)[\.\n]',
            r'(?i)(education|qualification).*?(degree|Bachelor|Master|PhD)[\.\n]'
        ]
        
        for pattern in education_patterns:
            match = re.search(pattern, description)
            if match:
                job_data["required_education"] = match.group(0).strip()
                break
        
        # Extract skills and responsibilities from bullet points or lists
        bullet_pattern = r'(?:•|\*|\-|\d+\.)\s*([^•\*\-\d\.]+)'
        bullet_items = re.findall(bullet_pattern, description)
        
        # Try to classify bullets as skills or responsibilities
        for item in bullet_items:
            item = item.strip()
            if not item:
                continue
                
            lower_item = item.lower()
            
            # Try to identify skills vs responsibilities
            if any(word in lower_item for word in ["ability to", "experience with", "knowledge of", "proficiency", "familiar with"]):
                skill = re.sub(r'(?i)ability to|experience with|knowledge of|proficiency in|familiar with', '', item).strip()
                job_data["required_skills"].append(skill)
            elif any(word in lower_item for word in ["develop", "design", "implement", "manage", "create", "build", "analyze", "oversee", "lead"]):
                job_data["responsibilities"].append(item)
            else:
                # Default to skill if uncertain
                job_data["required_skills"].append(item)
        
        return job_data


# For testing purposes
if __name__ == "__main__":
    # Create a mock LLM client for testing
    class MockLLMClient:
        def complete(self, prompt):
            # Return a mock response with job data
            return """
            {
                "required_skills": ["Python", "JavaScript", "Machine Learning", "Data Analysis", "Communication"],
                "preferred_skills": ["Docker", "AWS", "Kubernetes"],
                "required_experience": "5+ years of experience in software development",
                "required_education": "Bachelor's degree in Computer Science or related field",
                "responsibilities": [
                    "Develop and maintain machine learning models",
                    "Work with cross-functional teams to define requirements",
                    "Analyze large datasets to extract insights",
                    "Deploy models to production environments",
                    "Monitor model performance and make improvements"
                ]
            }
            """
    
    # Create an agent instance with mock LLM
    agent = JobDescriptionAgent(llm_client=MockLLMClient())
    
    # Test job description
    test_title = "Machine Learning Engineer"
    test_description = """
    We are looking for a skilled Machine Learning Engineer to develop, train, and deploy AI models for real-world applications. You will work with large datasets, optimize algorithms, and collaborate with cross-functional teams to drive innovation.

    Responsibilities:
    • Develop and optimize machine learning models for various applications.
    • Process and analyze large datasets to extract meaningful insights.
    • Deploy and maintain AI models in production environments.
    • Collaborate with data scientists, engineers, and product teams.
    • Stay updated with the latest advancements in AI and ML.

    Qualifications:
    • Bachelor's or Master's in Computer Science, Data Science, or a related field.
    • 5+ years of experience in software development and machine learning.
    • Proficiency in Python, TensorFlow, PyTorch, and Scikit-learn.
    • Experience with data preprocessing, model deployment, and cloud platforms.
    • Strong problem-solving skills and analytical mindset.
    
    Preferred Qualifications:
    • Experience with Docker and containerization technologies.
    • AWS or other cloud platform experience.
    • Kubernetes for container orchestration.
    """
    
    # Process job description with LLM
    job_data = agent.process_job_description_with_llm(test_title, test_description)
    
    # Generate summary
    summary = agent.summarize_job_description(job_data)
    
    # Print results
    print("Job Data:")
    print(json.dumps(job_data, indent=2))
    print("\nJob Summary:")
    print(summary) 