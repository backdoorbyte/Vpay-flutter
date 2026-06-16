# 🚀 Deploy VPay Backend to Railway

This guide walks you through deploying your VPay FastAPI backend to Railway.

---

## 📋 Prerequisites

1. **GitHub Account** - Your code will be deployed from GitHub
2. **Railway Account** - Sign up at [railway.com](https://railway.com)
3. **Git installed** locally

---

## 🛠️ Step 1: Prepare Your Backend

### 1.1 Update Flutter App Base URL

After deployment, you'll need to update your Flutter app to point to the Railway URL.

**File:** `frontend/lib/core/constants/api_constants.dart`

```dart
// For production (Railway)
static const String baseUrl = 'https://your-app.railway.app';

// For local development
// static const String baseUrl = 'http://10.0.2.2:8000'; // Android Emulator
// static const String baseUrl = 'http://localhost:8000'; // iOS Simulator/Web
```

---

## 🚀 Step 2: Deploy to Railway

### Option A: Deploy from GitHub (Recommended)

1. **Push your code to GitHub:**
   ```bash
   cd C:\Users\harsh\Documents\vpay-flutter
   git init
   git add backend/
   git commit -m "Initial VPay backend commit"
   # Create a repo on GitHub, then:
   git remote add origin https://github.com/yourusername/vpay-flutter.git
   git push -u origin main
   ```

2. **Deploy on Railway:**
   - Go to [railway.com](https://railway.com) and sign in
   - Click **"New Project"**
   - Select **"Deploy from GitHub repo"**
   - Choose your `vpay-flutter` repository
   - Railway will auto-detect the `backend` folder (via `nixpacks.toml`)

3. **Configure Root Directory:**
   - In your Railway project, go to **Settings**
   - Under **"Root Directory"**, enter: `backend`
   - This tells Railway to deploy from the backend folder

### Option B: Deploy via Railway CLI

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Navigate to backend folder
cd C:\Users\harsh\Documents\vpay-flutter\backend

# Initialize project
railway init

# Deploy
railway up
```

---

## ⚙️ Step 3: Configure Environment Variables

In your Railway project dashboard:

1. Go to **"Variables"** tab
2. Add the following:

| Variable | Value |
|----------|-------|
| `DATABASE_URL` | (Railway auto-provides this when you add PostgreSQL) |
| `SUPABASE_URL` | `https://qmuwykzbkcxabljiezsn.supabase.co` |
| `SUPABASE_KEY` | Your Supabase anon key |
| `CORS_ORIGINS` | `["https://your-app.railway.app","http://localhost:5173"]` |
| `HF_HOME` | `/tmp/huggingface` |
| `PORT` | (Auto-set by Railway, usually 8000) |

### Add PostgreSQL Database:

1. In Railway project, click **"New"** → **"Database"** → **"Add PostgreSQL"**
2. Railway will automatically add the `DATABASE_URL` variable
3. Wait for the database to provision

---

## 🧪 Step 4: Verify Deployment

### 4.1 Check Health Endpoint

Once deployed, test your API:

```bash
curl https://your-app.railway.app/health
```

Expected response:
```json
{"status":"ok","service":"VPay"}
```

### 4.2 Test Wallet Endpoint

```bash
curl https://your-app.railway.app/wallet
```

---

## 📱 Step 5: Update Flutter App

Update your Flutter app's API URL:

**File:** `frontend/lib/core/constants/api_constants.dart`

```dart
class ApiConstants {
  // Production (Railway)
  static const String baseUrl = 'https://your-app.railway.app';
  
  // Development (uncomment for local testing)
  // static const String baseUrl = 'http://10.0.2.2:8000';
}
```

Then rebuild your app:
```bash
cd frontend
flutter clean
flutter build apk  # or flutter build ios
```

---

## ⚠️ Important Notes

### ML Model Cold Start

Your backend uses ML models (Faster-Whisper, ECAPA-TDNN). On Railway:

- **First request after deploy:** 30-60 seconds (model loading)
- **Subsequent requests:** Fast (<2 seconds)

**Solutions:**
1. Keep `PRELOAD_ML_MODELS=true` (already set)
2. Use a [Railway Keep-Alive service](https://docs.railway.com/deploy/troubleshooting#keep-your-service-warm) (paid feature)
3. Accept the cold start for occasional use

### File Storage

Railway's filesystem is **ephemeral**. This means:

- ✅ SQLite database: **Will be lost** on redeploy - use PostgreSQL!
- ✅ Uploaded files: Will be lost - use cloud storage (S3, Supabase Storage)
- ✅ ML model cache: Set `HF_HOME=/tmp/huggingface` (cached per deployment)

### Logs & Debugging

View logs in Railway dashboard under **"Deployments"** → **"View Logs"**

Or use CLI:
```bash
railway logs
```

---

## 🔧 Troubleshooting

### "Connection refused" after deploy

1. Check that `DATABASE_URL` is set
2. Verify `CORS_ORIGINS` includes your Railway URL
3. Check logs for startup errors

### "Module not found" errors

Railway uses `nixpacks.toml` to install dependencies. If a package is missing:

1. Add it to `requirements.txt`
2. Redeploy (Railway auto-rebuilds on Git push)

### Database errors

- **SQLite mode (local):** Database is in `backend/data/vpay.db`
- **PostgreSQL mode (Railway):** Set `DATABASE_URL` environment variable

### High memory usage

ML models require ~2GB RAM. Railway's free tier may not be enough. Consider:

- Upgrading to Railway's paid plan
- Using smaller ML models (`WHISPER_MODEL_SIZE=tiny`)

---

## 📊 Deployment Checklist

- [ ] Code pushed to GitHub
- [ ] Railway project created
- [ ] Root directory set to `backend`
- [ ] PostgreSQL database added
- [ ] Environment variables configured
- [ ] Health endpoint responds (`/health`)
- [ ] Flutter app URL updated
- [ ] CORS configured for production

---

## 🎉 You're Done!

Your VPay backend is now running on Railway! 

**Next steps:**
1. Test all endpoints via the Swagger UI: `https://your-app.railway.app/docs`
2. Update your Flutter app's base URL
3. Test the complete flow (login → wallet → voice pay)

---

**Need help?** Check Railway's docs: [docs.railway.com](https://docs.railway.com)