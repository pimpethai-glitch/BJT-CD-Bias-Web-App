# BJT DC Bias Web App Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** สร้าง Flask web app หน้าเดียวที่รับค่า VCC, R1, R2, RC, RE, β, VBE แล้วคำนวณ DC operating point ของ BJT Common-Emitter Voltage-Divider Bias ด้วย Python พร้อม validation, region warning และ tests

**Architecture:** `app.py` ทำหน้าที่บาง ๆ รับ HTTP และเรียกชั้นวิศวกรรม `dc_bias.py` ซึ่งเป็น pure Python ไม่รู้จัก Flask — `parse_form()` แปลง/ตรวจค่าจาก mapping, `solve()` คำนวณและคืน `BiasResult` (SI) พร้อม region และ warnings; `templates/index.html` + `static/style.css` แสดงผลแบบ server-rendered ไม่มี JavaScript

**Tech Stack:** Python 3.15, Flask>=3.1,<4, Jinja2, unittest

**Spec:** `docs/superpowers/specs/2026-11-10-bjt-dc-bias-webapp-design.md`

## Global Constraints

- Python 3.15 on Windows; รันที่ `http://127.0.0.1:5000/`
- dependency เดียวที่อนุญาต: `Flask>=3.1,<4` (ใน `requirements.txt`)
- ทดสอบด้วย `python -m unittest discover -s tests -v` เท่านั้น (ไม่ใช้ pytest)
- UI ภาษาไทย หน้าเดียว server-rendered ไม่มี JavaScript
- `POST /` ที่ input ไม่ผ่าน validation ต้องตอบ **HTTP 400** และคงค่าที่กรอกไว้
- `dc_bias.py` ต้องไม่ import `flask` หรือรู้จัก HTTP/HTML
- ผลลัพธ์ห้าม hardcode ใน template — ต้องมาจาก `solve()` ทุกค่า
- เลขที่แสดง: แรงดัน 3 ตำแหน่งทศนิยม [V], IC/IE [mA] 3 ตำแหน่ง, IB [µA] 2 ตำแหน่ง, RTH [kΩ] 3 ตำแหน่ง
- **ห้ามรันคำสั่ง git ใด ๆ ในแผนนี้** — เจ้าของ repo commit/push เองผ่าน GitHub Desktop ที่จุด Checkpoint ของแต่ละ task
- ห้าม commit `.venv/`, `.env`, `__pycache__/`

## Review Focus

1. **ช่องที่เว้นว่างหรือมีแต่ช่องว่าง** (`""`, `"   "`) — ผู้ใช้คาดเห็นข้อความ "กรุณากรอก …" รายฟิลด์ ไม่ใช่ 500 (Task 1)
2. **พิมพ์ทศนิยมด้วยจุลภาค** (`"1,5"`) — ผู้ใช้คาดได้ข้อความบอกให้ใช้จุด ไม่ใช่ `ValueError` หลุด (Task 1)
3. **R1 + R2 = 0** — ตัวหารเป็นศูนย์ ผู้ใช้คาดได้ error ชัดเจน ไม่ใช่ `ZeroDivisionError` (Task 1)
4. **RC ใหญ่มากจน VCE ติดลบ** — ผู้ใช้คาดเห็น warning ว่าแบบจำลองใช้ไม่ได้ ไม่ใช่ตัวเลขที่ดูน่าเชื่อถือ (Task 3)
5. **POST ที่ไม่มี field ใดเลย** (request.form ว่าง) — ผู้ใช้คาดได้ 400 + ฟอร์มว่าง ไม่ใช่ 500 (Task 5)

---

### Task 1: ชั้นรับค่าและตรวจสอบ (`dc_bias.py` + venv)

**Files:**
- Create: `requirements.txt`, `dc_bias.py`, `tests/test_dc_bias.py`

**Interfaces:**
- Consumes: ไม่มี
- Produces:
  - `class ValidationError(Exception)` มี attribute `errors: dict[str, str]` (ชื่อฟิลด์ → ข้อความไทย)
  - `@dataclass(frozen=True) class BiasInput` fields: `vcc: float, r1: float, r2: float, rc: float, re: float, beta: float, vbe: float` — หน่วยตามที่มนุษย์กรอก (V, **kΩ**, -, V)
  - `def parse_form(values: Mapping[str, str]) -> BiasInput` — raises `ValidationError`

