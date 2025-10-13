# دليل رفع الملفات على GitHub 🚀

## المشكلة الحالية:
```
Permission denied to ibrahimmsihida
```

## الحل 1: استخدام Personal Access Token

### الخطوات:
1. **اذهب إلى GitHub.com**
2. **Settings → Developer settings → Personal access tokens → Tokens (classic)**
3. **Generate new token (classic)**
4. **اختر الصلاحيات:**
   - ✅ repo (full control)
   - ✅ workflow
5. **انسخ الـ Token**

### استخدام الـ Token:
```bash
git remote set-url origin https://bmsihida1999-spec:YOUR_TOKEN@github.com/bmsihida1999-spec/bmsihidascript.git
git push -u origin main
```

## الحل 2: رفع الملفات يدوياً

### الملفات المطلوبة للرفع:
- ✅ app.py
- ✅ requirements.txt  
- ✅ Procfile
- ✅ runtime.txt
- ✅ railway.json
- ✅ render.yaml
- ✅ .env.example
- ✅ README.md
- ✅ DEPLOYMENT_GUIDE.md
- ✅ .gitignore
- ✅ templates/index.html
- ✅ static/manifest.json
- ✅ static/service-worker.js
- ✅ static/icon-192x192.svg
- ✅ static/icon-512x512.svg

### الملفات التي لا يجب رفعها:
- ❌ __pycache__/
- ❌ visa_bookings.db
- ❌ .env (الملف الحقيقي)
- ❌ run.bat

## بعد رفع الملفات:
1. اذهب إلى Railway.app
2. New Project → Deploy from GitHub
3. اختر المستودع: bmsihidascript
4. أضف متغيرات البيئة
5. أضف PostgreSQL database
6. احصل على الرابط النهائي!