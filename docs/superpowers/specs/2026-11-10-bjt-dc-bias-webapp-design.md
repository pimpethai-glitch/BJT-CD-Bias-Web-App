# Design — BJT DC Bias Web App (Lab 02)

Date: 2026-11-10
Status: draft for approval
Scope size: small (one page, one circuit model, one calculation path)

## Intent

สร้าง Flask web app คำนวณ DC operating point ของวงจร NPN Common-Emitter
Voltage-Divider Bias สำหรับ ENG29 2121 Lab 02 โดย repo นี้ทำหน้าที่สองอย่างพร้อมกัน:

1. **ชิ้นงานที่ส่งได้** — ผ่านเกณฑ์ตรวจรับ A1–A7 ของ handout
2. **ตัวอย่างการสอน** — นักศึกษาโคลนไปอ่านแล้วเห็นว่าแยกชั้น Flask / สมการวิศวกรรม /
   template / CSS / tests อย่างไร และเห็นว่าผลลัพธ์มาจาก Python จริง ไม่ใช่ค่าที่ฝังใน HTML

## Goals

| เกณฑ์ | สิ่งที่ทำให้สำเร็จ |
| --- | --- |
| A1 GET / | เปิด localhost เห็นฟอร์ม, HTTP 200 |
| A2 POST / | กรอกค่า → Python คำนวณ → ผลแสดงใน HTML หน้าเดิม |
| A3 Engineering reference | ผลตรงกับค่าคำนวณอิสระภายใต้ forward-active model |
| A4 Validation | R≤0, β≤0, VCC≤0, ค่าไม่ใช่ตัวเลข → error รายฟิลด์ หน้าเว็บไม่ล้ม |
| A5 Outside active region | warning ชัดเจนเมื่อ cutoff / saturation |
| A6 Tests | unit tests ≥3 (math) + Flask client test ≥1 |
| A7 Reproducibility | clone → venv → pip install → flask run → unittest ตาม README |

## Non-goals

- AC small-signal, gain, Bode, transient, signal generator, overlay animation
- Bias ชนิดอื่น (fixed, emitter) — เป็นงาน W3
- SPICE/ngspice, DC load line, interactive schematic ที่ผูกค่ากับวงจร
- JavaScript ใด ๆ, ฐานข้อมูล, authentication, deploy สู่ public server
- เก็บประวัติการคำนวณ

## Anti-goals (ถือว่าล้มเหลวแม้โปรแกรมรันได้)

- ผลลัพธ์ถูก hardcode หรือคำนวณใน template แทน `dc_bias.py`
- หน้าเว็บล้ม (traceback) เมื่อกรอกค่าผิด
- แสดงผลนอก forward-active โดยไม่มี warning
- `dc_bias.py` import Flask หรือรู้จัก HTTP/HTML
- commit `.venv/`, `.env`, credential

## Constraints

- Python 3.15 (เครื่องนี้), Flask เท่านั้น — ไม่เพิ่ม dependency อื่น
- `requirements.txt` ระบุ `Flask>=3.1,<4` และต้องทดสอบติดตั้งใน venv ใหม่สะอาด
  (Python 3.15 ค่อนข้างใหม่ จึงต้องยืนยันว่า install ผ่านก่อนถือว่า A7 สำเร็จ)
- `unittest` (ตาม handout) ไม่ใช้ pytest
- Windows เป็นเครื่องพัฒนา, รันที่ `http://127.0.0.1:5000/`
- UI ภาษาไทย, ตัวเลข/หน่วยแบบสากล (V, mA, µA, kΩ)
- UI แบบ A: หน้าเดียว, server-rendered, ไม่มี JavaScript
- **Git ไม่ใช่งานของผู้สร้างโค้ด** — การ commit/push ทำโดยเจ้าของ repo ผ่าน
  GitHub Desktop เอง (ผู้สร้างโค้ดเพียงทำให้ไฟล์พร้อมและ `.gitignore` ถูกต้อง)

## Approaches considered

| ทาง | ข้อดี | ข้อเสีย | ผล |
| --- | --- | --- | --- |
| **A. Server-rendered form POST หน้าเดียว** | ตรงกับ A2 ตรงที่สุด, ไม่มี JS/state, test ง่าย, โค้ดสั้นอ่านง่าย | refresh แล้ว re-submit | **เลือก** |
| B. PRG (POST → redirect → GET /results) | refresh ปลอดภัย, ถูกหลัก production | ต้องเก็บผลใน session, เพิ่มความซับซ้อนโดยไม่ได้คะแนนเพิ่ม | ตัด |
| C. JSON API + JS fetch | แยก frontend/backend ชัด | ขัดเจตนา A2 (HTML จาก server), เพิ่ม JS ที่ทำให้อ่านโค้ดยากขึ้น | ตัด |

## Architecture