- [ ] **Step 1: สร้าง venv และติดตั้ง Flask**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install "Flask>=3.1,<4"
```

`requirements.txt` มีบรรทัดเดียว: `Flask>=3.1,<4`

- [ ] **Step 2: เขียน failing tests**

`tests/test_dc_bias.py`:

```python
import unittest

from dc_bias import BiasInput, ValidationError, parse_form

VALID = {
    "vcc": "12", "r1": "100", "r2": "22", "rc": "2.2",
    "re": "1", "beta": "100", "vbe": "0.70",
}


class ParseFormTests(unittest.TestCase):
    def test_parses_valid_values_to_floats(self):
        data = parse_form(VALID)
        self.assertIsInstance(data, BiasInput)
        self.assertAlmostEqual(data.r1, 100.0, places=9)

    def test_missing_field_rejected(self):
        values = dict(VALID)
        del values["rc"]
        with self.assertRaises(ValidationError) as ctx:
            parse_form(values)
        self.assertIn("rc", ctx.exception.errors)

    def test_blank_field_rejected(self):
        values = dict(VALID, r2="   ")
        with self.assertRaises(ValidationError) as ctx:
            parse_form(values)
        self.assertIn("r2", ctx.exception.errors)

    def test_non_numeric_rejected(self):
        values = dict(VALID, r1="abc")
        with self.assertRaises(ValidationError) as ctx:
            parse_form(values)
        self.assertIn("r1", ctx.exception.errors)

    def test_comma_decimal_rejected(self):
        values = dict(VALID, rc="2,2")
        with self.assertRaises(ValidationError) as ctx:
            parse_form(values)
        self.assertIn("rc", ctx.exception.errors)

    def test_zero_or_negative_resistance_rejected(self):
        values = dict(VALID, r1="0", r2="-22")
        with self.assertRaises(ValidationError) as ctx:
            parse_form(values)
        self.assertIn("r1", ctx.exception.errors)
        self.assertIn("r2", ctx.exception.errors)

    def test_zero_sum_divider_rejected(self):
        values = dict(VALID, r1="0", r2="0")
        with self.assertRaises(ValidationError) as ctx:
            parse_form(values)
        self.assertIn("r1", ctx.exception.errors)

    def test_non_positive_beta_rejected(self):
        values = dict(VALID, beta="0")
        with self.assertRaises(ValidationError) as ctx:
            parse_form(values)
        self.assertIn("beta", ctx.exception.errors)

    def test_vbe_must_be_below_vcc(self):
        values = dict(VALID, vbe="12")
        with self.assertRaises(ValidationError) as ctx:
            parse_form(values)
        self.assertIn("vbe", ctx.exception.errors)

    def test_vcc_error_does_not_duplicate_vbe_error(self):
        values = dict(VALID, vcc="abc")
        with self.assertRaises(ValidationError) as ctx:
            parse_form(values)
        self.assertIn("vcc", ctx.exception.errors)
        self.assertNotIn("vbe", ctx.exception.errors)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: รันให้เห็นว่า fail**

Run: `python -m unittest discover -s tests -v`
Expected: ERROR/FAIL — `ModuleNotFoundError: No module named 'dc_bias'`

- [ ] **Step 4: เขียน `dc_bias.py` (เฉพาะส่วน input layer)**

แนวทาง: `parse_form` วนทีละฟิลด์ตาม `FIELDS = ("vcc", "r1", "r2", "rc", "re", "beta", "vbe")`
— ถ้า field หายหรือ `.strip()` ว่าง → `"กรุณากรอก {field.upper()}"`
— ถ้ามี `","` → `"ใช้จุดทศนิยม (.) แทนเครื่องหมายจุลภาค"`
— แปลง `float()` ไม่ได้ → `"ค่าของ {field.upper()} ต้องเป็นตัวเลข"`
— เก็บ error ทั้งหมดก่อน แล้วค่อย raise `ValidationError(errors)` ครั้งเดียว
— หลังแปลงครบ: `vcc > 0`, `r1/r2/rc/re > 0`, `beta > 0`, และ `0 < vbe < vcc` **เฉพาะเมื่อ `vcc` แปลงผ่านแล้ว**
— ข้อความกำกับด้วยชื่อฟิลด์ตัวใหญ่ เช่น `"R1 ต้องมากกว่า 0"`

