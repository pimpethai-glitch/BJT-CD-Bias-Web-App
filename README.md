# BJT CE Amplifier Simulator — ENG29 2121 Lab 04

Flask web app ที่ต่อยอดจาก Lab 03 โดย **คง DC Bias แบบประมาณ 3 โหมดไว้ครบ**
(Fixed / Emitter / Voltage Divider) และเพิ่มจำลองจริงด้วย **ngspice** สำหรับ
**CE Voltage Divider Reference หนึ่งวงจร** (DC `.op`, AC `.ac`, Transient `.tran`)
พร้อมกราฟ SVG ที่ให้บริการจาก server ไม่มี JavaScript ในหน้าเว็บ

## ขอบเขต

- **Lab 03 เดิมยังใช้ได้เหมือนเดิม:** เลือกโหมดด้วย `divider` / `fixed` / `emitter`
  แล้วกด “เปลี่ยนโหมด / โหลดฟอร์มใหม่” เพื่อสลับช่องที่ใช้ คำนวณ `VB, VE, VC,
  VCE, IC, IE, IB` (Divider มี `VTH, RTH`) ด้วย forward-active approximation
- **Lab 04 เพิ่ม:** เลือก Analysis `dc` / `ac` / `transient` แล้วกด
  “Run Simulation” → `spice_engine.py` สร้าง netlist, เรียก ngspice จริง,
  อ่านผลกลับมาแล้วแสดง พร้อม Engine / Model / Run Status / Data points / log /
  netlist ที่ใช้รันจริง
- ผล **Analytical** และผล **SPICE** แสดงในคนละ panel และมีป้ายบอกที่มาชัดเจน
- ฟอร์ม SPICE รับ `VCC [V]`, `R1/R2/RC/RE/RL [kΩ]`, `Cin/Cout [µF]`,
  `Vin amplitude [mV peak]`, `Frequency [kHz]`; ตรวจค่าก่อนสร้าง netlist
  (ความถี่ 0.01–10000 kHz, amplitude ≤ VCC ในหน่วย mV)
- กราฟ Gain [dB] และ Phase [deg] ถูกแยกเป็นคนละ SVG (คนละแกน Y) และ waveform
  ถูกวาดจากจุดข้อมูลที่อ่านจากไฟล์ผล ngspice เท่านั้น
  ถ้าไม่มีผลหรือรันผิดจะแสดง Error state ไม่โชว์กราฟ/ตัวเลขเก่า
- UI ใช้ fieldset/legend แยกกลุ่มช่องกรอก, มี error summary + `aria-invalid`/`aria-describedby`,
  แถบ `Run Status · Engine · points` และปรับขนาดตัวอักษร SVG ให้ยืดหยุ่นตาม viewport
  (1280 px / 390 px) โดยไม่เปลี่ยนข้อมูลหรือหน่วย

## โครงสร้างโปรเจกต์

```text
.
├── app.py                 # Flask route: dispatch Analytical / SPICE, ไม่มีสูตรฟิสิกส์
├── dc_bias.py             # Lab 03: parse_form(), solve_mode(), solve_*() — ไม่รู้จัก Flask
├── spice_engine.py        # Lab 04: validate → netlist → subprocess → parse → สรุปผล
├── plots.py               # แปลงจุดข้อมูลจริงเป็น SVG (ไม่สร้างข้อมูลเอง)
├── templates/index.html   # ฟอร์ม + ผล + กราฟ (Jinja, ไม่มี JavaScript)
├── static/style.css       # styling, responsive
├── static/mobile-view.html# ตัวอย่าง iframe 390 px สำหรับตรวจ B8 ผ่าน HTTP
├── tests/
│   ├── test_dc_bias.py    # สมการ/validation/region ของ Lab 03
│   ├── test_web.py        # HTTP ของทั้งสองเส้นทาง
│   ├── test_spice_engine.py # netlist, parser, error handling, ngspice จริง
│   └── test_plots.py      # กราฟไม่สร้างข้อมูลขึ้นมาเอง
├── tools/ngspice/...      # ngspice-47 (Windows 64-bit) สำหรับรันซ้ำในเครื่องนี้
├── requirements.txt       # Flask>=3.1,<4 (ไม่มี dependency อื่น)
├── AGENTS.md
└── docs/
    ├── design-note.md
    ├── validation.md      # A1–A5 + B1–B8 พร้อมหลักฐาน
    ├── reflection.md
    └── screenshots/       # Desktop/Mobile screenshot จาก Browser จริง
```

