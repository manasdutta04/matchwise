# Deploying Matchwise on Vercel

This guide explains how to deploy Matchwise to Vercel for the backend API and Streamlit Cloud for the frontend.

## Prerequisites

- GitHub account
- [Vercel](https://vercel.com) account (free tier)
- [Streamlit Cloud](https://streamlit.io/cloud) account (free tier)

## Step 1: Prepare Your Repository

Ensure your code is pushed to a GitHub repository:

```bash
git init
git add .
git commit -m "Prepare for Vercel deployment"
git branch -M main
git remote add origin https://github.com/yourusername/matchwise.git
git push -u origin main
```

## Step 2: Deploy the FastAPI Backend to Vercel

### Using the Vercel Dashboard

1. **Sign in to Vercel**
   - Create an account if you don't have one (you can use your GitHub account)

2. **Import Project**
   - Click "Add New..." → "Project"
   - Choose "Import Git Repository"
   - Select your GitHub repository

3. **Configure Project**
   - **Project Name**: matchwise-api (or your preferred name)
   - **Framework Preset**: Other
   - **Root Directory**: ./
   - **Build and Output Settings**: Leave as default

4. **Environment Variables**
   - Add the following environment variables:
     - `ENVIRONMENT`: `production`
     - `APP_TYPE`: `api`
     - `SECRET_KEY`: Generate a random string (use `openssl rand -hex 32` or any random string generator)
     - `VERCEL`: `1` (to indicate we're on Vercel)

5. **Deploy**
   - Click "Deploy"
   - Wait for the deployment to complete (2-5 minutes)
   - Note your API URL (e.g., `https://matchwise-api.vercel.app`)

### Using the Vercel CLI (Alternative)

If you prefer using the command line:

1. **Install Vercel CLI**
   ```bash
   npm install -g vercel
   ```

2. **Log in to Vercel**
   ```bash
   vercel login
   ```

3. **Deploy the Project**
   ```bash
   vercel
   ```

4. **Answer the prompts**:
   - Set up and deploy: Yes
   - Existing project: No
   - Project name: matchwise-api
   - Directory: ./
   - Override settings: No

5. **Set Environment Variables**
   ```bash
   vercel env add ENVIRONMENT production
   vercel env add APP_TYPE api
   vercel env add SECRET_KEY your-secret-key
   vercel env add VERCEL 1
   ```

6. **Redeploy with Environment Variables**
   ```bash
   vercel --prod
   ```

## Step 3: Deploy the Streamlit Frontend to Streamlit Cloud

1. **Sign in to Streamlit Cloud**
   - Create an account if you don't have one

2. **Create a new app**
   - Click "New app"
   - Connect your GitHub repository
   - Enter repository details

3. **Configure app**
   - **Repository**: Your GitHub repo
   - **Branch**: main
   - **Main file path**: `src/app.py`
   - **Advanced Settings**:
     - Add secrets:
       - `STREAMLIT_API_URL`: Your Vercel API URL (e.g., `https://matchwise-api.vercel.app`)

4. **Deploy**
   - Click "Deploy"
   - Wait for the deployment to complete

## Step 4: Test Your Deployment

### Testing the Backend API

1. Visit your Vercel API URL (e.g., `https://matchwise-api.vercel.app`)
2. You should see the welcome message
3. Visit the health check endpoint: `https://matchwise-api.vercel.app/health`
4. Check the API documentation: `https://matchwise-api.vercel.app/docs`

### Testing the Frontend

1. Visit your Streamlit app URL (provided by Streamlit Cloud)
2. Test the functionality to ensure it connects to your Vercel API

## Important Notes About Vercel Serverless Functions

1. **Cold Starts**: Vercel functions may experience "cold starts" if not used frequently. The first request after a period of inactivity might be slower.

2. **Execution Time Limit**: Vercel serverless functions have a maximum execution time of 10 seconds on the free tier. Ensure your API operations complete within this timeframe.

3. **Statelessness**: The database is created in `/tmp` directory, which is ephemeral. It will be recreated on cold starts, so this deployment is best for demos, not for persistent data storage.

4. **File System Limitations**: The `/tmp` directory is the only writable location, and it has a 512MB size limit.

## Step 5: Production Considerations

For a more robust production setup:

1. **Database**: 
   - Connect to a persistent database service rather than using SQLite
   - Options include:
     - [Neon](https://neon.tech) (Free PostgreSQL)
     - [Supabase](https://supabase.com) (Free PostgreSQL)
     - [PlanetScale](https://planetscale.com) (Free MySQL)

2. **Environment Variables**:
   - Set DATABASE_URL to point to your external database
   - Update the PostgreSQL connection string in Vercel environment variables

3. **Monitoring**:
   - Use the Vercel Analytics dashboard to monitor function performance
   - Set up [UptimeRobot](https://uptimerobot.com) to monitor your API health endpoint

## Troubleshooting

### Common Issues with Vercel Deployment

1. **Function Size Limit**:
   - Vercel has a 50MB limit for serverless functions
   - If you exceed this, simplify dependencies or split functionality

2. **Database Errors**:
   - Check if `/tmp` directory is writable
   - If using external database, verify connection string and credentials

3. **Timeout Errors**:
   - Operations taking longer than 10 seconds will fail
   - Optimize database queries and API response times

4. **CORS Issues**:
   - Ensure allowed_origins in main.py includes your Streamlit app URL
   - Add your Streamlit URL to ADDITIONAL_CORS_ORIGINS environment variable

## Updating Your Deployment

To update your deployed application:

1. Make changes to your code
2. Push to your GitHub repository
3. Vercel and Streamlit Cloud will automatically redeploy 