- [ ] **Step 5: รัน tests ให้ผ่าน**

Run: `python -m unittest discover -s tests -v`
Expected: 10 tests, OK

- [ ] **Step 6: Checkpoint** — แจ้งเจ้าของ repo commit ผ่าน GitHub Desktop ด้วยข้อความ `feat: add BJT input parsing and validation`

---

### Task 2: คำนวณ DC operating point (`solve`)

**Files:**
- Modify: `dc_bias.py`
- Test: `tests/test_dc_bias.py`

**Interfaces:**
- Consumes: `BiasInput` จาก Task 1
- Produces:
  - `class Region(str, Enum)`: `ACTIVE = "active"`, `CUTOFF = "cutoff"`, `SATURATION = "saturation"`
  - `@dataclass(frozen=True) class BiasResult` fields: `vth: float, rth: float, ib: float, ic: float, ie: float, ve: float, vb: float, vc: float, vce: float` (SI: V, Ω, A), `region: Region`, `warnings: tuple[str, ...]`
  - `def solve(data: BiasInput) -> BiasResult`

- [ ] **Step 1: เขียน failing test (ค่าอ้างอิงจาก handout)**

เพิ่มใน `tests/test_dc_bias.py`:

```python
from dc_bias import Region, solve


class SolveTests(unittest.TestCase):
    def test_reference_operating_point(self):
        result = solve(parse_form(VALID))
        self.assertAlmostEqual(result.vth, 2.1639, places=4)
        self.assertAlmostEqual(result.rth, 18032.79, places=2)
        self.assertAlmostEqual(result.ib * 1e6, 12.299, places=3)
        self.assertAlmostEqual(result.ic * 1e3, 1.2299, places=4)
        self.assertAlmostEqual(result.ie * 1e3, 1.2422, places=4)
        self.assertAlmostEqual(result.ve, 1.2422, places=4)
        self.assertAlmostEqual(result.vb, 1.9422, places=4)
        self.assertAlmostEqual(result.vc, 9.2943, places=4)
        self.assertAlmostEqual(result.vce, 8.0522, places=4)
        self.assertIs(result.region, Region.ACTIVE)
        self.assertEqual(result.warnings, ())

    def test_kohm_to_ohm_scaling(self):
        result = solve(parse_form(VALID))
        self.assertAlmostEqual(result.rth, 18032.79, places=2)
```

- [ ] **Step 2: รันให้เห็นว่า fail**

Run: `python -m unittest discover -s tests -v`
Expected: FAIL — `ImportError: cannot import name 'Region'`

- [ ] **Step 3: เขียน `solve()`**

แนวทาง: แปลง `r1_ohm = data.r1 * 1000` และเดียวกันกับ r2/rc/re เป็นบรรทัดแรก
แล้วใช้สมการตาม spec ตรง ๆ: `vth`, `rth`, `ib`, `ic = beta*ib`, `ie = (beta+1)*ib`,
`ve = ie*re`, `vb = ve + vbe`, `vc = vcc - ic*rc`, `vce = vc - ve`
คืน `BiasResult(..., region=Region.ACTIVE, warnings=())` (region จริงมาใน Task 3)

- [ ] **Step 4: รัน tests ให้ผ่าน**

Run: `python -m unittest discover -s tests -v`
Expected: 12 tests, OK

- [ ] **Step 5: Checkpoint** — commit ผ่าน GitHub Desktop: `feat: calculate forward-active DC operating point`

---

### Task 3: ตรวจนอก forward-active region + warnings

**Files:**
- Modify: `dc_bias.py`
- Test: `tests/test_dc_bias.py`

**Interfaces:**
- Consumes: `solve()` จาก Task 2
- Produces: `solve()` คืน `region ∈ {ACTIVE, CUTOFF, SATURATION}` และ `warnings` เป็นภาษาไทย

- [ ] **Step 1: เขียน failing tests**