```
Browser ──GET/POST form──▶ app.py (routes, validation, error mapping)
                              │
                              ▼
                        dc_bias.py (pure functions, ไม่รู้จัก Flask)
                              │
                              ▼
                        templates/index.html (Jinja: form + results)
                        static/style.css
```

### Files

```
app.py                      # GET / และ POST /, แปลง form → dict, เรียก solve(), จับ error
dc_bias.py                  # BiasInput, BiasResult, solve(), ValidationError
templates/index.html        # ฟอร์ม + ตารางผล + warnings
static/style.css            # layout เรียบ ๆ อ่านง่าย รองรับจอเล็ก
tests/test_dc_bias.py       # สมการ + validation + region
tests/test_web.py           # HTTP: GET form, POST สำเร็จ, POST ผิด
requirements.txt            # Flask
README.md                   # วิธีติดตั้ง/รัน/ทดสอบ
AGENTS.md                   # กติกาสำหรับ AI agent ใน repo นี้
docs/design-note.md         # สรุปการออกแบบ (อ้าง design นี้)
docs/validation.md          # ตารางเทียบค่าคำนวณมือ vs ผลเว็บ + เคสขอบ
docs/reflection.md          # บทสะท้อนการเรียนรู้ (template)
.gitignore
```

## Calculation contract (`dc_bias.py`)

**Public API (3 ฟังก์ชัน/คลาสเท่านั้น):**

```python
parse_form(values: Mapping[str, str]) -> BiasInput     # raises ValidationError
solve(data: BiasInput) -> BiasResult
ValidationError(errors: dict[str, str])                # field -> ข้อความไทย
```

**หน่วย:** `BiasInput` เก็บค่าตามที่มนุษย์กรอก คือ `vcc [V]`, `r1,r2,rc,re [kΩ]`,
`beta [-]`, `vbe [V]` — `solve()` แปลง kΩ → Ω (`* 1000`) เป็นบรรทัดแรกของตัวเอง
ส่วน `BiasResult` คืนค่า SI ทั้งหมด (V, A, Ω) การแปลงหน่วยอยู่ที่เดียว ไม่กระจาย

`parse_form` รับ mapping ใดก็ได้ (ไม่ผูกกับ Flask) จึงเป็นที่เดียวที่รู้จักชื่อฟิลด์
และข้อความ error — `app.py` แค่ส่ง `request.form` เข้าไป

```
VTH = VCC * R2 / (R1 + R2)                  [V]
RTH = R1 * R2 / (R1 + R2)                   [Ω]  (ใช้ค่าที่แปลงแล้ว)
IB  = (VTH - VBE) / (RTH + (beta + 1) * RE) [A]
IC  = beta * IB                             [A]
IE  = (beta + 1) * IB                       [A]
VE  = IE * RE                               [V]
VB  = VE + VBE                              [V]
VC  = VCC - IC * RC                         [V]
VCE = VC - VE                               [V]
```

**Output:** `BiasResult` (dataclass, frozen) เก็บค่า SI: `vth, rth, ib, ic, ie, ve, vb, vc, vce`
พร้อม `region: Region` และ `warnings: tuple[str, ...]`

**Region rules** (ตรวจหลังคำนวณ, ตามลำดับ):

| เงื่อนไข | region | การจัดการ |
| --- | --- | --- |
| `VTH <= VBE` | `CUTOFF` | clamp `IB=IC=IE=0, VE=0, VB=VTH, VC=VCC` + warning ว่าวงจรไม่นำกระแส |
| `VCE <= 0.3 V` | `SATURATION` | แสดงค่าตามสมการ active แต่ warning ว่าแบบจำลองใช้ไม่ได้ |
| อื่น ๆ | `ACTIVE` | แสดงผลปกติ ไม่มี warning |

**Validation** (`ValidationError` เก็บ `dict[field, message]` ได้หลายฟิลด์พร้อมกัน):

- ทุกฟิลด์ต้องมีค่า และแปลงเป็น float ได้ (ไม่รับ comma, ไม่รับ單位ต่อท้าย)
- `VCC > 0`, `R1 > 0`, `R2 > 0`, `RC > 0`, `RE > 0`, `beta > 0`
- `0 < VBE < VCC` (ตรวจเฉพาะเมื่อ VCC ผ่านการแปลงและมากกว่า 0 แล้วเท่านั้น
  ถ้า VCC ผิด จะรายงานแค่ error ของ VCC หนึ่งข้อความ ไม่เพิ่ม error ของ VBE)
- ถ้า `R1 + R2 <= 0` ถือว่าผิด (ครอบด้วย R>0 อยู่แล้ว)

ข้อความ error เป็นภาษาไทย ระบุชื่อฟิลด์ เช่น `R1 ต้องมากกว่า 0`

## HTTP contract

