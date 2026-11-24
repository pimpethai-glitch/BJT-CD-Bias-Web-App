# Validation — Lab 03 + Lab 04

เอกสารนี้รวม (1) ค่าอ้างอิงที่คำนวณอิสระจากสมการและผลที่อ่านจริงจากหน้าเว็บ
ตามตาราง A1–A5 ของ Lab 03 และ (2) ผลตรวจ B1–B8 ของ Lab 04 จาก Flask + ngspice จริง

**วิธีตรวจที่ใช้จริง:** OpenCode Browser (`tabs.open`, `snapshot`, `select`, `fill`,
`press`, `evaluate`, `wait`, `screenshot`) + การรัน `ngspice_con.exe` จริงจาก adapter
**ไม่ได้ใช้ Playwright MCP ในรอบนี้** และไม่ใช้ `curl`/การอ่านโค้ดเป็นหลักฐานผล
(ดูสถานะ NOT RUN ในข้อ 10) เกณฑ์ Lab 03: |ΔIC| ≤ 0.01 mA และ |ΔVCE| ≤ 0.02 V

---

## 1. ค่าอ้างอิงอิสระ (Lab 03)

ใช้ร่วมกัน: `VCC = 12 V, RC = 2.2 kΩ, β = 100, VBE = 0.70 V`
สัญญาณเตือนเมื่อ `IB ≤ 0` หรือ `VCE ≤ 0.2 V` ตามใบงาน
**หน่วย RB ในฟอร์มคือ MΩ** ดังนั้นค่าที่กรอก `1` หมายถึง 1,000,000 Ω
(`solve_fixed()` / `solve_emitter()` คูณ 1e6) ส่วน RC/RE/R1/R2 ยังเป็น kΩ เหมือนเดิม

| กรณี | สมการที่ใช้ | ค่าคำนวณมือ |
| --- | --- | --- |
| A1 Divider | `VTH = 12·22/(100+22) = 2.1639 V`, `RTH = 18.0328 kΩ`, `IB = (2.1639−0.70)/(18032.8+101·1000)` | IC = 1.2299 mA, VCE = 8.0522 V |
| A2 Fixed | `IB = (12−0.70)/1,000,000 = 11.3 µA`, `IC = 100·IB`, `VCE = 12 − IC·2.2 kΩ` | IC = 1.1300 mA, VCE = 9.5140 V |
| A3 Emitter | `IB = 11.3/[1,000,000 + 101·1000]` | IC = 1.0263 mA, VCE = 8.7054 V |
| A4 Emitter | `IB = 11.3/[1,000,000 + 101·2000]` | IC = 0.9401 mA, VCE = 8.0328 V |

A4 ทำนายล่วงหน้า: เมื่อ `RE` เพิ่มจาก 1 → 2 kΩ ตัวหาร `RB+(β+1)RE` เพิ่มขึ้น
`IB` จึงลดลง และ `IC` ลดลงจาก A3 (ผลลัพธ์จริงเป็นไปตามที่ทำนาย)

## 2. ตาราง A1–A5 (ผลที่เห็นจริงจาก Browser)

| กรณี | เลือกโหมดและกรอกค่า | คาดหมายก่อนรัน | เห็นจริง (พร้อมหน่วย) | วิธีตรวจ | สถานะ |
| --- | --- | --- | --- | --- | --- |
| A1 · โหมดเดิม | Divider · `R1=100, R2=22, RE=1` kΩ | ผลตรง Lab 02: IC 1.2299 mA · VCE 8.0522 V | `IC 1.230 mA`, `VCE 8.052 V`, badge `Forward Active`, `VTH 2.164 V`, `RTH 18.033 kΩ` | OpenCode Browser | **PASS** |
| A2 · Fixed | Fixed · `RB=1 MΩ`, ไม่กรอก RE | IC 1.1300 mA · VCE 9.5140 V | `IC 1.130 mA`, `VCE 9.514 V`, `VE 0.000 V`, `VB 0.700 V` | OpenCode Browser | **PASS** |
| A3 · Emitter | Emitter · `RB=1 MΩ, RE=1 kΩ` | IC 1.0263 mA · VCE 8.7054 V | `IC 1.026 mA`, `VCE 8.705 V`, `VE 1.037 V`, `VB 1.737 V` | OpenCode Browser | **PASS** |
| A4 · เปลี่ยนค่าเดียว | Emitter · เหมือน A3 แต่ `RE=2 kΩ` | IC ลดลงจาก A3 ≈ 0.9401 mA · VCE ≈ 8.0328 V | `IC 0.940 mA`, `VCE 8.033 V`, `VE 1.899 V` → IC ลดลงจริง | OpenCode Browser | **PASS** |
| A5 · อินพุตผิด | Fixed · `RB=0` | ข้อความให้แก้ RB, เว็บไม่ล่ม, ไม่โชว์ผลเดิม | ข้อความ `"RB ต้องมากกว่า 0"` ปรากฏใต้ช่อง RB; ไม่มีหัวข้อผลคำนวณ; ไม่มี `9.514` บนหน้า | OpenCode Browser | **PASS** |

## 3. หลักฐานจากหน้าเว็บ Lab 03 (ข้อความจริงจาก snapshot)

- A1: `ผลการคำนวณ DC Bias — Voltage Divider Bias` · `IC` → `1.230 mA` · `VCE` → `8.052 V`
- A2: `ผลการคำนวณ DC Bias — Fixed Bias` · `IC` → `1.130 mA` · `VCE` → `9.514 V`
- A3: `ผลการคำนวณ DC Bias — Emitter Bias` · `IC` → `1.026 mA` · `VCE` → `8.705 V`
- A4: `ผลการคำนวณ DC Bias — Emitter Bias` · `RE` → `2` · `IC` → `0.940 mA` · `VCE` → `8.033 V`
- A5: `RB ต้องมากกว่า 0` · ไม่มี `ผลการคำนวณ DC Bias —` และไม่มี `9.514`

