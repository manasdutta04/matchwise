# Matchwise - AI Job Application Screening System

<div align="center">
  <img src="https://img.shields.io/badge/Status-Active-green.svg" alt="Status" />
  <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python" />
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License" />
</div>

Matchwise is an AI-powered job application screening system designed to connect job candidates with the right positions based on skills, experience, and education match. The system streamlines the recruitment process by automating candidate evaluation, shortlisting, and interview scheduling.

## ✨ Features

- **Smart Matching Algorithm**: Uses AI to analyze and score candidate-job matches based on multiple criteria
- **Profile Management**: View and manage job descriptions and candidate CVs with intuitive interfaces
- **Match Scoring**: Transparent scoring system explains matching rationale with detailed breakdowns
- **Auto-Shortlisting**: Automatically identifies high-scoring candidates (>59% match) for faster processing
- **Interview Scheduling**: Schedule interviews with shortlisted candidates through a streamlined workflow
- **Email Templates**: Generate professional interview invitation emails customized for each candidate
- **Data Visualization**: Visual indicators make it easy to identify the best matches at a glance
- **Clipboard Integration**: Copy generated emails with a single click for sending to candidates

## 🛠️ Tech Stack

- **Backend**: SQLite with Python SQLite3 for efficient data storage
- **Frontend**: Streamlit for a clean, responsive, minimal UI
- **AI/ML**: Simulated AI for text analysis and semantic matching
- **Data Processing**: Pandas and NumPy for data manipulation and analysis
- **Text Processing**: Regular expressions and NLP techniques for CV and job description parsing
- **PDF Handling**: PyPDF2 for processing candidate CV files

## 📋 Requirements

- Python 3.10 or higher
- Core dependencies: streamlit, pandas, numpy, PyPDF2
- Optional: pdf2image, pytesseract (for enhanced OCR capabilities)

## 🚀 Installation

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

3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## 🖥️ Usage

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

## 🏁 Initial Setup

On first run, the application will:
1. Create a `data` directory for the SQLite database
2. Initialize database tables for jobs, candidates, matches, and interviews
3. Generate sample job descriptions and candidate CVs for demo purposes

## 📊 Workflow

1. **Jobs Tab**: Browse and manage job descriptions
   - View job details including required skills, experience, and education
   - See detailed specifications for each position
   - Match candidates directly from the job details view

2. **Candidates Tab**: Browse and manage candidate CVs
   - View candidate details including extracted skills, experience, and education
   - Upload new candidate CVs or view existing ones
   - Inspect candidate qualifications at a glance

3. **Matching Tab**: Match candidates to jobs
   - Select jobs and view match scores across all candidates
   - See detailed breakdowns of skills, experience, and education matches
   - Shortlist promising candidates with a single click
   - Auto-shortlist feature for candidates with matches above 59%

4. **Interviews Tab**: Schedule and manage interviews
   - Schedule interviews with shortlisted candidates
   - Select date, time slot, and interview format
   - Generate professional email templates for candidates
   - Copy emails to clipboard with a single click

## 🔍 Advanced Features

### Automated CV Analysis
The system automatically extracts key information from candidate CVs:
- Contact information and personal details
- Skills and technical competencies
- Educational qualifications
- Work experience and career history

### Intelligent Job Description Processing
Job descriptions are analyzed to identify:
- Required skills and competencies
- Education requirements
- Experience levels needed
- Core responsibilities

### Match Quality Assessment
The matching algorithm evaluates candidates based on:
- Skills match percentage
- Experience relevance and duration
- Education appropriateness
- Overall compatibility score

## 🌐 Deployment Options

### Local Deployment
Follow the installation and usage instructions above for local deployment.

### Cloud Deployment
The application can be deployed to various cloud platforms:

1. **Streamlit Cloud**: Free hosting for the Streamlit frontend
   - Connect your GitHub repository
   - Point to `src/app.py`
   - Configure any necessary secrets

2. **Render**: Deploy the backend API
   - Use the included `run_production.py` script
   - Set environment variables as specified in `.env.example`

3. **Vercel**: Serverless deployment
   - Use the provided `vercel.json` configuration
   - Deploy with `vercel` CLI or through the Vercel dashboard

See `DEPLOYMENT.md` and `VERCEL_DEPLOYMENT.md` for detailed instructions.

## 🔧 Troubleshooting

If you encounter issues:

1. **Missing dependencies**: Ensure you've installed all required packages
   ```bash
   pip install -r requirements.txt
   ```

2. **Database errors**: If the database is corrupted, delete the `data/matchwise.db` file and restart
   ```bash
   # Windows
   del /F /S /Q src\data\*.db
   
   # macOS/Linux
   rm src/data/matchwise.db
   ```

3. **Port in use**: If port 8501 is already in use, Streamlit will automatically use another port

4. **Streamlit configuration errors**: If you get a `StreamlitSetPageConfigMustBeFirstCommandError`, ensure that:
   - Only one file calls `st.set_page_config()`
   - The `set_page_config()` call is the first Streamlit command in the file
   - No other Streamlit imports or functions are called before it

5. **CV Preview not showing**: In deployed environments, CV file access may be limited:
   - When deploying to cloud services, the CV PDF files may not be accessible
   - The application will show a placeholder and extracted CV information instead
   - For local development, ensure CV files are in the expected directories

## 📂 Project Structure

```
matchwise/
├── src/               # Source code
│   ├── app.py         # Main Streamlit entry point
│   ├── matchwise_app.py # Core application logic
│   ├── data/          # SQLite database
│   ├── database/      # Database models and utilities
│   │   ├── db.py      # Database connection and initialization
│   │   └── models.py  # SQLAlchemy models for database tables
│   ├── agents/        # AI agent implementations
│   │   ├── cv_processing_agent.py  # CV parsing and analysis
│   │   ├── job_description_agent.py # Job description analysis
│   │   ├── matching_agent.py      # Candidate-job matching logic
│   │   └── scheduler_agent.py     # Interview scheduling
│   ├── models/        # Matching models and algorithms
│   │   ├── embedding.py  # Text embedding functionality
│   │   └── scoring.py    # Match scoring algorithms
│   └── utils/         # Utility functions
│       ├── pdf_parser.py    # PDF extraction tools
│       ├── text_processor.py # Text analysis utilities
│       └── llm_client.py    # Language model integration
├── api/               # Vercel API deployment files
├── .streamlit/        # Streamlit configuration
├── run_app.py         # Convenience script to run the app
├── run_production.py  # Production deployment script
├── requirements.txt   # Project dependencies
├── DEPLOYMENT.md      # Deployment instructions
└── VERCEL_DEPLOYMENT.md # Vercel-specific deployment guide
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the project
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 👨‍💻 Developed by

**Manas Dutta**
- GitHub: [manasdutta04](https://github.com/manasdutta04)
- LinkedIn: [Manas Dutta](https://linkedin.com/in/manasdutta04)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgements

- Streamlit team for the excellent framework
- OpenAI for inspiration on AI matching techniques
- All contributors and testers who helped improve the application 