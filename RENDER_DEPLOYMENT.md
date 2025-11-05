# Deploying to Render - Complete Guide

## Prerequisites
1. A GitHub account
2. A Render account (sign up at render.com)
3. A Mapbox access token (get one free at mapbox.com)

## Step 1: Push Code to GitHub

1. Create a new repository on GitHub
2. Push this folder to your GitHub repo:
```bash
git init
git add .
git commit -m "Initial commit - Weather Intelligence App"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git push -u origin main
```

## Step 2: Create Web Service on Render

1. Go to https://dashboard.render.com/
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Select the repository you just created

## Step 3: Configure Build Settings

Fill in the following settings:

**Name:** `weather-intelligence-app` (or your preferred name)

**Region:** Choose closest to your location

**Branch:** `main`

**Root Directory:** Leave blank (unless your code is in a subdirectory)

**Runtime:** `Python 3`

**Build Command:**
```
pip install -r requirements.txt
```

**Start Command:**
```
gunicorn app:app -w 2 -k gevent -b 0.0.0.0:8000
```

**Instance Type:** Select `Free` (or paid if you need more resources)

## Step 4: Environment Variables

Click **"Advanced"** and add these environment variables:

| Key | Value | Notes |
|-----|-------|-------|
| `PORT` | `8000` | Port for the Flask app |
| `PYTHON_VERSION` | `3.11.0` | Specify Python version |
| `SPC_OUTLOOK_DAY` | `1` | Optional: SPC outlook day (1, 2, or 3) |

**Important:** You don't need to set MAPBOX_TOKEN as an environment variable. The app accepts it via URL parameter.

## Step 5: Deploy

1. Click **"Create Web Service"**
2. Render will start building and deploying your app
3. Wait for the build to complete (usually 2-5 minutes)

## Step 6: Access Your App

Once deployed, you'll get a URL like:
```
https://weather-intelligence-app.onrender.com
```

To use the map, append your Mapbox token:
```
https://weather-intelligence-app.onrender.com?mb=pk.YOUR_MAPBOX_TOKEN_HERE
```

The token will be stored in localStorage for future visits.

## Step 7: Use in OBS (Optional)

If you want to use this in OBS Studio:

1. Add a **Browser Source**
2. Set the URL to your Render app URL (with Mapbox token)
3. Set Width: 1920, Height: 1080 (or your stream resolution)
4. Check "Refresh browser when scene becomes active"
5. Check "Shutdown source when not visible"

## Troubleshooting

### Build Fails
- Check the build logs in Render dashboard
- Verify all dependencies are in requirements.txt
- Make sure Python version is compatible

### Map Doesn't Load
- Verify your Mapbox token is valid
- Check browser console for errors
- Try accessing with `?mb=YOUR_TOKEN` in URL

### 502 Bad Gateway
- Check if the app is running (look at Logs in Render)
- Verify the start command is correct
- Make sure PORT environment variable is set

### API Endpoints Not Working
- Check the Logs tab in Render dashboard
- Verify network access for external APIs (NOAA, etc.)
- Some free Render instances sleep after inactivity - first request may be slow

## Free Tier Limitations

Render's free tier:
- Spins down after 15