หลังเปลี่ยนหน่วย RB จาก kΩ เป็น MΩ ได้รัน A2 และ A3 ซ้ำผ่าน Browser อีกครั้ง
ช่องแสดง `RB [MΩ]` ค่า `1` ผลยังเป็น `IC 1.130 mA / VCE 9.514 V` (Fixed) และ
`IC 1.026 mA / VCE 8.705 V` (Emitter) เท่าเดิม
ในรอบ Lab 04 ยังเปิดทั้งสามโหมดซ้ำอีกครั้ง (B1) ผลยังตรงตารางด้านบน

## 4. เคสอินพุตผิดและขอบแบบจำลอง (Lab 03)

| อินพุต | ผล |
| --- | --- |
| POST ว่าง (ไม่ส่งโหมด → Divider) | HTTP 400 + error ครบทุกฟิลด์ของ Divider |
| `mode=unknown` | HTTP 400 + `โหมดวงจรไม่ถูกต้อง` (ไม่เดาเป็น Divider) |
| `R1 = 0` (Divider) | HTTP 400 + `R1 ต้องมากกว่า 0` |
| `RB = 0` (Fixed) | HTTP 400 + `RB ต้องมากกว่า 0` |
| Divider `R1 = 470 kΩ` | `VTH ≈ 0.537 V < VBE` → badge `Cutoff` + warning |
| Divider `RC = 47 kΩ` | `VCE < 0.2 V` → badge `Saturation` + warning |

## 5. วิธีทำซ้ำ Lab 03

```powershell
py -m unittest discover -s tests -v
py -m flask --app app run --debug
```

ผล unittest ปัจจุบันของทั้งโปรเจกต์: **72 tests, OK** (รวม test ของ Lab 04)

---

## 6. สภาพแวดล้อม Lab 04 ที่ใช้จริง

| รายการ | ค่าที่ตรวจได้ |
| --- | --- |
| ngspice | `ngspice-47 : Circuit level simulation program` จาก `tools\ngspice\Spice64\bin\ngspice_con.exe -v` |
| การค้นหา executable | `NGSPICE_PATH` → `PATH` → project-local `ngspice_con.exe` → `ngspice.exe` |
| การเรียก | `subprocess.run([exe, "-b", "circuit.cir"], shell=False, timeout=20, cwd=tempdir)` |
| BJT model | `.model QNPN NPN(IS=1E-14 BF=100 VAF=100 CJE=4P CJC=3P TF=0.3N)` (ระบุเองเพราะไม่มี model จากอาจารย์) |
| หน่วยฟอร์ม | `VCC [V]`, `R1/R2/RC/RE/RL [kΩ]`, `Cin/Cout [µF]`, `Vin [mV peak]`, `f [kHz]` |
| AC sweep | `ac dec 20 1 1G` + `set units=degrees` + `set wr_singlescale` + `set wr_vecnames` + `wrdata ac.csv vm(out) vp(out) vm(src) vp(src)` |
| Transient | `tran 10u 5m 0 10u` ที่ 1 kHz + `set wr_singlescale` + `set wr_vecnames` + `wrdata tran.csv v(src) v(out)` |
| ตรวจความจริง | ตรวจ exit code, ข้อความ `Error:` แม้ exit 0, ไฟล์ผลมี/ไม่ว่าง, จำนวน column ตรง, ค่าเป็นตัวเลขจำกัด |

Browser ที่ใช้: OpenCode Browser บน `http://127.0.0.1:5000/`
(ทดสอบผ่าน tab จริง มี POST 400/200 ใน network log) — **ไม่ใช่ Playwright MCP**

## 7. เปรียบเทียบ DC: analytical vs ngspice

เงื่อนไขเดียวกัน `VCC=12 V, R1=100 kΩ, R2=22 kΩ, RC=2.2 kΩ, RE=1 kΩ,
RL=10 kΩ, Cin=Cout=10 µF`; ไม่มี bypass capacitor

| ปริมาณ | Analytical (Lab 03) | ngspice-47 | Δ (SPICE − Analytical) |
| --- | --- | --- | --- |
| VB | 1.942 V | 1.949 V | +0.007 V |
| VE | 1.242 V | 1.289 V | +0.047 V |
| VC | 9.294 V | 9.189 V | −0.105 V |
| VCE | 8.052 V | 7.900 V | −0.152 V |
| IC | 1.230 mA | 1.278 mA | +0.048 mA |
| IB | 12.30 µA | 11.913 µA | −0.387 µA |

ความแตกต่างเกิดจากสมมติฐาน: analytical ใช้ β=100 และ VBE=0.70 V คงที่
ส่วน ngspice ใช้ IS/BF/VAF/CJE/CJC/TF และหาจุดทำงานจาก model จริง
จึงบันทึกแยก panel และไม่นำค่าตัวใดไปแทนที่อีกตัวโดยไม่ระบุที่มา

## 8. ตาราง B1–B8 (ผลที่เห็นจริงจาก Browser + ngspice log)

