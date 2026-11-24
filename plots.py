"""การนำจุดข้อมูลที่ ngspice ส่งมาไปวาดเป็น SVG (เฉพาะการแสดงผล)

ไม่มีสมการฟิสิกส์ในไฟล์นี้ — มีแต่การแปลงสเกลเพื่อวาดแกนและเส้นกราฟ
ไฟล์นี้ไม่สร้างข้อมูลขึ้นมาเอง ถ้าไม่มีจุดข้อมูลจะแสดงข้อความแทน
"""

from __future__ import annotations

import math
from typing import Sequence

from spice_engine import AcPoint, TimePoint

_WIDTH = 680
_HEIGHT = 300
_LEFT = 68
_RIGHT = 48
_TOP = 26
_BOTTOM = 56
_PLOT_W = _WIDTH - _LEFT - _RIGHT
_PLOT_H = _HEIGHT - _TOP - _BOTTOM


def _frame(title: str) -> list[str]:
    return [
        f'<svg class="plot" viewBox="0 0 {_WIDTH} {_HEIGHT}" '
        'xmlns="http://www.w3.org/2000/svg" role="img" '
        f'aria-label="{title}">',
        f"<title>{title}</title>",
    ]


def _empty(title: str) -> str:
    svg = _frame(title)
    svg.append(
        f'<text x="{_WIDTH / 2:.0f}" y="{_HEIGHT / 2:.0f}" '
        'text-anchor="middle" class="plot-empty">ไม่มีข้อมูลจากการจำลอง</text>'
    )
    svg.append("</svg>")
    return "\n".join(svg)


def _polyline(points: Sequence[tuple[float, float]], css_class: str) -> str:
    coords = " ".join(f"{x:.2f},{y:.2f}" for x, y in points)
    return f'<polyline class="{css_class}" points="{coords}" />'


def _axes(svg: list[str], x_label: str, y_label: str,
          x_min: str, x_max: str, y_min: str, y_max: str,
          y_tick_class: str = "", y_mid: str | None = None) -> None:
    x0, x1 = _LEFT, _WIDTH - _RIGHT
    y0, y1 = _TOP, _HEIGHT - _BOTTOM
    tick_class = f"axis-label {y_tick_class}".strip()
    svg += [
        f'<line class="axis" x1="{x0}" y1="{y1}" x2="{x1}" y2="{y1}" />',
        f'<line class="axis" x1="{x0}" y1="{y0}" x2="{x0}" y2="{y1}" />',
        f'<text class="axis-label" x="{x0}" y="{y1 + 34}">{x_min}</text>',
        f'<text class="axis-label" x="{x1}" y="{y1 + 34}" text-anchor="end">{x_max}</text>',
        f'<text class="axis-title" x="{(x0 + x1) / 2:.0f}" y="{y1 + 42}" '
        f'text-anchor="middle">{x_label}</text>',
        f'<text class="{tick_class}" x="{x0 - 8}" y="{y0 + 8}" '
        f'text-anchor="end">{y_max}</text>',
        f'<text class="{tick_class}" x="{x0 - 8}" y="{y1}" '
        f'text-anchor="end">{y_min}</text>',
        f'<text class="axis-title" transform="translate(14 {(y0 + y1) / 2:.0f}) '
        f'rotate(-90)" text-anchor="middle">{y_label}</text>',
    ]
    if y_mid is not None:
        svg.append(
            f'<text class="{tick_class}" x="{x0 - 8}" '
            f'y="{(y0 + y1) / 2 + 4:.0f}" text-anchor="end">{y_mid}</text>'
        )


def _ac_prep(points: Sequence[AcPoint]):
    frequencies = [max(point.frequency_hz, 1e-12) for point in points]
    log_f = [math.log10(value) for value in frequencies]
    log_min, log_max = min(log_f), max(log_f)
    if log_max == log_min:
        log_min -= 1.0
        log_max += 1.0
    return frequencies, log_f, log_min, log_max


