# Matchwise

Matchwise is an intelligent matching system designed to connect users based on preferences, interests, and compatibility factors. The system leverages advanced machine learning algorithms and natural language processing to create optimal matches.

## Features

- **Smart Matching Algorithm**: Uses ML models to find the best matches based on multiple criteria
- **Profile Management**: Create and manage detailed user profiles
- **Preference Settings**: Configure matching preferences and criteria
- **Match Scoring**: Transparent scoring system to explain matching rationale
- **API Integration**: RESTful API for integration with other systems

## Tech Stack

- **Backend**: FastAPI, Python 3.10+
- **Database**: PostgreSQL (with SQLAlchemy ORM)
- **AI/ML**: LangChain, scikit-learn, sentence-transformers
- **Authentication**: JWT with Python-jose
- **Testing**: Pytest with coverage reporting
- **Documentation**: OpenAPI (Swagger)
- **API Client**: HTTPX for async HTTP requests

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/matchwise.git
   cd matchwise
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root with the following variables:
   ```
   DATABASE_URL=postgresql://user:password@localhost/matchwise
   SECRET_KEY=your_secret_key
   ENVIRONMENT=development
   ```

## Project Structure

```
matchwise/
├── app/                  # Application code
│   ├── api/              # API endpoints
│   ├── core/             # Core functionality and config
│   ├── db/               # Database models and utils
│   ├── matching/         # Matching algorithms
│   ├── schemas/          # Pydantic models
│   └── services/         # Business logic services
├── tests/                # Test suite
├── alembic/              # Database migrations
├── .env                  # Environment variables (not tracked by git)
├── .gitignore            # Git ignore rules
├── requirements.txt      # Project dependencies
└── README.md             # Project documentation
```

## Usage (Local Development)

1. Start the FastAPI backend:
   ```bash
   python run.py
   ```

2. Start the Streamlit frontend:
   ```bash
   streamlit run src/app.py
   ```

3. Access the applications:
   - API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Web Interface: http://localhost:8501

## Deployment

### Option 1: Docker Deployment

1. Build and run using Docker Compose:
   ```bash
   docker-compose up --build
   ```

2. Access the applications:
   - API: http://localhost:8000
   - Web Interface: http://localhost:8501

### Option 2: Heroku Deployment

1. Create Heroku apps for backend and frontend:
   ```bash
   # For API
   heroku create matchwise-api
   
   # For Streamlit
   heroku create matchwise-web
   ```

2. Deploy the API:
   ```bash
   # Set environment variables
   heroku config:set APP_TYPE=api -a matchwise-api
   
   # Deploy
   git push https://git.heroku.com/matchwise-api.git main
   ```

3. Deploy the Streamlit interface:
   ```bash
   # Set environment variables
   heroku config:set APP_TYPE=streamlit -a matchwise-web
   heroku config:set STREAMLIT_API_URL=https://matchwise-api.herokuapp.com -a matchwise-web
   
   # Deploy
   git push https://git.heroku.com/matchwise-web.git main
   ```

### Option 3: Cloud Platform Deployment

Follow the documentation for your preferred cloud platform:
- [AWS Elastic Beanstalk Deployment Guide](https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/create-deploy-python-apps.html)
- [Google Cloud Run Guide](https://cloud.google.com/run/docs/quickstarts/build-and-deploy/deploy-python-service)
- [Azure App Service Guide](https://learn.microsoft.com/en-us/azure/app-service/quickstart-python)

## Development

### Database Migrations

```bash
# Generate a new migration
alembic revision --autogenerate -m "Description of changes"

# Run migrations
alembic upgrade head
```

### Testing

```bash
# Run all tests
pytest

# Run tests with coverage report
pytest --cov=app
```

## Developer

[Manas Dutta](https://github.com/manasdutta04)

## License

[MIT License](LICENSE)

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request 