```python
class RegionTests(unittest.TestCase):
    def test_cutoff_region_warns_and_zeroes_current(self):
        values = dict(VALID, r1="470", r2="22")          # VTH ≈ 0.5366 V < VBE
        result = solve(parse_form(values))
        self.assertIs(result.region, Region.CUTOFF)
        self.assertEqual(result.ic, 0.0)
        self.assertEqual(result.ie, 0.0)
        self.assertAlmostEqual(result.vb, 0.5366, places=3)
        self.assertAlmostEqual(result.vc, 12.0, places=9)
        self.assertTrue(result.warnings)

    def test_saturation_region_warns(self):
        values = dict(VALID, rc="47")                    # IC*RC ≈ 57.8 V > VCC
        result = solve(parse_form(values))
        self.assertIs(result.region, Region.SATURATION)
        self.assertTrue(result.warnings)

    def test_negative_vce_is_never_reported_as_active(self):
        values = dict(VALID, rc="10")                    # IC*RC ≈ 12.3 V → VCE ≈ -1.54 V
        result = solve(parse_form(values))
        self.assertLess(result.vce, 0.3)
        self.assertIsNot(result.region, Region.ACTIVE)
        self.assertTrue(result.warnings)
```

- [ ] **Step 2: รันให้เห็นว่า fail**

Run: `python -m unittest discover -s tests -v -k RegionTests`
Expected: FAIL — region ยังเป็น `ACTIVE`

- [ ] **Step 3: เพิ่มกฎ region ใน `solve()`**

แนวทาง: หลังคำนวณครบแล้ว
1. ถ้า `vth <= vbe` → คืน `BiasResult` ที่ `ib=ic=ie=0`, `ve=0`, `vb=vth`, `vc=vcc`, `vce=vcc`
   พร้อม `region=CUTOFF` และ warning ว่า VTH ไม่สูงพอจะทำให้ BE forward bias (แรงดันไม่พอเปิดรอยต่อ)
2. ถ้า `vce <= 0.3` → คงค่าตามสมการ active แต่ `region=SATURATION` และ warning ว่า
   แบบจำลอง forward-active ใช้ไม่ได้ ค่าที่ได้ไม่ควรนำไปใช้
3. อื่น ๆ → `ACTIVE`, `warnings=()`

- [ ] **Step 4: รัน tests ให้ผ่าน**

Run: `python -m unittest discover -s tests -v`
Expected: 15 tests, OK

- [ ] **Step 5: Checkpoint** — commit: `feat: warn when the operating point leaves forward active`

---

### Task 4: Flask app + หน้า GET /

**Files:**
- Create: `app.py`, `templates/index.html`, `static/style.css`, `tests/test_web.py`

**Interfaces:**
- Consumes: `solve`, `parse_form`, `ValidationError` จาก Task 1–3
- Produces:
  - `app` (Flask instance ระดับโมดูล, รันด้วย `python -m flask --app app run`)
  - `DEFAULTS: dict[str, str]` — ค่าตัวอย่าง: VCC=12, R1=100, R2=22, RC=2.2, RE=1, β=100, VBE=0.70
  - template context keys: `values` (dict[str,str]), `errors` (dict[str,str]), `result` (BiasResult | None)

- [ ] **Step 1: เขียน failing test**

`tests/test_web.py`:

```python
import unittest

from app import app


class IndexPageTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_get_index_returns_form(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        for field in ("vcc", "r1", "r2", "rc", "re", "beta", "vbe"):
            self.assertIn(f'name="{field}"', body)

    def test_form_is_prefilled_with_lab_defaults(self):
        body = self.client.get("/").get_data(as_text=True)
        self.assertIn('value="12"', body)
        self.assertIn('value="100"', body)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: รันให้เห็นว่า fail**

Run: `python -m unittest discover -s tests -v`
Expected: ERROR — `ModuleNotFoundError: No module named 'app'`

- [ ] **Step 3: สร้าง `app.py` + template + CSS**

แนวทาง `app.py`: `app = Flask(__name__)`, `DEFAULTS` ตามด้านบน, route `GET /`
ส่ง `render_template("index.html", values=DEFAULTS, errors={}, result=None)`

แนวทาง `templates/index.html`: `<form method="post" action="/">` มี input 7 ช่อง
(`name` ตรงกับ key, `value="{{ values.vcc }}"`, หน่วยใน label), ปุ่ม submit
`คำนวณ DC Bias`, และ `<link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">`
ส่วนผลลัพธ์/error จะเพิ่มใน Task 5

