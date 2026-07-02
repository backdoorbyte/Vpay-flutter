# 🚀 Deploy VPay Backend to Render

This guide walks you through deploying your VPay FastAPI backend to Render.

---

## 📋 Prerequisites

1. **GitHub Account** - Your code will be deployed from GitHub
2. **Render Account** - Sign up at [render.com](https://render.com)

---

## 🛠️ Step 1: Push Code to GitHub

Your backend code needs to be in a GitHub repository:

```bash
cd C:\Users\harsh\Documents\vpay-flutter

# Initialize git if not already done
git init

# Add backend files
git add backend/
git commit -m "Initial VPay backend commit"

# Create a repo on GitHub at: https://github.com/new
# Then push:
git remote add origin https://github.com/yourusername/vpay-flutter.git
git branch -M main
git push -u origin main
```

---

## 🚀 Step 2: Deploy to Render

### Option A: Using render.yaml Blueprint (Recommended)

1. **Go to Render Dashboard**: https://dashboard.render.com

2. **Create Blueprint**:
   - Click **"New"** → **"Blueprint"**
   - Connect your GitHub repository
   - Select `vpay-flutter/backend/render.yaml`
   - Click **"Apply"**

3. Render will automatically:
   - Create the web service (`vpay-backend`)
   - Create the PostgreSQL database (`vpay-db`)
   - Link them together

### Option B: Manual Setup

1. **Create Web Service**:
   - Click **"New"** → **"Web Service"**
   - Connect your GitHub repository
   - Select the `backend` folder as root directory
   - Configure:
     - **Name**: `vpay-backend`
     - **Region**: Choose closest to your users
     - **Branch**: `main`
     - **Root Directory**: `backend`
     - **Runtime**: `Python 3`
     - **Build Command**: `pip install --no-cache-dir -r requirements.txt`
     - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

2. **Add PostgreSQL Database**:
   - Click **"New"** → **"PostgreSQL"**
   - Name: `vpay-db`
   - Region: Same as your web service
   - After creation, copy the **Internal Database URL**

---

## ⚙️ Step 3: Configure Environment Variables

In your Render Web Service dashboard:

1. Go to **"Environment"** tab
2. Add the following variables:

| Variable | Value | Notes |
|----------|-------|-------|
| `DATABASE_URL` | (from Render PostgreSQL) | Internal DB URL |
| `SUPABASE_URL` | `https://qmuwykzbkcxabljiezsn.supabase.co` | Your Supabase project |
| `SUPABASE_KEY` | Your Supabase anon key | Get from Supabase dashboard |
| `CORS_ORIGINS` | `["https://your-app.onrender.com"]` | Update with your Render URL |
| `HF_HOME` | `/tmp/huggingface` | For ML model caching |
| `PRELOAD_ML_MODELS` | `true` | Warm up models on startup |
| `PYTHON_VERSION` | `3.12.0` | Match your local version |
| `PORT` | `10000` | Render default port |

### Additional Configuration Variables:

| Variable | Value | Description |
|----------|-------|-------------|
| `VERIFY_THRESHOLD` | `0.5` | Voice verification threshold |
| `WHISPER_MODEL_SIZE` | `base` | Whisper model size |
| `WHISPER_BEAM_SIZE` | `1` | Whisper beam size |
| `CHALLENGE_TTL_SECONDS` | `120` | Challenge TTL |
| `PARSE_MIN_CONFIDENCE` | `0.5` | Minimum parse confidence |
| `PHRASE_MATCH_MIN_RATIO` | `0.55` | Phrase match ratio |

---

## 🧪 Step 4: Verify Deployment

### 4.1 Check Health Endpoint

Once deployment completes (5-10 minutes), test:

```bash
curl https://your-app.onrender.com/health
```

Expected response:
```json
{"status":"ok","service":"VPay"}
```

### 4.2 Test API Documentation

Open in browser:
```
https://your-app.onrender.com/docs
```

### 4.3 Test Wallet Endpoint

```bash
curl https://your-app.onrender.com/wallet
```

---

## 📱 Step 5: Update Flutter App

Update your Flutter app's API URL:

**File:** `frontend/lib/core/constants/api_constants.dart`

```dart
class ApiConstants {
  // Production (Render)
  static const String baseUrl = 'https://your-app.onrender.com';
  
  // Development (uncomment for local testing)
  // static const String baseUrl = 'http://10.0.2.2:8000';
}
```

Then rebuild:
```bash
cd frontend
flutter clean
flutter build apk  # or flutter build ios
```

---

## ⚠️ Important Notes

### Cold Starts (Free/Basic Plans)

Render spins down idle services on basic plans:

- **First request after idle:** 30-60 seconds (cold start + ML model loading)
- **Subsequent requests:** Fast (<2 seconds)

**Solutions:**
1. `PRELOAD_ML_MODELS=true` is already set
2. Upgrade to a paid plan for always-on
3. Use a ping service to keep warm (not recommended for production)

### File System

Render's filesystem is **ephemeral**:

- ✅ PostgreSQL database: Persistent (managed service)
- ❌ Local SQLite: Lost on redeploy
- ❌ Uploaded files: Lost on redeploy - use Supabase Storage
- ✅ ML model cache: Cached per deployment in `/tmp`

### Build Time

First build takes 10-15 minutes due to:
- TensorFlow installation
- ML model downloads on first request

---

## 🔧 Troubleshooting

### Build fails with "Cannot find requirements.txt"

Ensure `Root Directory` is set to `backend` in Render settings.

### Service crashes on startup

1. Check **Logs** tab in Render dashboard
2. Verify `DATABASE_URL` is set correctly
3. Check `main:app` is the correct module path

### High memory usage errors

ML models require ~2GB RAM. If you see OOM errors:

1. Upgrade to a larger instance plan
2. Use smaller whisper model: `WHISPER_MODEL_SIZE=tiny`

### CORS errors

Update `CORS_ORIGINS` to include your Render URL:
```json
["https://your-app.onrender.com", "http://localhost:5173"]
```

---

## 📊 Deployment Checklist

- [ ] Code pushed to GitHub
- [ ] Render account created
- [ ] Web service created
- [ ] PostgreSQL database provisioned
- [ ] `DATABASE_URL` connected to web service
- [ ] All environment variables set
- [ ] Build completes successfully
- [ ] Health endpoint responds
- [ ] Flutter app URL updated

---

## 🎉 You're Done!

Your VPay backend is now running on Render!

**Your endpoints:**
- Health: `https://your-app.onrender.com/health`
- API Docs: `https://your-app.onrender.com/docs`
- Wallet: `https://your-app.onrender.com/wallet`

---

## 💰 Render Pricing Notes

- **Starter Web Service**: ~$7-25/month depending on usage
- **Starter PostgreSQL**: Free tier available (90 days), then ~$7/month
- ML workloads may require more RAM - monitor usage

Render bills by the minute - you can pause/delete services when not in use.