"""Web layer ของ Lab 02 — ทำหน้าที่บาง ๆ: รับ HTTP แล้วเรียกชั้นวิศวกรรม

ตรรกะการคำนวณทั้งหมดอยู่ใน dc_bias.py เพื่อให้ทดสอบแยกจาก Flask ได้
"""

from flask import Flask, render_template, request

from dc_bias import Region, ValidationError, parse_form, solve

app = Flask(__name__)

# ค่าตัวอย่างจาก handout ใช้เป็นค่าเริ่มต้นในฟอร์ม เพื่อให้สาธิตได้เร็ว
DEFAULTS = {
    "vcc": "12",
    "r1": "100",
    "r2": "22",
    "rc": "2.2",
    "re": "1",
    "beta": "100",
    "vbe": "0.70",
}

# ชื่อที่แสดงบนหน้าเว็บ (ชื่อ enum ภายในเป็นตัวพิมพ์ใหญ่ ไม่เหมาะกับผู้อ่าน)
REGION_LABELS = {
    Region.ACTIVE: "Forward Active",
    Region.CUTOFF: "Cutoff",
    Region.SATURATION: "Saturation",
}


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        return render_template(
            "index.html", values=DEFAULTS, errors={}, result=None, region_label=None
        )

    values = request.form.to_dict()
    try:
        result = solve(parse_form(values))
    except ValidationError as exc:
        # 400 = คำขอไม่ถูกต้อง และคงค่าที่กรอกไว้ให้ผู้ใช้แก้
        return (
            render_template(
                "index.html", values=values, errors=exc.errors, result=None, region_label=None
            ),
            400,
        )

    return render_template(
        "index.html",
        values=values,
        errors={},
        result=result,
        region_label=REGION_LABELS[result.region],
    )
