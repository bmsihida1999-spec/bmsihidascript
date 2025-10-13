@echo off
echo ========================================
echo    مراقب مواعيد فيزا إسبانيا التلقائي
echo ========================================
echo.
echo جاري تشغيل التطبيق...
echo.

REM تحقق من وجود Python
python --version >nul 2>&1
if errorlevel 1 (
    echo خطأ: Python غير مثبت على النظام
    echo يرجى تثبيت Python من python.org
    pause
    exit /b 1
)

REM تثبيت المكتبات المطلوبة
echo تثبيت المكتبات المطلوبة...
pip install -r requirements.txt

REM تشغيل التطبيق
echo.
echo تشغيل الخادم...
echo افتح المتصفح واذهب إلى: http://localhost:5000
echo.
echo لإيقاف التطبيق اضغط Ctrl+C
echo.

python app.py

pause