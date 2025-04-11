# Matchwise Deployment Guide

This guide explains how to deploy Matchwise to production using free hosting services.

## Prerequisites

- GitHub account
- [Render.com](https://render.com) account (free tier)
- [Streamlit Cloud](https://streamlit.io/cloud) account (free tier)
- [ElephantSQL](https://www.elephantsql.com/) account (free tier, optional)

## Step 1: Prepare Your Repository

Ensure your code is pushed to a GitHub repository:

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/yourusername/matchwise.git
git push -u origin main
```

## Step 2: Deploy the FastAPI Backend to Render.com

1. **Sign in to Render.com**
   - Create an account if you don't have one

2. **Create a new Web Service**
   - Click "New" → "Web Service"
   - Connect your GitHub repository
   - Select the Matchwise repository

3. **Configure service**
   - **Name**: `matchwise-api`
   - **Environment**: Docker
   - **Branch**: main
   - **Build Command**: Leave as default
   - **Start Command**: `python run_production.py`

4. **Add Environment Variables**
   - `APP_TYPE`: `api`
   - `SECRET_KEY`: Generate a random string (e.g., `openssl rand -hex 32`)
   - `ENVIRONMENT`: `production`
   - `DATABASE_URL`: Your database URL (if using ElephantSQL)

5. **Choose Plan**
   - Select "Free" plan
   - Click "Create Web Service"

6. **Wait for Deployment**
   - It takes 5-10 minutes for the first build
   - Note your API URL (e.g., `https://matchwise-api.onrender.com`)

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
       - `STREAMLIT_API_URL`: Your Render API URL (e.g., `https://matchwise-api.onrender.com`)

4. **Deploy**
   - Click "Deploy"
   - Wait for the deployment to complete

## Step 4: Set Up Database (Optional)

SQLite works fine for small deployments, but for a more robust solution:

1. **Sign up for ElephantSQL**
   - Go to [elephantsql.com](https://www.elephantsql.com/)
   - Sign up and create a new instance (Tiny Turtle - Free)

2. **Get Connection String**
   - Copy the PostgreSQL connection URL

3. **Update Database URL in Render**
   - Go to your Render dashboard
   - Navigate to your Matchwise API service
   - Add/update the `DATABASE_URL` environment variable with ElephantSQL URL

4. **Restart the service**
   - Wait for redeploy to complete

## Step 5: Set Up Monitoring (Optional)

1. **Sign up for UptimeRobot**
   - Go to [uptimerobot.com](https://uptimerobot.com)
   - Create a free account

2. **Set up monitors**
   - Add a new monitor for your API (health check endpoint)
   - Add a new monitor for your Streamlit app

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Check database URL format
   - Ensure credentials are correct
   - Verify that your IP is allowed in database firewall

2. **Application Crashes**
   - Check Render logs
   - Ensure all required environment variables are set
   - Check if your application exceeds free tier limits

3. **Streamlit Can't Connect to API**
   - Verify API URL in Streamlit environment variables
   - Check if API is running by accessing the health endpoint
   - Ensure CORS is properly configured on the API

## Maintenance and Updates

To update your deployed application:

1. Make changes to your code
2. Push to your GitHub repository
3. Render and Streamlit Cloud will automatically redeploy

## Additional Resources

- [Render.com Documentation](https://render.com/docs)
- [Streamlit Cloud Documentation](https://docs.streamlit.io/streamlit-cloud)
- [ElephantSQL Documentation](https://www.elephantsql.com/docs/) 