| Route | Method | ผล |
| --- | --- | --- |
| `/` | GET | 200, ฟอร์มเปล่า (หรือค่า default ตัวอย่าง VCC=12, R1=100, R2=22, RC=2.2, RE=1, β=100, VBE=0.70) |
| `/` | POST | สำเร็จ → 200 + ผลในหน้าเดิม<br>ไม่ผ่าน validation → **400** + ฟอร์มพร้อมค่าเดิม + error ใต้ฟิลด์ + ผลไม่แสดง |

ไม่ใช้ `flash()`, ไม่ใช้ session — ส่ง `result`, `errors`, `form_values` กลับเข้า template ตรง ๆ

## Presentation

- หน้าเดียว: ฟอร์ม (grid 2 คอลัมน์บนจอใหญ่, 1 คอลัมน์บนมือถือ) → ปุ่ม "คำนวณ DC Bias"
- ตารางผล: VB, VE, VC, VCE [V] (ทศนิยม 3 ตำแหน่ง), IC, IE [mA], IB [µA], VTH [V], RTH [kΩ]
- badge สถานะ: `Forward Active` (เขียว) / `Cutoff` (เทา) / `Saturation` (ส้ม)
- กล่อง warning สีอำพันเมื่อ region ≠ ACTIVE
- ใส่หน่วยกำกับทุกช่อง input และ label อธิบายสั้น ๆ (`R1 — ตัวต้านทานฐานไป VCC`)

## Test plan

**`tests/test_dc_bias.py`** (ค่าอ้างอิง VCC=12, R1=100k, R2=22k, RC=2.2k, RE=1k, β=100, VBE=0.70)

1. `test_reference_operating_point` — VTH 2.1639, RTH 18032.8 Ω, IB 12.30 µA, IC 1.2299 mA, IE 1.2422 mA, VE 1.2422, VB 1.9422, VC 9.2943, VCE 8.052 (±1e-3 relative)
2. `test_kohm_to_ohm_scaling` — `BiasInput(r1=100, ...)` (kΩ) → `result.rth ≈ 18032.8 Ω`
   ยืนยันว่าการแปลงหน่วยเกิดใน `solve()` จุดเดียว
3. `test_cutoff_region_warns` — R1 สูงมาก/VTH ≤ VBE → region CUTOFF + warning + กระแสเป็น 0
4. `test_saturation_region_warns` — RC ใหญ่มาก → VCE ≤ 0.3 → region SATURATION + warning
5. `test_invalid_resistance_rejected` — R ≤ 0 → ValidationError มี key ตรงฟิลด์
6. `test_non_numeric_rejected` — `parse_form({"r1": "abc", ...})` → ValidationError
7. `test_missing_field_rejected` — ไม่ส่ง `rc` มา → ValidationError ที่ key `rc`
8. `test_vbe_must_be_below_vcc`
9. `test_vcc_error_does_not_duplicate_vbe_error` — VCC = "abc" → ไม่มี key `vbe` ใน errors

**`tests/test_web.py`**

1. `test_get_index_returns_form` — 200 + มี `name="vcc"` ใน HTML
2. `test_post_valid_returns_results` — 200 + มี `8.052` และ `1.230` ใน HTML
3. `test_post_invalid_returns_400_with_message` — 400 + ข้อความ error + ไม่มีตารางผล

(รวม 12 tests — เกินเกณฑ์ขั้นต่ำ 3 + 1)

## Calls made during builder review

- `BiasInput` เก็บหน่วยตามที่กรอก (kΩ) — แก้ความขัดแย้งเดิมในเอกสาร
- `parse_form()` อยู่ใน `dc_bias.py` (ไม่ใช่ `app.py`) เพื่อให้ชั้นวิศวกรรมเป็นเจ้าของ
  การตรวจค่าและข้อความ error ทั้งหมด
- cross-check `VBE < VCC` ข้ามไปเมื่อ VCC ใช้ไม่ได้ (ไม่สร้าง error ซ้ำ)
- Pin `Flask>=3.1,<4` + ต้องพิสูจน์การติดตั้งใน venv สะอาด
- Git commit อยู่นอกขอบเขตของผู้สร้างโค้ด

## Open items (ตัดสินใจแล้ว)

- เลือก UI แบบ A (ไม่มีวงจร SVG) ตามที่ผู้ใช้ยืนยัน
- ใช้ `POST /` ตัวเดียว ไม่มี `/calculate` แยก
- ใช้ 400 สำหรับ input ผิด (ไม่ใช่ 200) เพื่อให้ test ตรวจได้ชัด
- ค่า default ในฟอร์ม = ค่าตัวอย่างจาก handout เพื่อให้ demo เร็ว

## What's left to the builder

- ถ้อยคำ label/คำอธิบายใน UI, การจัด spacing/สี
- การปัดเศษที่แสดงผล (ต้องคงความแม่นยำใน dataclass)
- เนื้อหา `docs/validation.md` (ตารางคำนวณมือ) และ `docs/reflection.md`
- ลำดับการเขียน test ก่อน/หลัง implementation ภายในแต่ละงาน
