"""การคำนวณ DC Bias ของ BJT Common-Emitter แบบ Voltage-Divider

โมดูลนี้เป็น "ชั้นวิศวกรรม" ที่ไม่รู้จัก Flask, HTTP หรือ HTML เลย
จึงนำไปทดสอบและนำไปใช้ซ้ำได้โดยไม่ต้องมีเว็บ
"""

from __future__ import annotations

import math

from dataclasses import dataclass
from enum import Enum
from typing import Mapping

FIELDS = ("vcc", "r1", "r2", "rc", "re", "beta", "vbe")


class Region(str, Enum):
    """บริเวณการทำงานที่แบบจำลอง forward-active ใช้ได้หรือไม่"""

    ACTIVE = "active"
    CUTOFF = "cutoff"
    SATURATION = "saturation"


@dataclass(frozen=True)
class BiasInput:
    """ค่าอุปกรณ์ตามที่ผู้ใช้กรอก: VCC/VBE [V], ตัวต้านทาน [kΩ], beta ไม่มีหน่วย"""

    vcc: float
    r1: float
    r2: float
    rc: float
    re: float
    beta: float
    vbe: float


class ValidationError(Exception):
    """ข้อมูลที่กรอกไม่ถูกต้อง เก็บข้อความแยกตามชื่อฟิลด์"""

    def __init__(self, errors: dict[str, str]) -> None:
        super().__init__("ข้อมูลไม่ถูกต้อง")
        self.errors = dict(errors)


def parse_form(values: Mapping[str, str]) -> BiasInput:
    """แปลงค่าจากฟอร์ม (string ทั้งหมด) เป็น BiasInput

    เก็บ error ของทุกฟิลด์ไว้พร้อมกันแล้วค่อย raise ครั้งเดียว
    เพื่อให้หน้าเว็บแสดงข้อผิดพลาดได้ครบในครั้งเดียว
    """
    errors: dict[str, str] = {}
    numbers: dict[str, float] = {}

    for field in FIELDS:
        label = field.upper()
        raw = values.get(field)
        if raw is None or str(raw).strip() == "":
            errors[field] = f"กรุณากรอก {label}"
            continue
        text = str(raw).strip()
        if "," in text:
            errors[field] = f"ใช้จุดทศนิยม (.) แทนเครื่องหมายจุลภาคใน {label}"
            continue
        try:
            number = float(text)
        except ValueError:
            errors[field] = f"ค่าของ {label} ต้องเป็นตัวเลข"
            continue
        if not math.isfinite(number):
            # "nan", "inf" และค่าที่ล้นช่วง เช่น "1e400" แปลงเป็น float ได้
            # แต่ไม่ใช่ค่าอุปกรณ์จริง และจะทำให้การคำนวณทั้งหมดไร้ความหมาย
            errors[field] = f"ค่าของ {label} ต้องเป็นตัวเลข"
            continue
        numbers[field] = number

    if "vcc" in numbers and numbers["vcc"] <= 0:
        errors["vcc"] = "VCC ต้องมากกว่า 0"

    for field in ("r1", "r2", "rc", "re"):
        if field in numbers and numbers[field] <= 0:
            errors[field] = f"{field.upper()} ต้องมากกว่า 0"

    if "beta" in numbers and numbers["beta"] <= 0:
        errors["beta"] = "BETA ต้องมากกว่า 0"

    # ตรวจข้ามฟิลด์เฉพาะเมื่อ VCC ใช้ได้แล้ว เพื่อไม่ให้เกิด error ซ้ำซ้อน
    if "vcc" in numbers and "vcc" not in errors and "vbe" in numbers:
        if not 0 < numbers["vbe"] < numbers["vcc"]:
            errors["vbe"] = "VBE ต้องมากกว่า 0 และน้อยกว่า VCC"

    if errors:
        raise ValidationError(errors)

    return BiasInput(**numbers)


@dataclass(frozen=True)
class BiasResult:
    """ผลการคำนวณในหน่วย SI: แรงดัน [V], กระแส [A], ความต้านทาน [Ω]"""

    vth: float
    rth: float
    ib: float
    ic: float
    ie: float
    ve: float
    vb: float
    vc: float
    vce: float
    region: Region
    warnings: tuple[str, ...] = ()


def solve(data: BiasInput) -> BiasResult:
    """คำนวณ DC operating point ด้วย forward-active approximation

    ค่าที่รับมาเป็น kΩ (ตามที่มนุษย์กรอก) จึงแปลงเป็น Ω ที่นี่ที่เดียว
    ค่าที่คืนออกไปเป็นหน่วย SI ทั้งหมด เพื่อให้ผู้เรียกไม่ต้องจำหน่วย
    """
    r1 = data.r1 * 1000.0
    r2 = data.r2 * 1000.0
    rc = data.rc * 1000.0
    re = data.re * 1000.0

    vth = data.vcc * r2 / (r1 + r2)
    rth = r1 * r2 / (r1 + r2)

    # VTH ไม่พอเปิดรอยต่อ base-emitter: กระแสทุกตัวเป็นศูนย์ตามทฤษฎี
    if vth <= data.vbe:
        warning = (
            f"VTH = {vth:.3f} V ไม่สูงพอที่จะเปิดรอยต่อ base-emitter "
            f"(VBE = {data.vbe:.3f} V) วงจรอยู่ในช่วง cutoff กระแสทุกตัวเป็นศูนย์"
        )
        return BiasResult(
            vth=vth, rth=rth, ib=0.0, ic=0.0, ie=0.0,
            ve=0.0, vb=vth, vc=data.vcc, vce=data.vcc,
            region=Region.CUTOFF, warnings=(warning,),
        )

    ib = (vth - data.vbe) / (rth + (data.beta + 1) * re)
    ic = data.beta * ib
    ie = (data.beta + 1) * ib

    ve = ie * re
    vb = ve + data.vbe
    vc = data.vcc - ic * rc
    vce = vc - ve

    if vce <= 0.3:
        warning = (
            f"VCE = {vce:.3f} V ต่ำกว่า 0.3 V ทรานซิสเตอร์อยู่ในช่วง saturation "
            "แบบจำลอง forward-active ใช้ไม่ได้ ค่าที่แสดงไม่ควรนำไปใช้"
        )
        return BiasResult(
            vth=vth, rth=rth, ib=ib, ic=ic, ie=ie,
            ve=ve, vb=vb, vc=vc, vce=vce,
            region=Region.SATURATION, warnings=(warning,),
        )

    return BiasResult(
        vth=vth,
        rth=rth,
        ib=ib,
        ic=ic,
        ie=ie,
        ve=ve,
        vb=vb,
        vc=vc,
        vce=vce,
        region=Region.ACTIVE,
        warnings=(),
    )
