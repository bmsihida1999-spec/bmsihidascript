#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
اختبار مرئي لبوت فيزا إسبانيا
يفتح المتصفح ويظهر كيف يعمل البوت بصريا
"""

import time
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class VisibleSpainVisaBot:
    def __init__(self):
        self.driver = None
        self.wait = None
        
    def setup_driver(self):
        """إعداد متصفح Chrome للاختبار المرئي"""
        print("🔧 إعداد متصفح Chrome...")
        
        chrome_options = Options()
        # إعدادات للاختبار المرئي - لا نخفي المتصفح
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # تعيين user agent طبيعي
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.wait = WebDriverWait(self.driver, 10)
            print("✅ تم تشغيل Chrome بنجاح!")
            return True
        except Exception as e:
            print(f"❌ خطأ في تشغيل Chrome: {e}")
            return False
    
    def check_and_close_warning_window(self, city_name):
        """فحص وإغلاق نافذة التحذير إذا كانت موجودة"""
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
        """إغلاق النافذة المنبثقة للتحذير إن وجدت"""
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
    
    def run_visible_test(self):
        """تشغيل الاختبار المرئي"""
        print("=" * 50)
        print("🧪 اختبار مرئي لبوت فيزا إسبانيا")
        print("=" * 50)
        print("🚀 بدء الاختبار المرئي...")
        
        if not self.setup_driver():
            return False
        
        try:
            # فتح الموقع
            print("📱 فتح موقع BLS Spain Morocco...")
            self.driver.get("https://blsspainmorocco.com")
            time.sleep(5)
            
            # إغلاق نافذة التحذير
            self.close_warning_popup()
            
            # تحليل الصفحة الرئيسية
            print("🔍 تحليل محتوى الصفحة الرئيسية...")
            page_source = self.driver.page_source
            print(f"📊 طول HTML: {len(page_source)} حرف")
            
            # البحث عن روابط المدن والانتقال إلى طنجة أولاً
            city_links = [
                ('Tangier', 'https://blsspainmorocco.com/tangier'),
                ('Agadir', 'https://blsspainmorocco.com/agadir'),
                ('Casablanca', 'https://blsspainmorocco.com/casablanca'),
                ('Rabat', 'https://blsspainmorocco.com/rabat'),
                ('Tetouan', 'https://blsspainmorocco.com/tetouan')
            ]
            
            print("🏙️ البحث عن روابط المدن...")
            city_found = False
            
            for city_name, city_url in city_links:
                try:
                    # البحث عن رابط المدينة
                    city_link = None
                    try:
                        city_link = self.driver.find_element(By.XPATH, f"//a[contains(@href, '{city_name.lower()}')]")
                    except:
                        try:
                            city_link = self.driver.find_element(By.XPATH, f"//a[contains(text(), '{city_name}')]")
                        except:
                            continue
                    
                    if city_link and city_link.is_displayed():
                        print(f"✅ تم العثور على رابط {city_name}")
                        print(f"🖱️ الانتقال إلى صفحة {city_name}...")
                        
                        # الانتقال مباشرة إلى صفحة المدينة
                        self.driver.get(city_url)
                        city_found = True
                        print(f"⏳ انتظار تحميل صفحة {city_name} بالكامل...")
                        time.sleep(5)  # انتظار تحميل الصفحة
                        
                        # البقاء في صفحة المدينة ومراقبة نافذة التحذير باستمرار
                        print(f"🏠 البقاء في صفحة {city_name} لمراقبة نافذة التحذير...")
                        print("⏳ مراقبة مستمرة لظهور نافذة التحذير (بدون حد زمني)...")
                        print("🌐 سيتم التعامل مع النافذة فور ظهورها")
                        
                        try:
                            warning_found = False
                            check_interval = 2  # فحص كل ثانيتين
                            elapsed_time = 0
                            max_wait_time = 120  # حد أقصى 2 دقيقة للانتظار
                            
                            # مراقبة مستمرة مع حد زمني أقصى
                            while elapsed_time < max_wait_time:
                                print(f"⏰ الوقت المنقضي: {elapsed_time} ثانية - مراقبة مستمرة...")
                                
                                # تحديث الصفحة تلقائياً كل 60 ثانية إذا لم تظهر النافذة
                                if elapsed_time > 0 and elapsed_time % 60 == 0:
                                    print(f"🔄 تحديث الصفحة تلقائياً بعد {elapsed_time} ثانية لإظهار نافذة التحذير...")
                                    try:
                                        self.driver.refresh()
                                        time.sleep(3)  # انتظار تحميل الصفحة
                                        print("✅ تم تحديث الصفحة بنجاح")
                                        print("🔍 مراقبة مكثفة لنافذة التحذير بعد التحديث...")
                                        
                                        # مراقبة مكثفة لمدة 30 ثانية بعد التحديث للتعامل مع النوافذ المتكررة
                                        intensive_monitoring_start = time.time()
                                        while time.time() - intensive_monitoring_start < 30:
                                            window_closed = self.check_and_close_warning_window(city_name)
                                            if window_closed:
                                                print("⏳ انتظار 5 ثوانِ للتأكد من عدم ظهور النافذة مرة أخرى...")
                                                time.sleep(5)
                                                # فحص مرة أخرى للتأكد
                                                if self.check_and_close_warning_window(city_name):
                                                    print("⚠️ ظهرت النافذة مرة أخرى - تم إغلاقها")
                                                    time.sleep(3)
                                            time.sleep(1)  # فحص كل ثانية
                                        
                                    except Exception as refresh_error:
                                        print(f"⚠️ خطأ في تحديث الصفحة: {refresh_error}")
                                
                                # إضافة رسائل تشخيصية لحالة الشبكة كل 30 ثانية
                                if elapsed_time > 0 and elapsed_time % 30 == 0:
                                    print(f"🌐 فحص حالة الاتصال... (مرت {elapsed_time} ثانية)")
                                    try:
                                        current_url = self.driver.current_url
                                        page_title = self.driver.title
                                        print(f"📍 الصفحة الحالية: {page_title}")
                                        print(f"🔗 الرابط: {current_url}")
                                        print("🔍 البحث عن نافذة التحذير...")
                                    except:
                                        print("⚠️ مشكلة في الاتصال بالصفحة")
                                
                                # فحص نافذة التحذير بشكل عادي
                                window_closed = self.check_and_close_warning_window(city_name)
                                if window_closed:
                                    print("⏳ انتظار 5 ثوانِ للتأكد من عدم ظهور النافذة مرة أخرى...")
                                    time.sleep(5)
                                    
                                    # فحص مرة أخرى للتأكد من عدم ظهور النافذة
                                    final_check = self.check_and_close_warning_window(city_name)
                                    if final_check:
                                        print("⚠️ ظهرت النافذة مرة أخرى - تم إغلاقها")
                                        time.sleep(3)
                                    
                                    print("✅ تأكدنا من عدم ظهور النافذة مرة أخرى")
                                    print("🔍 البحث عن زر المواعيد...")
                                    self.find_and_click_appointment_button(city_name)
                                    return  # الخروج من الدالة بعد النجاح
                                
                                time.sleep(check_interval)
                                elapsed_time += check_interval
                            
                            # إذا انتهى الوقت المحدد بدون ظهور نافذة التحذير، ننتقل مباشرة للبحث عن زر المواعيد
                            print(f"⏰ انتهى الوقت المحدد ({max_wait_time} ثانية) - الانتقال إلى البحث عن زر المواعيد...")
                            print("🔍 البحث عن زر المواعيد...")
                            self.find_and_click_appointment_button(city_name)
                            return  # الخروج من الدالة
                            
                            # فحص جميع العناصر المرئية في الصفحة للتشخيص
                            print("🔍 فحص جميع العناصر المرئية للتشخيص...")
                            all_elements = self.driver.find_elements(By.XPATH, "//*")
                            modal_found = False
                            
                            for element in all_elements:
                                try:
                                    if element.is_displayed():
                                        tag_name = element.tag_name
                                        class_attr = element.get_attribute('class') or ''
                                        id_attr = element.get_attribute('id') or ''
                                        text = element.text.strip()
                                        
                                        # البحث عن عناصر النافذة المنبثقة
                                        if ('modal' in class_attr.lower() or 
                                            'popup' in class_attr.lower() or 
                                            'dialog' in class_attr.lower() or
                                            'disclaimer' in class_attr.lower() or
                                            'overlay' in class_attr.lower()):
                                            print(f"🎯 عنصر نافذة منبثقة: {tag_name}, class='{class_attr}', id='{id_attr}'")
                                            modal_found = True
                                            
                                        # البحث عن أزرار الإغلاق
                                        if (text in ['×', 'X', 'Close', 'إغلاق'] or 
                                            'close' in class_attr.lower() or
                                            'btn-close' in class_attr.lower()):
                                            print(f"🎯 زر إغلاق محتمل: {tag_name}, class='{class_attr}', text='{text}'")
                                except:
                                    continue
                        except Exception as e:
                            print(f"⚠️ خطأ في البحث عن نافذة التحذير: {str(e)}")
                        
                        break  # الخروج من حلقة المدن بعد معالجة أول مدينة
                        
                except Exception as e:
                    print(f"⚠️ خطأ مع {city_name}: {e}")
                    continue
            
            if not city_found:
                print("❌ لم يتم العثور على أي روابط مدن")
                print("🔍 هذا يعني أن هيكل الموقع تغير أو هناك مشكلة في التحميل")
            
            # انتظار لمشاهدة النتيجة
            print("\n👀 المتصفح مفتوح الآن - يمكنك مشاهدة العملية!")
            print("🔍 تفحص الموقع وشاهد كيف يعمل البوت...")

            print("\n⏸️  اضغط Enter عندما تنتهي من المشاهدة لإغلاق المتصفح...")
            input()
            
            return True
            
        except Exception as e:
            print(f"❌ خطأ في الاختبار: {e}")
            return False
        finally:
            if self.driver:
                print("🔄 إغلاق المتصفح...")
                self.driver.quit()

    def find_and_click_appointment_button(self, city_name):
        """البحث عن زر المواعيد والنقر عليه"""
        try:
            print(f"🔍 البحث عن أزرار المواعيد في صفحة {city_name}...")
            current_url = self.driver.current_url
            print(f"🌐 الرابط الحالي: {current_url}")
            
            # أولاً: التحقق من أننا في الصفحة الرئيسية والانتقال إلى صفحة Book Appointment
            if "tangier" in current_url.lower() and "appointment" not in current_url.lower():
                print("📍 نحن في الصفحة الرئيسية - البحث عن رابط 'Book Appointment'...")
                
                # البحث عن رابط Book Appointment في القائمة العلوية أو الصفحة
                book_appointment_selectors = [
                    "//a[contains(@href, 'appointment') or contains(text(), 'Book Appointment')]",
                    "//a[contains(text(), 'Book Appointment')]",
                    "//a[contains(text(), 'Book your appointment')]",
                    "//a[contains(@class, 'appointment')]",
                    "//div[contains(text(), 'Book your appointment')]//parent::a",
                    "//div[contains(text(), 'Book an Appointment')]//parent::a",
                    "//*[contains(text(), 'Book Appointment')]",
                    "//*[contains(text(), 'Book your appointment')]"
                ]
                
                navigation_success = False
                for selector in book_appointment_selectors:
                    try:
                        elements = self.driver.find_elements(By.XPATH, selector)
                        for element in elements:
                            if element.is_displayed() and element.is_enabled():
                                print(f"✅ تم العثور على رابط المواعيد: '{element.text}'")
                                print("🖱️ النقر للانتقال إلى صفحة المواعيد...")
                                
                                # محاولة النقر بطرق متعددة
                                click_success = False
                                
                                # الطريقة 1: النقر العادي
                                try:
                                    element.click()
                                    click_success = True
                                    print("✅ نجح النقر العادي")
                                except Exception as e1:
                                    print(f"⚠️ فشل النقر العادي: {str(e1)}")
                                    
                                    # الطريقة 2: النقر باستخدام JavaScript
                                    try:
                                        print("🔄 محاولة النقر باستخدام JavaScript...")
                                        self.driver.execute_script("arguments[0].click();", element)
                                        click_success = True
                                        print("✅ نجح النقر باستخدام JavaScript")
                                    except Exception as e2:
                                        print(f"⚠️ فشل النقر باستخدام JavaScript: {str(e2)}")
                                        
                                        # الطريقة 3: التمرير إلى العنصر ثم النقر
                                        try:
                                            print("🔄 محاولة التمرير إلى العنصر ثم النقر...")
                                            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                                            time.sleep(2)
                                            element.click()
                                            click_success = True
                                            print("✅ نجح النقر بعد التمرير")
                                        except Exception as e3:
                                            print(f"⚠️ فشل النقر بعد التمرير: {str(e3)}")
                                            
                                            # الطريقة 4: استخدام ActionChains
                                            try:
                                                print("🔄 محاولة النقر باستخدام ActionChains...")
                                                from selenium.webdriver.common.action_chains import ActionChains
                                                actions = ActionChains(self.driver)
                                                actions.move_to_element(element).click().perform()
                                                click_success = True
                                                print("✅ نجح النقر باستخدام ActionChains")
                                            except Exception as e4:
                                                print(f"⚠️ فشل النقر باستخدام ActionChains: {str(e4)}")
                                
                                if click_success:
                                    print("⏳ انتظار تحميل الصفحة الجديدة...")
                                    
                                    # انتظار تدريجي مع فحص حالة الصفحة
                                    max_wait_attempts = 10
                                    wait_attempt = 0
                                    navigation_success_inner = False
                                    
                                    while wait_attempt < max_wait_attempts:
                                        try:
                                            time.sleep(1)  # انتظار ثانية واحدة في كل مرة
                                            wait_attempt += 1
                                            
                                            # محاولة الحصول على الرابط الجديد بحذر
                                            try:
                                                new_url = self.driver.current_url
                                                print(f"🌐 فحص الرابط (محاولة {wait_attempt}): {new_url}")
                                                
                                                # التحقق من تغيير الرابط أو وجود كلمة appointment
                                                if new_url != current_url or "appointment" in new_url.lower():
                                                    print("✅ تم الانتقال بنجاح إلى صفحة المواعيد!")
                                                    navigation_success_inner = True
                                                    break
                                                elif wait_attempt >= 8:
                                                    print("⚠️ لم يتغير الرابط بعد 8 محاولات، ربما لم ينجح النقر")
                                                    break
                                                    
                                            except Exception as url_error:
                                                print(f"⚠️ خطأ في الحصول على الرابط (محاولة {wait_attempt}): {str(url_error)}")
                                                if wait_attempt >= 8:
                                                    break
                                                continue
                                                
                                        except Exception as wait_error:
                                            print(f"⚠️ خطأ في انتظار تحميل الصفحة: {str(wait_error)}")
                                            break
                                    
                                    if navigation_success_inner:
                                        navigation_success = True
                                        break
                    except Exception as e:
                        print(f"⚠️ خطأ عام في معالجة العنصر: {str(e)}")
                        continue
                    
                    if navigation_success:
                        break
                
                if not navigation_success:
                    print("❌ فشل في الانتقال إلى صفحة المواعيد")
                    return False
            
            # ثانياً: الآن نحن في صفحة المواعيد، البحث عن المواعيد المتاحة
            print("🔍 البحث عن المواعيد المتاحة في الصفحة...")
            
            # بدء مراقبة المواعيد المتاحة
            return self.monitor_appointments(city_name)
            
        except Exception as e:
            print(f"⚠️ خطأ في البحث عن زر المواعيد: {str(e)}")
            return False

    def monitor_appointments(self, city_name):
        """مراقبة المواعيد المتاحة وملء النماذج تلقائياً"""
        try:
            print(f"🔍 بدء مراقبة المواعيد في صفحة {city_name}...")
            
            # معلومات المستخدم المحفوظة
            user_data = {
                'first_name': 'محمد',
                'last_name': 'أحمد',
                'email': 'mohammed.ahmed@example.com',
                'phone': '+212600123456',
                'passport': 'AB123456',
                'nationality': 'Morocco',
                'birth_date': '01/01/1990'
            }
            
            check_interval = 5  # فحص كل 5 ثوانِ
            elapsed_time = 0
            max_monitoring_time = 300  # 5 دقائق كحد أقصى للمراقبة
            
            while elapsed_time < max_monitoring_time:
                try:
                    print(f"⏰ مراقبة المواعيد - الوقت المنقضي: {elapsed_time} ثانية...")
                    
                    # البحث عن المواعيد المتاحة
                    available_appointments = self.find_available_appointments()
                    
                    if available_appointments:
                        print(f"🎉 تم العثور على {len(available_appointments)} موعد متاح!")
                        
                        # اختيار أول موعد متاح
                        first_appointment = available_appointments[0]
                        print(f"📅 اختيار الموعد: {first_appointment}")
                        
                        # النقر على الموعد
                        if self.click_appointment(first_appointment):
                            print("✅ تم النقر على الموعد بنجاح!")
                            
                            # ملء النموذج
                            if self.fill_appointment_form(user_data):
                                print("✅ تم ملء النموذج بنجاح!")
                                
                                # الانتقال للصفحة التالية
                                if self.proceed_to_next_page():
                                    print("✅ تم الانتقال للصفحة التالية!")
                                    
                                    # تطبيق نفس العملية على الصفحة الجديدة
                                    return self.handle_next_appointment_page()
                                else:
                                    print("⚠️ فشل في الانتقال للصفحة التالية")
                            else:
                                print("⚠️ فشل في ملء النموذج")
                        else:
                            print("⚠️ فشل في النقر على الموعد")
                    else:
                        print("⏳ لا توجد مواعيد متاحة حالياً...")
                    
                    # فحص نافذة التحذير
                    self.check_and_close_warning_window(city_name)
                    
                    time.sleep(check_interval)
                    elapsed_time += check_interval
                    
                except Exception as e:
                    print(f"⚠️ خطأ في مراقبة المواعيد: {str(e)}")
                    time.sleep(check_interval)
                    elapsed_time += check_interval
            
            print("⏰ انتهت فترة المراقبة المحددة")
            return False
            
        except Exception as e:
            print(f"❌ خطأ في مراقبة المواعيد: {str(e)}")
            return False

    def find_available_appointments(self):
        """البحث عن المواعيد المتاحة"""
        try:
            appointments = []
            
            # البحث عن أزرار أو روابط المواعيد المتاحة
            appointment_selectors = [
                "//button[contains(@class, 'available')]",
                "//a[contains(@class, 'appointment')]",
                "//div[contains(@class, 'slot')]",
                "//button[not(contains(@class, 'disabled'))]",
                "//*[contains(text(), 'Available')]",
                "//*[contains(text(), 'متاح')]",
                "//td[contains(@class, 'available')]",
                "//span[contains(@class, 'time-slot')]"
            ]
            
            for selector in appointment_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            text = element.text.strip()
                            if text and 'disabled' not in element.get_attribute('class').lower():
                                appointments.append(element)
                                print(f"📅 موعد متاح: {text}")
                except:
                    continue
            
            return appointments
            
        except Exception as e:
            print(f"⚠️ خطأ في البحث عن المواعيد: {str(e)}")
            return []

    def click_appointment(self, appointment_element):
        """النقر على موعد محدد"""
        try:
            print(f"🖱️ النقر على الموعد: {appointment_element.text}")
            appointment_element.click()
            time.sleep(2)
            return True
        except Exception as e:
            print(f"⚠️ خطأ في النقر على الموعد: {str(e)}")
            return False

    def fill_appointment_form(self, user_data):
        """ملء نموذج الموعد بالمعلومات المحفوظة"""
        try:
            print("📝 بدء ملء النموذج...")
            
            # قائمة الحقول المحتملة
            form_fields = {
                'first_name': ['first_name', 'firstName', 'fname', 'given_name', 'الاسم الأول'],
                'last_name': ['last_name', 'lastName', 'lname', 'family_name', 'الاسم الأخير'],
                'email': ['email', 'email_address', 'البريد الإلكتروني'],
                'phone': ['phone', 'telephone', 'mobile', 'رقم الهاتف'],
                'passport': ['passport', 'passport_number', 'رقم الجواز'],
                'nationality': ['nationality', 'country', 'الجنسية'],
                'birth_date': ['birth_date', 'dob', 'date_of_birth', 'تاريخ الميلاد']
            }
            
            filled_fields = 0
            
            for field_type, field_names in form_fields.items():
                if field_type in user_data:
                    value = user_data[field_type]
                    
                    for field_name in field_names:
                        try:
                            # البحث بالاسم
                            element = self.driver.find_element(By.NAME, field_name)
                            if element.is_displayed() and element.is_enabled():
                                element.clear()
                                element.send_keys(value)
                                print(f"✅ تم ملء {field_type}: {value}")
                                filled_fields += 1
                                break
                        except:
                            try:
                                # البحث بالـ ID
                                element = self.driver.find_element(By.ID, field_name)
                                if element.is_displayed() and element.is_enabled():
                                    element.clear()
                                    element.send_keys(value)
                                    print(f"✅ تم ملء {field_type}: {value}")
                                    filled_fields += 1
                                    break
                            except:
                                try:
                                    # البحث بالـ placeholder
                                    element = self.driver.find_element(By.XPATH, f"//input[@placeholder='{field_name}']")
                                    if element.is_displayed() and element.is_enabled():
                                        element.clear()
                                        element.send_keys(value)
                                        print(f"✅ تم ملء {field_type}: {value}")
                                        filled_fields += 1
                                        break
                                except:
                                    continue
            
            print(f"📊 تم ملء {filled_fields} حقل من أصل {len(user_data)} حقول")
            return filled_fields > 0
            
        except Exception as e:
            print(f"⚠️ خطأ في ملء النموذج: {str(e)}")
            return False

    def proceed_to_next_page(self):
        """الانتقال للصفحة التالية"""
        try:
            print("➡️ البحث عن زر المتابعة...")
            
            # أزرار المتابعة المحتملة
            next_buttons = [
                "//button[contains(text(), 'Next')]",
                "//button[contains(text(), 'Continue')]",
                "//button[contains(text(), 'Submit')]",
                "//button[contains(text(), 'Proceed')]",
                "//input[@type='submit']",
                "//*[contains(text(), 'التالي')]",
                "//*[contains(text(), 'متابعة')]",
                "//*[contains(text(), 'إرسال')]",
                "//button[@type='submit']"
            ]
            
            for selector in next_buttons:
                try:
                    element = self.driver.find_element(By.XPATH, selector)
                    if element.is_displayed() and element.is_enabled():
                        print(f"✅ تم العثور على زر المتابعة: {element.text}")
                        element.click()
                        time.sleep(3)
                        return True
                except:
                    continue
            
            print("⚠️ لم يتم العثور على زر المتابعة")
            return False
            
        except Exception as e:
            print(f"⚠️ خطأ في الانتقال للصفحة التالية: {str(e)}")
            return False

    def handle_next_appointment_page(self):
        """التعامل مع صفحة المواعيد الجديدة"""
        try:
            print("🔄 التعامل مع صفحة المواعيد الجديدة...")
            
            # انتظار تحميل الصفحة
            time.sleep(3)
            
            # تطبيق نفس عملية مراقبة المواعيد
            return self.monitor_appointments("الصفحة الجديدة")
            
        except Exception as e:
            print(f"⚠️ خطأ في التعامل مع الصفحة الجديدة: {str(e)}")
            return False

def main():
    """الدالة الرئيسية"""
    bot = VisibleSpainVisaBot()
    success = bot.run_visible_test()
    
    if success:
        print("✅ تم الاختبار بنجاح!")
        print("💡 الآن يمكنك تشغيل التطبيق الحقيقي باستخدام: python app.py")
    else:
        print("❌ فشل الاختبار!")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())