| Case | Method | Input | Expected/Reference | Observed (พร้อมหน่วย) | Evidence | Status |
| --- | --- | --- | --- | --- | --- | --- |
| B1 · Regression | OpenCode Browser: เลือก bias mode + กด “เปลี่ยนโหมด” + “คำนวณ” | Divider `100/22/1` kΩ; Fixed `RB=1 MΩ`; Emitter `RB=1 MΩ, RE=1 kΩ` | ตรง A1–A3 เดิม | Divider `IC 1.230 mA, VCE 8.052 V`; Fixed `IC 1.130 mA, VCE 9.514 V`; Emitter `IC 1.026 mA, VCE 8.705 V` | snapshot `.results` ของทั้ง 3 โหมด + ตาราง A1–A3 | **PASS** |
| B2 · DC SPICE | OpenCode Browser: analysis `dc`, กด Run Simulation | defaults ตามข้อ 6 | VB/VE/VC/VCE/IC จาก ngspice; มี engine/model/status | `Engine ngspice-47`, `Run Status: Success`, `Data points 7`, `VB 1.949 V`, `VE 1.289 V`, `VC 9.189 V`, `VCE 7.900 V`, `IC 1.278 mA`, `IB 11.913 µA`, `IE 1.289 mA` | `.spice-results`, `.provenance`, `<details>` netlist/log: `v(base) = 1.949110e+00`, `@q1[ic] = 1.277552e-03` | **PASS** |
| B3 · Change RE | เปลี่ยนเฉพาะ `RE` ในฟอร์ม SPICE → Run DC ซ้ำ | `RE` 1 → 2 kΩ (ค่าอื่นคงเดิม) | operating point ต้องเปลี่ยน ไม่โชว์ค่าค้าง | ก่อน `VB 1.949 V, VE 1.289 V, VC 9.189 V, VCE 7.900 V, IC 1.278 mA`; หลัง `VB 2.048 V, VE 1.405 V, VC 10.469 V, VCE 9.065 V, IC 0.696 mA, IB 6.418 µA, IE 0.702 mA` | snapshot ก่อน/หลัง + netlist `RE emitter 0 2k`; test `test_spice_inputs_do_not_leak_into_analytical_form` ยืนยันฟอร์ม Lab 03 ยังเป็น `RE=1` | **PASS** |
| B4 · AC | analysis `ac` → โหลดฟอร์ม → Run → เปิด details | defaults; `Vin 10 mV`, `f 1 kHz` (โชว์ในฟอร์ม) | มีกราฟ Gain [dB] และ Phase [deg] แยกกัน คนละแกน Y แต่ใช้แกนความถี่ [Hz] log ร่วมกัน จาก run จริง | `Gain สูงสุด 4.86 dB`, `Phase 180.0°`, `fL ≈ 1.82 Hz · fH ≈ 2.08e+08 Hz`, 181 points; axis text `1`, `1e+09`, `Frequency [Hz] (log)`, `Gain [dB]`, `Phase [deg]`; ที่ 1 kHz `gain 4.86 dB, phase −179.87°` | SVG `polyline.gain/phase` คนละ 181 จุด; log `No. of Data Rows : 181`; netlist `ac dec 20 1 1G`, `set units=degrees`, `set wr_singlescale`, `wrdata ac.csv ...`; `docs/screenshots/desktop-ac.png` | **PASS** |
| B5 · Transient | analysis `transient` → Run → อ่านตาราง/กราฟ | `Vin amplitude 10 mV peak`, `f 1 kHz` | waveform Vin/Vout ตามเวลา มีหน่วย ms/V และกลับเฟส | `Vin peak 10.00 mV`, `Vout peak 17.49 mV`, `ทิศทางเฟส กลับเฟส (~180°)`, 508 points; axis `0.000`, `5.000`, `Time [ms]`, `0.018`, `-0.017`, `Voltage [V]`; legend `Vin`, `Vout` | netlist `VIN src 0 DC 0 AC 0.01 SIN(0 0.01 1000)`, `tran 10u 5m 0 10u`; `docs/screenshots/desktop-transient.png` | **PASS** |
| B6 · Change Source | เปลี่ยน amplitude 10 → 20 mV → Run transient ซ้ำ | `Vin 20 mV peak`, `f 1 kHz` คงเดิม | waveform ต้องขยายตามค่าใหม่ ไม่ใช่กราฟ hard-code | ก่อน `Vin 10.00 mV / Vout 17.49 mV` (axis ±0.018 V); หลัง `Vin 20.00 mV / Vout 34.99 mV` (axis ±0.035 V) — อัตราส่วน ≈2; 508 points เท่าเดิม | netlist หลัง `VIN ... SIN(0 0.02 1000)`; `desktop-transient.png` vs `desktop-transient-20mv.png`; frequency-only `desktop-transient-freq2k.png` (ข้อ 13) | **PASS** (รันทั้ง amplitude และ frequency-only แล้ว) |
| B7 · Invalid / Fail | กรอก `RE=0` ในฟอร์ม SPICE → Run | `RE=0`, analysis `transient` | แจ้ง error, ไม่โชว์ Success/ผลเก่า | ข้อความ `RE ต้องมากกว่า 0` ปรากฏ; ไม่มี `Run Status: Success`; ไม่มี `34.99` (ค่ารอบก่อน); network POST → HTTP 400 | snapshot error state + `network.list` statusCode 400; engine-missing ทดสอบผ่าน Browser แล้ว (ข้อ 13) + test ใน `test_spice_engine.py` | **PASS** (ผ่านทั้ง invalid input และ engine-missing) |
| B8 · UI | เปิด desktop tab และ phone-size iframe ผ่าน HTTP + เปลี่ยน analysis/mode | desktop 1496×886; iframe 390×844 ที่ `http://127.0.0.1:5000/static/mobile-view.html` | กราฟ/หน่วย/ปุ่มอ่านง่าย ไม่ตัดเนื้อหาสำคัญ | desktop `scrollWidth 1481 < innerWidth 1496`; mobile app `innerWidth 390`, `scrollWidth 375`, `cardW 355`, `.form-grid` → `321px` (1 column), chart width 311px, ปุ่มทั้ง 4 อยู่ในขอบ (right ≤275 px); เปลี่ยนเป็น transient และรันได้ 508 points บนจอ 390 px | `desktop-ac.png`, `desktop-transient.png`, `desktop-transient-20mv.png`, `mobile-390-wrapper.png`, `mobile-transient.png` | **PASS** (mobile emulation ไม่ใช่เครื่องจริง) |

## 9. หลักฐานว่ากราฟมาจาก run จริง ไม่ใช่ mock

- ทุกกราฟถูก render จาก `sim_result.ac` / `sim_result.transient` เท่านั้น;
  `plots.py` ไม่สร้างจุดขึ้นมาเองและมี test ตรวจกรณีข้อมูลว่าง
