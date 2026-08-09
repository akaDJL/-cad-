"""压缩机（Compressor）机组布置图模块 —— 参数化外形 + 联轴器。

依据标准
--------
* GB/T 3853—2017《容积式压缩机 验收试验》——参数与验收
* GB/T 4980—2003《容积式压缩机噪声的测定》
* GB 50029—2014《压缩空气站设计规范》——机组布置与基础
* GB/T 5272—2017《梅花形弹性联轴器》/ GB/T 4323—2017《弹性套柱销联轴器》
* HG/T 20592—2009《钢制管法兰》——吸排气口法兰

.. note::
   机组外形尺寸（缸径、机身长宽高）由厂商样本确定，
   envcad standards_kb.json 未收录，本模块全部作为 **参数** 暴露，
   默认值仅为示意，见 ``# TODO: verify`` 标记。

坐标约定
--------
``(x, y)`` = **底座/基础底面中心**（基础顶面标高处）。
"""
from __future__ import annotations

import math
from typing import Optional, Sequence

from ezdxf.enums import TextEntityAlignment

from . import _common as C


def _coupling(msp, x: float, cy: float, gap: float, shaft_d: float,
              scale: float, guard: bool = True,
              ctype: str = "弹性柱销联轴器"):
    """联轴器 + 防护罩（GB/T 5272 / GB/T 4323）。

    x 为联轴器区间左端，gap 为两半联轴器轴向总长。
    """
    r = shaft_d * 1.75
    for k in (0.18, 0.82):
        cx = x + gap * k
        C.rect(msp, cx - C.P(0.9, scale), cy - r, cx + C.P(0.9, scale), cy + r,
               layer=C.L_THICK)
    # 中间连接段
    msp.add_line((x + gap * 0.18, cy + r * 0.55),
                 (x + gap * 0.82, cy + r * 0.55),
                 dxfattribs={"layer": C.L_MID})
    msp.add_line((x + gap * 0.18, cy - r * 0.55),
                 (x + gap * 0.82, cy - r * 0.55),
                 dxfattribs={"layer": C.L_MID})
    if guard:
        C.rect(msp, x, cy - r * 1.45, x + gap, cy + r * 1.45, layer=C.L_THIN)
    C.leader_note(msp, (x + gap / 2, cy + r * 1.45), ctype, scale, dx=8, dy=16)
    return x + gap


def _recip_cylinders(msp, x0: float, x1: float, cy: float, body_h: float,
                     n: int, bore: float, scale: float):
    """往复式气缸组（正视图，气缸竖直布置于机身之上）。"""
    for i in range(n):
        cx = x0 + (x1 - x0) * (i + 0.5) / n
        r = bore / 2.0
        C.rect(msp, cx - r, cy + body_h / 2, cx + r,
               cy + body_h / 2 + bore * 1.5, layer=C.L_THICK)
        # 缸盖
        C.rect(msp, cx - r * 1.22, cy + body_h / 2 + bore * 1.5,
               cx + r * 1.22, cy + body_h / 2 + bore * 1.72, layer=C.L_MID)
        # 气阀
        for sg in (-1, 1):
            C.rect(msp, cx + sg * r * 0.55 - r * 0.18,
                   cy + body_h / 2 + bore * 1.72,
                   cx + sg * r * 0.55 + r * 0.18,
                   cy + body_h / 2 + bore * 1.95, layer=C.L_THIN)
        # 活塞（虚线，不可见）
        msp.add_line((cx - r * 0.92, cy + body_h / 2 + bore * 0.55),
                     (cx + r * 0.92, cy + body_h / 2 + bore * 0.55),
                     dxfattribs={"layer": C.L_DASH})
        C.centerline(msp, (cx, cy), (cx, cy + body_h / 2 + bore * 2.05))


