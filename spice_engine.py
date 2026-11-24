"""Lab 04 — ngspice adapter สำหรับวงจร CE Voltage Divider อ้างอิง

หน้าที่ของไฟล์นี้คือแปลงค่าที่ตรวจแล้วเป็น netlist, เรียก ngspice ด้วย subprocess
(type list, ไม่ใช้ shell=True, มี timeout, แยก working directory ต่อรอบ) และอ่าน
ผลจริงจาก stdout / ไฟล์ที่ ngspice เขียนขึ้นมาเท่านั้น ไม่มีค่าจำลองฝังไว้ในโค้ด

สมการ DC แบบประมาณยังอยู่ใน dc_bias.py เหมือน Lab 03 — ไฟล์นี้ไม่แตะต้องมัน
"""

from __future__ import annotations

import math
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping

ANALYSES = ("dc", "ac", "transient")
MODEL_NAME = "QNPN"
BJT_MODEL = ".model QNPN NPN(IS=1E-14 BF=100 VAF=100 CJE=4P CJC=3P TF=0.3N)"

# หน่วยที่ผู้ใช้กรอก: kΩ, µF, mV peak, kHz — แปลงเป็น SI ใน parse_spice_form()
SPICE_DEFAULTS = {
    "vcc": "12", "r1": "100", "r2": "22", "rc": "2.2", "re": "1",
    "rl": "10", "cin": "10", "cout": "10", "amplitude": "10", "frequency": "1",
}
SPICE_FIELDS = {
    "dc": ("vcc", "r1", "r2", "rc", "re", "rl", "cin", "cout"),
    "ac": ("vcc", "r1", "r2", "rc", "re", "rl", "cin", "cout",
           "amplitude", "frequency"),
    "transient": ("vcc", "r1", "r2", "rc", "re", "rl", "cin", "cout",
                  "amplitude", "frequency"),
}


class SpiceValidationError(ValueError):
    """อินพุตไม่ถูกต้อง เก็บข้อความแยกตามฟิลด์เพื่อโชว์ในฟอร์ม"""

    def __init__(self, errors: dict[str, str]) -> None:
        super().__init__("ข้อมูลจำลองไม่ถูกต้อง")
        self.errors = dict(errors)


class SpiceRunError(RuntimeError):
    """ngspice ไม่พร้อม / รันไม่สำเร็จ / ผลว่าง — ห้ามแปลเป็น Success"""

    def __init__(self, message: str, log: str = "") -> None:
        super().__init__(message)
        self.log = log


@dataclass(frozen=True)
class SpiceInput:
    """ค่าด้านไฟฟ้าในหน่วย SI: Ω, F, V, Hz"""

    vcc: float
    r1: float
    r2: float
    rc: float
    re: float
    rl: float
    c_in: float
    c_out: float
    amplitude: float = 0.0
    frequency: float = 0.0


@dataclass(frozen=True)
class DcPoint:
    """DC operating point จาก ngspice [V, A]"""

    vb: float
    ve: float
    vc: float
    vce: float
    ic: float
    ib: float
    ie: float


@dataclass(frozen=True)
class AcPoint:
    """จุดBode หนึ่งความถี่: gain จาก |Vout/Vin| และเฟส [dB, deg]"""

    frequency_hz: float
    gain_db: float
    phase_deg: float


@dataclass(frozen=True)
class TimePoint:
    """จุด waveform หนึ่งช่วงเวลา [ms, V]"""

    time_ms: float
    vin_v: float
    vout_v: float


@dataclass(frozen=True)
class SimulationResult:
    """ผลรอบเดียว พร้อมที่มา (netlist, log, engine, model)"""

    analysis: str
    engine: str
    model: str
    status: str = "success"
    netlist: str = ""
    log: str = ""
    dc: DcPoint | None = None
    ac: tuple[AcPoint, ...] = ()
    transient: tuple[TimePoint, ...] = ()
    ac_summary: dict[str, object] = field(default_factory=dict)
    transient_summary: dict[str, object] = field(default_factory=dict)
    warnings: tuple[str, ...] = ()

    @property
    def point_count(self) -> int:
        if self.dc is not None:
            return 7
        return len(self.ac) or len(self.transient)