- เปลี่ยน `RE` → ผล DC เปลี่ยน; เปลี่ยน amplitude → ผล transient และช่วงแกน Y เปลี่ยน
  (B3, B6) แสดงว่าข้อมูลไม่ได้ฝังใน HTML/CSS
- netlist และ log ที่ใช้รันจริงถูกแนบไว้ใน `<details>` ของหน้า results
- รูปแบบ `wrdata` ตรวจแล้ว: column แรกคือ frequency/time ตามด้วย `vm(out) vp(out)
  vm(src) vp(src)` หรือ `v(src) v(out)`; parser เดิมที่อ่านเป็นคู่ real/imag ทำให้
  ได้ `gain −200 dB` และเฟส "ไม่กลับ" ถูกแก้และมี test กันซ้ำ
- ไฟล์ screenshot ที่เก็บไว้: `docs/screenshots/desktop-ac.png` (อัปเดตกราฟแยก),
  `desktop-transient.png`, `desktop-transient-20mv.png`, `desktop-b8.png`,
  `desktop-transient-freq2k.png`, `engine-missing.png`, `mobile-ac-split.png`,
  `mobile-390-wrapper.png`, `mobile-transient.png` (ถ่ายจาก Browser จริง ไม่ใช่ภาพแนวคิดจากใบงาน)

## 10. สิ่งที่ไม่ได้รัน / ข้อจำกัดที่ต้องบอกตรง ๆ

| รายการ | สถานะจริง |
| --- | --- |
| Playwright MCP ตามที่ใบงานแนะนำ | **NOT RUN** — ไม่ได้ติดตั้ง/ไม่มี tool ในรอบนี้ ใช้ OpenCode Browser แทนและไม่กล่าวอ้างว่าเป็น Playwright |
| Impeccable skill (UI critique/polish) | **NOT RUN** — skill ไม่พร้อม; CSS ปรับด้วยตนเอง ไม่มี before/after จาก skill |
| เปลี่ยน Frequency แยกจาก amplitude ใน B6 | **RUN แล้ว (ข้อ 13)** — เปลี่ยน `f 1 → 2 kHz` โดย amplitude คง 10 mV |
| ทดสอบ engine ไม่พร้อมผ่าน Browser | **RUN แล้ว (ข้อ 13)** — ย้าย binary ชั่วคราวแล้ว restore; HTTP 400 + error state |
| อุปกรณ์มือถือจริงสำหรับ B8 | **NOT RUN** — ใช้ iframe 390×844 จาก Flask static แทน |
| GitHub repo / commit SHA / push | **NOT RUN** — ไม่มี `git` ในเครื่องและไม่มี repo URL ใน workspace |
| ขอบเขต circuit | ไม่มี bypass cap, ไม่มี editor, ไม่มี AC สำหรับ Fixed/Emitter, AC sweep คงที่ 1 Hz–1 GHz |

## 11. วิธีทำซ้ำ

```powershell
cd BJT-CD-Bias-Web-App-main
py -m pip install -r requirements.txt
py -m unittest discover -s tests -v
py -m flask --app app run --debug
```

จาก Browser เปิด <http://127.0.0.1:5000/> แล้วทำตามลำดับ B1–B8 ในข้อ 8;
สำหรับจอโทรศัพท์เปิด <http://127.0.0.1:5000/static/mobile-view.html>
(โหลดแอปจริงใน iframe 390 px) แล้วเปลี่ยน analysis เป็น transient
เพื่อดูกราฟในขนาดดังกล่าว ผล unittest ที่รันจริงล่าสุด: **72 tests, OK**

---

## 12. รันซ้ำ B1–B8 บน server ที่ restart ใหม่ (2026-11-24)

รันตามลำดับเดิมใน tab เดียว (B8 เปิด tab iframe เพิ่ม) ด้วย OpenCode Browser จริง
ผลที่อ่านได้ตรงกับตารางข้อ 8 ทุกกรณี จึงไม่แก้ค่าอ้างอิงเดิม

| Case | ผลที่อ่านซ้ำ | หลักฐานใหม่ |
| --- | --- | --- |
| B1 | Divider `IC 1.230 mA / VCE 8.052 V`; Fixed `IC 1.130 mA / VCE 9.514 V`; Emitter `IC 1.026 mA / VCE 8.705 V` — ทั้งสาม badge `Forward Active` | snapshot `.results` ทั้ง 3 โหมด |
| B2 | `ngspice-47`, 7 points, `VB 1.949 V, VE 1.289 V, VC 9.189 V, VCE 7.900 V, IC 1.278 mA, IB 11.913 µA, IE 1.289 mA`; `Run Status: Success` | netlist/log ใน `<details>` |
| B3 | เปลี่ยน `RE 1 → 2 kΩ` → `VB 2.048 V, VE 1.405 V, VC 10.469 V, VCE 9.065 V, IC 0.696 mA, IB 6.418 µA, IE 0.702 mA`; netlist `RE emitter 0 2k` | snapshot ก่อน/หลัง |
| B4 | `Gain 4.86 dB`, `Phase 180.0°`, `fL ≈ 1.82 Hz · fH ≈ 2.08e+08 Hz`; gain/phase อย่างละ 181 จุด; netlist `ac dec 20 1 1G`, `set units=degrees`, `set wr_singlescale`, `set wr_vecnames`, `wrdata ac.csv ...` | `docs/screenshots/desktop-ac.png` (อัปเดต) |
| B5 | `Vin 10.00 mV`, `Vout 17.49 mV`, กลับเฟส ~180°; Vin/Vout 508 จุด; `tran 10u 5m 0 10u` | `docs/screenshots/desktop-transient.png` (อัปเดต) |
| B6 | `Vin 20.00 mV`, `Vout 34.99 mV`; แกน Y `0.035 / -0.035 V`; `VIN ... SIN(0 0.02 1000)` | `docs/screenshots/desktop-transient-20mv.png` (อัปเดต) |
| B7 | `RE=0` → ข้อความ `RE ต้องมากกว่า 0`, HTTP **400**, ไม่มี `Run Status: Success`, ไม่มี `34.99`, ไม่มีกราฟ/ตารางผล | `network.list` POST statusCode 400 + snapshot error state |
| B8 | desktop ปัจจุบัน `innerWidth 4533`, `scrollWidth 4533` (ไม่ overflow แนวนอน), chart 772 px, 508 จุด; mobile iframe `innerWidth 390`, `scrollWidth 345`, `cardW 325`, `.form-grid 287.5px` (1 column), chart 273 px, ปุ่ม right ≤281 px, รัน transient ได้ 508 จุด | `docs/screenshots/desktop-b8.png`, `docs/screenshots/mobile-transient.png` (อัปเดต) |

