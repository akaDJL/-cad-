# -*- coding: utf-8 -*-
"""活性炭吸附装置（固定床 VOC 治理）多视图制图 v1.0（HJ 2026、GB 16297）。

活性炭吸附装置的成套视图：外形总图(正立面/平面)、纵剖面、炭层详图、
脱附系统、管路系统。几何参数由 design.env_process.design_activated_carbon_full
从输入条件(废气量/VOC/空塔气速)算出并以 dict 传入——本模块只负责"画"。

坐标单位 mm（design 返回的罐径 m，此处 ×1000 转 mm）。图层沿用包内中文命名。
"""
from __future__ import annotations

import math

from ezdxf.enums import TextEntityAlignment

from ..utils import _r, _tri
from .annotate import _t

MC = TextEntityAlignment.MIDDLE_CENTER
ML = TextEntityAlignment.MIDDLE_LEFT
MR = TextEntityAlignment.MIDDLE_RIGHT


def _rect(msp, x0, y0, x1, y1, layer="设备"):
    x0, y0 = _r(x0, y0)
    msp.add_lwpolyline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)],
                       close=True, dxfattribs={"layer": layer})


def _ln(msp, p0, p1, layer="设备", linetype=None):
    attr = {"layer": layer}
    if linetype:
        attr["linetype"] = linetype
    msp.add_line(_r(*p0), _r(*p1), dxfattribs=attr)


def _circle(msp, c, r, layer="设备"):
    msp.add_circle(_r(*c), r, dxfattribs={"layer": layer})


def _zones(p):
    """竖向关键标高（相对罐底 oy 的 mm 偏移）。"""
    y0 = 0.0
    y_in = y0 + p["H_inlet"]                       # 进气区顶=首床底
    y_bed = y_in + p["H_bed_total"] + (p["n_bed"] - 1) * p["bed_gap"]  # 炭层区顶
    y_out = y_bed + p["H_outlet"]                  # 出气区顶=罐顶
    return dict(y0=y0, y_in=y_in, y_bed=y_bed, y_out=y_out)


