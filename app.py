"""Web layer — รับ HTTP แล้วเลือกว่าจะไปทาง Analytical (Lab 03) หรือ SPICE (Lab 04)

สูตรฟิสิกส์อยู่ใน dc_bias.py ข้อมูล/คำสั่ง ngspice อยู่ใน spice_engine.py
ไฟล์นี้มีหน้าที่เพียง validate เส้นทาง, เรียกโมดูลที่เหมาะสม และส่งผลให้ template
"""

from flask import Flask, render_template, request

import plots
import spice_engine
from dc_bias import Region, ValidationError, parse_form, solve_mode

app = Flask(__name__)

MODE_LABELS = {
    "divider": "Voltage Divider Bias",
    "fixed": "Fixed Bias",
    "emitter": "Emitter Bias",
}

ANALYSIS_LABELS = {
    "dc": "DC operating point (.op)",
    "ac": "AC frequency response (.ac)",
    "transient": "Transient response (.tran)",
}

# ค่าเริ่มต้นของแต่ละโหมด (R1/R2/RC/RE เป็น kΩ, RB เป็น MΩ)
DEFAULTS = {
    "divider": {
        "vcc": "12", "r1": "100", "r2": "22", "rc": "2.2",
        "re": "1", "beta": "100", "vbe": "0.70",
    },
    "fixed": {
        "vcc": "12", "rb": "1", "rc": "2.2",
        "beta": "100", "vbe": "0.70",
    },
    "emitter": {
        "vcc": "12", "rb": "1", "re": "1", "rc": "2.2",
        "beta": "100", "vbe": "0.70",
    },
}

# ชื่อที่แสดงบนหน้าเว็บ (ชื่อ enum ภายในเป็นตัวพิมพ์ใหญ่ ไม่เหมาะกับผู้อ่าน)
REGION_LABELS = {
    Region.ACTIVE: "Forward Active",
    Region.CUTOFF: "Cutoff",
    Region.SATURATION: "Saturation",
}


def render_page(
    values,
    mode="divider",
    errors=None,
    result=None,
    status=200,
    analysis="dc",
    spice_values=None,
    spice_errors=None,
    sim_result=None,
    sim_error=None,
    sim_log="",
):
    """render หน้าเดียวสำหรับ Analytical และ Simulator โดยแยกป้ายที่มาชัดเจน"""
    gain_chart = plots.gain_svg(sim_result.ac) if sim_result and sim_result.ac else ""
    phase_chart = plots.phase_svg(sim_result.ac) if sim_result and sim_result.ac else ""
    wave_chart = (plots.wave_svg(sim_result.transient)
                  if sim_result and sim_result.transient else "")
    body = render_template(
        "index.html",
        values=values,
        mode=mode,
        mode_labels=MODE_LABELS,
        errors=errors or {},
        result=result,
        region_label=REGION_LABELS[result.region] if result else None,
        analysis=analysis,
        analysis_labels=ANALYSIS_LABELS,
        spice_values=spice_values or spice_engine.SPICE_DEFAULTS,
        spice_errors=spice_errors or {},
        sim_result=sim_result,
        sim_error=sim_error,
        sim_log=sim_log,
        gain_chart=gain_chart,
        phase_chart=phase_chart,
        wave_chart=wave_chart,
    )
    return body, status


def handle_spice(values):
    """เส้นทาง Lab 04: ตรวจโหมด → เรียก ngspice → ส่งผล/ความผิดพลาดจริง"""
    analysis = values.get("analysis", "dc")
    action = values.get("action", "run")

    if action == "change":
        if analysis not in spice_engine.ANALYSES:
            return render_page(
                DEFAULTS["divider"], "divider", analysis=analysis,
                spice_values=values,
                spice_errors={"analysis": "โหมดการวิเคราะห์ไม่ถูกต้อง"}, status=400,
            )
        fresh = dict(spice_engine.SPICE_DEFAULTS)
        for field in ("vcc", "r1", "r2", "rc", "re", "rl", "cin", "cout",
                      "amplitude", "frequency"):
            if field in values and str(values[field]).strip():
                fresh[field] = values[field]
        return render_page(DEFAULTS["divider"], "divider",
                           analysis=analysis, spice_values=fresh)

    try:
        sim_result = spice_engine.run_simulation(analysis, values)
    except spice_engine.SpiceValidationError as exc:
        return render_page(
            DEFAULTS["divider"], "divider", analysis=analysis, spice_values=values,
            spice_errors=exc.errors, status=400,
        )
    except spice_engine.SpiceRunError as exc:
        return render_page(
            DEFAULTS["divider"], "divider", analysis=analysis, spice_values=values,
            sim_error=str(exc), sim_log=exc.log, status=400,
        )

    return render_page(DEFAULTS["divider"], "divider", analysis=analysis,
                       spice_values=values, sim_result=sim_result)


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        return render_page(DEFAULTS["divider"], "divider")

    values = request.form.to_dict()
    if values.get("form") == "spice":
        return handle_spice(values)

    mode = values.get("mode", "divider")
    action = values.get("action", "calculate")

    # เปลี่ยนโหมด: โหลดฟอร์มใหม่ด้วยช่องที่โหมดนั้นใช้ ไม่แสดงผลคำนวณเก่า
    if action == "change":
        if mode not in DEFAULTS:
            return render_page(
                values, mode, errors={"mode": "โหมดวงจรไม่ถูกต้อง"}, status=400
            )
        fresh = dict(DEFAULTS[mode])
        for field in ("vcc", "rc", "beta", "vbe"):
            if field in values and str(values[field]).strip():
                fresh[field] = values[field]
        return render_page(fresh, mode)

    try:
        result = solve_mode(mode, parse_form(values, mode))
    except ValidationError as exc:
        # 400 = คำขอไม่ถูกต้อง และคงค่าที่กรอกไว้ให้ผู้ใช้แก้
        # result=None จึงไม่มีโอกาสโชว์ผลรอบก่อนเป็นผลของรอบนี้
        return render_page(values, mode, errors=exc.errors, status=400)

    return render_page(values, mode, result=result)