แนวทาง `static/style.css`: grid 2 คอลัมน์สำหรับฟอร์ม, 1 คอลัมน์เมื่อ `max-width: 640px`,
ตารางผลมีเส้นตารางอ่อน, สีพื้นอ่อน อ่านง่าย

- [ ] **Step 4: รัน tests ให้ผ่าน**

Run: `python -m unittest discover -s tests -v`
Expected: 17 tests, OK

- [ ] **Step 5: ตรวจด้วยตาเปล่า**

Run: `python -m flask --app app run --debug` แล้วเปิด `http://127.0.0.1:5000/`
Expected: เห็นฟอร์ม 7 ช่องพร้อมค่าตัวอย่าง ไม่มี traceback

- [ ] **Step 6: Checkpoint** — commit: `feat: serve the DC bias input form`

---

### Task 5: POST / — แสดงผล, error, warning, region badge

**Files:**
- Modify: `app.py`, `templates/index.html`, `static/style.css`
- Test: `tests/test_web.py`

**Interfaces:**
- Consumes: `parse_form`, `solve`, `ValidationError`, `Region`
- Produces:
  - `POST /` → 200 + ผล / **400** + error รายฟิลด์
  - `REGION_LABELS: dict[Region, str]` = `{Region.ACTIVE: "Forward Active", Region.CUTOFF: "Cutoff", Region.SATURATION: "Saturation"}` ส่งเข้า template ในชื่อ `region_label`
  - template context: `values` (`request.form.to_dict()`), `errors`, `result`, `region_label`

- [ ] **Step 1: เขียน failing tests**

```python
class CalculateTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def post(self, **overrides):
        data = {"vcc": "12", "r1": "100", "r2": "22", "rc": "2.2",
                "re": "1", "beta": "100", "vbe": "0.70"}
        data.update(overrides)
        return self.client.post("/", data=data)

    def test_valid_input_renders_results(self):
        response = self.post()
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("9.294", body)          # VC
        self.assertIn("1.230", body)          # IC [mA]
        self.assertIn("8.052", body)          # VCE
        self.assertIn("Forward Active", body)

    def test_invalid_input_returns_400_with_message(self):
        response = self.post(r1="0")
        self.assertEqual(response.status_code, 400)
        body = response.get_data(as_text=True)
        self.assertIn("R1", body)
        self.assertNotIn("8.052", body)       # ไม่แสดงผลลัพธ์

    def test_empty_post_returns_400(self):
        response = self.client.post("/", data={})
        self.assertEqual(response.status_code, 400)
        self.assertIn("กรุณากรอก", response.get_data(as_text=True))

    def test_entered_value_is_escaped_in_form(self):
        response = self.post(r1="<script>alert(1)</script>")
        body = response.get_data(as_text=True)
        self.assertNotIn("<script>alert(1)</script>", body)

    def test_saturation_shows_warning(self):
        response = self.post(rc="47")
        body = response.get_data(as_text=True)
        self.assertIn("Saturation", body)
```

- [ ] **Step 2: รันให้เห็นว่า fail**

Run: `python -m unittest discover -s tests -v`
Expected: FAIL — ยังไม่มี route POST (405)

- [ ] **Step 3: เพิ่ม route POST และส่วนแสดงผลใน template**

แนวทาง `app.py`: `@app.route("/", methods=["GET", "POST"])`
— GET → เหมือน Task 4
— POST → `try: result = solve(parse_form(request.form))` แล้ว
`render_template(..., values=request.form.to_dict(), errors={}, result=result,
region_label=REGION_LABELS[result.region])`
— `except ValidationError as exc:` → `render_template(..., values=request.form.to_dict(),
  errors=exc.errors, result=None)`, `return ..., 400`

แนวทาง template: ส่วน error ใต้ input แต่ละช่อง (`errors.get('r1')`),
ตารางผลด้วย `"%.3f"|format(result.vb)` และ `"%.3f"|format(result.ic * 1000)` (mA),
`"%.2f"|format(result.ib * 1e6)` (µA), `"%.3f"|format(result.rth / 1000)` (kΩ),
badge แสดง `{{ region_label }}`, กล่อง warning วน `result.warnings` (แสดงเฉพาะเมื่อมี)

- [ ] **Step 4: รัน tests ให้ผ่าน**

Run: `python -m unittest discover -s tests -v`
Expected: 22 tests, OK