# ═══ 1. 外形总图 — 正立面 ═══
def draw_ac_elevation(msp, origin, p: dict, scale: float = 100.0,
                      label: str = "活性炭吸附装置外形图", tracker=None):
    s = scale
    ox, oy = _r(*origin)      # origin = 罐底左端
    D = p["D"] * 1000.0
    z = _zones(p)
    cx = ox + D / 2.0

    # 罐体
    _rect(msp, ox, oy + z["y0"], ox + D, oy + z["y_out"], "设备")
    # 上下封头
    msp.add_ellipse(_r(cx, oy + z["y_out"]), major_axis=(D / 2, 0), ratio=0.2,
                    dxfattribs={"layer": "设备"})
    msp.add_ellipse(_r(cx, oy + z["y0"]), major_axis=(D / 2, 0), ratio=0.2,
                    dxfattribs={"layer": "设备"})

    # 炭层横线（n_bed 层）
    for i in range(p["n_bed"]):
        by = oy + z["y_in"] + i * (p["H_bed"] + p["bed_gap"]) + p["H_bed"]
        _ln(msp, (ox, by), (ox + D, by), "细实线", linetype="DASHED")
    _t(msp, f"活性炭层×{p['n_bed']}", (ox + D + 200, oy + z["y_in"] + p["H_bed_total"] / 2),
       2.0 * s, align=ML, layer="文字", tracker=tracker)

    # 进气管（下部左侧）
    idn = p["inlet_dn"]
    iy = oy + z["y0"] + p["H_inlet"] / 2
    _rect(msp, ox - idn, iy - idn / 2, ox, iy + idn / 2, "设备")
    _tri(msp, (ox - idn - 3 * s, iy), (1, 0), s, "设备")
    _t(msp, f"进气 Φ{idn:.0f}", (ox - idn / 2, iy - idn / 2 - 4 * s), 2.2 * s,
       align=MC, layer="文字", tracker=tracker)

    # 出气管（顶部）
    odn = p["outlet_dn"]
    _rect(msp, cx - odn / 2, oy + z["y_out"], cx + odn / 2, oy + z["y_out"] + odn, "设备")
    _tri(msp, (cx, oy + z["y_out"] + odn + 3 * s), (0, 1), s, "设备")
    _t(msp, f"出气 Φ{odn:.0f}", (cx, oy + z["y_out"] + odn + 6 * s), 2.2 * s,
       align=MC, layer="文字", tracker=tracker)

    # 脱附蒸汽管（炭层区右侧）
    sdn = p["steam_dn"]
    sy = oy + z["y_in"] + p["H_bed_total"] / 2
    _ln(msp, (ox + D, sy), (ox + D + 600, sy), "设备")
    _t(msp, f"脱附蒸汽 Φ{sdn:.0f}", (ox + D + 300, sy + 3 * s), 2.0 * s,
       align=MC, layer="文字", tracker=tracker)

    # 检修人孔（侧壁中部）
    _circle(msp, (ox, oy + z["y_in"] + p["H_bed_total"] * 0.7), 250, "设备")
    _t(msp, "人孔", (ox - 300, oy + z["y_in"] + p["H_bed_total"] * 0.7), 2.0 * s,
       align=MR, layer="文字", tracker=tracker)

    if label:
        _t(msp, label, (cx, oy - 9 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (cx, oy, oy + z["y_out"])


# ═══ 2. 外形总图 — 平面 ═══
def draw_ac_plan(msp, origin, p: dict, scale: float = 100.0,
                 label: str = "平面图", tracker=None):
    s = scale
    ox, oy = _r(*origin)      # origin = 罐中心
    D = p["D"] * 1000.0
    R = D / 2.0

    _circle(msp, (ox, oy), R, "设备")
    # 炭层支撑格栅（十字线）
    for i in range(-3, 4):
        off = i * D / 8
        _ln(msp, (ox + off, oy - R * 0.9), (ox + off, oy + R * 0.9), "细实线")
        _ln(msp, (ox - R * 0.9, oy + off), (ox + R * 0.9, oy + off), "细实线")

    # 进气管（一侧）
    idn = p["inlet_dn"]
    _rect(msp, ox - R - idn, oy - idn / 2, ox - R, oy + idn / 2, "设备")
    _t(msp, "进气", (ox - R - idn / 2, oy + idn), 2.0 * s, align=MC, layer="文字", tracker=tracker)
    # 出气管（中心）
    _circle(msp, (ox, oy), p["outlet_dn"] / 2.0, "设备")
    # 蒸汽管（一侧）
    _circle(msp, (ox + R * 0.6, oy), p["steam_dn"] / 2.0, "设备")
    _t(msp, "蒸汽", (ox + R * 0.6, oy + 3 * s), 2.0 * s, align=MC, layer="文字", tracker=tracker)

    if label:
        _t(msp, label, (ox, oy + R + 6 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (ox + R, oy)


# ═══ 3. 纵剖面图 ═══
def draw_ac_section(msp, origin, p: dict, scale: float = 100.0,
                    label: str = "1-1 剖面图", tracker=None):
    s = scale
    ox, oy = _r(*origin)
    D = p["D"] * 1000.0
    z = _zones(p)
    cx = ox + D / 2.0

    # 罐体外壳
    _rect(msp, ox, oy + z["y0"], ox + D, oy + z["y_out"], "设备")

    # 进气分布器（底部多孔板）
    _ln(msp, (ox, oy + z["y_in"] - 150), (ox + D, oy + z["y_in"] - 150), "细实线")
    for k in range(1, int(D / 200)):
        _circle(msp, (ox + k * 200, oy + z["y_in"] - 150), 25, "细实线")
    _t(msp, "进气分布器", (cx, oy + z["y0"] + p["H_inlet"] / 2), 2.0 * s,
       align=MC, layer="文字", tracker=tracker)

    # 炭层（每层斜线填充 + 支撑格栅）
    for i in range(p["n_bed"]):
        b0 = oy + z["y_in"] + i * (p["H_bed"] + p["bed_gap"])
        b1 = b0 + p["H_bed"]
        # 支撑格栅（床底）
        _ln(msp, (ox, b0), (ox + D, b0), "设备")
        for k in range(1, int(D / 150)):
            _ln(msp, (ox + k * 150, b0), (ox + k * 150, b0 + 60), "细实线")
        # 炭粒（斜线填充示意）
        for k in range(int(D / 300)):
            hx = ox + k * 300
            _ln(msp, (hx, b0 + 60), (hx + 150, b1 - 40), "细实线")
    _t(msp, f"活性炭 {p['carbon_vol']}m³（{p['carbon_wt']:.0f}kg）",
       (cx, oy + z["y_in"] + p["H_bed_total"] / 2), 2.2 * s, align=MC,
       layer="文字", tracker=tracker)

    # 蒸汽分布管（炭层上方）
    _ln(msp, (ox, oy + z["y_bed"] - 100), (ox + D, oy + z["y_bed"] - 100), "设备")
    _t(msp, "脱附蒸汽分布管", (cx, oy + z["y_bed"] - 100 + 3 * s), 2.0 * s,
       align=MC, layer="文字", tracker=tracker)

    # 出气区
    odn = p["outlet_dn"]
    _rect(msp, cx - odn / 2, oy + z["y_out"], cx + odn / 2, oy + z["y_out"] + odn, "设备")

    # 进气管
    idn = p["inlet_dn"]
    iy = oy + z["y0"] + p["H_inlet"] / 2
    _rect(msp, ox - idn, iy - idn / 2, ox, iy + idn / 2, "设备")

    if label:
        _t(msp, label, (cx, oy - 9 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (cx, oy, oy + z["y_out"])


# ═══ 4. 炭层详图 ═══
def draw_ac_carbon_bed(msp, origin, p: dict, scale: float = 100.0,
                       label: str = "活性炭层详图", tracker=None):
    s = scale
    ox, oy = _r(*origin)
    W = p["D"] * 1000.0 * 0.7          # 局部放大宽度
    H = p["H_bed"]

    # 床层外框
    _rect(msp, ox, oy, ox + W, oy + H, "设备")
    # 底部支撑网（格栅）
    _ln(msp, (ox, oy + 100), (ox + W, oy + 100), "设备")
    for k in range(int(W / 100)):
        _ln(msp, (ox + k * 100, oy), (ox + k * 100, oy + 100), "细实线")
    _t(msp, "支撑格栅+滤网", (ox + W + 200, oy + 50), 2.0 * s, align=ML,
       layer="文字", tracker=tracker)
    # 炭粒（点/斜线填充）
    for r_ in range(int(H / 200)):
        for k in range(int(W / 200)):
            _circle(msp, (ox + 100 + k * 200, oy + 200 + r_ * 200), 40, "细实线")
    # 顶部压紧格栅
    _ln(msp, (ox, oy + H - 100), (ox + W, oy + H - 100), "设备")
    for k in range(int(W / 100)):
        _ln(msp, (ox + k * 100, oy + H - 100), (ox + k * 100, oy + H), "细实线")
    _t(msp, "压紧格栅（防炭层流化）", (ox + W + 200, oy + H - 50), 2.0 * s,
       align=ML, layer="文字", tracker=tracker)

    _t(msp, f"颗粒活性炭，床高 {H:.0f}mm，共 {p['n_bed']} 床",
       (ox + W / 2, oy - 5 * s), 2.3 * s, align=MC, layer="文字", tracker=tracker)
    if label:
        _t(msp, label, (ox + W / 2, oy + H + 6 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (ox + W, oy)


# ═══ 5. 脱附系统图 ═══
def draw_ac_desorption(msp, origin, p: dict, scale: float = 100.0,
                       label: str = "脱附系统图", avail_w: float = None, tracker=None):
    s = scale
    ox, oy = _r(*origin)
    # 流程：蒸汽发生器→吸附罐→冷凝器→回收槽
    boxes = ["蒸汽/热氮气", "吸附罐脱附", "冷凝器", "溶剂回收槽"]
    n = len(boxes)
    if avail_w:
        gap = avail_w * 0.06 / max(1, n - 1)
        bw = (avail_w - gap * (n - 1)) / n      # 框宽自适应图框
    else:
        bw, gap = 11000.0, 6000.0
    bh = 5500.0
    for i, bt in enumerate(boxes):
        bx = ox + i * (bw + gap)
        _rect(msp, bx, oy, bx + bw, oy + bh, "工艺")
        _t(msp, bt, (bx + bw / 2, oy + bh / 2), 2.8 * s, align=MC, layer="文字", tracker=tracker)
        if i < len(boxes) - 1:
            _ln(msp, (bx + bw, oy + bh / 2), (bx + bw + gap, oy + bh / 2), "设备")
            _tri(msp, (bx + bw + gap, oy + bh / 2), (1, 0), s, "设备")
    _t(msp, f"脱附周期约 {p['cycle_h']:.0f}h（蒸汽再生，溶剂回收）",
       (ox + (len(boxes) * (bw + gap)) / 2, oy - 5 * s), 2.5 * s, align=MC,
       layer="文字-标题", tracker=tracker)
    if label:
        _t(msp, label, (ox + (len(boxes) * (bw + gap)) / 2, oy + bh + 6 * s),
           3.2 * s, align=MC, layer="文字-标题", tracker=tracker)
    return (ox + len(boxes) * (bw + gap), oy)


# ═══ 6. 管路系统图 ═══
def draw_ac_piping(msp, origin, p: dict, scale: float = 100.0,
                   label: str = "管路系统图", tracker=None):
    s = scale
    ox, oy = _r(*origin)
    D = p["D"] * 1000.0
    # 主气路：进气→预过滤→吸附罐→风机→排气筒
    y = oy
    # 吸附罐（中央）
    _rect(msp, ox + 20000, y, ox + 20000 + D, y + p["H_total"], "设备")
    _t(msp, "吸附罐", (ox + 20000 + D / 2, y + p["H_total"] / 2), 2.5 * s,
       align=MC, layer="文字", tracker=tracker)
    # 进气主管（左）
    _ln(msp, (ox, y + p["H_inlet"] / 2), (ox + 20000, y + p["H_inlet"] / 2), "设备")
    _rect(msp, ox + 8000, y + p["H_inlet"] / 2 - 500, ox + 12000, y + p["H_inlet"] / 2 + 500, "设备")
    _t(msp, "预过滤器", (ox + 10000, y + p["H_inlet"] / 2 + 1200), 2.0 * s,
       align=MC, layer="文字", tracker=tracker)
    _tri(msp, (ox + 20000, y + p["H_inlet"] / 2), (1, 0), s, "设备")
    _t(msp, f"进气 Φ{p['inlet_dn']:.0f}", (ox + 4000, y + p["H_inlet"] / 2 + 800),
       2.0 * s, align=MC, layer="文字", tracker=tracker)
    # 出气主管（顶→风机→排气筒）
    _ln(msp, (ox + 20000 + D / 2, y + p["H_total"]), (ox + 20000 + D / 2, y + p["H_total"] + 3000), "设备")
    _rect(msp, ox + 20000 + D / 2 - 700, y + p["H_total"] + 3000, ox + 20000 + D / 2 + 700,
          y + p["H_total"] + 4000, "设备")
    _t(msp, "风机", (ox + 20000 + D / 2, y + p["H_total"] + 4600), 2.0 * s,
       align=MC, layer="文字", tracker=tracker)
    _ln(msp, (ox + 20000 + D / 2, y + p["H_total"] + 4000), (ox + 20000 + D / 2, y + p["H_total"] + 6000), "设备")
    _tri(msp, (ox + 20000 + D / 2, y + p["H_total"] + 6500), (0, 1), s, "设备")
    _t(msp, "排气筒", (ox + 20000 + D / 2 + 800, y + p["H_total"] + 5500), 2.0 * s,
       align=ML, layer="文字", tracker=tracker)
    # 蒸汽/冷凝管路（右侧虚线）
    _ln(msp, (ox + 20000 + D, y + p["H_total"] * 0.6), (ox + 20000 + D + 4000, y + p["H_total"] * 0.6),
        "设备", linetype="DASHED")
    _t(msp, f"脱附蒸汽 Φ{p['steam_dn']:.0f}", (ox + 20000 + D + 2000, y + p["H_total"] * 0.6 + 600),
       2.0 * s, align=MC, layer="文字", tracker=tracker)

    if label:
        _t(msp, label, (ox + 20000 + D / 2, y - 6 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (ox + 20000 + D, y)
