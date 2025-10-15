"""
لوحة تحكم ويب لعرض إحصائيات الحجوزات الناجحة
Web Dashboard for Successful Booking Statistics
"""

from flask import Flask, render_template_string, jsonify
import sqlite3
from datetime import datetime, timedelta
import json
import os

# إنشاء تطبيق Flask منفصل للوحة التحكم
dashboard_app = Flask(__name__)

def get_db_connection():
    """الحصول على اتصال بقاعدة البيانات"""
    try:
        conn = sqlite3.connect('notifications.db')
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print(f"خطأ في الاتصال بقاعدة البيانات: {e}")
        return None

def get_booking_statistics():
    """الحصول على إحصائيات الحجوزات"""
    conn = get_db_connection()
    if not conn:
        return {}
    
    try:
        cursor = conn.cursor()
        
        # إجمالي الحجوزات
        cursor.execute("SELECT COUNT(*) as total FROM booking_logs")
        total_bookings = cursor.fetchone()['total']
        
        # الحجوزات اليوم
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute("SELECT COUNT(*) as today FROM booking_logs WHERE DATE(booking_date) = ?", (today,))
        today_bookings = cursor.fetchone()['today']
        
        # الحجوزات هذا الأسبوع
        week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        cursor.execute("SELECT COUNT(*) as week FROM booking_logs WHERE DATE(booking_date) >= ?", (week_ago,))
        week_bookings = cursor.fetchone()['week']
        
        # المستخدمون الفريدون
        cursor.execute("SELECT COUNT(DISTINCT full_name) as unique_users FROM booking_logs")
        unique_users = cursor.fetchone()['unique_users']
        
        # آخر حجز
        cursor.execute("SELECT * FROM booking_logs ORDER BY booking_date DESC LIMIT 1")
        last_booking = cursor.fetchone()
        
        # الحجوزات حسب نوع الفيزا
        cursor.execute("""
            SELECT visa_type, COUNT(*) as count 
            FROM booking_logs 
            GROUP BY visa_type 
            ORDER BY count DESC
        """)
        visa_types = cursor.fetchall()
        
        # الحجوزات الأخيرة (آخر 10)
        cursor.execute("""
            SELECT * FROM booking_logs 
            ORDER BY booking_date DESC 
            LIMIT 10
        """)
        recent_bookings = cursor.fetchall()
        
        # إحصائيات يومية للأسبوع الماضي
        cursor.execute("""
            SELECT DATE(booking_date) as date, COUNT(*) as count
            FROM booking_logs 
            WHERE DATE(booking_date) >= ?
            GROUP BY DATE(booking_date)
            ORDER BY date
        """, (week_ago,))
        daily_stats = cursor.fetchall()
        
        return {
            'total_bookings': total_bookings,
            'today_bookings': today_bookings,
            'week_bookings': week_bookings,
            'unique_users': unique_users,
            'last_booking': dict(last_booking) if last_booking else None,
            'visa_types': [dict(row) for row in visa_types],
            'recent_bookings': [dict(row) for row in recent_bookings],
            'daily_stats': [dict(row) for row in daily_stats]
        }
        
    except Exception as e:
        print(f"خطأ في الحصول على الإحصائيات: {e}")
        return {}
    finally:
        conn.close()