- [ ] **Step 5: ตรวจด้วยตาเปล่า**

Run: `python -m flask --app app run --debug` → กดคำนวณด้วยค่าตัวอย่าง → เห็นตารางผล
→ เปลี่ยน R1 เป็น 0 → เห็น error สีแดงและค่าเดิมยังอยู่ → เปลี่ยน RC เป็น 47 → เห็น warning

- [ ] **Step 6: Checkpoint** — commit: `feat: render DC bias results, errors and region warnings`

---

### Task 6: เอกสาร, README, AGENTS.md และพิสูจน์ A7

**Files:**
- Modify: `README.md`
- Create: `AGENTS.md`, `docs/design-note.md`, `docs/validation.md`, `docs/reflection.md`

**Interfaces:**
- Consumes: ทุกอย่างจาก Task 1–5
- Produces: repo ที่ clone แล้วรันได้ตาม README

- [ ] **Step 1: เขียน `AGENTS.md`**

เนื้อหา: กติกา 5 ข้อ — (1) ห้ามใส่สูตรฟิสิกส์ใน template หรือ `app.py`
(2) การคำนวณใหม่ทุกครั้งต้องมี test ใน `tests/test_dc_bias.py`
(3) ห้ามเพิ่ม dependency นอกจาก Flask โดยไม่แก้ `requirements.txt`
(4) UI ภาษาไทย หน่วย SI, ไม่เพิ่ม JavaScript (5) รัน `python -m unittest discover -s tests -v`
ก่อนบอกว่างานเสร็จ

- [ ] **Step 2: เขียน `docs/validation.md`**

ตาราง: อินพุต 7 ค่า | ค่าที่คำนวณมือ (แสดงสมการย่อ 1 บรรทัดต่อค่า) | ค่าที่เว็บแสดง | ต่างกันเท่าไร
พร้อม 2 เคสขอบ: cutoff (R1=470 kΩ) และ saturation (RC=47 kΩ) ระบุว่าเป็น warning ไม่ใช่ค่าที่ใช้ได้

- [ ] **Step 3: เขียน `docs/design-note.md` และ `docs/reflection.md`**

`design-note.md`: สรุป 1 หน้า — ทำไมแยก `dc_bias.py`, ทำไมเลือก server-rendered form
(อ้าง design doc), ข้อจำกัดของ forward-active model
`reflection.md`: คำถาม 4 ข้อท้าย handout (ทำไมเปิด `index.html` ตรง ๆ ไม่เท่ากับรัน Flask,
ฟอร์มส่งข้อมูลไป Python อย่างไร, แก้สมการแล้วต้องแก้ HTML ไหม, ทำไมต้องมี warning) พร้อมคำตอบย่อ

- [ ] **Step 4: อัปเดต `README.md`**

เพิ่มส่วน: ภาพรวม, วิธีติดตั้ง/รัน/ทดสอบ (คำสั่งเดียวกับ Global Constraints), โครงสร้างไฟล์,
ค่าอ้างอิง 9 ค่า และหมายเหตุข้อจำกัดของแบบจำลอง

- [ ] **Step 5: พิสูจน์ A7 ใน venv สะอาด**

```powershell
python -m venv .venv-verify
.venv-verify\Scripts\python -m pip install -r requirements.txt
.venv-verify\Scripts\python -m unittest discover -s tests -v
```

Expected: ติดตั้งสำเร็จบน Python 3.15 และ tests ผ่าน 22 ตัว
จากนั้นลบ `.venv-verify` (มี `.venv/` ใน `.gitignore` แต่ `.venv-verify` ต้องลบด้วยมือ)

- [ ] **Step 6: Checkpoint** — commit: `docs: document design, validation and run instructions`

---

## Acceptance mapping

| เกณฑ์ | Task ที่ทำให้สำเร็จ |
| --- | --- |
| A1 GET / | Task 4 |
| A2 POST / คำนวณจริง | Task 5 |
| A3 ค่าตรงกับ reference | Task 2 (+ `docs/validation.md` Task 6) |
| A4 Validation | Task 1 + Task 5 |
| A5 Warning นอก active | Task 3 + Task 5 |
| A6 Tests | Task 1, 2, 3, 5 |
| A7 Reproducibility | Task 6 |
