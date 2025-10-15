"""
وضع تجريبي لاختبار نظام الإشعارات
Demo Mode for Testing Notification System
"""

import os
import json
from datetime import datetime
from notification_system import NotificationSystem

def test_notification_system():
    """اختبار نظام الإشعارات مع بيانات وهمية"""
    
    print("🧪 بدء اختبار نظام الإشعارات...")
    
    # بيانات وهمية للاختبار
    test_user_data = {
        'full_name': 'أحمد محمد علي',
        'passport_number': 'A12345678',
        'email': 'test@example.com',
        'phone': '+966501234567',
        'visa_type': 'فيزا دراسة',
        'nationality': 'السعودية'
    }
    
    # إنشاء نظام الإشعارات
    notification_system = NotificationSystem()
    
    try:
        # اختبار الإشعار الشامل
        print("📧 اختبار إرسال الإشعار الشامل...")
        
        success = notification_system.send_comprehensive_notification(
            user_data=test_user_data,
            booking_details={
                'appointment_date': '2024-01-15',
                'appointment_time': '10:30 AM',
                'location': 'القنصلية الإسبانية - الرياض',
                'reference_number': 'ESP-2024-001234',
                'visa_category': 'فيزا دراسة',
                'booking_id': 'ESP-2024-001234',
                'status': 'SUCCESS',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        )
        
        if success:
            print("✅ تم إرسال الإشعار الشامل بنجاح!")
            
            # عرض إحصائيات الحجوزات
            print("\n📊 إحصائيات الحجوزات:")
            stats = notification_system.get_booking_stats()
            
            print(f"📈 إجمالي الحجوزات الناجحة: {stats['total_bookings']}")
            print(f"📅 آخر حجز: {stats['last_booking_date']}")
            print(f"👤 المستخدمون الفريدون: {stats['unique_users']}")
            
            # عرض آخر 5 حجوزات
            print("\n📋 آخر الحجوزات:")
            recent_bookings = notification_system.get_recent_bookings(limit=5)
            
            for booking in recent_bookings:
                print(f"  • {booking[1]} - {booking[2]} - {booking[3]} ({booking[4]})")
            
            return True
        else:
            print("❌ فشل في إرسال الإشعار")
            return False
            
    except Exception as e:
        print(f"❌ خطأ في اختبار نظام الإشعارات: {e}")
        return False

def simulate_booking_process():
    """محاكاة عملية حجز كاملة"""
    
    print("\n🎭 محاكاة عملية حجز كاملة...")
    
    # بيانات متعددة للاختبار
    test_users = [
        {
            'full_name': 'سارة أحمد محمد',
            'passport_number': 'B98765432',
            'email': 'sara@example.com',
            'phone': '+966502345678',
            'visa_type': 'فيزا دراسة',
            'nationality': 'السعودية'
        },
        {
            'full_name': 'محمد علي حسن',
            'passport_number': 'C11223344',
            'email': 'mohammed@example.com',
            'phone': '+966503456789',
            'visa_type': 'فيزا دراسة',
            'nationality': 'الأردن'
        }
    ]
    
    notification_system = NotificationSystem()
    successful_bookings = 0
    
    for i, user_data in enumerate(test_users, 1):
        print(f"\n👤 اختبار المستخدم {i}: {user_data['full_name']}")
        
        try:
            success = notification_system.send_comprehensive_notification(
                user_data=user_data,
                booking_details={
                    'appointment_date': f'2024-01-{15 + i}',
                    'appointment_time': f'{9 + i}:30 AM',
                    'location': 'القنصلية الإسبانية - الرياض',
                    'reference_number': f'ESP-2024-00123{i}',
                    'visa_category': 'فيزا دراسة',
                    'booking_id': f'ESP-2024-00123{i}',
                    'status': 'SUCCESS',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            )
            
            if success:
                successful_bookings += 1
                print(f"  ✅ نجح حجز المستخدم {i}")
            else:
                print(f"  ❌ فشل حجز المستخدم {i}")
                
        except Exception as e:
            print(f"  ❌ خطأ في حجز المستخدم {i}: {e}")
    
    print(f"\n📊 نتائج المحاكاة:")
    print(f"✅ حجوزات ناجحة: {successful_bookings}/{len(test_users)}")
    print(f"📈 معدل النجاح: {(successful_bookings/len(test_users))*100:.1f}%")
    
    return successful_bookings == len(test_users)

if __name__ == "__main__":
    print("🚀 بدء الوضع التجريبي لاختبار نظام الإشعارات")
    print("=" * 50)
    
    # اختبار النظام الأساسي
    basic_test = test_notification_system()
    
    # محاكاة عملية حجز متعددة
    simulation_test = simulate_booking_process()
    
    print("\n" + "=" * 50)
    print("📋 ملخص النتائج:")
    print(f"🧪 الاختبار الأساسي: {'✅ نجح' if basic_test else '❌ فشل'}")
    print(f"🎭 محاكاة الحجوزات: {'✅ نجحت' if simulation_test else '❌ فشلت'}")
    
    if basic_test and simulation_test:
        print("\n🎉 جميع الاختبارات نجحت! نظام الإشعارات جاهز للاستخدام.")
    else:
        print("\n⚠️ بعض الاختبارات فشلت. يرجى مراجعة الإعدادات.")