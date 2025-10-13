# دليل النشر على Railway 🚀

## الخطوة 1: تحضير الكود
1. ارفع الكود إلى GitHub (إذا لم تفعل بعد)
2. تأكد من وجود جميع الملفات المطلوبة ✅

## الخطوة 2: إنشاء حساب Railway
1. اذهب إلى: https://railway.app
2. سجل دخول بـ GitHub
3. اختر "New Project"
4. اختر "Deploy from GitHub repo"
5. اختر مستودع التطبيق

## الخطوة 3: إعداد متغيرات البيئة
في لوحة Railway، اذهب إلى Variables وأضف:

```
SECRET_KEY=your-secret-key-here-make-it-long-and-random
FLASK_ENV=production
WHATSAPP_NUMBER=+966xxxxxxxxx
ALLOWED_HOSTS=*.railway.app
CHROME_BIN=/usr/bin/google-chrome
CHROMEDRIVER_PATH=/usr/bin/chromedriver
```

## الخطوة 4: إضافة قاعدة البيانات
1. في Railway، اضغط "Add Service"
2. اختر "PostgreSQL"
3. سيتم إنشاء DATABASE_URL تلقائياً

## الخطوة 5: النشر
- Railway سينشر التطبيق تلقائياً
- ستحصل على رابط مثل: https://your-app.railway.app

## 🔗 الرابط النهائي
بعد النشر، ستحصل على رابط يعمل 24/7 يمكنك مشاركته مع العملاء!