def _to_number(raw: object) -> float:
    text = str(raw).strip()
    if not text or "," in text:
        raise ValueError("รูปแบบตัวเลขไม่ถูกต้อง")
    number = float(text)  # ตัวเลขที่ไม่ใช่ float จะ raise ที่นี่
    if not math.isfinite(number):
        raise ValueError("ค่าต้องเป็นตัวเลขที่จำกัด")
    return number


def parse_spice_form(values: Mapping[str, object], analysis: str) -> SpiceInput:
    """ตรวจเฉพาะฟิลด์ที่ analysis นั้นใช้ แล้วแปลงเป็น SI

    ข้อความจากฟอร์มไม่มีทางไปถึง netlist โดยตรง เพราะทุกค่าผ่าน float() ก่อน
    """
    if analysis not in SPICE_FIELDS:
        raise SpiceValidationError({"analysis": "โหมดการวิเคราะห์ไม่ถูกต้อง"})

    errors: dict[str, str] = {}
    numbers: dict[str, float] = {}
    for name in SPICE_FIELDS[analysis]:
        raw = values.get(name)
        if raw is None or str(raw).strip() == "":
            errors[name] = f"กรุณากรอก {name.upper()}"
            continue
        try:
            numbers[name] = _to_number(raw)
        except ValueError:
            errors[name] = f"ค่าของ {name.upper()} ต้องเป็นตัวเลข (ใช้จุดทศนิยม)"

    for name in ("vcc", "r1", "r2", "rc", "re", "rl", "cin", "cout",
                 "amplitude", "frequency"):
        if name in numbers and numbers[name] <= 0:
            errors[name] = f"{name.upper()} ต้องมากกว่า 0"

    if "amplitude" in numbers and "vcc" in numbers:
        if "amplitude" not in errors and numbers["amplitude"] > numbers["vcc"] * 1000:
            errors["amplitude"] = "AMPLITUDE ต้องไม่เกิน VCC (หน่วย mV)"
    if "frequency" in numbers and "frequency" not in errors:
        frequency_hz = numbers["frequency"] * 1000.0
        if not 10.0 <= frequency_hz <= 10_000_000.0:
            errors["frequency"] = "FREQUENCY ต้องอยู่ระหว่าง 0.01–10000 kHz (10 Hz–10 MHz)"

    if errors:
        raise SpiceValidationError(errors)

    return SpiceInput(
        vcc=numbers["vcc"],
        r1=numbers["r1"] * 1000.0,
        r2=numbers["r2"] * 1000.0,
        rc=numbers["rc"] * 1000.0,
        re=numbers["re"] * 1000.0,
        rl=numbers["rl"] * 1000.0,
        c_in=numbers["cin"] * 1e-6,
        c_out=numbers["cout"] * 1e-6,
        amplitude=numbers.get("amplitude", 0.0) / 1000.0,
        frequency=numbers.get("frequency", 0.0) * 1000.0,
    )


def _resistance(ohm: float) -> str:
    for scale, suffix in ((1e6, "meg"), (1e3, "k"), (1.0, "")):
        if ohm >= scale:
            return f"{ohm / scale:.6g}{suffix}"
    return f"{ohm:.6g}"


def _capacitance(farad: float) -> str:
    for scale, suffix in ((1.0, ""), (1e-3, "m"), (1e-6, "u"),
                          (1e-9, "n"), (1e-12, "p")):
        if farad >= scale:
            return f"{farad / scale:.6g}{suffix}"
    return f"{farad:.6g}"


def _seconds(seconds: float) -> str:
    for scale, suffix in ((1.0, ""), (1e-3, "m"), (1e-6, "u"),
                          (1e-9, "n"), (1e-12, "p")):
        if seconds >= scale:
            return f"{seconds / scale:.6g}{suffix}"
    return f"{seconds:.6g}"


