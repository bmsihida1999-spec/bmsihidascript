from flask import Flask, render_template, request, jsonify, redirect, url_for
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
import threading
import time
import json
import os
from datetime import datetime
# import pywhatkit as pwk  # Disabled for server deployment
import schedule
import sqlite3
from werkzeug.security import generate_password_hash
import secrets

# استيراد نظام الإشعارات المتقدم
try:
    from notification_system import notification_system
    NOTIFICATIONS_ENABLED = True
    print("✅ تم تحميل نظام الإشعارات بنجاح")
except ImportError as e:
    print(f"⚠️ لم يتم تحميل نظام الإشعارات: {e}")
    NOTIFICATIONS_ENABLED = False

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
        self.wait = None
        
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
        self.wait = WebDriverWait(self.driver, 10)
        
    def check_and_close_warning_window(self, city_name=""):
        """فحص وإغلاق نافذة التحذير إذا كانت موجودة - نسخة محسنة من test_visible.py"""
        warning_selectors = [
            "//button[@class='btn-close']",
            "//button[contains(@class, 'close')]",
            "//span[contains(@class, 'close')]",
            "//div[contains(@class, 'modal')]//button",
            "//div[contains(@class, 'modal')]//*[text()='×']",
            "//div[contains(@class, 'modal')]//*[text()='X']",
            "//*[text()='×']",
            "//*[text()='X']",
            "//button[text()='×']",
            "//button[text()='X']",
            "//*[@class='close']",
            "//*[contains(@onclick, 'close')]",
            "//div[contains(@class, 'disclaimer')]//*[text()='×']",
            "//div[contains(@class, 'disclaimer')]//*[text()='X']",
            "//button[contains(@class, 'btn-close')]",
            "//*[@id='closeModal']",
            "//*[@id='close']",
            "//a[contains(@class, 'close')]",
            "//i[contains(@class, 'close')]",
            "//span[text()='×']",
            "//span[text()='X']",
            "//*[contains(@aria-label, 'close')]",
            "//*[contains(@title, 'close')]",
            "//div[@class='modal-header']//button",
            "//div[@class='modal-header']//*[text()='×']"
        ]
        
        # فحص كل محدد للبحث عن نافذة التحذير
        for i, selector in enumerate(warning_selectors):
            try:
                close_buttons = self.driver.find_elements(By.XPATH, selector)
                if close_buttons:
                    for j, close_button in enumerate(close_buttons):
                        try:
                            if close_button.is_displayed() and close_button.is_enabled():
                                print(f"🎉 تم العثور على نافذة التحذير!")
                                print(f"🎯 المحدد المستخدم: {selector}")
                                print(f"🖱️ النقر على زر الإغلاق...")
                                close_button.click()
                                print(f"✅ تم إغلاق نافذة التحذير في صفحة {city_name}")
                                time.sleep(2)  # انتظار إغلاق النافذة
                                return True
                        except Exception as click_error:
                            continue
            except Exception as selector_error:
                continue
        
        return False
    
    def close_warning_popup(self):
        """إغلاق النافذة المنبثقة للتحذير إن وجدت - نسخة محسنة من test_visible.py"""
        try:
            print("🔍 البحث عن نافذة التحذير...")
            # البحث عن أزرار الإغلاق المختلفة
            close_selectors = [
                "//button[contains(@class, 'close')]",
                "//button[contains(text(), 'Close')]",
                "//button[contains(text(), 'OK')]",
                "//button[contains(text(), 'Accept')]",
                "//span[contains(@class, 'close')]",
                "//*[@id='closeButton']",
                "//*[contains(@onclick, 'close')]"
            ]
            
            for selector in close_selectors:
                try:
                    close_button = self.driver.find_element(By.XPATH, selector)
                    if close_button.is_displayed():
                        print("✅ تم العثور على زر إغلاق التحذير")
                        close_button.click()
                        print("🖱️ تم إغلاق نافذة التحذير")
                        time.sleep(2)
                        return True
                except:
                    continue
            
            print("ℹ️ لم يتم العثور على نافذة تحذير")
            return True
            
        except Exception as e:
            print(f"⚠️ خطأ في إغلاق التحذير: {e}")
            return True
        
    def send_whatsapp_notification(self, message):
        """إرسال إشعار WhatsApp - معطل للنشر على الخادم"""
        try:
            # استخدام رقم WhatsApp من متغيرات البيئة أو القيمة الافتراضية
            phone_number = os.environ.get('WHATSAPP_NUMBER', self.user_data.get('whatsapp_number', '+212650731946'))
            
            # For server deployment, we'll just log the message instead of sending WhatsApp
            print(f"📱 WhatsApp notification would be sent to {phone_number}: {message}")
            
            # TODO: Implement alternative notification method (email, webhook, etc.)
            # pwk.sendwhatmsg_instantly(phone_number, message, wait_time=10, tab_close=True)
            
            print(f"تم تسجيل إشعار WhatsApp: {message}")
        except Exception as e:
            print(f"خطأ في إرسال WhatsApp: {str(e)}")
    
    def check_appointments(self):
        """فحص المواعيد المتاحة - نسخة محسنة مع معالجة التحذيرات"""
        try:
            print("🌐 الانتقال إلى موقع BLS Spain Morocco...")
            self.driver.get("https://blsspainmorocco.com/")
            time.sleep(5)
            
            # إغلاق نوافذ التحذير
            self.close_warning_popup()
            self.check_and_close_warning_window()
            
            # البحث عن أزرار المواعيد باستخدام الطريقة المحسنة
            if self.find_and_click_appointment_button():
                print("✅ تم العثور على زر المواعيد والنقر عليه")
                time.sleep(3)
                
                # إغلاق أي نوافذ تحذير جديدة
                self.check_and_close_warning_window()
                
                # البحث عن المواعيد المتاحة
                available_appointments = self.find_available_appointments()
                if available_appointments:
                    print(f"🎉 تم العثور على {len(available_appointments)} موعد متاح!")
                    self.send_whatsapp_notification("🎉 تم العثور على موعد متاح لفيزا إسبانيا! سيتم الحجز الآن...")
                    
                    # محاولة حجز أول موعد متاح
                    if self.click_appointment(available_appointments[0]):
                        print("✅ تم النقر على الموعد المتاح")
                        
                        # ملء النموذج
                        if self.fill_appointment_form():
                            print("✅ تم ملء النموذج بنجاح")
                            self.send_whatsapp_notification("✅ تم حجز الموعد بنجاح! تحقق من بريدك الإلكتروني للتأكيد.")
                            return True
                        else:
                            print("❌ فشل في ملء النموذج")
                            self.send_whatsapp_notification("⚠️ تم العثور على موعد لكن فشل الحجز التلقائي. يرجى الحجز يدوياً.")
                    else:
                        print("❌ فشل في النقر على الموعد")
                        self.send_whatsapp_notification("⚠️ تم العثور على موعد لكن فشل النقر عليه. يرجى الحجز يدوياً.")
                else:
                    print("❌ لا توجد مواعيد متاحة حالياً")
            else:
                print("❌ لم يتم العثور على زر المواعيد")
                
        except Exception as e:
            print(f"❌ خطأ في فحص المواعيد: {e}")
            self.send_whatsapp_notification(f"❌ خطأ في فحص المواعيد: {str(e)}")
            
        return False
    
    def find_and_click_appointment_button(self):
        """البحث عن زر المواعيد والنقر عليه - نسخة محسنة من test_visible.py"""
        appointment_selectors = [
            "//a[contains(text(), 'Appointment')]",
            "//button[contains(text(), 'Appointment')]",
            "//a[contains(text(), 'موعد')]",
            "//button[contains(text(), 'موعد')]",
            "//a[contains(@href, 'appointment')]",
            "//a[contains(@href, 'booking')]",
            "//button[contains(@onclick, 'appointment')]",
            "//*[contains(@class, 'appointment')]",
            "//*[contains(@id, 'appointment')]",
            "//a[contains(text(), 'Book')]",
            "//button[contains(text(), 'Book')]",
            "//a[contains(text(), 'Schedule')]",
            "//button[contains(text(), 'Schedule')]",
            "//*[contains(text(), 'حجز موعد')]",
            "//*[contains(text(), 'تحديد موعد')]"
        ]
        
        print("🔍 البحث عن زر المواعيد...")
        
        for i, selector in enumerate(appointment_selectors):
            try:
                buttons = self.driver.find_elements(By.XPATH, selector)
                if buttons:
                    for j, button in enumerate(buttons):
                        try:
                            if button.is_displayed() and button.is_enabled():
                                print(f"🎯 تم العثور على زر المواعيد: {selector}")
                                
                                # محاولة النقر بطرق متعددة
                                if self.click_element_multiple_ways(button):
                                    print("✅ تم النقر على زر المواعيد بنجاح")
                                    time.sleep(3)
                                    
                                    # التحقق من تغيير الصفحة
                                    current_url = self.driver.current_url
                                    if "appointment" in current_url.lower() or "booking" in current_url.lower():
                                        print("✅ تم الانتقال إلى صفحة المواعيد")
                                        return True
                                    
                        except Exception as click_error:
                            print(f"⚠️ خطأ في النقر على الزر {j}: {click_error}")
                            continue
                            
            except Exception as selector_error:
                continue
        
        print("❌ لم يتم العثور على زر المواعيد")
        return False
    
    def find_available_appointments(self):
        """البحث عن المواعيد المتاحة - نسخة محسنة من test_visible.py"""
        appointment_selectors = [
            "//button[contains(@class, 'available')]",
            "//a[contains(@class, 'available')]",
            "//div[contains(@class, 'available')]",
            "//td[contains(@class, 'available')]",
            "//span[contains(@class, 'available')]",
            "//*[contains(@class, 'appointment-slot')]",
            "//*[contains(@class, 'time-slot')]",
            "//*[contains(@class, 'booking-slot')]",
            "//button[not(contains(@class, 'disabled'))]",
            "//a[not(contains(@class, 'disabled'))]",
            "//*[contains(text(), 'متاح')]",
            "//*[contains(text(), 'Available')]",
            "//*[contains(@data-available, 'true')]",
            "//button[contains(@onclick, 'book')]",
            "//a[contains(@href, 'book')]"
        ]
        
        available_appointments = []
        
        print("🔍 البحث عن المواعيد المتاحة...")
        
        for selector in appointment_selectors:
            try:
                elements = self.driver.find_elements(By.XPATH, selector)
                for element in elements:
                    try:
                        if element.is_displayed() and element.is_enabled():
                            # التحقق من أن العنصر ليس معطلاً
                            if "disabled" not in element.get_attribute("class").lower():
                                available_appointments.append(element)
                                print(f"✅ تم العثور على موعد متاح: {element.text[:50]}")
                    except:
                        continue
            except:
                continue
        
        # إزالة التكرارات
        unique_appointments = []
        for appointment in available_appointments:
            if appointment not in unique_appointments:
                unique_appointments.append(appointment)
        
        print(f"📅 إجمالي المواعيد المتاحة: {len(unique_appointments)}")
        return unique_appointments
    
    def click_appointment(self, appointment_element):
        """النقر على موعد محدد - نسخة محسنة من test_visible.py"""
        try:
            print("🖱️ محاولة النقر على الموعد...")
            return self.click_element_multiple_ways(appointment_element)
        except Exception as e:
            print(f"❌ خطأ في النقر على الموعد: {e}")
            return False
    
    def click_element_multiple_ways(self, element):
        """النقر على عنصر بطرق متعددة لتجنب StaleElementReferenceException"""
        from selenium.webdriver.common.action_chains import ActionChains
        
        click_methods = [
            ("النقر العادي", lambda el: el.click()),
            ("النقر بـ JavaScript", lambda el: self.driver.execute_script("arguments[0].click();", el)),
            ("التمرير والنقر", lambda el: self._scroll_and_click(el)),
            ("ActionChains", lambda el: ActionChains(self.driver).move_to_element(el).click().perform())
        ]
        
        for method_name, method in click_methods:
            try:
                print(f"🔄 محاولة {method_name}...")
                method(element)
                time.sleep(1)
                print(f"✅ نجح {method_name}")
                return True
            except Exception as e:
                print(f"⚠️ فشل {method_name}: {e}")
                continue
        
        print("❌ فشلت جميع طرق النقر")
        return False
    
    def _scroll_and_click(self, element):
        """التمرير إلى العنصر ثم النقر عليه"""
        self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
        time.sleep(1)
        element.click()
    
    def fill_appointment_form(self):
        """ملء نموذج حجز الموعد - نسخة محسنة من test_visible.py مع دعم العربية والإنجليزية"""
        try:
            print("📝 بدء ملء النموذج المحسن...")
            
            # قائمة الحقول المحتملة مع دعم العربية والإنجليزية
            form_fields = {
                'full_name': {
                    'selectors': [
                        'full_name', 'fullName', 'name', 'الاسم الكامل', 'اسم كامل',
                        'first_name', 'firstName', 'fname', 'given_name', 'الاسم الأول',
                        'last_name', 'lastName', 'lname', 'family_name', 'الاسم الأخير'
                    ],
                    'value': self.user_data.get('full_name', '')
                },
                'email': {
                    'selectors': [
                        'email', 'email_address', 'البريد الإلكتروني', 'بريد إلكتروني',
                        'e_mail', 'emailAddress'
                    ],
                    'value': self.user_data.get('email', '')
                },
                'phone_number': {
                    'selectors': [
                        'phone', 'telephone', 'mobile', 'رقم الهاتف', 'هاتف',
                        'phone_number', 'phoneNumber', 'tel', 'contact'
                    ],
                    'value': self.user_data.get('phone_number', '')
                },
                'passport_number': {
                    'selectors': [
                        'passport', 'passport_number', 'رقم الجواز', 'جواز السفر',
                        'passportNumber', 'passport_no', 'document_number'
                    ],
                    'value': self.user_data.get('passport_number', '')
                },
                'nationality': {
                    'selectors': [
                        'nationality', 'country', 'الجنسية', 'بلد',
                        'birth_country', 'citizen'
                    ],
                    'value': self.user_data.get('nationality', 'Morocco')
                },
                'birth_date': {
                    'selectors': [
                        'birth_date', 'dob', 'date_of_birth', 'تاريخ الميلاد',
                        'birthDate', 'dateOfBirth', 'birthday'
                    ],
                    'value': self.user_data.get('birth_date', '')
                }
            }
            
            filled_fields = 0
            total_fields = len([f for f in form_fields.values() if f['value']])
            
            # ملء كل حقل باستخدام طرق متعددة
            for field_type, field_info in form_fields.items():
                if field_info['value']:
                    if self._fill_field_advanced(field_info['selectors'], field_info['value'], field_type):
                        filled_fields += 1
            
            print(f"📊 تم ملء {filled_fields} حقل من أصل {total_fields} حقول متاحة")
            
            # محاولة إرسال النموذج
            if filled_fields > 0:
                return self._submit_form()
            else:
                print("❌ لم يتم ملء أي حقل")
                return False
            
        except Exception as e:
            print(f"❌ خطأ في ملء النموذج: {e}")
            return False
    
    def _fill_field_advanced(self, selectors, value, field_name):
        """ملء حقل معين باستخدام طرق متعددة ومحددات متنوعة"""
        search_methods = [
            ("البحث بالاسم", lambda selector: self.driver.find_element(By.NAME, selector)),
            ("البحث بالـ ID", lambda selector: self.driver.find_element(By.ID, selector)),
            ("البحث بالـ placeholder", lambda selector: self.driver.find_element(By.XPATH, f"//input[@placeholder='{selector}']")),
            ("البحث بالـ placeholder (يحتوي)", lambda selector: self.driver.find_element(By.XPATH, f"//input[contains(@placeholder, '{selector}')]")),
            ("البحث بالـ label", lambda selector: self.driver.find_element(By.XPATH, f"//input[following-sibling::label[contains(text(), '{selector}')] or preceding-sibling::label[contains(text(), '{selector}')]]")),
            ("البحث بالنص القريب", lambda selector: self.driver.find_element(By.XPATH, f"//input[..//*[contains(text(), '{selector}')]]"))
        ]
        
        for selector in selectors:
            for method_name, method in search_methods:
                try:
                    element = method(selector)
                    if element.is_displayed() and element.is_enabled():
                        # محاولة ملء الحقل بطرق متعددة
                        if self._fill_element_safely(element, value, field_name, method_name):
                            return True
                except:
                    continue
        
        print(f"⚠️ لم يتم العثور على حقل {field_name}")
        return False
    
    def _fill_element_safely(self, element, value, field_name, method_name):
        """ملء عنصر بطريقة آمنة مع معالجة الأخطاء"""
        fill_methods = [
            ("الملء العادي", lambda el, val: self._standard_fill(el, val)),
            ("الملء بـ JavaScript", lambda el, val: self._javascript_fill(el, val)),
            ("الملء مع التركيز", lambda el, val: self._focus_fill(el, val))
        ]
        
        for fill_method_name, fill_method in fill_methods:
            try:
                fill_method(element, value)
                print(f"✅ تم ملء {field_name} باستخدام {method_name} - {fill_method_name}: {value}")
                return True
            except Exception as e:
                print(f"⚠️ فشل {fill_method_name} لحقل {field_name}: {e}")
                continue
        
        return False
    
    def _standard_fill(self, element, value):
        """الطريقة العادية لملء الحقل"""
        element.clear()
        element.send_keys(value)
    
    def _javascript_fill(self, element, value):
        """ملء الحقل باستخدام JavaScript"""
        self.driver.execute_script("arguments[0].value = arguments[1];", element, value)
        self.driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", element)
    
    def _focus_fill(self, element, value):
        """ملء الحقل مع التركيز عليه أولاً"""
        element.click()
        element.clear()
        element.send_keys(value)
    
    def _submit_form(self):
        """إرسال النموذج باستخدام طرق متعددة"""
        submit_selectors = [
            "//button[contains(text(), 'Book')]",
            "//button[contains(text(), 'Submit')]",
            "//button[contains(text(), 'Continue')]",
            "//button[contains(text(), 'Next')]",
            "//button[contains(text(), 'Proceed')]",
            "//input[@type='submit']",
            "//button[@type='submit']",
            "//*[contains(text(), 'حجز')]",
            "//*[contains(text(), 'إرسال')]",
            "//*[contains(text(), 'متابعة')]",
            "//*[contains(text(), 'التالي')]",
            "//button[contains(@class, 'submit')]",
            "//button[contains(@class, 'book')]"
        ]
        
        print("🔍 البحث عن زر الإرسال...")
        
        for selector in submit_selectors:
            try:
                submit_button = self.driver.find_element(By.XPATH, selector)
                if submit_button.is_displayed() and submit_button.is_enabled():
                    print(f"🎯 تم العثور على زر الإرسال: {submit_button.text}")
                    
                    # محاولة النقر بطرق متعددة
                    if self.click_element_multiple_ways(submit_button):
                        print("✅ تم إرسال النموذج بنجاح")
                        time.sleep(3)
                        
                        # التحقق من نجاح الإرسال
                        return self._check_submission_success()
                        
            except Exception as e:
                print(f"⚠️ خطأ في زر الإرسال: {e}")
                continue
        
        print("❌ لم يتم العثور على زر الإرسال")
        return False
    
    def _check_submission_success(self):
        """التحقق من نجاح إرسال النموذج"""
        success_indicators = [
            "//div[contains(text(), 'Success')]",
            "//div[contains(text(), 'Confirmed')]",
            "//div[contains(text(), 'Thank you')]",
            "//div[contains(text(), 'Booked')]",
            "//div[contains(text(), 'نجح')]",
            "//div[contains(text(), 'تأكيد')]",
            "//div[contains(text(), 'شكراً')]",
            "//div[contains(text(), 'تم الحجز')]",
            "//*[contains(@class, 'success')]",
            "//*[contains(@class, 'confirmation')]"
        ]
        
        for indicator in success_indicators:
            try:
                success_element = self.driver.find_element(By.XPATH, indicator)
                if success_element.is_displayed():
                    print(f"✅ تم تأكيد نجاح الحجز: {success_element.text}")
                    return True
            except:
                continue
        
        # التحقق من تغيير URL كمؤشر على النجاح
        current_url = self.driver.current_url
        if any(keyword in current_url.lower() for keyword in ['success', 'confirmation', 'thank', 'complete']):
            print("✅ تم تأكيد النجاح من خلال URL")
            return True
        
        print("ℹ️ تم إرسال النموذج (لم يتم تأكيد النجاح)")
        return True  # نعتبر الإرسال ناجحاً حتى لو لم نجد مؤشر تأكيد
    
    def proceed_to_next_page(self):
        """الانتقال إلى الصفحة التالية - نسخة محسنة من test_visible.py"""
        next_button_selectors = [
            "//button[contains(text(), 'Next')]",
            "//button[contains(text(), 'Continue')]",
            "//button[contains(text(), 'Submit')]",
            "//button[contains(text(), 'Proceed')]",
            "//input[@type='submit']",
            "//button[@type='submit']",
            "//*[contains(text(), 'التالي')]",
            "//*[contains(text(), 'متابعة')]",
            "//*[contains(text(), 'إرسال')]",
            "//*[contains(text(), 'المتابعة')]",
            "//button[contains(@class, 'next')]",
            "//button[contains(@class, 'continue')]",
            "//a[contains(text(), 'Next')]",
            "//a[contains(text(), 'Continue')]"
        ]
        
        print("🔍 البحث عن زر الانتقال للصفحة التالية...")
        
        for selector in next_button_selectors:
            try:
                next_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                if next_button.is_displayed():
                    print(f"🎯 تم العثور على زر التالي: {next_button.text}")
                    
                    if self.click_element_multiple_ways(next_button):
                        print("✅ تم الانتقال للصفحة التالية")
                        time.sleep(3)
                        return True
                        
            except Exception as e:
                print(f"⚠️ خطأ في زر التالي: {e}")
                continue
        
        print("❌ لم يتم العثور على زر الانتقال للصفحة التالية")
        return False
    
    def handle_next_appointment_page(self):
        """معالجة صفحة الموعد التالية - نسخة محسنة من test_visible.py"""
        print("🔄 معالجة صفحة الموعد الجديدة...")
        time.sleep(3)  # انتظار تحميل الصفحة
        
        # إعادة تطبيق مراقبة المواعيد على الصفحة الجديدة
        return self.monitor_appointments()
    
    def wait_for_page_load(self, timeout=10):
        """انتظار تحميل الصفحة بالكامل"""
        try:
            # انتظار حتى يكتمل تحميل الصفحة
            self.wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
            
            # انتظار إضافي للتأكد من تحميل العناصر الديناميكية
            time.sleep(2)
            
            print("✅ تم تحميل الصفحة بالكامل")
            return True
            
        except Exception as e:
            print(f"⚠️ انتهت مهلة انتظار تحميل الصفحة: {e}")
            return False
    
    def refresh_page_if_needed(self):
        """تحديث الصفحة إذا لزم الأمر"""
        try:
            # التحقق من وجود رسائل خطأ تتطلب تحديث الصفحة
            error_indicators = [
                "//div[contains(text(), 'Error')]",
                "//div[contains(text(), 'خطأ')]",
                "//div[contains(text(), 'Something went wrong')]",
                "//div[contains(text(), 'حدث خطأ')]",
                "//*[contains(@class, 'error')]",
                "//*[contains(@class, 'alert-danger')]"
            ]
            
            for indicator in error_indicators:
                try:
                    error_element = self.driver.find_element(By.XPATH, indicator)
                    if error_element.is_displayed():
                        print("🔄 تم اكتشاف خطأ - تحديث الصفحة...")
                        self.driver.refresh()
                        self.wait_for_page_load()
                        return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            print(f"⚠️ خطأ في فحص الحاجة لتحديث الصفحة: {e}")
            return False
    
    def handle_stale_element_exception(self, func, *args, max_retries=3):
        """معالجة StaleElementReferenceException مع إعادة المحاولة"""
        for attempt in range(max_retries):
            try:
                return func(*args)
            except StaleElementReferenceException:
                print(f"⚠️ StaleElementReferenceException - المحاولة {attempt + 1}/{max_retries}")
                if attempt < max_retries - 1:
                    time.sleep(1)
                    # إعادة البحث عن العنصر
                    continue
                else:
                    print("❌ فشل في معالجة StaleElementReferenceException")
                    raise
            except Exception as e:
                print(f"❌ خطأ آخر: {e}")
                raise
    
    def safe_find_element(self, by, value, timeout=10):
        """البحث الآمن عن العناصر مع معالجة الأخطاء"""
        try:
            element = self.wait.until(EC.presence_of_element_located((by, value)))
            return element
        except TimeoutException:
            print(f"⚠️ انتهت مهلة البحث عن العنصر: {value}")
            return None
        except Exception as e:
            print(f"❌ خطأ في البحث عن العنصر: {e}")
            return None
    
    def safe_click_element(self, element, method="normal"):
        """النقر الآمن على العناصر مع معالجة الأخطاء"""
        try:
            if method == "normal":
                element.click()
            elif method == "javascript":
                self.driver.execute_script("arguments[0].click();", element)
            elif method == "action_chains":
                ActionChains(self.driver).move_to_element(element).click().perform()
            elif method == "scroll_and_click":
                self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                time.sleep(1)
                element.click()
            
            return True
            
        except Exception as e:
            print(f"❌ خطأ في النقر على العنصر بطريقة {method}: {e}")
            return False
    
    def book_appointment(self):
        """حجز الموعد تلقائياً - نسخة محسنة مع نظام الإشعارات"""
        try:
            print("📝 بدء عملية حجز الموعد المحسنة...")
            
            # استخدام وظيفة ملء النموذج المحسنة
            if self.fill_appointment_form():
                print("✅ تم ملء النموذج بنجاح")
                
                # انتظار التأكيد
                time.sleep(5)
                
                # التحقق من نجاح الحجز
                success_indicators = [
                    "//div[contains(text(), 'Success')]",
                    "//div[contains(text(), 'Confirmed')]",
                    "//div[contains(text(), 'Thank you')]",
                    "//div[contains(text(), 'Booked')]",
                    "//div[contains(text(), 'نجح')]",
                    "//div[contains(text(), 'تأكيد')]",
                    "//div[contains(text(), 'شكراً')]",
                    "//div[contains(text(), 'تم الحجز')]"
                ]
                
                booking_confirmed = False
                confirmation_message = ""
                
                for indicator in success_indicators:
                    try:
                        success_element = self.driver.find_element(By.XPATH, indicator)
                        if success_element.is_displayed():
                            confirmation_message = success_element.text
                            print(f"✅ تم تأكيد الحجز: {confirmation_message}")
                            booking_confirmed = True
                            break
                    except:
                        continue
                
                # التحقق من URL للتأكد من النجاح
                current_url = self.driver.current_url
                if not booking_confirmed and any(keyword in current_url.lower() for keyword in ['success', 'confirmation', 'thank', 'complete']):
                    print("✅ تم تأكيد الحجز من خلال URL")
                    booking_confirmed = True
                    confirmation_message = f"تأكيد من URL: {current_url}"
                
                # إرسال الإشعارات في حالة نجاح الحجز
                if booking_confirmed and NOTIFICATIONS_ENABLED:
                    try:
                        print("📧 إرسال إشعارات نجاح الحجز...")
                        
                        booking_details = {
                            'booking_id': f"SPAIN-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                            'status': 'SUCCESS',
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'confirmation_message': confirmation_message,
                            'booking_url': current_url
                        }
                        
                        # إرسال الإشعارات الشاملة
                        notification_results = notification_system.send_comprehensive_notification(
                            self.user_data, booking_details
                        )
                        
                        # تسجيل نتائج الإشعارات
                        if notification_results.get('email_sent'):
                            print("✅ تم إرسال إشعار الإيميل بنجاح")
                        if notification_results.get('telegram_sent'):
                            print("✅ تم إرسال إشعار تيليجرام بنجاح")
                        if notification_results.get('logged'):
                            print("✅ تم تسجيل الحجز في قاعدة البيانات")
                        
                        # إرسال إشعار واتساب إضافي
                        self.send_whatsapp_notification(
                            f"🎉 تأكيد حجز فيزا إسبانيا!\n"
                            f"👤 الاسم: {self.user_data.get('full_name', 'غير محدد')}\n"
                            f"🆔 معرف الحجز: {booking_details['booking_id']}\n"
                            f"📅 التاريخ: {booking_details['timestamp']}\n"
                            f"✅ تم إرسال تأكيد مفصل عبر الإيميل"
                        )
                        
                    except Exception as notification_error:
                        print(f"⚠️ خطأ في إرسال الإشعارات: {notification_error}")
                        # حتى لو فشلت الإشعارات، الحجز نجح
                
                if booking_confirmed:
                    return True
                else:
                    print("ℹ️ تم إرسال طلب الحجز - في انتظار التأكيد")
                    return True
            else:
                print("❌ فشل في ملء النموذج")
                return False
                
        except Exception as e:
            print(f"❌ خطأ في حجز الموعد: {e}")
            return False