## การติดตั้งและรัน

```powershell
cd BJT-CD-Bias-Web-App-main
py -m pip install -r requirements.txt
py -m flask --app app run --debug
```

เปิด <http://127.0.0.1:5000/>

> ต้องรันผ่าน Flask server เพราะ `templates/index.html` เป็น Jinja template
> การดับเบิลคลิกเปิดด้วย `file://` จะเห็น `{{ ... }}` และไม่มีใครคำนวณ/รัน ngspice
> (`py app.py` ไม่ได้เปิด server เพราะไฟล์ไม่มี `app.run()`; ใช้ Flask CLI ตามด้านบน)

### ngspice

โปรแกรมจำลองเป็น **external binary ไม่ใช่ pip package** adapter หา executable ตามลำดับ:

1. `NGSPICE_PATH` (ถ้าตั้ง)
2. `ngspice` / `ngspice_con` ใน `PATH`
3. `tools\ngspice\Spice64\bin\ngspice_con.exe` (แนบมากับโปรเจกต์; ตรวจแล้วว่าเป็น `ngspice-47`)
4. `tools\ngspice\Spice64\bin\ngspice.exe`

ตัวอย่างตั้งค่าเอง:

```powershell
$env:NGSPICE_PATH = "C:\path\to\ngspice_con.exe"
```

การเรียกใช้จริงคือ `subprocess.run([exe, "-b", "circuit.cir"], shell=False,
timeout=20)` ใน temporary directory แยกต่อรอบ ตรวจ exit code, ข้อความ `Error:`
ที่พิมพ์แล้ว exit 0, ไฟล์ผลว่าง/เสีย และ OSError/Timeout ก่อนแปลเป็น Success

## การทดสอบ

```powershell
py -m unittest discover -s tests -v
```

ผลที่รันจริงในเครื่องนี้: **72 tests, OK**

## ค่าอ้างอิง

### Lab 03 (analytical)

ใช้ร่วมกัน `VCC = 12 V, RC = 2.2 kΩ, β = 100, VBE = 0.70 V`
`RB` ในฟอร์มเป็น **MΩ**, `R1/R2/RC/RE` เป็น **kΩ**

| กรณี | อินพุตเพิ่ม | IC | VCE |
| --- | --- | --- | --- |
| Divider (A1) | `R1=100, R2=22, RE=1` kΩ | 1.2299 mA | 8.0522 V |
| Fixed (A2) | `RB=1` MΩ | 1.1300 mA | 9.5140 V |
| Emitter (A3) | `RB=1` MΩ, `RE=1` kΩ | 1.0263 mA | 8.7054 V |
| Emitter (A4) | `RB=1` MΩ, `RE=2` kΩ | 0.9401 mA | 8.0328 V |

### Lab 04 (ngspice-47, ค่าเริ่มต้น)

`VCC=12 V`, `R1=100 kΩ`, `R2=22 kΩ`, `RC=2.2 kΩ`, `RE=1 kΩ`, `RL=10 kΩ`,
`Cin=Cout=10 µF`, `Vin=10 mV peak`, `f=1 kHz`, ไม่มี bypass capacitor

| Analysis | ผลที่อ่านจริง |
| --- | --- |
| DC `.op` | `VB 1.949 V`, `VE 1.289 V`, `VC 9.189 V`, `VCE 7.900 V`, `IC 1.278 mA`, `IB 11.913 µA`, `IE 1.289 mA` (7 จุด) |
| AC `.ac` | Gain สูงสุด `4.86 dB`, phase `180.0°`, `fL ≈ 1.82 Hz`, `fH ≈ 2.08e+08 Hz` (181 จุด, 1 Hz–1 GHz, 20 points/decade) |
| Transient `.tran` | `Vin peak 10.00 mV`, `Vout peak 17.49 mV`, กลับเฟส ~180° (508 จุด, 5 periods, step = period/100) |

