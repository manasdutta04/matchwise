# Matchwise - AI Job Application Screening System

Matchwise is an AI-powered job application screening system designed to connect job candidates with the right positions based on skills, experience, and education match.

## Features

- **Smart Matching Algorithm**: Uses AI to match candidates to jobs based on multiple criteria
- **Profile Management**: View and manage job descriptions and candidate CVs 
- **Match Scoring**: Transparent scoring system to explain matching rationale
- **Interview Scheduling**: Schedule interviews with shortlisted candidates
- **Email Templates**: Generate professional interview invitation emails

## Tech Stack

- **Backend**: SQLite (with Python SQLite3)
- **Frontend**: Streamlit for a clean, minimal UI
- **AI/ML**: Simulated AI for text analysis and matching
- **Data Processing**: Pandas and NumPy for data operations
- **Text Processing**: Regular expressions for CV and job description parsing

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/matchwise.git
   cd matchwise
   ```

2. Set up a virtual environment (recommended):
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate
   
   # macOS/Linux
   python -m venv venv
   source venv/bin/activate
   ```

3. Install the minimal required dependencies:
   ```bash
   pip install streamlit pandas numpy PyPDF2
   ```

## Usage

Run the application using the provided script:
```bash
python run_app.py
```

Alternatively, you can run the Streamlit app directly:
```bash
cd src
streamlit run app.py
```

The application will be accessible at http://localhost:8501 in your browser.

## Initial Setup

On first run, the application will:
1. Create a `data` directory for the SQLite database
2. Initialize database tables for jobs, candidates, matches, and interviews
3. Simulate job descriptions and candidate CVs for demo purposes

## Workflow

1. **Jobs Tab**: Browse and manage job descriptions
   - View job details including required skills, experience, and education
   - Add new job descriptions

2. **Candidates Tab**: Browse and manage candidate CVs
   - View candidate details including extracted skills, experience, and education
   - Upload new candidate CVs

3. **Matching Tab**: Match candidates to jobs
   - View match scores based on skills, experience, and education
   - Shortlist promising candidates for interviews

4. **Interviews Tab**: Schedule and manage interviews
   - Schedule interviews with shortlisted candidates
   - Generate and copy interview invitation emails

## Troubleshooting

If you encounter issues:

1. **Missing dependencies**: Ensure you've installed all required packages
   ```bash
   pip install streamlit pandas numpy PyPDF2
   ```

2. **Database errors**: If the database is corrupted, delete the `data/matchwise.db` file and restart
   ```bash
   rm src/data/matchwise.db  # or delete manually
   ```

3. **Port in use**: If port 8501 is already in use, Streamlit will automatically use another port

4. **Streamlit configuration errors**: If you get a `StreamlitSetPageConfigMustBeFirstCommandError`, ensure that:
   - Only one file calls `st.set_page_config()`
   - The `set_page_config()` call is the first Streamlit command in the file
   - No other Streamlit imports or functions are called before it

## Project Structure

```
matchwise/
├── src/               # Source code
│   ├── app.py         # Main Streamlit entry point
│   ├── matchwise_app.py # Core application logic
│   ├── data/          # SQLite database
│   ├── database/      # Database models and utilities
│   ├── agents/        # AI agent implementations
│   ├── models/        # Matching models and algorithms
│   └── utils/         # Utility functions
├── run_app.py         # Convenience script to run the app
└── requirements.txt   # Project dependencies
```

## License

[MIT License](LICENSE) 