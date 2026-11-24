import subprocess
import requests
import time
import json

# إعدادات بوت التلغرام
TOKEN = "9262195612:AAHvhixjILczZNAp4AR2B7mRQAy1heKj6Is"
CHAT_ID = "865508765"
URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

seen_notifications = set()

def send_telegram(title, text, app_name):
    message = f"📱 التطبيق: {app_name}\n📌 العنوان: {title}\n💬 النص: {text}"
    payload = {"chat_id": CHAT_ID, "text": message}
    try:
        requests.post(URL, json=payload, timeout=5)
    except Exception as e:
        print(f"[-] فشل الإرسال: {e}")

def main():
    print("[*] بدء مراقبة الإشعارات...")
    while True:
        try:
            # سحب الإشعارات الحالية عبر Termux API
            output = subprocess.check_output(["termux-notification-list"], text=True)
            notifications = json.loads(output)

            for notif in notifications:
                notif_id = notif.get("id")
                app_name = notif.get("packageName", "Unknown")
                
                # تصفية: واتساب فقط
                if app_name in ["com.whatsapp", "com.whatsapp.w4b"] and notif_id not in seen_notifications:
                    title = notif.get("title", "")
                    text = notif.get("content", "")
                    
                    if title or text:
                        print(f"[+] إشعار جديد من {app_name}: {title} - {text}")
                        send_telegram(title, text, "WhatsApp")
                        seen_notifications.add(notif_id)

        except subprocess.CalledProcessError:
            print("[-] خطأ: تأكد من تثبيت تطبيق Termux:API ومنحه الصلاحيات.")
            time.sleep(10)
        except Exception as e:
            print(f"[-] خطأ غير متوقع: {e}")
            
        time.sleep(3) # فحص الإشعارات كل 3 ثواني

if __name__ == "__main__":
    main()
