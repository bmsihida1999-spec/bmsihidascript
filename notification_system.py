"""
نظام الإشعارات المتقدم لتطبيق حجز فيزا إسبانيا
يدعم الإشعارات عبر الإيميل وتيليجرام مع تسجيل مفصل
"""

import smtplib
import requests
import json
import os
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sqlite3
import logging

# إعداد نظام التسجيل
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('booking_notifications.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class NotificationSystem:
    def __init__(self):
        """تهيئة نظام الإشعارات"""
        self.setup_database()
        
        # إعدادات الإيميل
        self.smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.environ.get('SMTP_PORT', '587'))
        self.email_user = os.environ.get('EMAIL_USER', '')
        self.email_password = os.environ.get('EMAIL_PASSWORD', '')
        
        # إعدادات تيليجرام
        self.telegram_bot_token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
        self.telegram_chat_id = os.environ.get('TELEGRAM_CHAT_ID', '')
        
        logging.info("🔧 تم تهيئة نظام الإشعارات")
    
    def setup_database(self):
        """إعداد قاعدة بيانات الإشعارات"""
        try:
            conn = sqlite3.connect('notifications.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS booking_notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    booking_id TEXT,
                    user_name TEXT,
                    user_email TEXT,
                    visa_type TEXT,
                    appointment_date TEXT,
                    booking_status TEXT,
                    notification_sent BOOLEAN DEFAULT FALSE,
                    email_sent BOOLEAN DEFAULT FALSE,
                    telegram_sent BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notification_details TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
            logging.info("✅ تم إعداد قاعدة بيانات الإشعارات")
            
        except Exception as e:
            logging.error(f"❌ خطأ في إعداد قاعدة البيانات: {e}")
    
    def send_email_notification(self, user_data, booking_details):
        """إرسال إشعار عبر الإيميل"""
        try:
            if not self.email_user or not self.email_password:
                logging.warning("⚠️ بيانات الإيميل غير مكتملة")
                return False
            
            # إنشاء الرسالة
            msg = MIMEMultipart('alternative')
            msg['From'] = self.email_user
            msg['To'] = user_data.get('email', '')
            msg['Subject'] = "🎉 تأكيد حجز موعد فيزا إسبانيا - Spain Visa Appointment Confirmed"
            
            # محتوى الرسالة بالعربية والإنجليزية
            html_content = f"""
            <!DOCTYPE html>
            <html dir="rtl" lang="ar">
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
                    .container {{ background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                    .header {{ background-color: #28a745; color: white; padding: 20px; text-align: center; border-radius: 5px; margin-bottom: 20px; }}
                    .success-icon {{ font-size: 48px; margin-bottom: 10px; }}
                    .details {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0; }}
                    .footer {{ text-align: center; margin-top: 30px; color: #666; }}
                    .english {{ direction: ltr; text-align: left; margin-top: 30px; border-top: 2px solid #eee; padding-top: 20px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <div class="success-icon">🎉</div>
                        <h1>تم حجز موعدك بنجاح!</h1>
                        <p>Your Spain Visa Appointment Has Been Successfully Booked!</p>
                    </div>
                    
                    <div class="details">
                        <h3>📋 تفاصيل الحجز - Booking Details:</h3>
                        <p><strong>الاسم الكامل - Full Name:</strong> {user_data.get('full_name', 'غير محدد')}</p>
                        <p><strong>رقم الجواز - Passport Number:</strong> {user_data.get('passport_number', 'غير محدد')}</p>
                        <p><strong>نوع الفيزا - Visa Type:</strong> {user_data.get('visa_type', 'فيزا دراسة')}</p>
                        <p><strong>المدينة - City:</strong> {user_data.get('preferred_city', 'غير محدد')}</p>
                        <p><strong>تاريخ الحجز - Booking Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                        <p><strong>معرف الحجز - Booking ID:</strong> {booking_details.get('booking_id', 'AUTO-' + str(int(datetime.now().timestamp())))}</p>
                    </div>
                    
                    <div class="details">
                        <h3>📧 معلومات الاتصال - Contact Information:</h3>
                        <p><strong>البريد الإلكتروني - Email:</strong> {user_data.get('email', 'غير محدد')}</p>
                        <p><strong>رقم الهاتف - Phone:</strong> {user_data.get('phone_number', 'غير محدد')}</p>
                        <p><strong>واتساب - WhatsApp:</strong> {user_data.get('whatsapp_number', 'غير محدد')}</p>
                    </div>
                    
                    <div class="details">
                        <h3>⚠️ ملاحظات مهمة - Important Notes:</h3>
                        <ul>
                            <li>يرجى التحقق من بريدك الإلكتروني للحصول على تأكيد رسمي من BLS Spain</li>
                            <li>Please check your email for official confirmation from BLS Spain</li>
                            <li>احتفظ بهذا الإيميل كدليل على الحجز</li>
                            <li>Keep this email as proof of booking</li>
                            <li>في حالة عدم وصول التأكيد الرسمي خلال 24 ساعة، يرجى التواصل معنا</li>
                            <li>If you don't receive official confirmation within 24 hours, please contact us</li>
                        </ul>
                    </div>
                    
                    <div class="footer">
                        <p>🤖 تم إرسال هذا الإشعار تلقائياً بواسطة نظام حجز فيزا إسبانيا</p>
                        <p>This notification was sent automatically by Spain Visa Booking System</p>
                        <p>⏰ وقت الإرسال: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # إرفاق المحتوى
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            # إرسال الإيميل
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_user, self.email_password)
            server.send_message(msg)
            server.quit()
            
            logging.info(f"✅ تم إرسال إشعار الإيميل إلى: {user_data.get('email')}")
            return True
            
        except Exception as e:
            logging.error(f"❌ خطأ في إرسال الإيميل: {e}")
            return False
    
    def send_telegram_notification(self, user_data, booking_details):
        """إرسال إشعار عبر تيليجرام"""
        try:
            if not self.telegram_bot_token or not self.telegram_chat_id:
                logging.warning("⚠️ بيانات تيليجرام غير مكتملة")
                return False
            
            # إنشاء الرسالة
            message = f"""
🎉 *تأكيد حجز موعد فيزا إسبانيا*
✅ *Spain Visa Appointment Confirmed*

📋 *تفاصيل الحجز:*
👤 الاسم: `{user_data.get('full_name', 'غير محدد')}`
🛂 رقم الجواز: `{user_data.get('passport_number', 'غير محدد')}`
📄 نوع الفيزا: `{user_data.get('visa_type', 'فيزا دراسة')}`
🏙️ المدينة: `{user_data.get('preferred_city', 'غير محدد')}`
📅 تاريخ الحجز: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`
🆔 معرف الحجز: `{booking_details.get('booking_id', 'AUTO-' + str(int(datetime.now().timestamp())))}`

📧 *معلومات الاتصال:*
✉️ الإيميل: `{user_data.get('email', 'غير محدد')}`
📱 الهاتف: `{user_data.get('phone_number', 'غير محدد')}`
💬 واتساب: `{user_data.get('whatsapp_number', 'غير محدد')}`

⚠️ *ملاحظة مهمة:*
يرجى التحقق من بريدك الإلكتروني للحصول على التأكيد الرسمي من BLS Spain

🤖 تم الإرسال تلقائياً بواسطة نظام حجز فيزا إسبانيا
            """
            
            # إرسال الرسالة
            url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
            data = {
                'chat_id': self.telegram_chat_id,
                'text': message,
                'parse_mode': 'Markdown'
            }
            
            response = requests.post(url, data=data)
            
            if response.status_code == 200:
                logging.info("✅ تم إرسال إشعار تيليجرام بنجاح")
                return True
            else:
                logging.error(f"❌ فشل إرسال تيليجرام: {response.text}")
                return False
                
        except Exception as e:
            logging.error(f"❌ خطأ في إرسال تيليجرام: {e}")
            return False
    
    def log_booking_success(self, user_data, booking_details):
        """تسجيل نجاح الحجز في قاعدة البيانات"""
        try:
            conn = sqlite3.connect('notifications.db')
            cursor = conn.cursor()
            
            booking_id = booking_details.get('booking_id', 'AUTO-' + str(int(datetime.now().timestamp())))
            
            cursor.execute('''
                INSERT INTO booking_notifications 
                (booking_id, user_name, user_email, visa_type, appointment_date, 
                 booking_status, notification_details)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                booking_id,
                user_data.get('full_name', ''),
                user_data.get('email', ''),
                user_data.get('visa_type', 'فيزا دراسة'),
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'SUCCESS',
                json.dumps(booking_details, ensure_ascii=False)
            ))
            
            conn.commit()
            conn.close()
            
            logging.info(f"✅ تم تسجيل نجاح الحجز: {booking_id}")
            return True
            
        except Exception as e:
            logging.error(f"❌ خطأ في تسجيل الحجز: {e}")
            return False
    
    def send_comprehensive_notification(self, user_data, booking_details=None):
        """إرسال إشعار شامل عبر جميع القنوات"""
        if booking_details is None:
            booking_details = {
                'booking_id': 'AUTO-' + str(int(datetime.now().timestamp())),
                'status': 'SUCCESS',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        
        results = {
            'email_sent': False,
            'telegram_sent': False,
            'logged': False
        }
        
        # إرسال الإيميل
        results['email_sent'] = self.send_email_notification(user_data, booking_details)
        
        # إرسال تيليجرام
        results['telegram_sent'] = self.send_telegram_notification(user_data, booking_details)
        
        # تسجيل في قاعدة البيانات
        results['logged'] = self.log_booking_success(user_data, booking_details)
        
        # تحديث حالة الإشعارات في قاعدة البيانات
        try:
            conn = sqlite3.connect('notifications.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE booking_notifications 
                SET email_sent = ?, telegram_sent = ?, notification_sent = ?
                WHERE booking_id = ?
            ''', (
                results['email_sent'],
                results['telegram_sent'],
                results['email_sent'] or results['telegram_sent'],
                booking_details['booking_id']
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logging.error(f"❌ خطأ في تحديث حالة الإشعارات: {e}")
        
        # تسجيل النتائج
        success_count = sum(results.values())
        logging.info(f"📊 نتائج الإشعارات: {success_count}/3 نجح")
        
        if results['email_sent']:
            logging.info("✅ تم إرسال الإيميل")
        if results['telegram_sent']:
            logging.info("✅ تم إرسال تيليجرام")
        if results['logged']:
            logging.info("✅ تم التسجيل في قاعدة البيانات")
        
        return results
    
    def get_booking_stats(self):
        """الحصول على إحصائيات الحجوزات"""
        try:
            conn = sqlite3.connect('notifications.db')
            cursor = conn.cursor()
            
            # إجمالي الحجوزات
            cursor.execute("SELECT COUNT(*) FROM booking_logs")
            total_bookings = cursor.fetchone()[0]
            
            # آخر حجز
            cursor.execute("SELECT booking_date FROM booking_logs ORDER BY booking_date DESC LIMIT 1")
            last_booking = cursor.fetchone()
            last_booking_date = last_booking[0] if last_booking else 'لا يوجد'
            
            # المستخدمون الفريدون
            cursor.execute("SELECT COUNT(DISTINCT full_name) FROM booking_logs")
            unique_users = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'total_bookings': total_bookings,
                'last_booking_date': last_booking_date,
                'unique_users': unique_users
            }
            
        except Exception as e:
            logging.error(f"خطأ في الحصول على الإحصائيات: {e}")
            return {
                'total_bookings': 0,
                'last_booking_date': 'خطأ',
                'unique_users': 0
            }
    
    def get_recent_bookings(self, limit=5):
        """الحصول على آخر الحجوزات"""
        try:
            conn = sqlite3.connect('notifications.db')
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT booking_date, full_name, passport_number, visa_type, 'نجح' as status
                FROM booking_logs 
                ORDER BY booking_date DESC 
                LIMIT ?
            """, (limit,))
            
            bookings = cursor.fetchall()
            conn.close()
            
            return bookings
            
        except Exception as e:
            logging.error(f"خطأ في الحصول على الحجوزات الأخيرة: {e}")
            return []
    
    def get_booking_statistics(self):
        """الحصول على إحصائيات الحجوزات"""
        try:
            conn = sqlite3.connect('notifications.db')
            cursor = conn.cursor()
            
            # إجمالي الحجوزات
            cursor.execute("SELECT COUNT(*) FROM booking_notifications")
            total_bookings = cursor.fetchone()[0]
            
            # الحجوزات الناجحة
            cursor.execute("SELECT COUNT(*) FROM booking_notifications WHERE booking_status = 'SUCCESS'")
            successful_bookings = cursor.fetchone()[0]
            
            # الحجوزات اليوم
            today = datetime.now().strftime('%Y-%m-%d')
            cursor.execute("SELECT COUNT(*) FROM booking_notifications WHERE DATE(created_at) = ?", (today,))
            today_bookings = cursor.fetchone()[0]
            
            # الإشعارات المرسلة
            cursor.execute("SELECT COUNT(*) FROM booking_notifications WHERE notification_sent = 1")
            notifications_sent = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'total_bookings': total_bookings,
                'successful_bookings': successful_bookings,
                'today_bookings': today_bookings,
                'notifications_sent': notifications_sent,
                'success_rate': (successful_bookings / total_bookings * 100) if total_bookings > 0 else 0
            }
            
        except Exception as e:
            logging.error(f"❌ خطأ في الحصول على الإحصائيات: {e}")
            return {}

# إنشاء مثيل عام للنظام
notification_system = NotificationSystem()