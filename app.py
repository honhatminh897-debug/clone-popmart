import os, io, time, json, random, string
from flask import Flask, request, render_template_string, Response
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__)

DAYS = [
    {"id": "35", "label": "13/08/2025"},
    {"id": "36", "label": "14/08/2025"},
    {"id": "37", "label": "15/08/2025"},
    {"id": "38", "label": "16/08/2025"},
]

full_pair = os.getenv("FULL_PAIR", "")
FULL_SESSIONS = set()
if full_pair:
    try:
        d, s = [x.strip() for x in full_pair.split(",", 1)]
        FULL_SESSIONS.add((d, s))
    except Exception:
        pass
FULL_SESSIONS.add(("37", "S1"))

CAPTCHA_STORE = {}
QR_CACHE = {}

def gen_code(n=5):
    import string, random
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=n))

def make_png_with_text(text: str, size=(180, 50), bg=(242,242,242), fg=(18,18,18)):
    img = Image.new('RGB', size, color=bg)
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 28)
    except:
        font = ImageFont.load_default()
    try:
        bbox = d.textbbox((0,0), text, font=font)
        tw = bbox[2]-bbox[0]; th = bbox[3]-bbox[1]
    except Exception:
        tw, th = d.textlength(text, font=font), 28
    x = max(10, (size[0]-tw)//2)
    y = max(10, (size[1]-th)//2)
    d.text((x, y), text, fill=fg, font=font)
    bio = io.BytesIO()
    img.save(bio, format="PNG")
    return bio.getvalue()

PAGE_HTML = """<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml"><head><meta http-equiv="Content-Type" content="text/html; charset=UTF-8"><title>ĐĂNG KÝ THÔNG TIN POP-MART</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0"><meta http-equiv="X-UA-Compatible" content="ie=edge">
<style>
.body{background:#f2f2f2;font-family:Arial,Helvetica,sans-serif}
.MyButton{background:#f89d17;color:#fff;padding:10px 16px;border-radius:8px;display:inline-block;cursor:pointer;text-decoration:none}
.MySelect,.myTextBox{padding:9px 12px;border:1px solid #da253475;border-radius:8px;width:100%;box-sizing:border-box}
.ConScreen{max-width:900px;margin:16px auto}
.TieuDe{font-size:22px;font-weight:bold;text-align:center;margin-bottom:10px}
.dvField1{margin-top:8px}
</style>
<script>
function OpenThongBao(){document.getElementById("dvThongBao").style.display="block";}
function CloseThongBao(){document.getElementById("dvThongBao").style.display="none";LoadCaptcha();}
window.onload=function(){LoadCaptcha();}
function LoadCaptcha(){
  var x=new XMLHttpRequest();
  x.onreadystatechange=function(){if(x.readyState==4 && x.status==200){document.getElementById("dvCaptcha").innerHTML=x.responseText.trim();}}
  x.open("GET","/Ajax.aspx?Action=LoadCaptcha",true);x.send();
}
function LoadPhien(){
  var idNgayBanHang=document.getElementById("slNgayBanHang").value;
  var x=new XMLHttpRequest();
  x.onreadystatechange=function(){if(x.readyState==4 && x.status==200){
    var arr=x.responseText.trim().split("||@@||");
    if(arr.length==2){document.getElementById("slPhien").innerHTML=arr[0].trim();document.getElementById("dvGhiChuNgayBanHang").innerHTML=arr[1].trim();}
    else{document.getElementById("slPhien").innerHTML="";document.getElementById("dvGhiChuNgayBanHang").innerHTML="";}}
  }
  x.open("GET","/Ajax.aspx?Action=LoadPhien&idNgayBanHang="+idNgayBanHang,true);x.send();
}
function DangKyThamDu(){
  var idNgayBanHang=document.getElementById("slNgayBanHang").value.trim();
  var idPhien=document.getElementById("slPhien").value.trim();
  var HoTen=document.getElementById("txtHoTen").value.trim();
  var Ngay=document.getElementById("txtNgaySinh_Ngay").value.trim();
  var Thang=document.getElementById("txtNgaySinh_Thang").value.trim();
  var Nam=document.getElementById("txtNgaySinh_Nam").value.trim();
  var SoDienThoai=document.getElementById("txtSoDienThoai").value.trim();
  var Email=document.getElementById("txtEmail").value.trim();
  var CCCD=document.getElementById("txtCCCD").value.trim();
  var Captcha=document.getElementById("txtCaptcha").value.trim();
  var url="/Ajax.aspx?Action=DangKyThamDu&idNgayBanHang="+encodeURIComponent(idNgayBanHang)+"&idPhien="+encodeURIComponent(idPhien)+"&HoTen="+encodeURIComponent(HoTen)+"&NgaySinh_Ngay="+encodeURIComponent(Ngay)+"&NgaySinh_Thang="+encodeURIComponent(Thang)+"&NgaySinh_Nam="+encodeURIComponent(Nam)+"&SoDienThoai="+encodeURIComponent(SoDienThoai)+"&Email="+encodeURIComponent(Email)+"&CCCD="+encodeURIComponent(CCCD)+"&Captcha="+encodeURIComponent(Captcha);
  var x=new XMLHttpRequest();
  x.onreadystatechange=function(){
    if(x.readyState==4 && x.status==200){
      var result=x.responseText.trim();
      if(result.indexOf("!!!True|~~|")>=0){
        var arr=result.split("|~~|");
        var ma=arr[3].trim();      // match JS gốc: arr[3] là mã
        var htmlKQ=arr[2].trim();  // arr[2] là HTML confirm
        document.getElementById("dvConXacNhan_Content").innerHTML="<div style='font-weight:bold;color:#329a36;font-size:23px;margin-bottom:5px;text-align:center;margin-top:15px'>ĐĂNG KÝ THÀNH CÔNG</div>"+htmlKQ;
        document.getElementById("txtQRCode").value=ma;
        GenQRImage(idPhien,ma);
      }else{
        if(result!=""){
          if(result.toLowerCase().indexOf("captcha")>=0){LoadCaptcha();}
          document.getElementById("dvNoiDungThongBao").innerHTML=result;OpenThongBao();
        }else{
          document.getElementById("dvNoiDungThongBao").innerHTML="<div>Có vấn đề xảy ra. Bạn vui lòng thử lại!</div><div style='font-style:italic;margin-top:5px;'>Something went wrong. Please try again!</div>";OpenThongBao();
        }
      }
    }
  }
  x.open("GET",url,true);x.send();
}
function GenQRImage(idPhien,MaThamDu){
  var x=new XMLHttpRequest();
  x.open("POST","/DangKy.aspx/GenQRImage",true);
  x.setRequestHeader("Content-Type","application/json; charset=utf-8");
  x.onreadystatechange=function(){
    if(x.readyState==4 && x.status==200){
      try{
        var j=JSON.parse(x.responseText||"{}");
        if(j.d){
          document.getElementById("qrdl").href=j.d;
          // Hiện khối QR & render ảnh
          document.getElementById("dvTaoMaQR").style.display="";
          document.getElementById("qrcode").innerHTML="<img src='"+j.d+"' style='width:150px'/>";
          SendEmail(idPhien,MaThamDu);
        }
      }catch(e){}
    }
  }
  x.send(JSON.stringify({GiaTri:MaThamDu,NoiDungHienBenDuoi:MaThamDu}));
}
function SendEmail(idPhien,MaThamDu){
  var x=new XMLHttpRequest();
  x.open("GET","/Ajax.aspx?Action=SendEmail&idPhien="+encodeURIComponent(idPhien)+"&MaThamDu="+encodeURIComponent(MaThamDu),true);
  x.onreadystatechange=function(){};
  x.send();
}
function CloseThongBao(){document.getElementById("dvThongBao").style.display="none";}
</script>
</head>
<body class="body">
<form>
<div class="ConScreen">
  <div style="background:#fff;padding:12px;border-radius:10px;box-shadow:0 0 10px rgba(0,0,0,.2);">
    <div class="TieuDe">ĐĂNG KÝ THAM GIA</div>
    <div class="dvField1">
      <div>Sales date (Ngày bán hàng)</div>
      <select id="slNgayBanHang" onchange="LoadPhien()" class="MySelect">
        {% for d in days %}
          <option value="{{d.id}}">{{d.label}}</option>
        {% endfor %}
        <option value="" selected="selected">-- Chọn --</option>
      </select>
      <div id="dvGhiChuNgayBanHang" style="font-weight:bold;font-style:italic;font-size:16px;margin-top:4px"></div>
    </div>
    <div class="dvField1">
      <div>Session (Phiên)</div>
      <select id="slPhien" class="MySelect"></select>
    </div>
    <div class="dvField1">
      <div>Full name (Họ tên)</div>
      <input id="txtHoTen" type="text" class="myTextBox">
    </div>
    <div class="dvField1">
      <div>Date of birth (Ngày Sinh)</div>
      <table><tr>
        <td><input id="txtNgaySinh_Ngay" placeholder="Ngày" type="number" class="myTextBox" style="width:120px"></td>
        <td style="padding:3px;color:#939">/</td>
        <td><input id="txtNgaySinh_Thang" placeholder="Tháng" type="number" class="myTextBox" style="width:120px"></td>
        <td style="padding:3px;color:#939">/</td>
        <td><input id="txtNgaySinh_Nam" placeholder="Năm" type="number" class="myTextBox" style="width:160px"></td>
      </tr></table>
    </div>
    <div class="dvField1">
      <div>Phone number (Số điện thoại)</div>
      <input id="txtSoDienThoai" type="text" class="myTextBox">
    </div>
    <div class="dvField1">
      <div>Email</div>
      <input id="txtEmail" type="text" class="myTextBox">
    </div>
    <div class="dvField1">
      <div>ID Card/Passport (CCCD/Hộ chiếu)</div>
      <input id="txtCCCD" type="text" class="myTextBox">
    </div>
    <div class="dvField1">
      <div>Captcha</div>
      <table><tr>
        <td id="dvCaptcha" style="width:100px;vertical-align:bottom;"></td>
        <td style="width:70px">
          <input type="text" id="txtCaptcha" placeholder="Nhập captcha (*)" class="myTextBox" style="width:110px">
        </td>
        <td style="text-align:left">
          <a class="MyButton" onclick="LoadCaptcha()">Refresh</a>
        </td>
      </tr></table>
    </div>
    <div id="dvDangKyThamDu" style="text-align:center;padding:10px;margin-top:10px">
      <a id="btDangKyThamGia" onclick="DangKyThamDu()" class="MyButton">Đăng ký</a>
    </div>
    <div id="dvConXacNhan_Content"></div>

    <div id="dvTaoMaQR" style="display:none">
      <input id="txtQRCode" type="text" value="0000" style="display:none">
      <div id="qrcode"></div>
      <div style="text-align:center;margin-top:12%"><a id="qrdl" style="font-weight:bold;color:#4b9f4f;font-size:17px;" download="">Tải mã QR</a></div>
    </div>
  </div>
</div>

<div class="form-popup" id="dvThongBao" style="display:none;position:fixed;left:0;right:0;top:0;bottom:0;background:rgba(0,0,0,.3)">
  <div class="form-container" style="background:#fff;color:#f94c4c;max-width:500px;margin:7% auto;padding:20px;border-radius:10px;text-align:center">
    <div style="text-align:right"><span onclick="CloseThongBao()" style="cursor:pointer;font-weight:bold">x</span></div>
    <div id="dvNoiDungThongBao" style="font-weight:bold;font-size:18px;margin-top:10px"></div>
  </div>
</div>
</form>
</body></html>
"""

@app.route("/popmart")
def popmart():
    return render_template_string(PAGE_HTML, days=DAYS)

@app.route("/Ajax.aspx")
def ajax():
    action = request.args.get("Action", "")
    if action == "LoadCaptcha":
        code = gen_code()
        token = gen_code(8)
        CAPTCHA_STORE[token] = {"code": code, "ts": time.time()}
        img_html = f"<img src='/captcha/{token}.png' style='height:45px;border-radius:10px;margin-left:3px;'>"
        return img_html

    if action == "LoadPhien":
        day_id = request.args.get("idNgayBanHang", "")
        options = []
        for i in range(1, 4):
            val = f"S{i}"
            label = f"Session {i}"
            options.append(f"<option value='{val}'>{label}</option>")
        note = f"<b>Ghi chú</b>: Mock sessions cho day_id={day_id}."
        return "".join(options) + "||@@||" + note

    if action == "DangKyThamDu":
        id_day = request.args.get("idNgayBanHang", "")
        id_ses = request.args.get("idPhien", "")
        captcha = request.args.get("Captcha", "")
        now = time.time()
        valid = {v["code"] for v in CAPTCHA_STORE.values() if now - v["ts"] < 120}
        if captcha.upper() not in valid:
            return "Sai Captcha! / Invalid Captcha!"
        if (id_day, id_ses) in FULL_SESSIONS:
            return "Đã hết số lượng đăng ký phiên này! (This session is full!)"
        ma = gen_code(10)
        html_xn = "<div>Đăng ký thành công (Mock)</div>"
        # IMPORTANT: make arr[2] = HTML, arr[3] = MaThamDu
        payload = f"!!!True|~~|OK|~~|{html_xn}|~~|{ma}"
        return payload

    if action == "SendEmail":
        return "True"

    return "Unknown Action"

@app.route("/DangKy.aspx/GenQRImage", methods=["POST"])
def gen_qr():
    try:
        data = request.get_json(force=True, silent=True) or {}
        value = data.get("GiaTri", "") or data.get("NoiDungHienBenDuoi", "")
        if not value:
            value = gen_code(10)
        png = Image.new('RGB', (220, 220), color=(240,240,240))
        d = ImageDraw.Draw(png)
        try:
            font = ImageFont.truetype("arial.ttf", 24)
        except:
            font = ImageFont.load_default()
        txt = f"{value}"
        w, h = d.textsize(txt, font=font)
        d.text(((220-w)//2, (220-h)//2), txt, fill=(20,20,20), font=font)
        bio = io.BytesIO()
        png.save(bio, format="PNG")
        QR_CACHE[value] = bio.getvalue()
        url = f"/qr/{value}.png"
        return json.dumps({"d": url})
    except Exception:
        return json.dumps({"d": ""})

@app.route("/qr/<code>.png")
def qr_png(code):
    png = QR_CACHE.get(code.replace(".png",""))
    if not png:
        png = make_png_with_text("N/A", size=(220, 220))
    return Response(png, mimetype="image/png")

@app.route("/captcha/<token>.png")
def captcha_png(token):
    token = token.replace(".png", "")
    item = CAPTCHA_STORE.get(token)
    if not item:
        code = gen_code()
        CAPTCHA_STORE[token] = {"code": code, "ts": time.time()}
    else:
        code = item["code"]
    img_bytes = make_png_with_text(code)
    return Response(img_bytes, mimetype="image/png")

@app.route("/")
def index():
    return ("<a href='/popmart'>Go to POP-MART mock</a>", 200)

@app.route("/healthz")
def health():
    return "ok", 200

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)
