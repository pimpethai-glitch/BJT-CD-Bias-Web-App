# Reflection — Lab 02

คำถามรายบุคคลท้าย handout พร้อมคำตอบจากงานที่สร้างจริงใน repo นี้

## 1. ทำไมการเปิด `templates/index.html` ตรง ๆ จึงไม่เท่ากับการรัน Flask

เพราะไฟล์ `.html` ในโปรเจกต์นี้เป็น **Jinja template** ไม่ใช่หน้าเว็บสำเร็จรูป
ข้างในมี `{{ values.vcc }}`, `{{ "%.3f"|format(result.vb) }}` และ
`{% if errors.vcc %}` ซึ่งเป็นคำสั่งให้ template engine เติมค่า
ถ้าเปิดด้วย `file://` จะเห็น `{{ ... }}` เป็นข้อความดิบ และ **ไม่มีใครคำนวณ**
เพราะสมการอยู่ใน `dc_bias.py` ซึ่งเป็นโปรแกรม Python ที่ต้องรันบน server
การเปิดผ่าน `http://127.0.0.1:5000/` เท่านั้นที่ทำให้ browser ส่ง HTTP request
ไปถึง Flask แล้วได้ HTML ที่เติมค่าครบแล้วกลับมา

## 2. ฟอร์มส่งข้อมูลไปยัง Python อย่างไร

`<form method="post" action="/">` รวบ `name` ของ input ทั้ง 7 ช่อง
(`vcc`, `r1`, … , `vbe`) เป็น `application/x-www-form-urlencoded`
แล้ว browser ส่งเป็น HTTP POST ไปที่ path `/`
Flask รับไว้ใน `request.form` → `app.py` ส่งต่อให้ `parse_form()` แปลงเป็น
`BiasInput` → `solve()` คำนวณ → template เดิมถูก render ใหม่พร้อมผลลัพธ์

จุดสำคัญ: ค่าที่ส่งมาถึง server เป็น **ข้อความ** ทั้งหมด การแปลงเป็นตัวเลข
และการตรวจความถูกต้องจึงต้องเกิดฝั่ง Python (ไม่ใช่เชื่อ browser)

## 3. แก้สมการใน `dc_bias.py` แล้วต้องแก้ HTML หรือไม่

โดยปกติ **ไม่ต้อง** เพราะ HTML แสดงผลจาก `BiasResult` ผ่านชื่อฟิลด์
ถ้าแก้แค่สูตรภายใน `solve()` (เช่น เปลี่ยนวิธีคำนวณ IB) หน้าเว็บจะแสดงค่าใหม่ทันที
โดยไม่ต้องแตะ template

ต้องแก้ template เฉพาะเมื่อ **เพิ่ม/ลบฟิลด์ของผลลัพธ์** (เช่น เพิ่ม `VBC`)
หรือเปลี่ยนหน่วย/จำนวนตำแหน่งทศนิยมที่แสดง และต้องแก้ `tests/` ด้วยเสมอ
เพราะเทสต์ผูกกับค่าตัวเลขที่คาดหวัง

## 4. ทำไมผลใน region ที่แบบจำลองใช้ไม่ได้จึงต้องมี warning

เพราะสมการที่ใช้ (forward-active) **ตั้งสมมติฐานว่ารอยต่อ base-emitter
forward bias และรอยต่อ collector-base reverse bias** เมื่อวงจรอยู่ใน cutoff
หรือ saturation สมมติฐานนี้ไม่จริงอีกต่อไป — ตัวเลขที่คำนวณได้จึงไม่ใช่
คำตอบของวงจรจริง เช่นใน saturation กระแส collector จะถูกจำกัดด้วย RC
ไม่ใช่ด้วย β·IB

ถ้าไม่แจ้ง warning ผู้ใช้จะเข้าใจผิดว่าค่าที่เห็นคือคำตอบที่แม่นยำ
warning จึงเป็นส่วนหนึ่งของความซื่อสัตย์ของเครื่องมือวัด/จำลอง: บอกทั้งค่า
และบอกว่าเมื่อไรค่าเหล่านั้นใช้ไม่ได้

## 5. MCP เชื่อม OpenCode กับเบราว์เซอร์อย่างไร (Lab 03)

MCP (Model Context Protocol) คือมาตรฐานที่ให้แอป AI รู้ว่าเครื่องมืออะไรพร้อมใช้ เรียก
เครื่องมือนั้น และรับผลกลับมา ใน Lab 03 **OpenCode เป็น MCP Client** ส่วน **Playwright MCP
เป็น MCP Server** ที่เปิดเครื่องมือควบคุมเบราว์เซอร์ เมื่อเอเจนต์เรียก tool เช่น
`browser_navigate` คำสั่งจะไปหา MCP Server → Server ควบคุม Browser → Browser ส่ง HTTP
ไป Flask → Flask คืน HTML → Browser ส่ง snapshot กลับมาให้เอเจนต์อ่าน

รอบนี้เครื่องไม่ได้ตั้งค่า Playwright MCP จึงใช้ **OpenCode Browser Tool** ที่มีอยู่แล้ว
วิธีตรวจจึงถูกบันทึกว่า `OpenCode Browser` ใน `docs/validation.md` ไม่ได้ใช้ `curl`
หรืออ่านโค้ดแทนการรันหน้าเว็บ

## 6. ค่า `RE` ใน A4 เดินทางถึงสมการอย่างไร

ในหน้าเว็บ Emitter มี `<input id="re" name="re">` เมื่อกดคำนวณ Browser ส่งฟอร์ม
แบบ `POST /` พร้อม `mode=emitter`, `rb=1` (หน่วย MΩ) และ `re=2` (หน่วย kΩ) `app.py` อ่าน
`request.form.to_dict()` → `parse_form(values, "emitter")` แปลงสตริงเป็น float และ
ตรวจว่า `RB, RE > 0` → `solve_mode("emitter", data)` เรียก `solve_emitter()` →
ภายในแปลง `rb = data.rb * 1_000_000.0` และ `re = data.re * 1000.0` เป็น Ω แล้วใช้ในตัวหาร
`RB + (β + 1)RE` → ค่า `IB` ลดลง → `IC = β·IB` ลดลงจาก 1.026 mA เป็น 0.940 mA
ผลที่เห็นจึงเปลี่ยนตามที่ทำนาย ไม่ใช่ค่าคงที่ใน HTML