def build_netlist(analysis: str, data: SpiceInput) -> str:
    """สร้าง netlist ที่ตรวจได้จากค่าตัวเลขเท่านั้น (ไม่มีข้อความจากผู้ใช้)"""
    if analysis not in ANALYSES:
        raise SpiceValidationError({"analysis": "โหมดการวิเคราะห์ไม่ถูกต้อง"})

    lines = [
        f"* CE voltage-divider amplifier - Lab 04 - {analysis}",
        f"VCC VCC 0 DC {data.vcc:.6g}",
        f"R1 VCC base {_resistance(data.r1)}",
        f"R2 base 0 {_resistance(data.r2)}",
        f"RC VCC collector {_resistance(data.rc)}",
        f"RE emitter 0 {_resistance(data.re)}",
        f"Q1 collector base emitter {MODEL_NAME}",
        "VIN src 0 DC 0 "
        f"AC {data.amplitude:.8g} SIN(0 {data.amplitude:.8g} {data.frequency:.8g})",
        f"CIN src base {_capacitance(data.c_in)}",
        f"COUT collector out {_capacitance(data.c_out)}",
        f"RL out 0 {_resistance(data.rl)}",
        BJT_MODEL,
        ".options RELTOL=1e-4",
        ".control",
    ]

    if analysis == "dc":
        lines += [
            "op",
            "print V(base) V(emitter) V(collector) V(base)-V(emitter) "
            "@q1[ic] @q1[ib] @q1[ie]",
        ]
    elif analysis == "ac":
        lines += [
            "ac dec 20 1 1G",
            # vp() ออก radian ตามค่าเริ่มต้น → บังคับเป็นองศาก่อนเขียนไฟล์
            "set units=degrees",
            # wr_singlescale: column แรกคือ frequency, ถัดไปคือข้อมูล 4 column
            "set wr_singlescale",
            "set wr_vecnames",
            "wrdata ac.csv vm(out) vp(out) vm(src) vp(src)",
        ]
    else:
        period = 1.0 / data.frequency
        t_step = _seconds(period / 100.0)
        t_stop = _seconds(5.0 * period)
        lines += [
            f"tran {t_step} {t_stop} 0 {t_step}",
            "set wr_singlescale",
            "set wr_vecnames",
            "wrdata tran.csv v(src) v(out)",
        ]

    lines += [".endc", ".end"]
    return "\n".join(lines) + "\n"


_DC_PATTERN = re.compile(
    r"^\s*(.+?)\s*=\s*([+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?)\s*$"
)


def parse_dc_print(stdout: str) -> DcPoint:
    """อ่านบรรทัด `name = value` ที่ ngspice พิมพ์จากคำสั่ง print ใน .control"""
    values: dict[str, float] = {}
    for line in (stdout or "").splitlines():
        match = _DC_PATTERN.match(line)
        if match:
            values[match.group(1).strip().lower()] = float(match.group(2))

    needed = ("v(base)", "v(emitter)", "v(collector)", "@q1[ic]", "@q1[ib]")
    missing = [name for name in needed if name not in values]
    if missing:
        raise SpiceRunError(
            "ผล .op จาก ngspice ไม่ครบถ้วน: " + ", ".join(missing), stdout or ""
        )

    vb = values["v(base)"]
    ve = values["v(emitter)"]
    vc = values["v(collector)"]
    return DcPoint(
        vb=vb,
        ve=ve,
        vc=vc,
        vce=vc - ve,
        ic=abs(values["@q1[ic]"]),
        ib=abs(values["@q1[ib]"]),
        ie=abs(values.get("@q1[ie]", -(values["@q1[ic]"] + values["@q1[ib]"]))),
    )


def parse_wrdata(text: str, vectors: int) -> tuple[tuple[float, ...], ...]:
    """อ่านผล `wrdata` หลัง `set wr_singlescale` / `set wr_vecnames`

    column แรกคือ scale (frequency หรือ time) ตามด้วยข้อมูลอีก `vectors` column
    บรรทัดหัวตารางที่เป็นชื่อเวกเตอร์จะถูกข้าม ไม่มีข้อมูลจริง → คืน empty tuple
    """
    rows: list[tuple[float, ...]] = []
    for line in (text or "").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = stripped.split()
        if not rows:
            try:
                float(parts[0])
            except ValueError:
                continue  # บรรทัดหัวตารางจาก set wr_vecnames
        if len(parts) < vectors + 1:
            raise SpiceRunError("ข้อมูลจาก ngspice ไม่ครบตามจำนวนเวกเตอร์", text)
        try:
            rows.append(tuple(float(part) for part in parts[:vectors + 1]))
        except ValueError as exc:
            raise SpiceRunError("ข้อมูลจาก ngspice ไม่ใช่ตัวเลข", text) from exc
    return tuple(rows)


