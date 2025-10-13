from flask import Flask, render_template, request, jsonify, redirect, url_for
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import threading
import time
import json
import os
from datetime import datetime
import pywhatkit as pwk
import schedule
import sqlite3
from werkzeug.security import generate_password_hash
import secrets

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(16))

# Global variables
monitoring_active = False
user_data = {}
monitoring_thread = None

# Database setup
def init_db():
    """Initialize database for storing user data - supports both SQLite and PostgreSQL"""
    database_url = os.environ.get('DATABASE_URL')
    
    if database_url and database_url.startswith('postgres'):
        # Cloud PostgreSQL database
        import psycopg2
        from urllib.parse import urlparse
        
        # Parse the database URL
        parsed_url = urlparse(database_url)
        
        # Connect to PostgreSQL
        conn = psycopg2.connect(
            host=parsed_url.hostname,
            database=parsed_url.path[1:],
            user=parsed_url.username,
            password=parsed_url.password,
            port=parsed_url.port
        )
        cursor = conn.cursor()
        
        # Create table with PostgreSQL syntax
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bookings (
                id SERIAL PRIMARY KEY,
                session_id VARCHAR(255) UNIQUE,
                full_name VARCHAR(255),
                passport_number VARCHAR(50),
                birth_date VARCHAR(20),
                phone_number VARCHAR(20),
                email VARCHAR(255),
                visa_type VARCHAR(100),
                preferred_city VARCHAR(100),
                whatsapp_number VARCHAR(20),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status VARCHAR(20) DEFAULT 'active'
            )
        ''')
        conn.commit()
        conn.close()
        print("PostgreSQL database initialized successfully")
        
    else:
        # Local SQLite database
        conn = sqlite3.connect('visa_bookings.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE,
                full_name TEXT,
                passport_number TEXT,
                birth_date TEXT,
                phone_number TEXT,
                email TEXT,
                visa_type TEXT,
                preferred_city TEXT,
                whatsapp_number TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'active'
            )
        ''')
        conn.commit()
        conn.close()
        print("SQLite database initialized successfully")

def get_db_connection():
    """Get database connection - supports both SQLite and PostgreSQL"""
    database_url = os.environ.get('DATABASE_URL')
    
    if database_url and database_url.startswith('postgres'):
        import psycopg2
        from urllib.parse import urlparse
        parsed_url = urlparse(database_url)
        
        return psycopg2.connect(
            host=parsed_url.hostname,
            database=parsed_url.path[1:],
            user=parsed_url.username,
            password=parsed_url.password,
            port=parsed_url.port
        )
    else:
        return sqlite3.connect('visa_bookings.db')

def save_user_data(session_id, data):
    """Save user data to database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        if os.environ.get('DATABASE_URL', '').startswith('postgres'):
            # PostgreSQL syntax
            cursor.execute('''
                INSERT INTO bookings (session_id, full_name, passport_number, birth_date, 
                                    phone_number, email, visa_type, preferred_city, whatsapp_number)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (session_id) DO UPDATE SET
                    full_name = EXCLUDED.full_name,
                    passport_number = EXCLUDED.passport_number,
                    birth_date = EXCLUDED.birth_date,
                    phone_number = EXCLUDED.phone_number,
                    email = EXCLUDED.email,
                    visa_type = EXCLUDED.visa_type,
                    preferred_city = EXCLUDED.preferred_city,
                    whatsapp_number = EXCLUDED.whatsapp_number
            ''', (session_id, data.get('full_name'), data.get('passport_number'), 
                  data.get('birth_date'), data.get('phone_number'), data.get('email'),
                  data.get('visa_type'), data.get('preferred_city'), data.get('whatsapp_number')))
        else:
            # SQLite syntax
            cursor.execute('''
                INSERT OR REPLACE INTO bookings (session_id, full_name, passport_number, birth_date, 
                                               phone_number, email, visa_type, preferred_city, whatsapp_number)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (session_id, data.get('full_name'), data.get('passport_number'), 
                  data.get('birth_date'), data.get('phone_number'), data.get('email'),
                  data.get('visa_type'), data.get('preferred_city'), data.get('whatsapp_number')))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error saving user data: {e}")
        return False
    finally:
        conn.close()

def load_user_data(session_id):
    """Load user data from database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        if os.environ.get('DATABASE_URL', '').startswith('postgres'):
            cursor.execute('SELECT * FROM bookings WHERE session_id = %s', (session_id,))
        else:
            cursor.execute('SELECT * FROM bookings WHERE session_id = ?', (session_id,))
        
        row = cursor.fetchone()
        if row:
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))
        return None
    except Exception as e:
        print(f"Error loading user data: {e}")
        return None
    finally:
        conn.close()