หมายเหตุเรื่อง B8: ขนาด desktop ที่วัดได้ในรอบนี้กว้างกว่าครั้งก่อน (4533 px เทียบ 1496 px)
เพราะหน้าต่าง Browser ที่ใช้มี viewport กว้างขึ้น แต่ `scrollWidth == innerWidth`
จึงยังไม่มี horizontal overflow ข้อมูล mobile มาจาก iframe 390 px เหมือนเดิม
(**ไม่ใช่อุปกรณ์จริง**) ส่วน Playwright MCP / Impeccable / git ยังเป็น **NOT RUN** ตามข้อ 10

---

## 13. ปิด NOT RUN ที่ทำได้ในรอบนี้

### 13.1 เปลี่ยน Frequency อย่างเดียว (ปิด B6 frequency-only)

จาก transient `Vin 10 mV, f 1 kHz` เปลี่ยนเฉพาะ `Frequency [kHz]` เป็น `2`
โดยไม่แตะ amplitude แล้วกด Run Simulation

| รายการ | ก่อน | หลัง |
| --- | --- | --- |
| `Vin amplitude` (ฟอร์ม) | 10 mV | **10 mV (คงเดิม)** |
| `Frequency` (ฟอร์ม) | 1 kHz | **2 kHz** |
| ผลตาราง | `Vin 10.00 mV / Vout 17.49 mV / กลับเฟส ~180°` | `Vin 10.00 mV / Vout 17.49 mV / กลับเฟส ~180°` |
| แกนเวลา | `0.000 → 5.000 ms` | `0.000 → 2.500 ms` |
| netlist | `SIN(0 0.01 1000)`, `tran 10u 5m 0 10u` | `SIN(0 0.01 2000)`, `tran 5u 2.5m 0 5u` |
| จุดกราฟ | 508 | 508 |

`Vout` ยังเท่าเดิมเพราะ 1–2 kHz อยู่ในช่วง midband ของวงจรนี้ แต่ **แกนเวลาและ
netlist เปลี่ยนตามความถี่ที่กรอก** จึงพิสูจน์ว่าค่า frequency ถูกส่งเข้า ngspice จริง
ไม่ใช่ค่าคงที่ หลักฐาน: `docs/screenshots/desktop-transient-freq2k.png`

### 13.2 ทดสอบ engine ไม่พร้อมผ่าน Browser (ปิด NOT RUN เดิม)

จำลองสภาพแวดล้อมที่ไม่มี ngspice:

1. ตั้ง `NGSPICE_PATH=C:\does-not-exist\ngspice.exe` (พบว่ายัง fallback ไป PATH/local ได้)
2. ตรวจ `Get-Command ngspice,ngspice_con` → ไม่มีใน PATH
3. ย้าย `tools\ngspice\Spice64\bin\ngspice.exe` และ `ngspice_con.exe` ไป temp ชั่วคราว
4. reload หน้าเว็บ → analysis `dc` → Run Simulation

ผลที่อ่านจริง:

- ข้อความ `ไม่พบ ngspice ให้รัน: ตั้ง NGSPICE_PATH หรือติดตั้ง ngspice ก่อน` ปรากฏ
- HTTP POST → **400**
- ไม่มี `Run Status: Success`, ไม่มี `.spice-results`, ไม่มี `.chart svg`
- panel Analytical ยังแสดงได้ปกติ (เส้นทาง Lab 03 ไม่ถูกกระทบ)

จากนั้น **ย้าย binary กลับที่เดิม**, restart Flask โดยไม่ตั้ง `NGSPICE_PATH` และรัน dc ซ้ำ
ได้ `Run Status: Success`, `ngspice-47`, `IC 1.278 mA` เท่าเดิม
หลักฐาน: `docs/screenshots/engine-missing.png` + network log 400

### 13.3 ที่ยังทำไม่ได้จริง (คงเป็น NOT RUN ตามข้อ 10)

| รายการ | เหตุผล |
| --- | --- |
| Playwright MCP | ไม่มี tool ในรอบนี้ ใช้ OpenCode Browser แทน |
| Impeccable skill | skill ไม่พร้อม CSS ปรับด้วยตนเอง |
| อุปกรณ์มือถือจริง | ใช้ iframe 390 px จาก Flask static แทน |
| git commit / push | ไม่มี `git` และไม่มี repo URL ใน workspace |

---

## 14. แก้กราฟ AC Frequency Response (B4)

ปัญหาที่พบ: เส้น `Phase [deg]` ถูกวาดด้วยสเกล +180…-180° บนพื้นที่เดียวกับ
เส้น gain แต่ **ไม่มีแกน/ตัวเลขด้านขวา** ทำให้อ่านค่า phase ไม่ได้

สิ่งที่เปลี่ยน (เฉพาะชั้นนำเสนอ ไม่แตะสมการ/ngspice):

- `plots.py`: เพิ่ม `_phase_axis()` วาดแกนขวา + tick `180 / 0 / -180` + ชื่อ
  `Phase [deg]` แบบหมุน 90° สีเดียวกับเส้น phase