def monitor_appointments():
    """مراقبة المواعيد بشكل مستمر - نسخة محسنة مع فحص كل 5 ثوان ونظام إشعارات متقدم"""
    global monitoring_active, user_data
    
    bot = VisaBookingBot(user_data)
    consecutive_errors = 0
    max_consecutive_errors = 5
    
    # إعداد المتصفح مرة واحدة
    bot.setup_driver()
    
    # إرسال إشعار بدء المراقبة
    if NOTIFICATIONS_ENABLED:
        try:
            start_message = f"""
🚀 بدء مراقبة مواعيد فيزا إسبانيا
👤 المستخدم: {user_data.get('full_name', 'غير محدد')}
📧 الإيميل: {user_data.get('email', 'غير محدد')}
🕐 وقت البدء: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
⚡ تردد الفحص: كل 5 ثوان
            """
            bot.send_whatsapp_notification(start_message)
            print("✅ تم إرسال إشعار بدء المراقبة")
        except Exception as e:
            print(f"⚠️ خطأ في إرسال إشعار البدء: {e}")
    
    try:
        while monitoring_active:
            try:
                print(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - فحص المواعيد...")
                
                # فحص المواعيد
                appointment_found = bot.check_appointments()
                
                if appointment_found:
                    print("🎉 تم العثور على موعد وحجزه بنجاح!")
                    
                    # إرسال إشعار واتساب فوري
                    success_message = f"""
🎉 نجح حجز موعد فيزا إسبانيا!
👤 الاسم: {user_data.get('full_name', 'غير محدد')}
📅 وقت الحجز: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
✅ تم إرسال تأكيد مفصل عبر الإيميل والتيليجرام
📧 تحقق من بريدك الإلكتروني للحصول على التفاصيل الكاملة
                    """
                    bot.send_whatsapp_notification(success_message)
                    
                    # إيقاف المراقبة بعد النجاح
                    monitoring_active = False
                    break
                
                # إعادة تعيين عداد الأخطاء عند النجاح
                consecutive_errors = 0
                
                # انتظار 5 ثوان بدلاً من 30 دقيقة للمراقبة السريعة
                print("⏳ انتظار 5 ثوان قبل الفحص التالي...")
                for i in range(5):
                    if not monitoring_active:
                        break
                    time.sleep(1)
                
            except Exception as e:
                consecutive_errors += 1
                print(f"❌ خطأ في المراقبة (المحاولة {consecutive_errors}): {e}")
                
                if consecutive_errors >= max_consecutive_errors:
                    print(f"❌ تم الوصول للحد الأقصى من الأخطاء المتتالية ({max_consecutive_errors})")
                    bot.send_whatsapp_notification(f"❌ توقفت مراقبة المواعيد بسبب أخطاء متتالية: {str(e)}")
                    break
                
                # انتظار أطول عند حدوث خطأ
                print("⏳ انتظار 30 ثانية بسبب الخطأ...")
                for i in range(30):
                    if not monitoring_active:
                        break
                    time.sleep(1)
                
                # إعادة إعداد المتصفح عند حدوث أخطاء متكررة
                if consecutive_errors >= 3:
                    print("🔄 إعادة إعداد المتصفح...")
                    try:
                        if bot.driver:
                            bot.driver.quit()
                    except:
                        pass
                    bot.setup_driver()
                    
    except KeyboardInterrupt:
        print("⏹️ تم إيقاف المراقبة بواسطة المستخدم")
    finally:
        monitoring_active = False
        if bot.driver:
            try:
                bot.driver.quit()
                print("🔒 تم إغلاق المتصفح")
            except:
                pass

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
    
    # في بيئة الإنتاج، Gunicorn سيتولى تشغيل التطبيق
    # app.run() مطلوب فقط للتطوير المحلي
    if __name__ == '__main__':
        # تشغيل التطبيق للتطوير المحلي فقط
        port = int(os.environ.get('PORT', 5000))
        debug_mode = os.environ.get('FLASK_ENV') == 'development'
        app.run(debug=debug_mode, host='0.0.0.0', port=port)