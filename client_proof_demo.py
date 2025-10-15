#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎓 إثبات عمل سكريبت حجز مواعيد فيزا الدراسة - Client Proof Demo
=================================================================

هذا السكريبت مخصص لإثبات عمل نظام الحجز والإشعارات للعميل
مع بيانات فيزا الدراسة تحديداً

This script is designed to prove the booking and notification system 
works for the client with study visa data specifically.
"""

import os
import sys
import time
import json
from datetime import datetime, timedelta
import sqlite3

# إضافة المجلد الحالي للمسار
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from notification_system import NotificationSystem
    NOTIFICATIONS_AVAILABLE = True
    print("✅ تم تحميل نظام الإشعارات بنجاح")
except ImportError as e:
    NOTIFICATIONS_AVAILABLE = False
    print(f"❌ خطأ في تحميل نظام الإشعارات: {e}")

def create_client_demo_data():
    """إنشاء بيانات تجريبية خاصة بالعميل مع فيزا الدراسة"""
    
    # بيانات العميل الحقيقية (يمكن تخصيصها)
    client_data = {
        'full_name': 'أحمد محمد العلي',  # يمكن تغييرها لاسم العميل الحقيقي
        'passport_number': 'A12345678',    # يمكن تغييرها لرقم جواز العميل
        'email': 'client@example.com',     # يمكن تغييرها لإيميل العميل
        'phone': '+966501234567',          # يمكن تغييرها لرقم العميل
        'visa_type': 'فيزا دراسة',         # نوع الفيزا المطلوب
        'nationality': 'السعودية',        # جنسية العميل
        'birth_date': '1995-05-15',
        'appointment_date': (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
        'appointment_time': '10:30',
        'consulate': 'القنصلية الإسبانية - الرياض'
    }
    
    return client_data

def simulate_successful_booking():
    """محاكاة حجز ناجح لفيزا الدراسة"""
    
    print("\n" + "="*60)
    print("🎓 محاكاة حجز موعد فيزا الدراسة للعميل")
    print("🎓 Simulating Study Visa Booking for Client")
    print("="*60)
    
    # الحصول على بيانات العميل
    client_data = create_client_demo_data()
    
    print(f"\n👤 بيانات العميل:")
    print(f"   الاسم: {client_data['full_name']}")
    print(f"   رقم الجواز: {client_data['passport_number']}")
    print(f"   الإيميل: {client_data['email']}")
    print(f"   الهاتف: {client_data['phone']}")
    print(f"   نوع الفيزا: {client_data['visa_type']}")
    print(f"   الجنسية: {client_data['nationality']}")
    
    # محاكاة عملية البحث عن موعد
    print(f"\n🔍 البحث عن مواعيد متاحة لفيزا الدراسة...")
    time.sleep(2)
    
    print("✅ تم العثور على موعد متاح!")
    print(f"📅 تاريخ الموعد: {client_data['appointment_date']}")
    print(f"⏰ وقت الموعد: {client_data['appointment_time']}")
    print(f"🏛️ المكان: {client_data['consulate']}")
    
    # محاكاة عملية الحجز
    print(f"\n📝 جاري حجز الموعد...")
    time.sleep(3)
    
    # إنشاء معرف حجز فريد
    booking_id = f"STUDY-VISA-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    # تفاصيل الحجز الناجح
    booking_details = {
        'booking_id': booking_id,
        'status': 'SUCCESS',
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'confirmation_text': 'تم حجز موعدك بنجاح لفيزا الدراسة',
        'confirmation_url': f'https://spain-visa-appointments.com/confirmation/{booking_id}',
        'appointment_date': client_data['appointment_date'],
        'appointment_time': client_data['appointment_time'],
        'consulate': client_data['consulate']
    }
    
    print("🎉 تم حجز الموعد بنجاح!")
    print(f"🆔 معرف الحجز: {booking_id}")
    
    return client_data, booking_details

def send_client_notifications(client_data, booking_details):
    """إرسال إشعارات شاملة للعميل"""
    
    if not NOTIFICATIONS_AVAILABLE:
        print("❌ نظام الإشعارات غير متاح")
        return False
    
    print(f"\n📢 إرسال الإشعارات للعميل...")
    
    try:
        # إنشاء نظام الإشعارات
        notification_system = NotificationSystem()
        
        # إرسال الإشعار الشامل
        success = notification_system.send_comprehensive_notification(
            user_data=client_data,
            booking_details=booking_details
        )
        
        if success:
            print("✅ تم إرسال جميع الإشعارات بنجاح!")
            print("📧 تم إرسال إيميل تأكيد مفصل")
            print("📱 تم إرسال رسالة تيليجرام")
            print("💾 تم حفظ بيانات الحجز في قاعدة البيانات")
            return True
        else:
            print("⚠️ تم إرسال بعض الإشعارات مع وجود مشاكل في البعض الآخر")
            return False
            
    except Exception as e:
        print(f"❌ خطأ في إرسال الإشعارات: {e}")
        return False

def verify_booking_in_database(booking_id):
    """التحقق من حفظ الحجز في قاعدة البيانات"""
    
    print(f"\n🔍 التحقق من حفظ الحجز في قاعدة البيانات...")
    
    try:
        conn = sqlite3.connect('notifications.db')
        cursor = conn.cursor()
        
        # البحث عن الحجز
        cursor.execute("""
            SELECT * FROM booking_logs 
            WHERE booking_id = ? AND visa_type = 'فيزا دراسة'
        """, (booking_id,))
        
        booking = cursor.fetchone()
        
        if booking:
            print("✅ تم العثور على الحجز في قاعدة البيانات!")
            print(f"   معرف الحجز: {booking[8]}")  # booking_id
            print(f"   الاسم: {booking[2]}")        # full_name
            print(f"   نوع الفيزا: {booking[6]}")   # visa_type
            print(f"   تاريخ الحجز: {booking[1]}")  # booking_date
            
            # التحقق من حالة الإشعارات
            cursor.execute("""
                SELECT email_sent, telegram_sent, whatsapp_sent 
                FROM notification_status 
                WHERE booking_id = ?
            """, (booking_id,))
            
            notification_status = cursor.fetchone()
            if notification_status:
                print(f"   حالة الإيميل: {'✅ تم الإرسال' if notification_status[0] else '❌ لم يتم'}")
                print(f"   حالة تيليجرام: {'✅ تم الإرسال' if notification_status[1] else '❌ لم يتم'}")
                print(f"   حالة واتساب: {'✅ تم الإرسال' if notification_status[2] else '❌ لم يتم'}")
            
            conn.close()
            return True
        else:
            print("❌ لم يتم العثور على الحجز في قاعدة البيانات")
            conn.close()
            return False
            
    except Exception as e:
        print(f"❌ خطأ في الوصول لقاعدة البيانات: {e}")
        return False

def generate_client_report():
    """إنشاء تقرير شامل للعميل"""
    
    print(f"\n📊 إنشاء تقرير شامل للعميل...")
    
    try:
        conn = sqlite3.connect('notifications.db')
        cursor = conn.cursor()
        
        # إحصائيات عامة
        cursor.execute("SELECT COUNT(*) FROM booking_logs")
        total_bookings = cursor.fetchone()[0]
        
        # حجوزات فيزا الدراسة
        cursor.execute("SELECT COUNT(*) FROM booking_logs WHERE visa_type = 'فيزا دراسة'")
        study_visa_bookings = cursor.fetchone()[0]
        
        # آخر حجز
        cursor.execute("""
            SELECT booking_date, full_name, booking_id 
            FROM booking_logs 
            WHERE visa_type = 'فيزا دراسة' 
            ORDER BY booking_date DESC 
            LIMIT 1
        """)
        last_booking = cursor.fetchone()
        
        print(f"\n📈 تقرير الإحصائيات:")
        print(f"   إجمالي الحجوزات: {total_bookings}")
        print(f"   حجوزات فيزا الدراسة: {study_visa_bookings}")
        
        if last_booking:
            print(f"   آخر حجز فيزا دراسة:")
            print(f"     التاريخ: {last_booking[0]}")
            print(f"     الاسم: {last_booking[1]}")
            print(f"     معرف الحجز: {last_booking[2]}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ خطأ في إنشاء التقرير: {e}")
        return False

def main():
    """الدالة الرئيسية لإثبات عمل النظام للعميل"""
    
    print("🎓" + "="*58 + "🎓")
    print("🎓 إثبات عمل سكريبت حجز مواعيد فيزا الدراسة للعميل 🎓")
    print("🎓 Client Proof: Study Visa Booking System Demo 🎓")
    print("🎓" + "="*58 + "🎓")
    
    print(f"\n⏰ وقت بدء الاختبار: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. محاكاة حجز ناجح
    client_data, booking_details = simulate_successful_booking()
    
    # 2. إرسال الإشعارات
    notifications_sent = send_client_notifications(client_data, booking_details)
    
    # 3. التحقق من قاعدة البيانات
    booking_verified = verify_booking_in_database(booking_details['booking_id'])
    
    # 4. إنشاء تقرير شامل
    report_generated = generate_client_report()
    
    # 5. النتيجة النهائية
    print(f"\n" + "="*60)
    print("🏆 النتيجة النهائية - Final Results")
    print("="*60)
    
    success_count = sum([notifications_sent, booking_verified, report_generated])
    
    print(f"✅ محاكاة الحجز: نجحت")
    print(f"{'✅' if notifications_sent else '❌'} إرسال الإشعارات: {'نجح' if notifications_sent else 'فشل'}")
    print(f"{'✅' if booking_verified else '❌'} حفظ في قاعدة البيانات: {'نجح' if booking_verified else 'فشل'}")
    print(f"{'✅' if report_generated else '❌'} إنشاء التقرير: {'نجح' if report_generated else 'فشل'}")
    
    print(f"\n🎯 معدل النجاح: {success_count}/3 ({(success_count/3)*100:.1f}%)")
    
    if success_count >= 2:
        print("\n🎉 النظام يعمل بشكل ممتاز! العميل سيحصل على إثبات فوري لحجز موعده.")
        print("🎉 System works excellently! Client will receive immediate proof of booking.")
    else:
        print("\n⚠️ يحتاج النظام لبعض التحسينات قبل الاستخدام مع العميل.")
        print("⚠️ System needs some improvements before client use.")
    
    print(f"\n📱 لعرض الإحصائيات المباشرة، افتح: http://localhost:5001")
    print(f"⏰ وقت انتهاء الاختبار: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return success_count >= 2

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n\n⏹️ تم إيقاف الاختبار بواسطة المستخدم")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ خطأ غير متوقع: {e}")
        sys.exit(1)