def _x_log(log_value: float, log_min: float, log_max: float) -> float:
    return _LEFT + (log_value - log_min) / (log_max - log_min) * _PLOT_W


def _phase_axis(svg: list[str]) -> None:
    """แกนขวาสำหรับ phase [deg] — เส้น phase ใช้สเกล −180…180 คนละสเกลกับ gain"""
    x = _WIDTH - _RIGHT
    y0, y1 = _TOP, _HEIGHT - _BOTTOM
    svg += [
        f'<line class="axis phase-axis" x1="{x}" y1="{y0}" x2="{x}" y2="{y1}" />',
        f'<text class="axis-label phase-label" x="{x + 8}" y="{y0 + 8}">180</text>',
        f'<text class="axis-label phase-label" x="{x + 8}" y="{(y0 + y1) / 2 + 4:.0f}">0</text>',
        f'<text class="axis-label phase-label" x="{x + 8}" y="{y1}">-180</text>',
        f'<text class="axis-title phase-title" '
        f'transform="translate({_WIDTH - 8} {(y0 + y1) / 2:.0f}) rotate(90)" '
        'text-anchor="middle">Phase [deg]</text>',
    ]


def bode_svg(points: Sequence[AcPoint]) -> str:
    if len(points) < 2:
        return _empty("Bode plot — ไม่มีข้อมูล")

    frequencies = [max(point.frequency_hz, 1e-12) for point in points]
    log_f = [math.log10(value) for value in frequencies]
    log_min, log_max = min(log_f), max(log_f)
    if log_max == log_min:
        log_min -= 1.0
        log_max += 1.0

    gains = [point.gain_db for point in points]
    gain_min, gain_max = min(gains), max(gains)
    if gain_max == gain_min:
        gain_min -= 1.0
        gain_max += 1.0
    pad = (gain_max - gain_min) * 0.08
    gain_min -= pad
    gain_max += pad

    def x_of(log_value: float) -> float:
        return _LEFT + (log_value - log_min) / (log_max - log_min) * _PLOT_W

    def y_gain(value: float) -> float:
        return _TOP + (gain_max - value) / (gain_max - gain_min) * _PLOT_H

    def y_phase(value: float) -> float:
        return _TOP + (180.0 - value) / 360.0 * _PLOT_H

    gain_line = [(
        x_of(current), y_gain(point.gain_db)
    ) for current, point in zip(log_f, points)]
    phase_line = [(
        x_of(current), y_phase(point.phase_deg)
    ) for current, point in zip(log_f, points)]

    svg = _frame("Bode plot — Gain [dB] และ Phase [deg] จาก ngspice")
    _axes(
        svg, "Frequency [Hz] (log)", "Gain [dB]",
        f"{frequencies[0]:.3g}", f"{frequencies[-1]:.3g}",
        f"{gain_min + pad:.1f}", f"{gain_max - pad:.1f}",
    )
    _phase_axis(svg)
    svg += [
        _polyline(phase_line, "phase"),
        _polyline(gain_line, "gain"),
        '<text class="legend gain-text" x="470" y="18">Gain [dB]</text>',
        f'<text class="legend phase-text" x="{_WIDTH - _RIGHT}" y="18" '
        'text-anchor="end">Phase [deg]</text>',
    ]
    svg.append("</svg>")
    return "\n".join(svg)


