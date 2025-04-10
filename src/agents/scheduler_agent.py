"""
Interview Scheduler Agent module.
This agent sends personalized interview requests to shortlisted candidates.
"""

import json
import logging
import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SchedulerAgent:
    """
    Agent for scheduling interviews with shortlisted candidates.
    """
    
    def __init__(self, llm_client=None, email_sender=None):
        """
        Initialize the scheduler agent.
        
        Args:
            llm_client: Client for LLM interactions
            email_sender: Service for sending email (not implemented)
        """
        self.llm_client = llm_client
        self.email_sender = email_sender
        
        # Default interview options
        self.default_interview_slots = [
            "10:00 AM - 11:00 AM",
            "2:00 PM - 3:00 PM",
            "4:00 PM - 5:00 PM"
        ]
        
        self.default_interview_formats = ["Video call", "Phone call", "In-person"]
    
    def schedule_interview(self, match_result: Dict[str, Any], candidate_data: Dict[str, Any], job_data: Dict[str, Any],
                          interview_date: datetime.date = None, interview_slots: List[str] = None,
                          interview_formats: List[str] = None) -> Dict[str, Any]:
        """
        Schedule an interview for a shortlisted candidate.
        
        Args:
            match_result: Match result data
            candidate_data: Candidate CV data
            job_data: Job description data
            interview_date: Date for the interview (default: 5 business days from now)
            interview_slots: List of available time slots
            interview_formats: List of available interview formats
            
        Returns:
            Dictionary with interview schedule details
        """
        # Check if candidate is shortlisted
        if not match_result.get("is_shortlisted", False):
            logger.warning(f"Candidate {candidate_data.get('cv_filename', 'Unknown')} is not shortlisted for job {job_data.get('title', 'Unknown')}")
            return {
                "status": "rejected",
                "reason": "Candidate is not shortlisted",
                "match_score": match_result.get("total_score", 0)
            }
        
        # Set default date if not provided (5 business days from now)
        if not interview_date:
            interview_date = self._get_next_business_day(datetime.date.today(), 5)
        
        # Set default slots and formats if not provided
        interview_slots = interview_slots or self.default_interview_slots
        interview_formats = interview_formats or self.default_interview_formats
        
        # Generate interview details
        interview_details = {
            "candidate_id": candidate_data.get("cv_filename", ""),
            "job_id": job_data.get("title", ""),
            "match_id": match_result.get("id", None),  # If available from database
            "scheduled_date": interview_date.strftime("%Y-%m-%d"),
            "available_slots": interview_slots,
            "available_formats": interview_formats,
            "status": "pending",
            "email_sent": False
        }
        
        # Generate email content
        email_content = self.generate_interview_email(
            candidate_data, job_data, interview_date, interview_slots, interview_formats)
        
        interview_details["email_content"] = email_content
        
        # Send email if sender is available
        if self.email_sender:
            try:
                recipient = candidate_data.get("contact_info", {}).get("email", "")
                if recipient:
                    self.email_sender.send_email(
                        recipient=recipient,
                        subject=f"Interview Invitation: {job_data.get('title', 'Position')} at Our Company",
                        content=email_content
                    )
                    interview_details["email_sent"] = True
                else:
                    logger.warning("No email address found for candidate")
            except Exception as e:
                logger.error(f"Error sending interview email: {e}")
        
        return interview_details
    
    def batch_schedule_interviews(self, match_results: List[Dict[str, Any]], candidates_data: Dict[str, Dict[str, Any]],
                                job_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Schedule interviews for all shortlisted candidates.
        
        Args:
            match_results: List of match results
            candidates_data: Dictionary mapping candidate IDs to candidate data
            job_data: Job description data
            
        Returns:
            List of interview schedule details
        """
        scheduled_interviews = []
        
        # Get only shortlisted candidates
        shortlisted_matches = [m for m in match_results if m.get("is_shortlisted", False)]
        
        # Schedule interviews on consecutive business days
        interview_date = self._get_next_business_day(datetime.date.today(), 5)
        
        for match in shortlisted_matches:
            candidate_id = match.get("candidate_filename", "")
            if candidate_id in candidates_data:
                candidate_data = candidates_data[candidate_id]
                
                # Schedule interview with incrementing dates
                interview_details = self.schedule_interview(
                    match, candidate_data, job_data, interview_date=interview_date)
                
                scheduled_interviews.append(interview_details)
                
                # Move to next business day for next candidate
                interview_date = self._get_next_business_day(interview_date, 1)
        
        return scheduled_interviews
    
    def generate_interview_email(self, candidate_data: Dict[str, Any], job_data: Dict[str, Any],
                               interview_date: datetime.date, interview_slots: List[str],
                               interview_formats: List[str]) -> str:
        """
        Generate a personalized interview invitation email.
        
        Args:
            candidate_data: Candidate CV data
            job_data: Job description data
            interview_date: Date for the interview
            interview_slots: List of available time slots
            interview_formats: List of available interview formats
            
        Returns:
            Email content as a string
        """
        # Extract needed information
        candidate_name = candidate_data.get("contact_info", {}).get("name", "Candidate")
        job_title = job_data.get("title", "position")
        
        # Format date for display
        formatted_date = interview_date.strftime("%A, %B %d, %Y")
        
        # Format slots and formats for display
        slots_text = "\n".join([f"- {slot}" for slot in interview_slots])
        formats_text = ", ".join(interview_formats)
        
        # Generate personalized email using LLM if available
        if self.llm_client:
            try:
                # Prepare candidate strengths if available
                strengths = candidate_data.get("strengths", [])
                strengths_text = ""
                if strengths:
                    strengths_text = "We were particularly impressed with your " + ", ".join(strengths[:3]) + "."
                
                prompt = f"""
                Write a professional and personalized interview invitation email for {candidate_name} who has been shortlisted 
                for the {job_title} position. The interview is scheduled for {formatted_date} with the following available slots:
                {slots_text}
                
                The interview can be conducted via {formats_text}.
                
                {strengths_text}
                
                The email should be professional, welcoming, and include:
                1. A personalized greeting
                2. Congratulations on being shortlisted
                3. Details about the interview date and available time slots
                4. Available interview formats
                5. A request to confirm their preferred time slot and format
                6. A brief note about what to expect during the interview
                7. Contact information for questions
                8. A professional closing
                
                Write the complete email, ready to send.
                """
                
                response = self.llm_client.complete(prompt)
                
                # Clean up the response if needed
                email_content = response.strip()
                return email_content
                
            except Exception as e:
                logger.error(f"Error generating interview email with LLM: {e}")
                # Fall back to template if LLM fails
        
        # Default template if LLM not available or fails
        email_content = f"""
Subject: Interview Invitation: {job_title} Position at Our Company

Dear {candidate_name},

Congratulations! We are pleased to inform you that you have been shortlisted for the {job_title} position at Our Company. Your skills and experience have impressed our hiring team, and we would like to invite you for an interview.

Interview Details:
- Date: {formatted_date}
- Available Time Slots:
{slots_text}
- Format: {formats_text}

Please reply to this email with your preferred time slot and interview format at your earliest convenience.

During the interview, we will discuss your experience, skills, and how they align with our team's needs. You will also have the opportunity to learn more about our company, the role, and ask any questions you may have.

If you have any questions before the interview or need to reschedule, please don't hesitate to contact us at hr@ourcompany.com or call us at (123) 456-7890.

We look forward to speaking with you soon!

Best regards,

HR Department
Our Company
hr@ourcompany.com
(123) 456-7890
        """
        
        return email_content.strip()
    
    def _get_next_business_day(self, start_date: datetime.date, days_to_add: int) -> datetime.date:
        """
        Get a future business day (skipping weekends).
        
        Args:
            start_date: Starting date
            days_to_add: Number of business days to add
            
        Returns:
            Future date that is a business day
        """
        current_date = start_date
        business_days_added = 0
        
        while business_days_added < days_to_add:
            current_date += datetime.timedelta(days=1)
            # Skip weekends (5 = Saturday, 6 = Sunday)
            if current_date.weekday() < 5:
                business_days_added += 1
        
        return current_date


# For testing purposes
if __name__ == "__main__":
    # Create a mock LLM client for testing
    class MockLLMClient:
        def complete(self, prompt):
            # Return a mock email
            return """
Subject: Interview Invitation: Data Scientist Position at Our Company

Dear Jane Doe,

Congratulations! I am delighted to inform you that you have been shortlisted for the Data Scientist position at Our Company. Your impressive background in machine learning and data analysis, combined with your relevant project experience, stood out to our hiring team.

We would like to invite you for an interview on Monday, August 28, 2023. Please select one of the following time slots that works best for you:
- 10:00 AM - 11:00 AM
- 2:00 PM - 3:00 PM
- 4:00 PM - 5:00 PM

The interview can be conducted via video call, phone call, or in-person at our headquarters. Please let us know your preferred format when confirming your time slot.

During the interview, we will discuss your experience with machine learning models, your approach to data analytics, and how your skills align with our current projects. You'll also have the opportunity to learn more about our data science team and ask any questions about the role or our company.

If you need any accommodations or have questions before the interview, please contact me at recruiter@ourcompany.com or call (123) 456-7890.

We're excited to meet you and learn more about your expertise!

Best regards,

Alex Johnson
Senior Recruiter
Our Company
recruiter@ourcompany.com
(123) 456-7890
            """
    
    # Create test data
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
                "description": "Developed predictive models using machine learning techniques."
            }
        ],
        "strengths": [
            "Strong background in machine learning",
            "Relevant data science experience",
            "Advanced education in Computer Science"
        ]
    }
    
    test_job = {
        "title": "Data Scientist",
        "required_skills": ["Python", "Machine Learning", "SQL", "Data Analysis", "AWS"],
        "required_experience": "3+ years of experience in data science or similar role",
        "required_education": "Master's degree in Computer Science, Statistics, or related field"
    }
    
    test_match = {
        "is_shortlisted": True,
        "total_score": 0.85,
        "job_title": "Data Scientist",
        "candidate_filename": "test_candidate.pdf"
    }
    
    # Create agent instance with mock LLM
    agent = SchedulerAgent(llm_client=MockLLMClient())
    
    # Set a specific date for testing
    test_date = datetime.date(2023, 8, 28)  # August 28, 2023
    
    # Generate interview schedule
    interview_details = agent.schedule_interview(
        test_match, test_candidate, test_job, interview_date=test_date)
    
    # Print results
    print("Interview Details:")
    print(json.dumps({k: v for k, v in interview_details.items() if k != "email_content"}, indent=2))
    print("\nEmail Content:")
    print(interview_details["email_content"]) 