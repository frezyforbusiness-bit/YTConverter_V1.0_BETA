# Deployment Guide

This guide explains how to deploy the Producer Tools YouTube Audio Converter to various hosting platforms.

## Option 1: Render (Recommended - Easy & Free)

### Backend Deployment

1. **Create a Render account** at https://render.com

2. **Create a new Web Service:**
   - Connect your GitHub repository
   - Name: `producer-tools-backend`
   - Environment: `Python 3`
   - **Root Directory**: Leave empty (uses repo root)
   - **Build Command**: `pip install -r backend/requirements.txt`
   - **Start Command**: `cd backend && python app.py`
   - **Python Version**: 3.12.3 (or latest 3.12.x)

3. **Add Environment Variables:**
   - `PORT`: 5000 (optional, Render sets this automatically)
   - No other variables needed for basic setup

4. **Important - FFmpeg Installation:**
   - Render doesn't install system packages by default
   - **Option A**: Use the Dockerfile (recommended)
     - Change service type to "Docker" instead of "Python"
     - Render will use the Dockerfile automatically
   - **Option B**: Add to build command:
     - Build Command: `apt-get update && apt-get install -y ffmpeg && pip install -r backend/requirements.txt`
     - Note: This may not work on all Render plans
   - **Option C**: Use a custom Dockerfile (see Dockerfile in repo)

### Frontend Deployment

1. **Create a Static Site:**
   - Connect your GitHub repository
   - Build Command: (leave empty)
   - Publish Directory: `frontend`

2. **Update API URL:**
   - The frontend automatically detects the environment
   - For custom domains, update `script.js` API_URL

## Option 2: Railway

### Backend

1. **Install Railway CLI:**
   ```bash
   npm i -g @railway/cli
   ```

2. **Login and create project:**
   ```bash
   railway login
   railway init
   ```

3. **Deploy:**
   ```bash
   railway up
   ```

4. **Add ffmpeg:**
   - Railway uses Docker, so the Dockerfile will handle it
   - Or add a buildpack for ffmpeg

### Frontend

1. Deploy frontend folder to Vercel/Netlify (see below)

## Option 3: Vercel (Frontend) + Railway/Render (Backend)

### Frontend on Vercel

1. **Install Vercel CLI:**
   ```bash
   npm i -g vercel
   ```

2. **Deploy:**
   ```bash
   cd frontend
   vercel
   ```

3. **Update API URL in script.js** to point to your backend URL

### Backend on Railway/Render

Follow Option 1 or 2 for backend deployment.

## Option 4: Docker + Any Cloud Provider

### Build Docker Image

```bash
docker build -t producer-tools-backend .
```

### Run Locally

```bash
docker run -p 5000:5000 producer-tools-backend
```

### Deploy to:
- **DigitalOcean App Platform**
- **AWS ECS/Fargate**
- **Google Cloud Run**
- **Azure Container Instances**

## Option 5: Heroku

### Backend

1. **Install Heroku CLI**

2. **Create app:**
   ```bash
   heroku create producer-tools-backend
   ```

3. **Add buildpack for ffmpeg:**
   ```bash
   heroku buildpacks:add https://github.com/jonathanong/heroku-buildpack-ffmpeg-latest
   heroku buildpacks:add heroku/python
   ```

4. **Deploy:**
   ```bash
   git push heroku master
   ```

### Frontend

Deploy `frontend` folder to Netlify or Vercel.

## Environment Variables

If needed, you can set these environment variables:

- `PORT`: Server port (default: 5000)
- `TEMP_DIR`: Temporary files directory (default: system temp)
- `COOKIES_FILE`: Path to YouTube cookies file (optional, default: `backend/cookies.txt`)

### YouTube Cookies Configuration

To avoid YouTube bot detection, cookies are handled using yt-dlp's official methods:

1. **Local Development** (Automatic):
   - The app automatically tries `--cookies-from-browser chrome` (or other browsers)
   - If no browser is available, uses `--cookies cookies.txt` if the file exists
   - To extract cookies manually:
     ```bash
     yt-dlp --cookies-from-browser chrome --cookies backend/cookies.txt
     ```

2. **Production (Render/Railway/etc.)**:
   - Place `cookies.txt` in the `backend/` directory (upload via SSH/Shell)
   - Or set `COOKIES_FILE=/path/to/cookies.txt` environment variable
   - The file must be in Netscape format (first line: `# HTTP Cookie File` or `# Netscape HTTP Cookie File`)

**Note**: The `cookies.txt` file is gitignored for security. Use yt-dlp's official methods to extract cookies from your browser.

## CORS Configuration

The backend already has CORS enabled. If you deploy frontend and backend on different domains, make sure:

1. Backend allows your frontend domain
2. Update `flask-cors` configuration in `app.py` if needed

## Quick Start: Render (Easiest)

### Backend:

1. Go to https://render.com
2. New → Web Service
3. Connect GitHub repo
4. Settings:
   - **Name**: `producer-tools-api`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r backend/requirements.txt && apt-get update && apt-get install -y ffmpeg`
   - **Start Command**: `cd backend && python app.py`
   - **Plan**: Free (or paid for better performance)

### Frontend:

1. New → Static Site
2. Connect GitHub repo
3. Settings:
   - **Build Command**: (empty)
   - **Publish Directory**: `frontend`
   - **Plan**: Free

4. Update `frontend/script.js`:
   ```javascript
   const API_URL = 'https://your-backend-url.onrender.com';
   ```

## Notes

- **Free tiers** may have cold starts (first request takes longer)
- **ffmpeg** is required on the backend server
- **File size limits** may apply on free tiers
- Consider using **CDN** for frontend assets
- For production, use **environment variables** for sensitive data

## Testing Deployment

After deployment:

1. Test backend: `https://your-backend-url/health`
2. Test frontend: Open in browser and try a conversion
3. Check logs for any errors

