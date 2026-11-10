# BJT DC Bias Web App — ENG29 2121 Lab 02

Flask web application สำหรับคำนวณ **DC operating point** ของวงจรขยาย BJT
NPN Common-Emitter แบบ **Voltage-Divider Bias** ด้วย forward-active approximation
ผลลัพธ์คำนวณด้วย Python ทั้งหมด (ไม่ใช่ค่าที่ฝังใน HTML)

## ขอบเขต

- รับค่า `VCC, R1, R2, RC, RE, β, VBE`
- คำนวณ `VB, VE, VC, VCE, IC` พร้อม `IB, IE, VTH, RTH`
- ตรวจข้อมูลผิด (ค่าติดลบ/ศูนย์, ไม่ใช่ตัวเลข, ช่องว่าง) และแสดง error รายฟิลด์
- แจ้ง warning เมื่ออยู่นอกช่วง forward-active (cutoff / saturation)
- **ไม่มี** AC, transient, Bode plot, SPICE หรือ bias ชนิดอื่นในเวอร์ชันนี้

## โครงสร้างโปรเจกต์

```text
.
├── app.py                # Flask: HTTP routes + เลือก template
├── dc_bias.py            # ชั้นวิศวกรรม: parse_form(), solve() — ไม่รู้จัก Flask
├── templates/index.html  # ฟอร์ม + ตารางผล (Jinja)
├── static/style.css      # การจัดหน้า
├── tests/
│   ├── test_dc_bias.py   # สมการ, validation, region
│   └── test_web.py       # HTTP: GET /, POST / (สำเร็จ และ 400)
├── requirements.txt      # Flask>=3.1,<4
├── AGENTS.md             # กติกาสำหรับ AI agent ใน repo นี้
└── docs/
    ├── design-note.md    # เหตุผลการออกแบบ
    ├── validation.md     # เทียบค่าคำนวณมือกับผลจากเว็บ
    └── reflection.md     # คำถามท้าย Lab พร้อมคำตอบ
```

## การติดตั้งและรัน

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m flask --app app run --debug
```

จากนั้นเปิด <http://127.0.0.1:5000/>

> ต้องรันผ่าน Flask server เท่านั้น การดับเบิลคลิกเปิด `templates/index.html`
> ด้วย `file://` จะไม่ทำงาน เพราะ template ต้องให้ Python เติมค่าและคำนวณก่อน

## การทดสอบ

```powershell
python -m unittest discover -s tests -v
```

ผลที่ต้องได้: **22 tests, OK**

## ค่าอ้างอิง

`VCC=12 V, R1=100 kΩ, R2=22 kΩ, RC=2.2 kΩ, RE=1 kΩ, β=100, VBE=0.70 V`

| ปริมาณ | ค่า |
| --- | --- |
| VTH | 2.1639 V |
| RTH | 18.033 kΩ |
| IB | 12.30 µA |
| IC | 1.2299 mA |
| IE | 1.2422 mA |
| VE | 1.2422 V |
| VB | 1.9422 V |
| VC | 9.2943 V |
| VCE | 8.052 V (forward active) |

## ข้อจำกัด

แบบจำลองนี้ใช้ β คงที่และ VBE คงที่ ไม่ใช่ ngspice ผลที่อยู่นอกช่วง forward-active
(cutoff เมื่อ `VTH ≤ VBE`, saturation เมื่อ `VCE ≤ 0.3 V`) จะแสดง warning และ
ไม่ควรนำไปใช้เป็นคำตอบที่แม่นยำ ดูรายละเอียดใน `docs/validation.md`