- `static/style.css`: เพิ่ม `.axis.phase-axis`, `.phase-label`, `.phase-title`
  ให้ใช้สีน้ำเงิน `#1d638b` เหมือนเส้น phase
- `tests/test_plots.py`: เขียน test ใหม่ **ก่อน** แก้โค้ด เห็น FAIL แล้วแก้จน PASS

ตรวจซ้ำใน Browser หลัง reload + run AC:

- axis texts: `1`, `1e+09`, `Frequency [Hz] (log)`, `4.9`, `-2.6`, `Gain [dB]`,
  **`180`, `0`, `-180`, `Phase [deg]`**, `Gain [dB]`, `Phase [deg]`
- `line.phase-axis` มีจริง, `.phase-label` มี 3 ตัว, สี `rgb(29, 99, 139)` → เป็นน้ำเงิน
- gain/phase ยังคนละ **181 จุด** เท่าเดิม; ค่าสรุป `4.86 dB / 180.0° /
  fL 1.82 Hz / fH 2.08e+08 Hz` ไม่เปลี่ยน
- หลักฐาน: `docs/screenshots/desktop-ac.png` (อัปเดต)

ผลทดสอบหลังแก้: **72 tests, OK** (69 → 70 หลังเพิ่มแกน phase → 72 หลังแยกกราฟ)

---

## 15. แยกกราฟ Gain กับ Phase ออกจากกัน

ตามที่ผู้ใช้ขอ **“แยกกราฟ Gain กับ Phase”** — เดิมทั้งสองเส้นอยู่ใน SVG เดียวกัน
(phase ใช้แกนขวา) เปลี่ยนเป็น **svg คนละอัน** แสดงใน `.chart-grid`

สิ่งที่เปลี่ยน (ไม่แตะข้อมูล/สูตรจาก ngspice):

- `plots.py`: เพิ่ม `gain_svg(points)` และ `phase_svg(points)`; ทั้งคู่ใช้จุด
  `AcPoint` ชุดเดิมจากผล `.ac` — gain ใช้แกนซ้ายแบบปรับสเกลอัตโนมัติ,
  phase ใช้สเกลคงที่ `+180 → −180°` และมี tick `180 / 0 / −180`
  (`bode_svg()` เดิมยังเก็บไว้เพื่อความเข้ากันได้ของ test เก่า)
- `app.py`: ส่ง `gain_chart` และ `phase_chart` แทน `bode_chart`
- `templates/index.html`: แยก `<figure>` เป็น 2 อัน พร้อม caption บอกหน่วย/ที่มา
- `static/style.css`: `.chart-grid` 2 คอลัมน์บนจอใหญ่, 1 คอลัมน์ที่ ≤900 px
- `tests/test_plots.py`: เขียน test ใหม่ **ก่อน** แก้โค้ด → เห็น ImportError
  (`cannot import name 'gain_svg'`) → แก้แล้ว PASS (ตามกติกา `AGENTS.md`)

ตรวจซ้ำใน Browser หลัง run AC ด้วย ngspice จริง:

| รายการ | กราฟ Gain | กราฟ Phase |
| --- | --- | --- |
| `<title>` | `Gain [dB] จาก ngspice` | `Phase [deg] จาก ngspice` |
| จำนวน `<polyline>` | **1** (`class="gain"`) | **1** (`class="phase"`) |
| จุดข้อมูล | **181** | **181** |
| แกน Y | `Gain [dB]`, tick `4.9 / −2.6` | `Phase [deg]`, tick `180 / 0 / −180` |
| แกน X | `Frequency [Hz] (log)`, `1 → 1e+09` | `Frequency [Hz] (log)`, `1 → 1e+09` |
| Legend | `Gain [dB]` | `Phase [deg]` |

- desktop: `.chart-grid` → `390.667px 390.667px` (2 คอลัมน์); HTTP POST **200**
- mobile 390 px: `.chart-grid` → `316px` (1 คอลัมน์), svg กว้าง `305.33px`,
  `innerWidth 390 / scrollWidth 370` → **ไม่มี horizontal overflow**;
  `Run Status: Success`
- ค่าสรุปไม่เปลี่ยนเลย: `Gain 4.86 dB`, `Phase 180.0°`,
  `fL ≈ 1.82 Hz`, `fH ≈ 2.08e+08 Hz`
- หลักฐาน: `docs/screenshots/desktop-ac.png` (อัปเดต),
  `docs/screenshots/mobile-ac-split.png`
- ผล unittest สุดท้าย: **72 tests, OK** (เพิ่มจาก 70)

---

## 16. UI polish หลัง audit (Desktop 1280 px / Mobile 390 px)

ทำตามที่ผู้ใช้อนุมัติ **เฉพาะชั้นนำเสนอ**: `templates/index.html`,
`static/style.css` และค่าการวาดใน `plots.py` (legend position / plot margin)
**ไม่แตะ** `dc_bias.py`, `app.py`, `spice_engine.py`, สูตร หรือข้อมูลจาก ngspice

| รายการ | ก่อน | หลัง (วัดจริงใน Browser) |
| --- | --- | --- |
| card / chart desktop | `860px`, figure `391px`, svg `373px` | `1180px` (x=43), figure `551px`, svg `533px`, `innerWidth 1280 / scrollWidth 1265` |
| input group | `fieldset = 0` | `fieldset = 6` พร้อม legend `1.1–1.2` (Analytical) และ `2.1–2.4` (SPICE) |
| axis text desktop | แสดงจริง ~`6.03px` | `15px` user unit → ~`11.76px` ที่ scale `0.784` |
| axis text mobile | แสดงจริง ~`4.94px` | `24px` user unit → ~`10.78px` ที่ scale `0.449` |
| trace desktop / mobile | ~`1.1px` / `0.9px` | ~`1.96px` / `1.12px` (`vector-effect="non-scaling-stroke"`) |
| error state | `<p class="error">` อย่างเดียว | `aria-invalid="true"`, `aria-describedby="err-s-re"`, `role="alert"`, `aria-live="polite"` + error summary |
| engine status | badge `12px` เดี่ยว | `run-strip` แสดง `Run Status: Success · Engine ngspice-47 · AC · 181 points` (และเก็บ `<dl class="provenance">` เดิมไว้) |

