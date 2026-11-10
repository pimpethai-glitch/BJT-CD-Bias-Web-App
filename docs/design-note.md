# Design Note — BJT DC Bias Web App

เอกสารนี้อธิบายเหตุผลเบื้องหลังการออกแบบ (design ฉบับเต็มอยู่ที่
`docs/superpowers/specs/2026-11-10-bjt-dc-bias-webapp-design.md`)

## ทำไมแยก `dc_bias.py` ออกจาก `app.py`

`dc_bias.py` ไม่ import Flask และไม่รู้จัก HTTP/HTML เลย ทำให้

- ทดสอบสมการได้ตรง ๆ ด้วย `unittest` โดยไม่ต้องเปิด web server
- นำไปใช้ซ้ำได้ (เช่น CLI หรือ notebook) โดยไม่ต้องแก้โค้ดเว็บ
- เมื่ออาจารย์ตรวจงาน เห็นได้ชัดว่าผลลัพธ์มาจาก Python ไม่ใช่ค่าที่ฝังใน HTML

`app.py` จึงเหลือหน้าที่เพียง: รับ request → เรียก `parse_form()`/`solve()` →
เลือก template และ HTTP status

## ทำไมใช้ server-rendered form (ไม่มี JavaScript)

ฟอร์มส่งข้อมูลด้วย `POST` ธรรมดา แล้ว server ตอบ HTML กลับมาทั้งหน้า

- ตรงกับเกณฑ์ตรวจรับ A2: ผลลัพธ์ "แสดงใน HTML" ที่ server สร้าง
- ไม่มี state ฝั่ง client จึงทดสอบด้วย Flask test client ได้ตรงไปตรงมา
- นักศึกษาเห็นเส้นทางข้อมูลครบ: form → HTTP request → Python → template
- ข้อเสียที่ยอมรับ: กด refresh หลัง POST จะส่งข้อมูลซ้ำ (ยอมรับได้ในขอบเขต lab)

## ทำไมเลือกใช้ 400 เมื่อ input ผิด

`POST /` ที่ข้อมูลไม่ผ่าน validation ตอบ HTTP 400 พร้อมฟอร์มที่คงค่าเดิมไว้
เพื่อให้เห็นชัดว่าคำขอไม่ถูกต้อง (ไม่ใช่ 200 ที่ดูเหมือนสำเร็จ) และทดสอบได้ด้วย
`assertEqual(response.status_code, 400)`

## ข้อจำกัดของแบบจำลอง

ใช้ forward-active approximation: β คงที่, VBE คงที่, ไม่มี Early effect,
ไม่มีความต้านทาน base ที่ขึ้นกับกระแส และไม่ใช่ SPICE

- **Cutoff** (`VTH ≤ VBE`): กระแสทุกตัวเป็นศูนย์ → แจ้ง warning
- **Saturation** (`VCE ≤ 0.3 V`): สมการ forward-active ใช้ไม่ได้ → แจ้ง warning
  และไม่ควรนำค่าที่แสดงไปใช้

## การแปลงหน่วย

ผู้ใช้กรอกตัวต้านทานเป็น kΩ (หน่วยที่ใช้จริงบนแผ่นวงจร) แต่ `BiasResult` คืนค่า
เป็น SI ทั้งหมด การแปลงเกิดที่ `solve()` เพียงจุดเดียว จึงไม่มีจุดที่ลืมคูณ 1000
