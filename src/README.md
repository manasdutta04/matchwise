# Matchwise Job Application Screening System

A minimal AI-powered job application screening system that helps match candidates to job descriptions and manage the interview process.

## Features

- **Job Description Management**: Load and process job descriptions to extract key requirements
- **CV Processing**: Parse candidate CVs to extract skills, experience, and education
- **Smart Matching**: Match candidates to jobs based on skills, experience, and education compatibility
- **Interview Scheduling**: Schedule interviews with shortlisted candidates and generate email templates

## Installation

1. Ensure you have Python 3.8+ installed
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Run the Streamlit app:

```bash
streamlit run app.py
```

The application will be accessible at http://localhost:8501 in your browser.

## Workflow

1. **Jobs**: Browse job descriptions and view detailed information about each position
2. **Candidates**: Browse candidate CVs and view parsed skills, experience, and education
3. **Matching**: Match candidates to jobs and shortlist the best candidates
4. **Interviews**: Schedule interviews with shortlisted candidates and generate email templates

## Development

This application uses:
- **Streamlit** for the web interface
- **SQLite** for data storage
- **Pandas** for data manipulation
- **Regular expressions** for text extraction

## Project Structure

- `app.py`: Main entry point for the application
- `matchwise_app.py`: Core application functionality
- `data/`: Directory for SQLite database
- `AI-Powered Job Application Screening System/`: Dataset directory containing job descriptions and CVs 