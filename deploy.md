# 🚀 MOMENTUM TRADING SIGNALS - DEPLOYMENT REHBERİ

## 📋 **ÖN HAZIRLIK**

### 1. Gerekli Hesaplar
- ✅ **GitHub** hesabı
- ✅ **Vercel** hesabı (GitHub ile bağla)
- ✅ **Domain** (opsiyonel - vercel subdomain kullanabilirsin)

### 2. Yerel Test
```bash
# Backend test
cd backend
python simple_server.py

# Frontend test  
cd frontend
npm start
```

## 🌐 **VERCEL DEPLOYMENT (ÖNERİLEN)**

### ADIM 1: GitHub'a Push
```bash
# Proje klasöründe
git init
git add .
git commit -m "Production ready: KRO+LMO strategies with 1.5+ RR filter"
git branch -M main
git remote add origin https://github.com/USERNAME/momentum-trading-signals.git
git push -u origin main
```

### ADIM 2: Vercel Deploy
1. **Vercel.com** → Sign up with GitHub
2. **Import Project** → GitHub repository seç
3. **Framework**: React (otomatik algılar)
4. **Root Directory**: Leave empty (. kullan)
5. **Build Settings**:
   - Build Command: `cd frontend && npm run build`
   - Output Directory: `frontend/build`
6. **Deploy** butonuna bas!

### ADIM 3: Environment Variables (Vercel Dashboard)
```
API_BASE_URL=https://your-app.vercel.app/api
NODE_ENV=production
```

## 🔧 **NETLIFY DEPLOYMENT (ALTERNATIF)**

### ADIM 1: Build Settings
```bash
# Build command
cd frontend && npm run build

# Publish directory  
frontend/build

# Functions directory
backend
```

### ADIM 2: Netlify Functions
```bash
# netlify.toml oluştur
[build]
  command = "cd frontend && npm run build"
  publish = "frontend/build"
  functions = "backend"

[build.environment]
  NODE_ENV = "production"

[[redirects]]
  from = "/api/*"
  to = "/.netlify/functions/:splat"
  status = 200

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200
```

## 🐳 **DOCKER DEPLOYMENT (ADVANCED)**

### ADIM 1: Dockerfile
```dockerfile
# Multi-stage build
FROM node:18-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci --only=production
COPY frontend/ ./
RUN npm run build

FROM python:3.9-slim AS backend
WORKDIR /app
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./
COPY --from=frontend-build /app/frontend/build ./static

EXPOSE 8000
CMD ["uvicorn", "vercel_app:app", "--host", "0.0.0.0", "--port", "8000"]
```

### ADIM 2: Deploy to Railway/Render
```bash
# Railway
npm i -g @railway/cli
railway login
railway init
railway up

# Render
# GitHub'a push → Render.com → New Web Service
```

## 🔑 **PRODUCTION CHECKLIST**

### ✅ Güvenlik
- [ ] API rate limiting ekle
- [ ] CORS origins'i specific domain'e sınırla  
- [ ] Environment variables kullan
- [ ] HTTPS enforce et

### ✅ Performance
- [ ] Frontend minification enabled
- [ ] API response caching
- [ ] CDN kullan
- [ ] Image optimization

### ✅ Monitoring
- [ ] Error logging (Sentry)
- [ ] Analytics (Google Analytics)
- [ ] Uptime monitoring
- [ ] Performance monitoring

## 🌟 **HIZLI BAŞLANGIÇ - 5 DAKİKA**

```bash
# 1. GitHub'a push
git add . && git commit -m "Production ready" && git push

# 2. Vercel'e git
vercel.com → Import Project → Your Repo → Deploy

# 3. 2-3 dakika bekle
# 4. Site hazır! 🎉
```

## 🆘 **SORUN GİDERME**

### Build Errors
```bash
# Frontend build error
cd frontend && npm install && npm run build

# Backend import error  
cd backend && pip install -r requirements.txt
```

### API Errors
- Environment variables doğru mu?
- CORS settings production için güncel mi?
- API endpoints production URL kullanıyor mu?

## 📱 **MOBILE OPTIMIZATION**

Frontend PWA için:
```javascript
// public/manifest.json
{
  "name": "Momentum Trading Signals",
  "short_name": "MomentumSignals", 
  "display": "standalone",
  "theme_color": "#000000"
}
```

---

**🎯 SONUÇ**: Bu adımları takip ederek profesyonel trading signals platformunu canlıya alabilirsin! 