# Initialize database on startup
init_db()

class VisaBookingBot:
    def __init__(self, user_data):
        self.user_data = user_data
        self.driver = None
        
    def setup_driver(self):
        """إعداد متصفح Chrome للبيئة السحابية"""
        chrome_options = Options()
        
        # إعدادات للبيئة السحابية
        chrome_options.add_argument("--headless")  # تشغيل بدون واجهة
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # استخدام ChromeDriverManager للتحديث التلقائي
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
        except:
            # Fallback للبيئة المحلية
            self.driver = webdriver.Chrome(options=chrome_options)
            
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
    def send_whatsapp_notification(self, message):
        """إرسال إشعار WhatsApp"""
        try:
            # استخدام رقم WhatsApp من متغيرات البيئة أو القيمة الافتراضية
            phone_number = os.environ.get('WHATSAPP_NUMBER', self.user_data.get('whatsapp_number', '+212650731946'))
            pwk.sendwhatmsg_instantly(phone_number, message, wait_time=10, tab_close=True)
            print(f"تم إرسال إشعار WhatsApp: {message}")
        except Exception as e:
            print(f"خطأ في إرسال WhatsApp: {str(e)}")
    
    def check_appointments(self):
        """فحص توفر المواعيد"""
        try:
            self.setup_driver()
            self.driver.get("https://blsspainmorocco.com/")
            
            # انتظار تحميل الصفحة
            WebDriverWait(self.driver, 10).wait(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # البحث عن أزرار أو روابط المواعيد
            appointment_buttons = self.driver.find_elements(By.XPATH, "//a[contains(text(), 'Appointment') or contains(text(), 'موعد') or contains(text(), 'Book')]")
            
            if appointment_buttons:
                print("تم العثور على أزرار المواعيد")
                appointment_buttons[0].click()
                
                # انتظار تحميل صفحة المواعيد
                time.sleep(3)
                
                # البحث عن المواعيد المتاحة
                available_slots = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'available') or contains(@class, 'free') or contains(text(), 'Available')]")
                
                if available_slots:
                    print("تم العثور على مواعيد متاحة!")
                    self.send_whatsapp_notification("🎉 تم العثور على موعد متاح لفيزا إسبانيا! سيتم الحجز الآن...")
                    
                    # محاولة الحجز التلقائي
                    success = self.book_appointment()
                    if success:
                        self.send_whatsapp_notification("✅ تم حجز الموعد بنجاح! تحقق من بريدك الإلكتروني للتأكيد.")
                    else:
                        self.send_whatsapp_notification("⚠️ تم العثور على موعد لكن فشل الحجز التلقائي. يرجى الحجز يدوياً.")
                    
                    return True
                else:
                    print("لا توجد مواعيد متاحة حالياً")
                    return False
            else:
                print("لم يتم العثور على أزرار المواعيد")
                return False
                
        except Exception as e:
            print(f"خطأ في فحص المواعيد: {str(e)}")
            self.send_whatsapp_notification(f"❌ خطأ في فحص المواعيد: {str(e)}")
            return False
        finally:
            if self.driver:
                self.driver.quit()
    
    def book_appointment(self):
        """حجز الموعد تلقائياً"""
        try:
            # ملء النموذج بالبيانات المحفوظة
            if 'full_name' in self.user_data:
                name_field = self.driver.find_element(By.XPATH, "//input[@name='name' or @id='name' or contains(@placeholder, 'Name')]")
                name_field.clear()
                name_field.send_keys(self.user_data['full_name'])
            
            if 'passport_number' in self.user_data:
                passport_field = self.driver.find_element(By.XPATH, "//input[@name='passport' or @id='passport' or contains(@placeholder, 'Passport')]")
                passport_field.clear()
                passport_field.send_keys(self.user_data['passport_number'])
            
            if 'email' in self.user_data:
                email_field = self.driver.find_element(By.XPATH, "//input[@name='email' or @id='email' or @type='email']")
                email_field.clear()
                email_field.send_keys(self.user_data['email'])
            
            if 'phone' in self.user_data:
                phone_field = self.driver.find_element(By.XPATH, "//input[@name='phone' or @id='phone' or @type='tel']")
                phone_field.clear()
                phone_field.send_keys(self.user_data['phone'])
            
            # النقر على زر الحجز
            book_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Book') or contains(text(), 'Submit') or contains(text(), 'حجز')]")
            book_button.click()
            
            # انتظار التأكيد
            time.sleep(5)
            
            # التحقق من نجاح الحجز
            success_indicators = self.driver.find_elements(By.XPATH, "//div[contains(text(), 'Success') or contains(text(), 'Confirmed') or contains(text(), 'نجح')]")
            
            return len(success_indicators) > 0
            
        except Exception as e:
            print(f"خطأ في حجز الموعد: {str(e)}")
            return False