# قالب HTML للوحة التحكم
DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>لوحة تحكم حجوزات فيزا إسبانيا</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #ff6b6b, #ee5a24);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .header p {
            font-size: 1.2em;
            opacity: 0.9;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            padding: 30px;
        }
        
        .stat-card {
            background: linear-gradient(135deg, #74b9ff, #0984e3);
            color: white;
            padding: 25px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 10px 20px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
        }
        
        .stat-card h3 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .stat-card p {
            font-size: 1.1em;
            opacity: 0.9;
        }
        
        .content-section {
            padding: 30px;
            border-top: 1px solid #eee;
        }
        
        .section-title {
            font-size: 1.8em;
            color: #333;
            margin-bottom: 20px;
            text-align: center;
        }
        
        .bookings-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        
        .bookings-table th,
        .bookings-table td {
            padding: 15px;
            text-align: right;
            border-bottom: 1px solid #eee;
        }
        
        .bookings-table th {
            background: linear-gradient(135deg, #a29bfe, #6c5ce7);
            color: white;
            font-weight: bold;
        }
        
        .bookings-table tr:hover {
            background: #f8f9fa;
        }
        
        .visa-types {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }
        
        .visa-type-card {
            background: linear-gradient(135deg, #fd79a8, #e84393);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }
        
        .refresh-btn {
            position: fixed;
            bottom: 30px;
            left: 30px;
            background: linear-gradient(135deg, #00b894, #00a085);
            color: white;
            border: none;
            padding: 15px 25px;
            border-radius: 50px;
            font-size: 1.1em;
            cursor: pointer;
            box-shadow: 0 10px 20px rgba(0,0,0,0.2);
            transition: all 0.3s ease;
        }
        
        .refresh-btn:hover {
            transform: translateY(-3px);
            box-shadow: 0 15px 30px rgba(0,0,0,0.3);
        }
        
        .last-update {
            text-align: center;
            color: #666;
            margin-top: 20px;
            font-style: italic;
        }
        
        @media (max-width: 768px) {
            .stats-grid {
                grid-template-columns: 1fr;
            }
            
            .header h1 {
                font-size: 2em;
            }
            
            .bookings-table {
                font-size: 0.9em;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🇪🇸 لوحة تحكم حجوزات فيزا إسبانيا</h1>
            <p>نظام مراقبة وإحصائيات الحجوزات الناجحة</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <h3>{{ stats.total_bookings }}</h3>
                <p>إجمالي الحجوزات</p>
            </div>
            <div class="stat-card">
                <h3>{{ stats.today_bookings }}</h3>
                <p>حجوزات اليوم</p>
            </div>
            <div class="stat-card">
                <h3>{{ stats.week_bookings }}</h3>
                <p>حجوزات الأسبوع</p>
            </div>
            <div class="stat-card">
                <h3>{{ stats.unique_users }}</h3>
                <p>المستخدمون الفريدون</p>
            </div>
        </div>
        
        {% if stats.last_booking %}
        <div class="content-section">
            <h2 class="section-title">آخر حجز ناجح</h2>
            <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; text-align: center;">
                <p><strong>الاسم:</strong> {{ stats.last_booking.full_name }}</p>
                <p><strong>نوع الفيزا:</strong> {{ stats.last_booking.visa_type }}</p>
                <p><strong>التاريخ:</strong> {{ stats.last_booking.booking_date }}</p>
            </div>
        </div>
        {% endif %}
        
        {% if stats.visa_types %}
        <div class="content-section">
            <h2 class="section-title">الحجوزات حسب نوع الفيزا</h2>
            <div class="visa-types">
                {% for visa_type in stats.visa_types %}
                <div class="visa-type-card">
                    <h3>{{ visa_type.count }}</h3>
                    <p>{{ visa_type.visa_type }}</p>
                </div>
                {% endfor %}
            </div>
        </div>
        {% endif %}
        
        {% if stats.recent_bookings %}
        <div class="content-section">
            <h2 class="section-title">آخر الحجوزات (10 حجوزات)</h2>
            <table class="bookings-table">
                <thead>
                    <tr>
                        <th>الاسم الكامل</th>
                        <th>رقم الجواز</th>
                        <th>نوع الفيزا</th>
                        <th>تاريخ الحجز</th>
                        <th>الحالة</th>
                    </tr>
                </thead>
                <tbody>
                    {% for booking in stats.recent_bookings %}
                    <tr>
                        <td>{{ booking.full_name }}</td>
                        <td>{{ booking.passport_number }}</td>
                        <td>{{ booking.visa_type }}</td>
                        <td>{{ booking.booking_date }}</td>
                        <td style="color: #00b894; font-weight: bold;">✅ نجح</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        {% endif %}
        
        <div class="last-update">
            آخر تحديث: {{ current_time }}
        </div>
    </div>
    
    <button class="refresh-btn" onclick="location.reload()">
        🔄 تحديث
    </button>
    
    <script>
        // تحديث تلقائي كل 30 ثانية
        setInterval(function() {
            location.reload();
        }, 30000);
    </script>
</body>
</html>
"""

@dashboard_app.route('/')
def dashboard():
    """عرض لوحة التحكم الرئيسية"""
    stats = get_booking_statistics()
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    return render_template_string(DASHBOARD_TEMPLATE, 
                                stats=stats, 
                                current_time=current_time)

@dashboard_app.route('/api/stats')
def api_stats():
    """API للحصول على الإحصائيات بصيغة JSON"""
    stats = get_booking_statistics()
    return jsonify(stats)

@dashboard_app.route('/api/bookings')
def api_bookings():
    """API للحصول على قائمة الحجوزات"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'})
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM booking_logs ORDER BY booking_date DESC")
        bookings = [dict(row) for row in cursor.fetchall()]
        return jsonify(bookings)
    except Exception as e:
        return jsonify({'error': str(e)})
    finally:
        conn.close()

def run_dashboard(host='127.0.0.1', port=5001, debug=False):
    """تشغيل لوحة التحكم"""
    print(f"🚀 تشغيل لوحة التحكم على: http://{host}:{port}")
    dashboard_app.run(host=host, port=port, debug=debug)

if __name__ == "__main__":
    print("🎛️ بدء تشغيل لوحة تحكم حجوزات فيزا إسبانيا")
    print("=" * 50)
    
    # التحقق من وجود قاعدة البيانات
    if not os.path.exists('notifications.db'):
        print("⚠️ لم يتم العثور على قاعدة بيانات الإشعارات")
        print("💡 قم بتشغيل السكريبت الرئيسي أولاً لإنشاء قاعدة البيانات")
    else:
        print("✅ تم العثور على قاعدة البيانات")
    
    # تشغيل لوحة التحكم
    run_dashboard(debug=True)