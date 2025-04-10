"""
Matching Agent module.
This agent compares candidate qualifications with job descriptions and calculates match scores.
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MatchingAgent:
    """
    Agent for matching candidates to job descriptions.
    """
    
    def __init__(self, scorer=None, llm_client=None, threshold=0.8):
        """
        Initialize the matching agent.
        
        Args:
            scorer: Scorer for calculating match scores
            llm_client: Client for LLM interactions
            threshold: Threshold score for shortlisting (0-1)
        """
        self.scorer = scorer
        self.llm_client = llm_client
        self.threshold = threshold
    
    def match_candidate_to_job(self, job_data: Dict[str, Any], candidate_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Match a candidate to a job and calculate a match score.
        
        Args:
            job_data: Dictionary with job description data
            candidate_data: Dictionary with candidate CV data
            
        Returns:
            Dictionary with match results
        """
        logger.info(f"Matching candidate {candidate_data.get('cv_filename', 'Unknown')} to job {job_data.get('title', 'Unknown')}")
        
        # Use scorer if available
        if self.scorer:
            match_results = self.scorer.score_match(job_data, candidate_data)
        else:
            # Basic fallback scoring if no scorer available
            match_results = self._basic_match_scoring(job_data, candidate_data)
        
        # Add identifiers for database storage
        match_results["job_title"] = job_data.get("title", "")
        match_results["candidate_filename"] = candidate_data.get("cv_filename", "")
        
        # Determine if candidate is shortlisted based on threshold
        match_results["is_shortlisted"] = match_results.get("total_score", 0) >= self.threshold
        
        return match_results
    
    def match_candidate_to_job_with_llm(self, job_data: Dict[str, Any], candidate_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Match a candidate to a job using LLM for enhanced matching.
        
        Args:
            job_data: Dictionary with job description data
            candidate_data: Dictionary with candidate CV data
            
        Returns:
            Dictionary with match results
        """
        if not self.llm_client:
            logger.warning("LLM client not available, falling back to basic matching")
            return self.match_candidate_to_job(job_data, candidate_data)
        
        try:
            # First use the scorer to get quantitative match data
            if self.scorer:
                match_results = self.scorer.score_match(job_data, candidate_data)
            else:
                match_results = self._basic_match_scoring(job_data, candidate_data)
            
            # Extract key information for LLM analysis
            job_title = job_data.get("title", "")
            required_skills = ", ".join(job_data.get("required_skills", []))
            job_responsibilities = ", ".join(job_data.get("responsibilities", []))
            required_experience = job_data.get("required_experience", "")
            required_education = job_data.get("required_education", "")
            
            # Candidate information
            candidate_skills = ", ".join(candidate_data.get("skills", []))
            candidate_experience = self._format_experience_for_llm(candidate_data.get("experience", []))
            candidate_education = self._format_education_for_llm(candidate_data.get("education", []))
            
            # Create LLM prompt for qualitative analysis
            prompt = f"""
            You are an expert recruiter evaluating a candidate for a job. Analyze the match between this job and candidate.
            
            JOB DETAILS:
            Title: {job_title}
            Required Skills: {required_skills}
            Responsibilities: {job_responsibilities}
            Required Experience: {required_experience}
            Required Education: {required_education}
            
            CANDIDATE DETAILS:
            Skills: {candidate_skills}
            Experience: {candidate_experience}
            Education: {candidate_education}
            
            Provide a detailed analysis of this match with specific strengths and gaps. Format your response as a JSON object with these keys:
            - strengths: array of strings (specific strengths of the candidate for this role)
            - gaps: array of strings (specific areas where the candidate doesn't meet requirements)
            - match_explanation: string (overall assessment of the match in 2-3 sentences)
            - recommendation: string (either "Highly Recommend", "Recommend", "Consider" or "Not Recommended")
            """
            
            response = self.llm_client.complete(prompt)
            
            try:
                # Parse LLM response as JSON
                parsed_analysis = json.loads(response)
                
                # Combine quantitative scores with qualitative analysis
                match_results.update({
                    "strengths": parsed_analysis.get("strengths", []),
                    "gaps": parsed_analysis.get("gaps", []),
                    "match_explanation": parsed_analysis.get("match_explanation", ""),
                    "recommendation": parsed_analysis.get("recommendation", "")
                })
                
                # Override shortlist decision based on recommendation if needed
                recommendation = parsed_analysis.get("recommendation", "")
                if recommendation in ["Highly Recommend", "Recommend"]:
                    match_results["is_shortlisted"] = True
                elif recommendation == "Not Recommended":
                    match_results["is_shortlisted"] = False
                # For "Consider", keep the threshold-based decision
                
            except json.JSONDecodeError:
                logger.error("Failed to parse LLM response as JSON")
                # Continue with just the quantitative scores
            
            # Add identifiers
            match_results["job_title"] = job_title
            match_results["candidate_filename"] = candidate_data.get("cv_filename", "")
            
            return match_results
                
        except Exception as e:
            logger.error(f"Error using LLM for candidate matching: {e}")
            return self.match_candidate_to_job(job_data, candidate_data)
    
    def batch_match_candidates(self, job_data: Dict[str, Any], candidates_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Match multiple candidates to a job description.
        
        Args:
            job_data: Dictionary with job description data
            candidates_data: List of dictionaries with candidate CV data
            
        Returns:
            List of dictionaries with match results, sorted by match score
        """
        results = []
        
        for candidate_data in candidates_data:
            # Use LLM matching if available, otherwise use basic matching
            if self.llm_client:
                match_result = self.match_candidate_to_job_with_llm(job_data, candidate_data)
            else:
                match_result = self.match_candidate_to_job(job_data, candidate_data)
            
            results.append(match_result)
        
        # Sort results by total score in descending order
        results.sort(key=lambda x: x.get("total_score", 0), reverse=True)
        
        return results
    
    def get_shortlisted_candidates(self, match_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter the match results to get shortlisted candidates.
        
        Args:
            match_results: List of dictionaries with match results
            
        Returns:
            List of dictionaries for shortlisted candidates only
        """
        return [result for result in match_results if result.get("is_shortlisted", False)]
    
    def generate_match_report(self, match_result: Dict[str, Any]) -> str:
        """
        Generate a human-readable report of the match.
        
        Args:
            match_result: Dictionary with match results
            
        Returns:
            String with a human-readable match report
        """
        job_title = match_result.get("job_title", "Unknown Position")
        candidate = match_result.get("candidate_filename", "Unknown Candidate")
        total_score = match_result.get("total_score", 0)
        is_shortlisted = match_result.get("is_shortlisted", False)
        
        # Format scores as percentages
        total_score_pct = f"{total_score * 100:.1f}%"
        
        # Get component scores if available
        skills_score = match_result.get("skills_match", {}).get("score", 0)
        skills_score_pct = f"{skills_score * 100:.1f}%"
        
        experience_score = match_result.get("experience_match", {}).get("score", 0)
        experience_score_pct = f"{experience_score * 100:.1f}%"
        
        education_score = match_result.get("education_match", {}).get("score", 0)
        education_score_pct = f"{education_score * 100:.1f}%"
        
        # Get qualitative analysis if available
        strengths = match_result.get("strengths", [])
        gaps = match_result.get("gaps", [])
        recommendation = match_result.get("recommendation", "")
        match_explanation = match_result.get("match_explanation", "")
        
        # Build the report
        report = f"Match Report: {candidate} for {job_title}\n\n"
        
        # Overall result
        report += f"Overall Match Score: {total_score_pct}\n"
        report += f"Shortlisted: {'Yes' if is_shortlisted else 'No'}\n"
        if recommendation:
            report += f"Recommendation: {recommendation}\n"
        report += "\n"
        
        # Component scores
        report += "Component Scores:\n"
        report += f"- Skills Match: {skills_score_pct}\n"
        report += f"- Experience Match: {experience_score_pct}\n"
        report += f"- Education Match: {education_score_pct}\n\n"
        
        # Qualitative analysis
        if match_explanation:
            report += f"Match Analysis: {match_explanation}\n\n"
        
        if strengths:
            report += "Strengths:\n"
            for strength in strengths:
                report += f"- {strength}\n"
            report += "\n"
        
        if gaps:
            report += "Improvement Areas:\n"
            for gap in gaps:
                report += f"- {gap}\n"
            report += "\n"
        
        # Skills details
        skills_details = match_result.get("skills_match", {}).get("details", {})
        if skills_details:
            exact_matches = skills_details.get("exact_matches", [])
            similar_matches = skills_details.get("similar_matches", {})
            missing_skills = skills_details.get("missing_skills", [])
            
            if exact_matches:
                report += "Matched Skills:\n"
                for skill in exact_matches:
                    report += f"- {skill}\n"
                report += "\n"
            
            if similar_matches:
                report += "Similar Skills:\n"
                for req_skill, matched_skill in similar_matches.items():
                    report += f"- {req_skill} (matched to {matched_skill})\n"
                report += "\n"
            
            if missing_skills:
                report += "Missing Skills:\n"
                for skill in missing_skills:
                    report += f"- {skill}\n"
                report += "\n"
        
        return report
    
    def _basic_match_scoring(self, job_data: Dict[str, Any], candidate_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Basic matching algorithm when no scorer is available.
        
        Args:
            job_data: Dictionary with job description data
            candidate_data: Dictionary with candidate CV data
            
        Returns:
            Dictionary with basic match results
        """
        # Initialize result
        match_result = {
            "total_score": 0.0,
            "skills_match": {"score": 0.0, "details": {}},
            "experience_match": {"score": 0.0, "details": {}},
            "education_match": {"score": 0.0, "details": {}}
        }
        
        # Basic skills matching
        required_skills = [s.lower() for s in job_data.get("required_skills", [])]
        candidate_skills = [s.lower() for s in candidate_data.get("skills", [])]
        
        matched_skills = [s for s in required_skills if s in candidate_skills]
        skills_score = len(matched_skills) / len(required_skills) if required_skills else 0.0
        
        match_result["skills_match"] = {
            "score": skills_score,
            "details": {
                "exact_matches": matched_skills,
                "missing_skills": [s for s in required_skills if s not in candidate_skills],
                "match_percentage": skills_score
            }
        }
        
        # Basic experience matching (assumption-based)
        experience_score = 0.5  # Default middle score without detailed analysis
        match_result["experience_match"] = {
            "score": experience_score,
            "details": {"match_explanation": "Basic matching used without detailed analysis"}
        }
        
        # Basic education matching (assumption-based)
        education_score = 0.5  # Default middle score without detailed analysis
        match_result["education_match"] = {
            "score": education_score,
            "details": {"match_explanation": "Basic matching used without detailed analysis"}
        }
        
        # Calculate total score (simplified weighting)
        match_result["total_score"] = (
            0.5 * skills_score +
            0.3 * experience_score +
            0.2 * education_score
        )
        
        return match_result
    
    def _format_experience_for_llm(self, experience: List[Dict[str, str]]) -> str:
        """Format experience data for LLM prompt."""
        if not experience:
            return "No experience data available"
        
        result = ""
        for exp in experience:
            title = exp.get("title", "")
            company = exp.get("company", "")
            duration = exp.get("duration", "")
            description = exp.get("description", "")
            
            result += f"{title} at {company} ({duration}): {description}\n"
        
        return result
    
    def _format_education_for_llm(self, education: List[Dict[str, str]]) -> str:
        """Format education data for LLM prompt."""
        if not education:
            return "No education data available"
        
        result = ""
        for edu in education:
            degree = edu.get("degree", "")
            institution = edu.get("institution", "")
            year = edu.get("year", "")
            
            result += f"{degree} from {institution} ({year})\n"
        
        return result


# For testing purposes
if __name__ == "__main__":
    # Import required modules for testing
    try:
        from ..models.scoring import MatchScorer
        scorer = MatchScorer()
    except ImportError:
        # When running as a script, paths are different
        import sys
        import os
        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
        from models.scoring import MatchScorer
        scorer = MatchScorer()
    
    # Create a mock LLM client for testing
    class MockLLMClient:
        def complete(self, prompt):
            # Return a mock response with match analysis
            return """
            {
                "strengths": [
                    "Strong technical skills in Python and Machine Learning",
                    "Relevant experience in data science projects",
                    "Advanced degree in Computer Science"
                ],
                "gaps": [
                    "Limited experience with cloud platforms",
                    "No mention of experience with specific ML frameworks required"
                ],
                "match_explanation": "The candidate has strong technical skills and relevant experience that align well with the job requirements. Some additional cloud experience would make them an even stronger match.",
                "recommendation": "Recommend"
            }
            """
    
    # Create test job data
    test_job = {
        "title": "Data Scientist",
        "required_skills": ["Python", "Machine Learning", "SQL", "Data Analysis", "AWS"],
        "preferred_skills": ["TensorFlow", "PyTorch", "Spark"],
        "required_experience": "3+ years of experience in data science or similar role",
        "required_education": "Master's degree in Computer Science, Statistics, or related field",
        "responsibilities": [
            "Develop machine learning models for predictive analytics",
            "Analyze large datasets to extract business insights",
            "Build data pipelines for model deployment"
        ]
    }
    
    # Create test candidate data
    test_candidate = {
        "cv_filename": "test_candidate.pdf",
        "contact_info": {
            "name": "Jane Doe",
            "email": "jane.doe@example.com",
            "phone": "123-456-7890"
        },
        "skills": ["Python", "Machine Learning", "SQL", "Data Analysis", "Statistics", "R"],
        "education": [
            {"degree": "MS in Computer Science", "institution": "Example University", "year": "2018-2020"}
        ],
        "experience": [
            {
                "title": "Data Scientist",
                "company": "Tech Corp",
                "duration": "2020-present",
                "description": "Developed predictive models using machine learning techniques. Analyzed customer data to derive insights."
            },
            {
                "title": "Data Analyst",
                "company": "Analytics Inc",
                "duration": "2018-2020",
                "description": "Performed statistical analysis on business data. Created dashboards for business intelligence."
            }
        ]
    }
    
    # Create an agent instance with mock components
    agent = MatchingAgent(scorer=scorer, llm_client=MockLLMClient())
    
    # Match candidate to job
    match_result = agent.match_candidate_to_job_with_llm(test_job, test_candidate)
    
    # Generate report
    match_report = agent.generate_match_report(match_result)
    
    # Print results
    print("Match Result:")
    print(json.dumps({k: v for k, v in match_result.items() if k not in ["strengths", "gaps", "match_explanation"]}, indent=2))  # Exclude verbose fields
    print("\nMatch Report:")
    print(match_report) 