
import os, io, random, string, time
from flask import Flask, request, render_template, send_file, jsonify, Response
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__)

# --- Mock data ---
DAYS = [
    {"id": "35", "label": "13/08/2025"},
    {"id": "36", "label": "14/08/2025"},
    {"id": "37", "label": "15/08/2025"},
    {"id": "38", "label": "16/08/2025"},
]
# For simulating "full" sessions easily: day_id -> set(session_value)
FULL_SESSIONS = set()  # e.g. add ("36","S1") to make day 36 S1 full

# In-memory captcha store: token -> answer
CAPTCHA_STORE = {}

def gen_captcha_text(n=5):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=n))

def make_captcha_png(text: str) -> bytes:
    img = Image.new('RGB', (160, 48), color=(240, 240, 240))
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 28)
    except:
        font = ImageFont.load_default()
    d.text((10, 10), text, fill=(20,20,20), font=font)
    bio = io.BytesIO()
    img.save(bio, format="PNG")
    bio.seek(0)
    return bio.getvalue()

@app.route("/popmart")
def popmart():
    return render_template("popmart.html", days=DAYS)

@app.route("/Ajax.aspx")
def ajax():
    action = request.args.get("Action", "")
    if action == "LoadCaptcha":
        # create a new captcha
        code = gen_captcha_text()
        token = gen_captcha_text(8)
        CAPTCHA_STORE[token] = {"code": code, "ts": time.time()}
        # serve an <img> that points to /captcha/<token>.png
        img_html = f'<img src="/captcha/{token}.png" style="height:45px;border-radius:10px;margin-left:3px">'
        return img_html

    if action == "LoadPhien":
        day_id = request.args.get("idNgayBanHang", "")
        # Return 3 sessions for any day id
        options = []
        for i in range(1, 4):
            val = f"S{i}"
            label = f"Session {i}"
            options.append(f'<option value="{val}">{label}</option>')
        note = f"<b>Ghi chú</b>: Đây là mock sessions cho day_id={day_id}."
        return "".join(options) + "||@@||" + note

    if action == "DangKyThamDu":
        # Validate minimal params
        id_day = request.args.get("idNgayBanHang", "")
        id_ses = request.args.get("idPhien", "")
        captcha = request.args.get("Captcha", "")
        # Find latest captcha value (mock: accept last generated within 2 minutes)
        now = time.time()
        valid_codes = {v["code"] for v in CAPTCHA_STORE.values() if now - v["ts"] < 120}
        if captcha.upper() not in valid_codes:
            return "Sai Captcha! / Invalid Captcha!"
        # Simulate "full" when day 37 + S1 as an example
        if (id_day, id_ses) in FULL_SESSIONS or (id_day == "37" and id_ses == "S1"):
            return "Đã hết số lượng đăng ký phiên này! (This session is full!)"
        # Otherwise, success format similar-ish to original
        ma = gen_captcha_text(10)
        msg = "!!!True|~~|<div>Cảm ơn bạn đã đăng ký (Mock)</div>|~~|{}|~~|{}".format("OK", ma)
        return msg

    if action == "SendEmail":
        return "True"

    return "Unknown Action"

@app.route("/captcha/<token>.png")
def captcha_png(token):
    token = token.replace(".png", "")
    item = CAPTCHA_STORE.get(token)
    if not item:
        # create a new one for robustness
        code = gen_captcha_text()
        CAPTCHA_STORE[token] = {"code": code, "ts": time.time()}
    else:
        code = item["code"]
    img_bytes = make_captcha_png(code)
    return Response(img_bytes, mimetype="image/png")

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)