ตรวจซ้ำด้วย ngspice จริงหลัง reload:

- AC ยังให้ `Gain 4.86 dB`, `Phase 180.0°`, `fL ≈ 1.82 Hz`, `fH ≈ 2.08e+08 Hz`
- กราฟ Gain/Phase ยังมี **181 จุดต่อเส้น** (อ่านจาก `points` attribute) ไม่มีการสร้างจุดเพิ่ม
- mobile `innerWidth 390 / scrollWidth 370`, `.chart-grid` ยังเป็น 1 column `316px`, svg `305px`
  → ไม่มี horizontal overflow; legend อยู่ขอบขวาและมีพื้นหลัง stroke สีขาว
- invalid `RE=0`: HTTP 400, ไม่มี `.spice-results`, ไม่มี `.chart svg`, ไม่มีข้อความ
  `Run Status: Success` — error message/counterpart aria ถูกต้องทั้ง inline และ summary
- หลักฐาน: `docs/screenshots/audit-before-desktop-1280.png`,
  `docs/screenshots/audit-after-desktop-1280.png`,
  `docs/screenshots/audit-before-mobile-390.png`,
  `docs/screenshots/audit-after-mobile-390.png`,
  `docs/screenshots/audit-after-error-1280.png`
- ปรับ `tests/test_web.py` เฉพาะ assertion เดิมที่เทียบสตริง `<input ...>` แบบเต็ม
  ให้ใช้ regex `id/name[^>]*value` เพราะตอนนี้มี `aria-*` ต่อท้าย; ความหมายเดิม
  (ฟอร์มทั้งสองคงค่า `1` / `2`) ยังตรงอยู่
- ผล unittest จริง: `py -m unittest discover -s tests` → **Ran 72 tests / OK**
  (`python` ไม่มีบน PATH ของเครื่องนี้ จึงใช้ `py` ตามที่ใช้มาตลอด)

ยังคงเป็นข้อจำกัดเดิม: Impeccable skill ไม่พร้อม, ไม่มีอุปกรณ์มือถือจริง
(ใช้ iframe 390 px), ไม่มี `git`/repo สำหรับ commit และโมเดลไม่ได้อ่านพิกเซล screenshot
ด้วยตนเอง — ข้อสรุปมาจาก DOM + computed style + netlist/log จริง
(Playwright MCP ถูกติดตั้งเพิ่มในภายหลัง — ดูข้อ 17)

---

## 17. ติดตั้ง Playwright MCP (หลังข้อ 16)

ตามที่ผู้ใช้ขอ “ติดตั้ง MCP” ได้เลือก **Playwright MCP แบบ global**:

- config: `C:\Users\B6814151\.config\opencode\opencode.json`
- server: `playwright` → `@playwright/mcp@latest`
- CLI ที่ใช้: `C:\Users\B6814151\AppData\Roaming\ai.opencode.desktop\cli\2.4.1-x64\opencode-cli.exe`
  (คำสั่ง `opencode` ไม่มีบน PATH แต่ binary มีอยู่ใน Desktop app)

ปัญหาตอนติดตั้งครั้งแรก: `npx.cmd` เรียก `node` จาก PATH ไม่เจอ
→ แก้โดยเรียก `node.exe` ของ Visual Studio พร้อม `npx-cli.js` ตรง ๆ และใส่
`environment.PATH` ให้ process ลูกด้วย

ตรวจจริง:

- `opencode mcp list` → **`✓ playwright connected`**
- smoke test ผ่าน MCP จริง: navigate ถึง `http://127.0.0.1:5000/`,
  resize `1280×900`, `document.title` ตรง, `innerWidth 1280`,
  `cardWidth 1180px`, `fieldset = 5` (ฟอร์มเริ่มต้น analysis `dc`)
- console ตอน smoke มี 1 error คือ `favicon.ico 404` เท่านั้น ไม่ใช่ JS error
- ยัง **ไม่ได้รัน audit ใหม่ทับข้อ 16** — การติดตั้ง/ smoke test เพียงพิสูจน์ว่า
  tools พร้อมใช้งานตามที่ผู้ใช้ขอ

---

## 18. รันซ้ำ B5 ด้วย Playwright MCP จริง

ตามที่ผู้ใช้ขอ “รัน B5 ต่อ” หลังติดตั้ง MCP — ครั้งนี้ใช้ `tools.playwright.*`
**ไม่ใช่ OpenCode Browser** และไม่ใช้ข้อมูลจากรอบก่อน

ลำดับที่ทำใน Playwright (viewport `1280×900`):

1. navigate `http://127.0.0.1:5000/`
2. select `#analysis = transient` → กด “โหลดฟอร์มตาม Analysis”
   → ฟอร์มมี `Vin amplitude = 10`, `Frequency = 1`, `fieldset = 6`
3. กด “Run Simulation” → รอข้อความ `Run Status: Success`

หลักฐานจาก network/หน้า results ที่อ่านจริง:

