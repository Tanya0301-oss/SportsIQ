# 🚀 Quick Start Guide - From Zero to Deployed

Get your Sports Analytics Platform up and running in 30 minutes!

---

## 🎯 What You'll Have After This Guide

✅ Backend running on Railway  
✅ Frontend running on Vercel  
✅ Real-time predictions working  
✅ Live updates streaming via WebSocket  
✅ Database synced and populated  

---

## ⏱️ 5-Minute Setup (Local Development)

### Prerequisites
- Python 3.9+
- Node.js 16+
- Git

### Windows Users
```bash
# Run the setup helper
setup-helper.bat

# Choose option 4 "Setup both"
# Choose option 6 "Run development servers"
```

### Linux/Mac Users
```bash
# Make script executable
chmod +x setup.sh

# Run setup
./setup.sh

# Choose option 4 "Setup both"
# Choose option 6 "Run development servers"
```

**Done!** 🎉
- Backend: http://localhost:8000
- Frontend: http://localhost:5173
- API Docs: http://localhost:8000/docs

---

## 🚄 15-Minute Deployment (Railway + Vercel)

### Step 1: Prepare GitHub (2 minutes)

```bash
# Make sure code is on GitHub
git add .
git commit -m "Ready for deployment"
git push origin main
```

### Step 2: Deploy Backend to Railway (5 minutes)

1. Go to https://railway.app
2. Sign up with GitHub
3. Click "Create New Project"
4. Select "Deploy from GitHub repo"
5. Choose `sports-analytics`
6. Click "Import"
7. Click "Add Service" → "Database" → "PostgreSQL"
8. Click Backend service → "Variables"
9. Add these variables:
   ```env
   APP_NAME=Sports Analytics Platform
   DEBUG=False
   SECRET_KEY=random-secret-key-here
   DATA_SOURCE=simulator
   LOG_LEVEL=INFO
   ```
10. Wait for ✅ Deployment Complete
11. **Copy your Railway backend URL** (looks like: `https://sports-analytics-backend-production-xxxx.railway.app`)

### Step 3: Deploy Frontend to Vercel (5 minutes)

1. Go to https://vercel.app
2. Sign up with GitHub
3. Click "Add New..." → "Project"
4. Select `sports-analytics` repo
5. Set Root Directory: `frontend/`
6. Under "Environment Variables", add:
   ```env
   VITE_API_URL=https://your-railway-url/api/v1
   VITE_WS_URL=wss://your-railway-url/ws
   ```
   (Replace `your-railway-url` with your Railway URL from Step 2)
7. Click "Deploy"
8. Wait for ✅ Build Complete
9. **Copy your Vercel frontend URL** (looks like: `https://sports-analytics-frontend.vercel.app`)

### Step 4: Update Backend CORS (3 minutes)

1. Go back to Railway Dashboard
2. Click Backend service
3. Go to "Variables"
4. Update `CORS_ORIGINS`:
   ```env
   CORS_ORIGINS=https://your-vercel-url,http://localhost:5173
   ```
5. Save - Railway auto-redeploys

**Done!** 🎉 Your app is live!

- **Frontend:** https://your-vercel-url.vercel.app
- **API Docs:** https://your-railway-url.railway.app/docs
- **WebSocket:** wss://your-railway-url.railway.app/ws

---

## ✅ Verify It Works

### Test 1: Check API
```bash
# Replace with your Railway URL
curl https://your-railway-url.railway.app/docs
# Should show Swagger UI
```

### Test 2: Check Frontend
1. Visit your Vercel URL
2. Go to "Match List"
3. Should see match data loading
4. Check browser console (F12) - no errors

### Test 3: Check WebSocket
1. In browser console, should see WebSocket connection
2. Predictions should update in real-time

---

## 🔄 Making Changes & Redeploying

### Update Backend
```bash
# 1. Make changes locally
# 2. Test on localhost
# 3. Push to GitHub

git add backend/
git commit -m "Fix: description"
git push origin main

# Railway automatically redeploys!
```

### Update Frontend
```bash
# 1. Make changes locally
# 2. Test with npm run dev
# 3. Push to GitHub

git add frontend/
git commit -m "Update: description"
git push origin main

# Vercel automatically redeploys!
```