def monitor_appointments():
    """مراقبة المواعيد كل 30 دقيقة"""
    global monitoring_active, user_data
    
    bot = VisaBookingBot(user_data)
    
    while monitoring_active:
        try:
            print(f"فحص المواعيد في {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            appointment_found = bot.check_appointments()
            
            if appointment_found:
                print("تم العثور على موعد وتم الحجز!")
                # يمكن إيقاف المراقبة بعد الحجز الناجح
                # monitoring_active = False
                # break
            
            # انتظار 30 دقيقة قبل الفحص التالي
            for i in range(1800):  # 30 دقيقة = 1800 ثانية
                if not monitoring_active:
                    break
                time.sleep(1)
                
        except Exception as e:
            print(f"خطأ في المراقبة: {str(e)}")
            time.sleep(60)  # انتظار دقيقة واحدة في حالة الخطأ

@app.route('/')
def index():
    """الصفحة الرئيسية"""
    return render_template('index.html')

@app.route('/start_monitoring', methods=['POST'])
def start_monitoring():
    """بدء مراقبة المواعيد"""
    global monitoring_active, user_data, monitoring_thread
    
    # إنشاء معرف جلسة فريد
    session_id = request.form.get('session_id') or secrets.token_hex(8)
    
    # حفظ بيانات المستخدم
    user_data = {
        'full_name': request.form.get('full_name'),
        'passport_number': request.form.get('passport_number'),
        'birth_date': request.form.get('birth_date'),
        'phone_number': request.form.get('phone'),
        'email': request.form.get('email'),
        'visa_type': request.form.get('visa_type'),
        'preferred_city': request.form.get('city'),
        'whatsapp_number': request.form.get('whatsapp_number') or request.form.get('phone')
    }
    
    # حفظ البيانات في قاعدة البيانات
    if save_user_data(session_id, user_data):
        print(f"تم حفظ بيانات المستخدم بنجاح - معرف الجلسة: {session_id}")
    else:
        print("فشل في حفظ بيانات المستخدم")
    
    # حفظ البيانات في ملف
    with open('user_data.json', 'w', encoding='utf-8') as f:
        json.dump(user_data, f, ensure_ascii=False, indent=2)
    
    if not monitoring_active:
        monitoring_active = True
        monitoring_thread = threading.Thread(target=monitor_appointments)
        monitoring_thread.daemon = True
        monitoring_thread.start()
        
        # إرسال إشعار بدء المراقبة
        bot = VisaBookingBot(user_data)
        bot.send_whatsapp_notification("🚀 تم بدء مراقبة مواعيد فيزا إسبانيا. سيتم فحص المواعيد كل 30 دقيقة.")
        
        return jsonify({'status': 'success', 'message': 'تم بدء المراقبة بنجاح!'})
    else:
        return jsonify({'status': 'info', 'message': 'المراقبة تعمل بالفعل!'})

@app.route('/stop_monitoring', methods=['POST'])
def stop_monitoring():
    """إيقاف مراقبة المواعيد"""
    global monitoring_active
    
    monitoring_active = False
    
    # إرسال إشعار إيقاف المراقبة
    if user_data:
        bot = VisaBookingBot(user_data)
        bot.send_whatsapp_notification("⏹️ تم إيقاف مراقبة مواعيد فيزا إسبانيا.")
    
    return jsonify({'status': 'success', 'message': 'تم إيقاف المراقبة!'})

@app.route('/status')
def get_status():
    """الحصول على حالة المراقبة"""
    return jsonify({
        'monitoring_active': monitoring_active,
        'last_check': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

if __name__ == '__main__':
    # إنشاء مجلد القوالب إذا لم يكن موجوداً
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    # تشغيل التطبيق مع إعدادات الإنتاج
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    app.run(debug=debug_mode, host='0.0.0.0', port=port)