def _normalize_phase(degrees: float) -> float:
    phase = (degrees + 180.0) % 360.0 - 180.0
    return 180.0 if phase <= -180.0 else phase


def ac_points(rows: tuple[tuple[float, ...], ...]) -> tuple[AcPoint, ...]:
    """row = (frequency, |Vout|, phase Vout, |Vin|, phase Vin) จาก wrdata"""
    points: list[AcPoint] = []
    for row in rows:
        frequency, vout, pout, vin, pin = row[:5]
        gain = vout / vin if vin else 0.0
        gain_db = 20.0 * math.log10(gain) if gain > 0 else -200.0
        points.append(AcPoint(frequency, gain_db, _normalize_phase(pout - pin)))
    return tuple(points)


def ac_summary(points: tuple[AcPoint, ...]) -> dict[str, object]:
    """หา gain สูงสุดและจุดตัด -3 dB แบบ interpolate บน logarithms ของความถี่"""
    if not points:
        return {"gain_mid_db": 0.0, "phase_mid_deg": 0.0,
                "f_low": None, "f_high": None,
                "cutoff": "not determined in sweep range (empty output)"}

    peak = max(points, key=lambda point: point.gain_db)
    target = peak.gain_db - 3.0103
    f_low: float | None = None
    f_high: float | None = None

    def crossing(first: AcPoint, second: AcPoint) -> float | None:
        span = second.gain_db - first.gain_db
        if span == 0:
            return None
        ratio = (target - first.gain_db) / span
        if not 0.0 <= ratio <= 1.0:
            return None
        return math.exp(
            math.log(first.frequency_hz)
            + ratio * (math.log(second.frequency_hz) - math.log(first.frequency_hz))
        )

    for index in range(len(points) - 1):
        before, after = points[index], points[index + 1]
        if before.gain_db < target <= after.gain_db and f_low is None:
            f_low = crossing(before, after)
        if before.gain_db >= target > after.gain_db and f_high is None:
            f_high = crossing(before, after)

    if f_low is not None and f_high is not None:
        cutoff = f"fL ≈ {f_low:.3g} Hz · fH ≈ {f_high:.3g} Hz (-3 dB)"
    else:
        cutoff = "not determined in sweep range"
    return {
        "gain_mid_db": peak.gain_db,
        "phase_mid_deg": peak.phase_deg,
        "f_low": f_low,
        "f_high": f_high,
        "cutoff": cutoff,
    }


def transient_points(rows: tuple[tuple[float, ...], ...]) -> tuple[TimePoint, ...]:
    return tuple(TimePoint(row[0] * 1000.0, row[1], row[2]) for row in rows)


def transient_summary(points: tuple[TimePoint, ...]) -> dict[str, object]:
    """วัด amplitude และทิศทางเฟสจากข้อมูลจริงช่วงท้ายของ waveform"""
    if len(points) < 4:
        return {"vin_peak_mv": 0.0, "vout_peak_mv": 0.0,
                "phase_relation": "undetermined", "span_ms": 0.0}
    tail = points[max(0, int(len(points) * 0.6)):]
    vin = [point.vin_v for point in tail]
    vout = [point.vout_v for point in tail]
    vin_peak = (max(vin) - min(vin)) / 2.0 * 1000.0
    vout_peak = (max(vout) - min(vout)) / 2.0 * 1000.0
    mean_vin = sum(vin) / len(vin)
    mean_vout = sum(vout) / len(vout)
    products = sum((a - mean_vin) * (b - mean_vout) for a, b in zip(vin, vout))
    if abs(products) < 1e-12:
        relation = "undetermined"
    else:
        relation = "inverted" if products < 0 else "non-inverted"
    return {
        "vin_peak_mv": vin_peak,
        "vout_peak_mv": vout_peak,
        "phase_relation": relation,
        "span_ms": tail[-1].time_ms - tail[0].time_ms,
    }


def find_ngspice() -> str | None:
    """หา executable จาก env → PATH → ไบนารีที่แนบกับโปรเจกต์"""
    candidates = [
        os.environ.get("NGSPICE_PATH"),
        shutil.which("ngspice"),
        shutil.which("ngspice_con"),
        str(Path(__file__).parent / "tools" / "ngspice" / "Spice64" / "bin"
            / "ngspice_con.exe"),
        str(Path(__file__).parent / "tools" / "ngspice" / "Spice64" / "bin"
            / "ngspice.exe"),
    ]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return str(candidate)
    return None


