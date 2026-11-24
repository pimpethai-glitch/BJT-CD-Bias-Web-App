# Design Note — BJT DC Bias Web App (Lab 03)

เอกสารนี้อธิบายเหตุผลเบื้องหลังการออกแบบ Lab 02 และการต่อยอดใน Lab 03

## ทำไมแยก `dc_bias.py` ออกจาก `app.py`

`dc_bias.py` ไม่ import Flask และไม่รู้จัก HTTP/HTML เลย ทำให้

- ทดสอบสมการได้ตรง ๆ ด้วย `unittest` โดยไม่ต้องเปิด web server
- นำไปใช้ซ้ำได้ (เช่น CLI หรือ notebook) โดยไม่ต้องแก้โค้ดเว็บ
- เมื่ออาจารย์ตรวจงาน เห็นได้ชัดว่าผลลัพธ์มาจาก Python ไม่ใช่ค่าที่ฝังใน HTML

`app.py` จึงเหลือหน้าที่เพียง: รับ request → ตรวจโหมด → เรียก `parse_form(values, mode)`/
`solve_mode(mode, data)` → เลือก template และ HTTP status

## ทำไมเลือกฟังก์ชันด้วย `if/elif` ใน `app.py`

Lab 03 ใส่ฟังก์ชัน `solve_fixed()`, `solve_emitter()` และ `solve_divider()` แยกกันใน
`dc_bias.py` ส่วน `app.py` เป็นที่เดียวที่เลือกว่าจะเรียกตัวไหนตามค่าที่ส่งมาจากฟอร์ม
โหมดที่ไม่รู้จักจะถูกปฏิเสธด้วย HTTP 400 ไม่มีการตกไปใช้ Divider โดยอัตโนมัติ
`parse_form()` ยังตรวจเฉพาะฟิลด์ที่โหมดนั้นใช้ จึงไม่บังคับให้กรอก R1/R2 ในโหมด Fixed

## ทำไมเปลี่ยนโหมดต้องกดปุ่มแยก

ตามข้อกำหนด "ไม่มี JavaScript" การเปลี่ยน `<select>` จึงยังไม่เปลี่ยนช่องในฟอร์ม
ผู้ใช้กด **“เปลี่ยนโหมด / โหลดฟอร์มใหม่”** เพื่อส่ง `action=change` ให้ Flask render
ฟอร์มของโหมดนั้นใหม่ ผลที่แสดงจึงไม่ถูกสับสนกับรอบก่อน และเมื่อ input ผิด
`result=None` เสมอ จึงไม่มีโอกาสโชว์ค่เก่าเป็นผลของรอบใหม่

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

- **Cutoff** (`VTH ≤ VBE` ใน Divider หรือ `IB ≤ 0`): กระแสทุกตัวเป็นศูนย์ → แจ้ง warning
- **Saturation** (`VCE ≤ 0.2 V` ตามใบงาน Lab 03): สมการ forward-active ใช้ไม่ได้ →
  แจ้ง warning และไม่ควรนำค่าที่แสดงไปใช้

## การแปลงหน่วย

ผู้ใช้กรอก R1/R2/RC/RE เป็น kΩ ส่วน RB เป็น MΩ (ค่า `1` หมายถึง 1 MΩ) แต่ `BiasResult`
คืนค่าเป็น SI ทั้งหมด การแปลงเกิดในฟังก์ชัน `solve_*()` ใน `dc_bias.py` เท่านั้น
(คูณ 1000 สำหรับ kΩ และคูณ 1,000,000 สำหรับ MΩ) ไม่มีจุดอื่นที่ต้องจำหน่วย

---

# Lab 04 — ส่วนต่อขยาย

## ทำไมไม่แตะ `dc_bias.py` และเส้นทาง Lab 03

Lab 04 ต้องการความต่อเนื่อง: ผล A1–A5 ต้องยังตรงกับเดิมทุกประการ
จึงคง `solve()` / `solve_mode()` ไว้เหมือนเดิม แล้วเพิ่มเส้นทางใหม่ใน `app.py`
โดยดูจาก hidden field `form=spice` ถ้าไม่ใช่ SPICE จะไปทาง analytical เหมือนเดิม
การแยกนี้ทำให้ regression ไม่เสียและตอบคำถาม "ผลนี้มาจากสมการหรือจาก ngspice" ได้ชัด

## ทำไมแยก `spice_engine.py` ออกจาก `app.py` และ `dc_bias.py`

`dc_bias.py` มีหน้าที่คำนวณสมการประมาณอย่างเดียว ไม่ควรรู้จัก subprocess
ส่วน `app.py` ก็ไม่ควรสร้าง netlist หรือแปลง stdout ของ solver
จึง thêm adapter หนึ่งไฟล์ที่รับเฉพาะค่าที่ตรวจแล้ว (float ในหน่วย SI) แล้ว:

1. สร้าง netlist จากตัวเลขเท่านั้น (ไม่มีข้อความจากผู้ใช้ต่อเข้าไปตรง ๆ)
2. เรียก ngspice ด้วย `subprocess.run(..., shell=False, timeout=20)` ใน temp dir ใหม่
3. ตรวจ exit code / `Error:` / ไฟล์ผล / จำนวน column / ค่าตัวเลข
4. คืน `SimulationResult` ที่มี engine, model, netlist และ log มาด้วย

ถ้า solver พัง จะ raise `SpiceRunError` → Flask ตอบ HTTP 400 + error state
ไม่มีทางที่ `sim_result` เก่าจะถูกส่งกลับมาแสดงเป็นผลรอบใหม่

## ทำไมกราฟอยู่ใน `plots.py` แยกอีกชั้น

`plots.py` ได้เฉพาะ `AcPoint` / `TimePoint` จาก parser และแปลงเป็น SVG
ไม่มีสมการฟิสิกส์ และไม่สร้างจุดขึ้นมาเอง ถ้าผลว่างจะแสดงข้อความแทน
การแยกนี้ทำให้ทดสอบได้ว่า "กราฟมาจากข้อมูลจริง" โดยไม่ต้องพึ่ง screenshot

## ทำไมต้อง `set wr_singlescale` / `set wr_vecnames` / `set units=degrees`

- `wrdata` แบบเริ่มต้นเขียน scale ซ้ำในทุกคู่ของเวกเตอร์ ทำให้ parser อ่าน
  frequency/time เป็น Vin/Vout ได้ (เคยเห็น `gain −200 dB` และเฟสกลับหัว)
- `set wr_singlescale` ทำให้ column แรกเป็น scale และตามด้วยข้อมูลจริงทีละ column
- `set wr_vecnames` เขียนหัวตารางชื่อเวกเตอร์ ซึ่ง parser ข้ามด้วยการลอง `float()`
- `vp()` ของ ngspice ออกเป็น radian ตามค่าเริ่มต้น `set units=degrees`
  ทำให้ phase ที่แสดงเป็นองศาตรงกับแกนกราฟ

## ทำไมต้องระบุ model เอง

ไม่มี `.model` จากไฟล์เริ่มต้นของอาจารย์ใน workspace นี้ จึงใช้
`QNPN (IS=1E-14 BF=100 VAF=100 CJE=4P CJC=3P TF=0.3N)` แบบที่ระบุชัดใน netlist
และโชว์บนหน้า results ทุกครั้ง ผล DC จึงต่างจาก analytical เล็กน้อยตามธรรมชาติ
(detail และตัวเลขเปรียบเทียบอยู่ใน `validation.md` ข้อ 7)

## ทำไม UI ยังไม่มี JavaScript

การเปลี่ยน analysis ยังใช้ปุ่ม “โหลดฟอร์มตาม Analysis” ส่ง `action=change`
ให้ server render ฟอร์มใหม่ เหมือน Lab 03; กราฟก็เป็น SVG ที่ server สร้าง
จึงไม่มี state ฝั่ง client ที่ต้อง synchronize กับผลจาก ngspice

## ทำไมต้องแยกกราฟ Gain และ Phase

Gain [dB] และ Phase [deg] มีหน่วยและช่วงค่าคนละแบบ (gain ประมาณ −3…5 dB,
phase +180…−180°) การวางทั้งสองเส้นใน SVG เดียวกันแม้มีแกนขวาแยกก็ยังอ่านยาก
จึงเปลี่ยนเป็น `gain_svg()` กับ `phase_svg()` คนละ `<figure>` / คนละแกน Y
โดยใช้จุด `AcPoint` ชุดเดิมที่อ่านจาก ngspice เหมือนเดิม ไม่มีสูตรฟิสิกส์เพิ่ม
และไม่แตะข้อมูลจาก ngspice (`bode_svg()` เดิมยังอยู่เพื่อความเข้ากันได้ของ test เก่า)

## ทำไม UI polish ยังอยู่ในชั้นนำเสนอ

หลัง audit ตอน 1280 px และ 390 px ได้เพิ่ม `fieldset/legend`, error summary พร้อม
`aria-*`, แถบ `Run Status · Engine · points` และขยายความกว้างการ์ด/ขนาดตัวอักษร SVG
เพื่อให้กราฟอ่านได้จริง สิ่งที่เปลี่ยนมีเพียง `templates/index.html`, `static/style.css`
และค่าตำแหน่ง legend/margin ใน `plots.py` — ไม่มีสูตร หน่วย หรือจุดข้อมูลใหม่
จุดกราฟยังมาจากผล ngspice ทุกจุดและ error ยังซ่อนผลเก่าอย่างเดิม
รายละเอียดการวัดอยู่ใน `validation.md` ข้อ 16