def draw_compressor(msp, x: float, y: float, scale: float = 50.0,
                    comp_type: str = "reciprocating",
                    body_length: float = 2200.0,
                    body_height: float = 900.0,
                    shaft_height: float = 700.0,
                    n_cylinders: int = 2,
                    cylinder_bore: float = 320.0,
                    suction_dn: float = 200.0,
                    discharge_dn: float = 150.0,
                    motor_length: float = 1100.0,
                    motor_diameter: float = 700.0,
                    coupling_gap: float = 260.0,
                    baseplate_height: float = 260.0,
                    baseplate_margin: float = 300.0,
                    orientation: str = "right",
                    with_gearbox: bool = False,
                    gearbox_length: float = 700.0,
                    tag: str = "C-801",
                    name: str = "往复式压缩机",
                    capacity: str = "20 m³/min",
                    suction_pressure: str = "0.1 MPa(a)",
                    discharge_pressure: str = "0.8 MPa(g)",
                    motor_power: str = "160 kW",
                    speed: str = "740 r/min",
                    medium: str = "空气",
                    with_dims: bool = True,
                    with_table: bool = True,
                    **params):
    """绘制压缩机机组正视布置图（GB/T 3853 / GB 50029）。

    参数
    ----
    comp_type       ``reciprocating`` 往复式 / ``screw`` 螺杆式 /
                    ``centrifugal`` 离心式
    body_length     机身长度 mm  # TODO: verify against 厂商样本
    body_height     机身高度 mm
    shaft_height    曲轴/主轴中心线到底座顶面高度 mm
    n_cylinders     气缸数（仅 reciprocating 有效）
    cylinder_bore   气缸缸径 mm
    with_gearbox    是否含增速齿轮箱（离心式常配）
    orientation     ``right`` 电机在右 / ``left`` 电机在左

    返回 ``dict``：机组关键坐标。
    """
    s = scale
    sgn = 1.0 if orientation == "right" else -1.0

    drive_len = motor_length + (gearbox_length if with_gearbox else 0.0)
    total_len = body_length + coupling_gap + drive_len
    bp_len = total_len + baseplate_margin * 2

    y_base = y
    y_bp = y_base + baseplate_height
    cy = y_bp + shaft_height

    x_left = x - total_len / 2.0
    if sgn > 0:
        x_body0, x_body1 = x_left, x_left + body_length
        x_cpl = x_body1
        x_drive0 = x_cpl + coupling_gap
    else:
        x_drive0 = x_left
        x_cpl = x_left + drive_len
        x_body0, x_body1 = x_cpl + coupling_gap, x_left + total_len

    # ── 基础与底座（GB 50029 §5 机组基础）──
    C.rect(msp, x - bp_len / 2, y_base, x + bp_len / 2, y_bp, layer=C.L_THICK)
    C.hatch_area(msp, [(x - bp_len / 2, y_base), (x + bp_len / 2, y_base),
                       (x + bp_len / 2, y_bp), (x - bp_len / 2, y_bp)],
                 scale=s, pattern_scale=0.8)
    for f in (-0.44, -0.15, 0.15, 0.44):
        bx = x + bp_len * f
        msp.add_line((bx, y_base - C.P(6, s)), (bx, y_bp + C.P(2, s)),
                     dxfattribs={"layer": C.L_THIN})
    gx0, gx1 = x - bp_len * 0.62, x + bp_len * 0.62
    msp.add_line((gx0, y_base), (gx1, y_base), dxfattribs={"layer": C.L_THICK})
    for i in range(15):
        gx = gx0 + (gx1 - gx0) * i / 14.0
        msp.add_line((gx, y_base), (gx - C.P(3, s), y_base - C.P(3, s)),
                     dxfattribs={"layer": C.L_THIN})

    # ── 主轴中心线 ──
    C.centerline(msp, (x - bp_len * 0.54, cy), (x + bp_len * 0.54, cy))

    # ── 机身 ──
    C.rect(msp, x_body0, cy - body_height / 2, x_body1, cy + body_height / 2,
           layer=C.L_THICK)
    C.rect(msp, x_body0 + body_length * 0.06, y_bp,
           x_body1 - body_length * 0.06, cy - body_height / 2,
           layer=C.L_THICK)                       # 机身底座

    if comp_type == "reciprocating":
        _recip_cylinders(msp, x_body0, x_body1, cy, body_height,
                         max(n_cylinders, 1), cylinder_bore, s)
        top_y = cy + body_height / 2 + cylinder_bore * 2.05
    elif comp_type == "screw":
        # 螺杆主机：两条平行转子（虚线）
        for d in (-1, 1):
            msp.add_circle((x_body0 + body_length * 0.42,
                            cy + d * cylinder_bore * 0.32),
                           cylinder_bore * 0.42,
                           dxfattribs={"layer": C.L_DASH})
        C.rect(msp, x_body0 + body_length * 0.12, cy + body_height / 2,
               x_body0 + body_length * 0.55,
               cy + body_height / 2 + cylinder_bore * 0.6, layer=C.L_MID)
        top_y = cy + body_height / 2 + cylinder_bore * 0.6
    else:  # centrifugal
        # 蜗壳形机壳
        msp.add_circle((x_body0 + body_length * 0.5, cy), body_height * 0.46,
                       dxfattribs={"layer": C.L_THICK})
        msp.add_circle((x_body0 + body_length * 0.5, cy), body_height * 0.28,
                       dxfattribs={"layer": C.L_DASH})
        top_y = cy + body_height / 2

    # ── 吸/排气口 ──
    nl = max(suction_dn * 1.5, C.P(9, s))
    p_suc = C.nozzle(msp, (x_body0, cy - body_height * 0.22), "left",
                     suction_dn, nl, s, tag="吸入")
    p_dis = C.nozzle(msp, (x_body1, cy + body_height * 0.22), "right",
                     discharge_dn, max(discharge_dn * 1.7, C.P(9, s)), s,
                     tag="排出")

    # ── 联轴器 ──
    shaft_d = max(body_height * 0.10, 50.0)
    for d in (-1, 1):
        msp.add_line((x_cpl, cy + d * shaft_d / 2),
                     (x_cpl + coupling_gap, cy + d * shaft_d / 2),
                     dxfattribs={"layer": C.L_THICK})
    _coupling(msp, x_cpl, cy, coupling_gap, shaft_d, s)

    # ── 增速机（可选）+ 电机 ──
    xd = x_drive0
    if with_gearbox:
        gh = motor_diameter * 0.85
        C.rect(msp, xd, cy - gh / 2, xd + gearbox_length, cy + gh / 2,
               layer=C.L_THICK)
        C.rect(msp, xd + gearbox_length * 0.1, y_bp,
               xd + gearbox_length * 0.9, cy - gh / 2, layer=C.L_THICK)
        C.text(msp, "增速机", (xd + gearbox_length / 2, cy), 3.5, s,
               layer=C.L_TEXT)
        xd += gearbox_length

    mr = motor_diameter / 2.0
    C.rect(msp, xd, cy - mr, xd + motor_length, cy + mr, layer=C.L_THICK)
    for i in range(9):
        fx = xd + motor_length * (0.08 + 0.84 * i / 8.0)
        msp.add_line((fx, cy + mr), (fx, cy + mr * 0.80),
                     dxfattribs={"layer": C.L_THIN})
    C.rect(msp, xd + motor_length * 0.12, y_bp,
           xd + motor_length * 0.88, cy - mr, layer=C.L_THICK)
    C.rect(msp, xd + motor_length * 0.40, cy + mr,
           xd + motor_length * 0.62, cy + mr * 1.26, layer=C.L_MID)  # 接线盒
    C.eng_text(msp, "M", (xd + motor_length / 2, cy), 5.0, s, layer=C.L_TITLE)
    top_y = max(top_y, cy + mr * 1.26)

    # ── 标注 ──
    if with_dims:
        C.dim_linear(msp, (x - bp_len / 2, y_base), (x + bp_len / 2, y_base),
                     offset=26, scale=s, label=f"基础 {int(bp_len)}")
        C.dim_linear(msp, (x_body0, y_bp), (x_body1, y_bp),
                     offset=14, scale=s, label=f"机身 {int(body_length)}")
        C.dim_linear(msp, (x - bp_len / 2, y_bp), (x - bp_len / 2, cy),
                     offset=20, scale=s, label=f"轴心高 {int(shaft_height)}")
        ct = {"reciprocating": "往复式", "screw": "螺杆式",
              "centrifugal": "离心式"}.get(comp_type, comp_type)
        if comp_type == "reciprocating":
            C.leader_note(msp, (x_body0 + body_length * 0.25,
                                cy + body_height / 2 + cylinder_bore),
                          f"{n_cylinders}级气缸 φ{int(cylinder_bore)}",
                          s, dx=-24, dy=14)
        else:
            C.leader_note(msp, (x_body0 + body_length * 0.5, cy),
                          f"{ct}主机", s, dx=-26, dy=20)
        C.leader_note(msp, p_suc, f"吸入 DN{int(suction_dn)}", s, dx=-14, dy=-16)
        C.leader_note(msp, p_dis, f"排出 DN{int(discharge_dn)}", s, dx=14, dy=14)
        C.elevation_mark(msp, (gx0 + C.P(4, s), y_base), "±0.000", s)

    C.eng_text(msp, tag, (x, top_y + C.P(16, s)), 5.0, s, layer=C.L_TITLE)
    C.text(msp, name, (x, top_y + C.P(10, s)), 3.5, s, layer=C.L_TITLE)

    if with_table:
        C.spec_table(msp, (x + bp_len * 0.52, top_y + C.P(6, s)), [
            ["排气量", capacity],
            ["吸气压力", suction_pressure],
            ["排气压力", discharge_pressure],
            ["转速 n", speed],
            ["电机功率", motor_power],
            ["介质", medium],
            ["执行标准", "GB/T 3853-2017"],
        ], s, col_w=(28.0, 42.0), title="压缩机数据表")

    return {"tag": tag, "base": y_base, "shaft_y": cy,
            "body": (x_body0, x_body1), "suction": p_suc, "discharge": p_dis,
            "top": top_y}