- POST body (request #9): `form=spice&analysis=transient&vcc=12&r1=100&r2=22&rc=2.2&re=1&rl=10&cin=10&cout=10&amplitude=10&frequency=1&action=run`
- POST → **HTTP 200**, `content-length 27027`, `text/html; charset=utf-8`
- `Run Status: Success | Engine ngspice-47 | Transient response (.tran) | Data points 508`
- ตาราง: `Vin peak 10.00 mV`, `Vout peak 17.49 mV`, `ทิศทางเฟส กลับเฟส (~180°)`
- กราฟ: `figure.chart` 1 อัน, `<polyline class="vin">` **508 จุด** และ
  `<polyline class="vout">` **508 จุด**, axis `0.000 / 5.000 / Time [ms]`,
  `0.018 / -0.017 / Voltage [V]`, legend `Vin` / `Vout`
- netlist ที่ใช้รันจริง: `VIN src 0 DC 0 AC 0.01 SIN(0 0.01 1000)`,
  `tran 10u 5m 0 10u`, `wrdata tran.csv v(src) v(out)`
- ngspice log: `No. of Data Rows : 508`, `Simulation executed from .control section`
- ไม่มี `.error-state`, ไม่มีผลเก่าปน; console มีเพียง `favicon.ico 404`
- screenshot ผ่าน Playwright MCP: `docs/screenshots/b5-playwright-transient.png`
  (full page `1265×3031`, `scale=css`)

**สถานะ B5: PASS** (รันใหม่ด้วย Playwright MCP สำเร็จ; ไม่ได้รัน B6/B7/B8 ซ้ำในรอบนี้)

---

## 19. รันซ้ำ B6 ด้วย Playwright MCP จริง

ต่อจากข้อ 18 บนหน้าเดียวกัน viewport `1280×900` ใช้ `tools.playwright.*`

### 19.1 เปลี่ยน amplitude 10 → 20 mV

- fill `#s-amplitude = 20` → กด Run Simulation
- POST #11 body: `...&amplitude=20&frequency=1&action=run` → **HTTP 200**
- ผล: `Vin peak 20.00 mV`, `Vout peak 34.99 mV`, กลับเฟส (~180°)
- axis Y เปลี่ยนจาก `0.018 / -0.017` → **`0.035 / -0.035 V`**
- netlist เปลี่ยนเป็น `VIN src 0 DC 0 AC 0.02 SIN(0 0.02 1000)`;
  `tran 10u 5m 0 10u` คงเดิม; 508 จุดต่อเส้น
- screenshot: `docs/screenshots/b6-playwright-20mv.png` (`1265×3031`)

### 19.2 เปลี่ยน frequency-only 1 → 2 kHz (amplitude คง 10 mV)

- fill `#s-amplitude = 10`, `#s-frequency = 2` → กด Run Simulation
- POST #13 body: `...&amplitude=10&frequency=2&action=run` → **HTTP 200**
- ผลกลับมา `Vin peak 10.00 mV`, `Vout peak 17.49 mV` (เท่ากับ B5)
- axis X เปลี่ยน `0.000 / 5.000 / Time [ms]` → **`0.000 / 2.500 / Time [ms]`**
- netlist เปลี่ยนเป็น `SIN(0 0.01 2000)` และ `tran 5u 2.5m 0 5u`
  → พิสูจน์ว่า frequency ถูกส่งเข้า ngspice จริง ไม่ใช่ค่าคงที่ในหน้า
- 508 จุดต่อเส้นเท่าเดิม; ไม่มี `.error-state`
- screenshot: `docs/screenshots/b6-playwright-freq2k.png` (`1265×3031`)

console ตลอด B6 มีเพียง `favicon.ico 404` เหมือนเดิม ไม่มี JS error

**สถานะ B6: PASS** — ทั้ง amplitude-only และ frequency-only ผ่านด้วย Playwright MCP;
ยังไม่ได้รัน B7/B8 ซ้ำในรอบนี้

---

## 20. รันซ้ำ B7 ด้วย Playwright MCP จริง

### 20.1 invalid `RE = 0`

ต่อจาก B6 (analysis `transient`, `Vin=10`, `f=2 kHz`, ผลก่อนหน้า `Vout 17.49 mV`)
fill `#s-re = 0` → กด Run Simulation:

- POST #15 body: `...&re=0&...&amplitude=10&frequency=2&action=run`
  → **HTTP 400 BAD REQUEST**
- inline error: `RE ต้องมากกว่า 0`, `id="err-s-re"`, `role="alert"`,
  `aria-live="polite"`; input `aria-invalid="true"`,
  `aria-describedby="err-s-re"`
- error summary: `ตรวจค่าก่อนรัน ngspice / RE ต้องมากกว่า 0`,
  `role="alert"`, `aria-live="polite"`
- ไม่มี `.spice-results`, ไม่มี `polyline`, ไม่มี `Run Status: Success`
- ข้อความ `17.49` และ `34.99` หายจากหน้า → ไม่มีผลเก่าปน
- screenshot: `docs/screenshots/b7-playwright-invalid-re.png` (`1265×2070`)

### 20.2 engine-missing

ย้ายชั่วคราว `ngspice.exe` และ `ngspice_con.exe` จาก
`tools\ngspice\Spice64\bin\` ไป `C:\Users\B6814151\AppData\Local\Temp\opencode\ngspice-b7-backup\`
(ไม่ต้อง restart server เพราะ discovery เกิดตอน run) จากนั้น fresh GET → Run `dc`:

- POST #19 body: `form=spice&analysis=dc&...&re=1&...&action=run`
  → **HTTP 400 BAD REQUEST**
- error text: `ไม่พบ ngspice ให้รัน: ตั้ง NGSPICE_PATH หรือติดตั้ง ngspice ก่อน`
- `Run Status: Error`; ไม่มี `.spice-results`, ไม่มีกราฟ, ไม่มี Success
- screenshot: `docs/screenshots/b7-playwright-engine-missing.png` (`1265×2026`)

**Restore ทันทีหลังทดสอบ:** ย้าย binary กลับครบ 2 ตัว (backup เหลือ 0 ตัว)
แล้วรัน dc ซ้ำ POST #23 → **HTTP 200**,
`Run Status: Success | ngspice-47 | DC operating point (.op) | 7 points`,
`VB 1.949 V, VE 1.289 V, VC 9.189 V, VCE 7.900 V, IC 1.278 mA`

console ตลอด B7 มีเพียง `favicon.ico 404` เหมือนเดิม ไม่มี JS error

**สถานะ B7: PASS** — ผ่านทั้ง invalid input และ engine-missing ด้วย Playwright MCP;
ยังไม่ได้รัน B8 ซ้ำในรอบนี้