---

## 🆘 Troubleshooting

### Frontend shows blank page
1. Open browser console (F12)
2. Look for error messages
3. Check `VITE_API_URL` environment variable in Vercel

### Can't connect to API
1. Check your Railway backend URL is correct
2. Test: `curl https://your-railway-url.railway.app/docs`
3. Update `VITE_API_URL` in Vercel if URL changed

### WebSocket not connecting
1. Make sure `VITE_WS_URL` uses `wss://` (not `ws://`)
2. Check CORS settings in Railway backend
3. Check browser console for specific error

### Database errors
1. In Railway, make sure PostgreSQL is linked to Backend
2. Check logs for connection errors
3. Database_URL should be auto-set by Railway

### Model not found error
1. Run: `railway run python backend/ml/train.py`
2. Or check that `ml/artifacts/` folder has files

### Can't access admin panel / predictions
1. Check the `/docs` API endpoint exists
2. Verify database was created
3. Check logs for startup errors

---

## 📊 Monitor Your App

### Railway Dashboard
- Check CPU/Memory usage
- View real-time logs
- Monitor database size
- See deployment history

### Vercel Dashboard
- Check build times
- View performance analytics
- See deployment history
- Check Core Web Vitals

### Check Logs
```bash
# View Railway logs (requires Railway CLI)
railway run python -c "print('Connected to database')"
```

---

## 🔐 Security Reminder

⚠️ **Important:**
- Change `SECRET_KEY` to a random value
- Never commit `.env` files
- Keep API keys in environment variables only
- Use `DEBUG=False` in production
- HTTPS is automatic on both platforms

---

## 📚 Next Steps

After deployment:

1. **Read the full docs:**
   - [README.md](README.md) - Complete project overview
   - [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Detailed deployment steps
   - [DEPLOYMENT_REFERENCE.md](DEPLOYMENT_REFERENCE.md) - Quick reference

2. **Customize your app:**
   - Add your own data
   - Train the ML model with more matches
   - Add new features
   - Integrate other APIs

3. **Scale it up:**
   - Add more consumer instances
   - Use Redis for caching
   - Add more database replicas
   - Implement rate limiting

4. **Go live:**
   - Buy a custom domain
   - Set up custom email
   - Create marketing page
   - Monitor user feedback

---

## 🎓 Learning Resources

- **FastAPI:** https://fastapi.tiangolo.com/
- **React:** https://react.dev/
- **Railway:** https://docs.railway.app/
- **Vercel:** https://vercel.com/docs
- **XGBoost:** https://xgboost.readthedocs.io/
- **SHAP:** https://shap.readthedocs.io/

---

## ❓ FAQ

**Q: How much does this cost?**
A: Both Railway and Vercel have free tiers. Railway includes free PostgreSQL and compute. Vercel includes free hosting and builds.

**Q: Can I use a different database?**
A: Yes! Railway supports MySQL, MongoDB, etc. Update `DATABASE_URL` in config.

**Q: How do I use real football data instead of simulator?**
A: Get API key from football-data.org, set `FOOTBALL_DATA_API_KEY` in Railway, change `DATA_SOURCE=live`.

**Q: How do I train a better ML model?**
A: Get more historical match data, run `python backend/ml/train.py`, Railway will use new model.

**Q: Can I deploy to AWS/GCP instead?**
A: Yes! See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for AWS/DigitalOcean options.

**Q: How do I rollback if something breaks?**
A: Both Railway and Vercel keep deployment history. Click "Rollback" in dashboard.

---

## 🎉 You're Done!

Your Sports Analytics Platform is now:
- ✅ Running in production
- ✅ Accessible from anywhere
- ✅ Automatically updating from GitHub
- ✅ Monitored and logged
- ✅ Secure with HTTPS
- ✅ Scalable for future growth

**Congrats!** 🏆

---

## 📞 Need Help?

- Check browser console (F12) for error messages
- Review Railway/Vercel logs
- See [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) for detailed steps
- Visit [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for troubleshooting

---

**Last Updated:** May 2026

**Status:** ✅ Production Ready

**Deployment Time:** ~30 minutes