ผล DC ของสองวิธีต่างกันเล็กน้อยตามสมมติฐาน: analytical ใช้ β=100 คงที่และ
VBE=0.70 V คงที่ ส่วน ngspice ใช้ model ด้านล่างกับจุดทำงานจริง จึงไม่ควรนำ
ค่าจาก panel ใดไปแทนที่อีก panel โดยไม่บอกที่มา

## BJT model ที่ใช้

ไม่มี model จากอาจารย์ใน workspace จึงใช้ model ที่ระบุชัดใน netlist และแสดงบนหน้าเว็บ:

```spice
.model QNPN NPN(IS=1E-14 BF=100 VAF=100 CJE=4P CJC=3P TF=0.3N)
```

`vp()` ถูกบังคับเป็นองศาด้วย `set units=degrees`; `wrdata` ใช้
`set wr_singlescale` + `set wr_vecnames` เพื่อให้ column แรกเป็น frequency/time
แล้วตามด้วยข้อมูลจริง (ไม่อนุญาตให้ parser เดาคู่ real/imag)

## ข้อจำกัดและสิ่งที่ยังไม่ได้ทำ

- จำลองได้เฉพาะ CE Voltage Divider อ้างอิงเดียว — ไม่มี editor ลากวงจร, ไม่มี
  AC ของ Fixed/Emitter, ไม่มี FET และไม่มี emitter bypass capacitor
- AC sweep ถูกกำหนด 1 Hz–1 GHz; ค่า `fL/fH` ที่แสดงเป็นผลจาก sweep/model นี้
  ไม่ควรตีความเป็น bandwidth ออกแบบจริงของวงจรที่ต่อ bypass
- Transient ใช้สัญญาณ sine จาก amplitude/frequency ที่กรอก; AC ใช้ค่า `AC`
  ของ source (amplitude เดียวกัน) แต่ความถี่ถูกสแกนโดย `.ac` ไม่ใช่ค่าที่กรอก
- ไม่มี JavaScript; เปลี่ยนโหมด/analysis ต้องกดปุ่มแยก (server-rendered ใหม่)
- **git ไม่พร้อมใช้งาน** และไม่มี repo URL ใน workspace นี้ จึงไม่มี commit SHA,
  การ push หรือประวัติแก้ไข; ไฟล์ทั้งหมดเป็นการแก้ใน machinery ที่มีอยู่
- **Playwright MCP และ Impeccable skill ไม่ได้ติดตั้งในรอบนี้** การตรวจ B1–B8
  ใช้ OpenCode Browser จริงและปรับ CSS ด้วยตนเอง; ดู `docs/validation.md`
  สำหรับสถานะ NOT RUN ที่เกี่ยวข้อง
- รัน frequency-only (`1 → 2 kHz` โดย amplitude คงเดิม) และกรณี engine ไม่พร้อม
  ผ่าน Browser แล้ว; ดู `docs/validation.md` ข้อ 13
- ผลทดสอบ Browser บันทึกใน `docs/validation.md` และ screenshot ใน
  `docs/screenshots/` (`desktop-ac.png`, `desktop-b8.png`,
  `desktop-transient-freq2k.png`, `engine-missing.png`, `mobile-ac-split.png`,
  mobile emulation 390 px ผ่าน `static/mobile-view.html` — ไม่ใช่อุปกรณ์จริง)

## บันทึก AI / การตรวจของนักศึกษา

- AI ปรับ `app.py`, เพิ่ม `spice_engine.py` + `plots.py`, แก้ UI/CSS, เขียน test
  และเอกสารนี้จากโครง Lab 03 เดิม
- AI รัน ngspice-47 จริงและบันทึกผล/netlist/log กับค่าที่อ่านจาก Browser ไว้แล้ว
- สิ่งที่ควรตรวจเองก่อนส่ง: หน่วยในฟอร์ม, ความสอดคล้องของ model กับใบงาน,
  ความแตกต่าง analytical/SPICE, และว่าสภาพแวดล้อมของ TA มี ngspice path เดียวกัน
- ไม่มีการบันทึกว่านักศึกษาได้ตรวจหรืออนุมัติการเปลี่ยนแปลงใน workspace นี้