def gain_svg(points: Sequence[AcPoint]) -> str:
    """กราฟ Gain [dB] แยกต่างหาก — แกนซ้ายเป็น gain เพียงเส้นเดียว"""
    if len(points) < 2:
        return _empty("Gain [dB] — ไม่มีข้อมูล")

    frequencies, log_f, log_min, log_max = _ac_prep(points)
    gains = [point.gain_db for point in points]
    gain_min, gain_max = min(gains), max(gains)
    if gain_max == gain_min:
        gain_min -= 1.0
        gain_max += 1.0
    pad = (gain_max - gain_min) * 0.08
    gain_min -= pad
    gain_max += pad

    line = [(
        _x_log(current, log_min, log_max),
        _TOP + (gain_max - point.gain_db) / (gain_max - gain_min) * _PLOT_H,
    ) for current, point in zip(log_f, points)]

    svg = _frame("Gain [dB] จาก ngspice")
    _axes(
        svg, "Frequency [Hz] (log)", "Gain [dB]",
        f"{frequencies[0]:.3g}", f"{frequencies[-1]:.3g}",
        f"{gain_min + pad:.1f}", f"{gain_max - pad:.1f}",
    )
    svg += [
        _polyline(line, "gain"),
        f'<text class="legend gain-text" x="{_WIDTH - _RIGHT}" y="18" '
        'text-anchor="end">Gain [dB]</text>',
    ]
    svg.append("</svg>")
    return "\n".join(svg)


def phase_svg(points: Sequence[AcPoint]) -> str:
    """กราฟ Phase [deg] แยกต่างหาก — ใช้สเกล −180…180 ของตัวเอง"""
    if len(points) < 2:
        return _empty("Phase [deg] — ไม่มีข้อมูล")

    frequencies, log_f, log_min, log_max = _ac_prep(points)
    line = [(
        _x_log(current, log_min, log_max),
        _TOP + (180.0 - point.phase_deg) / 360.0 * _PLOT_H,
    ) for current, point in zip(log_f, points)]

    svg = _frame("Phase [deg] จาก ngspice")
    _axes(
        svg, "Frequency [Hz] (log)", "Phase [deg]",
        f"{frequencies[0]:.3g}", f"{frequencies[-1]:.3g}",
        "-180", "180", y_tick_class="phase-label", y_mid="0",
    )
    svg += [
        _polyline(line, "phase"),
        f'<text class="legend phase-text" x="{_WIDTH - _RIGHT}" y="18" '
        'text-anchor="end">Phase [deg]</text>',
    ]
    svg.append("</svg>")
    return "\n".join(svg)


def wave_svg(points: Sequence[TimePoint]) -> str:
    if len(points) < 2:
        return _empty("Waveform — ไม่มีข้อมูล")

    times = [point.time_ms for point in points]
    voltages = [value for point in points for value in (point.vin_v, point.vout_v)]
    time_min, time_max = min(times), max(times)
    if time_max == time_min:
        time_min -= 1.0
        time_max += 1.0
    v_min, v_max = min(voltages), max(voltages)
    if v_max == v_min:
        v_min -= 0.001
        v_max += 0.001
    pad = (v_max - v_min) * 0.10
    v_min -= pad
    v_max += pad

    def x_of(value: float) -> float:
        return _LEFT + (value - time_min) / (time_max - time_min) * _PLOT_W

    def y_of(value: float) -> float:
        return _TOP + (v_max - value) / (v_max - v_min) * _PLOT_H

    vin_line = [(x_of(point.time_ms), y_of(point.vin_v)) for point in points]
    vout_line = [(x_of(point.time_ms), y_of(point.vout_v)) for point in points]

    svg = _frame("Transient waveform — Vin และ Vout จาก ngspice")
    _axes(
        svg, "Time [ms]", "Voltage [V]",
        f"{time_min:.3f}", f"{time_max:.3f}",
        f"{v_min + pad:.3f}", f"{v_max - pad:.3f}",
    )
    svg += [
        _polyline(vin_line, "vin"),
        _polyline(vout_line, "vout"),
        '<text class="legend vin-text" x="470" y="18">Vin</text>',
        f'<text class="legend vout-text" x="{_WIDTH - _RIGHT}" y="18" '
        'text-anchor="end">Vout</text>',
    ]
    svg.append("</svg>")
    return "\n".join(svg)