def _engine_version(executable: str, cwd: str) -> str:
    try:
        done = subprocess.run(
            [executable, "-v"], cwd=cwd, capture_output=True, text=True, timeout=5
        )
        match = re.search(r"ngspice-([\w.]+)", done.stdout or "")
        return "ngspice-" + match.group(1) if match else "ngspice"
    except (OSError, subprocess.SubprocessError):
        return "ngspice"


def run_simulation(
    analysis: str,
    values: Mapping[str, object],
    executable: str | None = None,
    timeout: float = 20.0,
) -> SimulationResult:
    """รันจริง 1 รอบ คืน SimulationResult หรือ raise SpiceRunError เท่านั้น"""
    data = parse_spice_form(values, analysis)
    exe = executable or find_ngspice()
    if not exe:
        raise SpiceRunError(
            "ไม่พบ ngspice ให้รัน: ตั้ง NGSPICE_PATH หรือติดตั้ง ngspice ก่อน"
        )
    netlist = build_netlist(analysis, data)

    with tempfile.TemporaryDirectory(prefix="ce_spice_") as workdir:
        (Path(workdir) / "circuit.cir").write_text(netlist, encoding="utf-8")
        try:
            done = subprocess.run(
                [exe, "-b", "circuit.cir"], cwd=workdir,
                capture_output=True, text=True, timeout=timeout, shell=False,
            )
        except FileNotFoundError as exc:
            raise SpiceRunError("ไม่พบ ngspice executable ที่ระบุ") from exc
        except subprocess.TimeoutExpired as exc:
            raise SpiceRunError(f"ngspice หมดเวลา ({timeout:g} s)") from exc
        except OSError as exc:
            raise SpiceRunError(f"เรียก ngspice ไม่ได้: {exc}") from exc

        log = ((done.stdout or "") + "\n" + (done.stderr or "")).strip()
        if done.returncode != 0:
            raise SpiceRunError(
                f"ngspice run failed (exit {done.returncode}): "
                + (log[-400:] or "ไม่มีข้อความจาก solver"),
                log,
            )
        # ngspice บางกรณีพิมพ์ Error: แล้ว exit 0 — ต้องไม่แปลเป็น Success
        error_match = re.search(r"(?:^|\n)\s*(?:Error|Fatal error)\s*:", log,
                                re.IGNORECASE)
        if error_match:
            raise SpiceRunError(
                "ngspice report error: " + log[error_match.start():][:400].strip(),
                log,
            )

        engine = _engine_version(exe, workdir)
        result = SimulationResult(
            analysis=analysis, engine=engine,
            model=f"{MODEL_NAME} (IS=1E-14 BF=100 VAF=100 CJE=4P CJC=3P TF=0.3N)",
            netlist=netlist, log=log,
        )

        if analysis == "dc":
            point = parse_dc_print(done.stdout or "")
            warnings: list[str] = []
            if point.vce <= 0.2:
                warnings.append("VCE จาก ngspice ต่ำมาก อาจอยู่ในช่วง saturation")
            if point.ib <= 0:
                warnings.append("IB จาก ngspice ไม่มากกว่าศูนย์ อาจอยู่ในช่วง cutoff")
            return SimulationResult(
                **{**result.__dict__, "dc": point, "warnings": tuple(warnings)}
            )

        filename = "ac.csv" if analysis == "ac" else "tran.csv"
        output = Path(workdir) / filename
        if not output.is_file():
            raise SpiceRunError(f"ngspice ไม่สร้างไฟล์ผล {filename}", log)
        text = output.read_text(encoding="utf-8", errors="replace")
        rows = parse_wrdata(text, 4 if analysis == "ac" else 2)
        if not rows:
            raise SpiceRunError(f"ไฟล์ผล {filename} ว่างเปล่า", log)

        if analysis == "ac":
            points = ac_points(rows)
            return SimulationResult(
                **{**result.__dict__, "ac": points, "ac_summary": ac_summary(points)}
            )
        points_time = transient_points(rows)
        return SimulationResult(
            **{**result.__dict__, "transient": points_time,
               "transient_summary": transient_summary(points_time)}
        )
