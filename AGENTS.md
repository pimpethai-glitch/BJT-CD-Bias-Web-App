# AGENTS.md — กติกาสำหรับ AI agent ใน repo นี้

repo นี้เป็นตัวอย่างการสอนของ ENG29 2121 Lab 02 (BJT DC Bias Web App)

1. **ห้ามใส่สูตรฟิสิกส์ใน `templates/` หรือ `app.py`** — การคำนวณทั้งหมดอยู่ใน
   `dc_bias.py` เท่านั้น ถ้าต้องเปลี่ยนสมการ ให้แก้ที่ `dc_bias.py`
2. **การคำนวณใหม่ทุกครั้งต้องมี test** ใน `tests/test_dc_bias.py` ที่เขียนก่อน
   และเคยเห็นมัน fail ก่อนแก้โค้ด
3. **dependency เพิ่มได้เฉพาะ Flask** ตามที่ระบุใน `requirements.txt`
   (ทดสอบด้วย `unittest` ของ standard library ไม่ใช้ pytest)
4. **UI เป็นภาษาไทย หน่วย SI หน้าเดียว ไม่มี JavaScript** — ค่าที่แสดงต้องมาจาก
   `BiasResult` ไม่ใช่ค่าคงที่ในเทมเพลต
5. **ก่อนบอกว่างานเสร็จ** ต้องรัน `python -m unittest discover -s tests -v`
   แล้วรายงานผลจริง ไม่ใช่คาดเดา

## ข้อจำกัดของแบบจำลอง

`dc_bias.py` ใช้ forward-active approximation (β คงที่, VBE คงที่) ไม่ใช่ SPICE
ผลที่ออกนอกช่วง forward-active ต้องมี warning เสมอ ห้ามนำเสนอเป็นค่าที่เชื่อถือได้
