# -*- coding: utf-8 -*-
"""离心风机多视图制图 v1.0（GB/T 1236、通风机性能试验与安装规范）。

离心风机的成套视图：外形总图(正立面/平面)、纵剖面、进出口法兰、减振基础、
安装系统。几何参数由 design.env_process.design_fan_full 算出并以 dict 传入。

坐标单位 mm。图层沿用包内中文命名。
"""
from __future__ import annotations

import math

from ezdxf.enums import TextEntityAlignment

from ..utils import _r, _tri
from .annotate import _t

MC = TextEntityAlignment.MIDDLE_CENTER
ML = TextEntityAlignment.MIDDLE_LEFT
MR = TextEntityAlignment.MIDDLE_RIGHT


def _ln(msp, p0, p1, layer="设备", linetype=None):
    attr = {"layer": layer}
    if linetype:
        attr["linetype"] = linetype
    msp.add_line(_r(*p0), _r(*p1), dxfattribs=attr)


def _circle(msp, c, r, layer="设备"):
    msp.add_circle(_r(*c), r, dxfattribs={"layer": layer})


def _rect(msp, x0, y0, x1, y1, layer="设备"):
    x0, y0 = _r(x0, y0)
    msp.add_lwpolyline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)],
                       close=True, dxfattribs={"layer": layer})


def _motor(msp, x, y, w, h, layer="设备"):
    """电机（矩形+地脚）。"""
    _rect(msp, x, y, x + w, y + h, layer)
    _ln(msp, (x + w, y + h / 2), (x + w + 200, y + h / 2), "细实线")


# ═══ 1. 外形总图 — 正立面 ═══
def draw_fan_elevation(msp, origin, p: dict, scale: float = 100.0,
                       label: str = "离心风机外形图", tracker=None):
    s = scale
    ox, oy = _r(*origin)
    W = p["W"]
    R = W / 2.0
    cx, cy = ox + R + 500, oy + R + 800

    # 底座
    _ln(msp, (ox, oy + 300), (ox + p["L"], oy + 300), "设备")
    _rect(msp, ox, oy, ox + p["L"], oy + 300, "设备")
    _t(msp, "钢底座", (ox + p["L"] / 2, oy + 150), 2.0 * s, align=MC, layer="文字", tracker=tracker)

    # 蜗壳（圆+蜗舌）
    _circle(msp, (cx, cy), R, "设备")
    _ln(msp, (cx + R, cy + R * 0.4), (cx + R + 600, cy + R * 0.4), "设备")  # 蜗舌
    # 进口（轴向，圆心）
    _circle(msp, (cx, cy), p["inlet_dn"] / 2.0, "设备")
    _t(msp, f"进口Φ{p['inlet_dn']:.0f}", (cx, cy - p["inlet_dn"] / 2 - 3 * s), 2.0 * s,
       align=MC, layer="文字", tracker=tracker)
    # 出口（顶部切向，方形）
    odn = p["outlet_dn"]
    _rect(msp, cx - odn / 2, cy + R, cx + odn / 2, cy + R + odn, "设备")
    _tri(msp, (cx, cy + R + odn + 3 * s), (0, 1), s, "设备")
    _t(msp, f"出口Φ{odn:.0f}", (cx, cy + R + odn + 6 * s), 2.2 * s, align=MC,
       layer="文字", tracker=tracker)
    # 电机（右侧，通过轴）
    _ln(msp, (cx + R, cy), (cx + R + 400, cy), "设备")
    _motor(msp, cx + R + 400, cy - 400, 900, 800)
    _t(msp, f"电机 {p['N_rated']}kW", (cx + R + 850, cy - 700), 2.0 * s, align=MC,
       layer="文字", tracker=tracker)

    if label:
        _t(msp, label, (cx, oy - 8 * s), 3.2 * s, align=MC, layer="文字-标题", tracker=tracker)
    return (cx, oy, cy + R)


# ═══ 2. 外形总图 — 平面 ═══
def draw_fan_plan(msp, origin, p: dict, scale: float = 100.0,
                  label: str = "平面图", tracker=None):
    s = scale
    ox, oy = _r(*origin)
    L, W = p["L"], p["W"]
    # 外形（俯视矩形）
    _rect(msp, ox, oy, ox + L, oy + W, "设备")
    # 蜗壳区（圆）
    _circle(msp, (ox + W / 2 + 300, oy + W / 2), W / 2.0, "细实线")
    # 电机区（一侧矩形）
    _rect(msp, ox + L - 900, oy + W / 2 - 400, ox + L, oy + W / 2 + 400, "设备")
    _t(msp, "电机", (ox + L - 450, oy + W / 2), 2.0 * s, align=MC, layer="文字", tracker=tracker)
    # 出口（顶部）
    odn = p["outlet_dn"]
    _rect(msp, ox + W / 2 + 300 - odn / 2, oy + W, ox + W / 2 + 300 + odn / 2, oy + W + odn, "设备")
    _t(msp, f"出口Φ{odn:.0f}", (ox + W / 2 + 300, oy + W + odn + 4 * s), 2.0 * s,
       align=MC, layer="文字", tracker=tracker)
    # 底座（外框）
    _rect(msp, ox - 200, oy - 200, ox + L + 200, oy, "细实线")
    _t(msp, f"外形 {p['L']:.0f}×{p['W']:.0f}mm", (ox + L / 2, oy - 5 * s), 2.2 * s,
       align=MC, layer="文字", tracker=tracker)
    if label:
        _t(msp, label, (ox + L / 2, oy + W + odn + 8 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (ox + L, oy)


# ═══ 3. 纵剖面图（电机侧看）═══
def draw_fan_section(msp, origin, p: dict, scale: float = 100.0,
                     label: str = "1-1 剖面图", tracker=None):
    s = scale
    ox, oy = _r(*origin)
    W = p["W"]
    R = W / 2.0
    cx, cy = ox + R + 800, oy + R + 600
    # 蜗壳剖面（圆+蜗室）
    _circle(msp, (cx, cy), R, "设备")
    _circle(msp, (cx, cy), R * 0.75, "细实线")   # 叶轮室
    # 叶轮（叶片放射）
    for a in range(0, 360, 30):
        ang = math.radians(a)
        _ln(msp, (cx + R * 0.2 * math.cos(ang), cy + R * 0.2 * math.sin(ang)),
            (cx + R * 0.72 * math.cos(ang), cy + R * 0.72 * math.sin(ang)), "细实线")
    _circle(msp, (cx, cy), R * 0.2, "设备")      # 轮毂
    _t(msp, "叶轮", (cx, cy - R * 0.5), 2.0 * s, align=MC, layer="文字", tracker=tracker)
    # 轴 + 轴承座 + 电机
    _ln(msp, (cx, cy), (cx + R + 800, cy), "设备")
    _rect(msp, cx + R + 200, cy - 300, cx + R + 500, cy + 300, "设备")
    _t(msp, "轴承座", (cx + R + 350, cy - 600), 2.0 * s, align=MC, layer="文字", tracker=tracker)
    _motor(msp, cx + R + 800, cy - 450, 900, 900)
    _t(msp, f"电机 {p['N_rated']}kW", (cx + R + 1250, cy - 750), 2.0 * s, align=MC,
       layer="文字", tracker=tracker)
    # 进口（左）
    _circle(msp, (cx, cy), p["inlet_dn"] / 2.0, "设备")
    # 出口（顶）
    odn = p["outlet_dn"]
    _rect(msp, cx - odn / 2, cy + R, cx + odn / 2, cy + R + odn, "设备")
    # 底座
    _rect(msp, ox, oy, ox + p["L"] + 800, oy + 300, "设备")
    if label:
        _t(msp, label, (cx, oy - 8 * s), 3.2 * s, align=MC, layer="文字-标题", tracker=tracker)
    return (cx, oy, cy + R)


# ═══ 4. 进出口法兰详图 ═══
def draw_fan_flange(msp, origin, p: dict, scale: float = 100.0,
                    label: str = "进出口法兰详图", tracker=None):
    s = scale
    ox, oy = _r(*origin)
    idn = p["inlet_dn"]
    # 进口法兰（圆+螺栓孔）
    _circle(msp, (ox + 2000, oy + 2000), idn / 2.0, "设备")
    _circle(msp, (ox + 2000, oy + 2000), idn / 2.0 + 200, "设备")
    for a in range(0, 360, 30):
        ang = math.radians(a)
        _circle(msp, (ox + 2000 + (idn / 2 + 100) * math.cos(ang),
                      oy + 2000 + (idn / 2 + 100) * math.sin(ang)), 50, "细实线")
    _t(msp, f"进口法兰 Φ{idn:.0f} 螺栓孔12×Φ14", (ox + 2000, oy + 2000 - idn / 2 - 5 * s),
       2.2 * s, align=MC, layer="文字", tracker=tracker)
    # 出口法兰（方+螺栓孔）
    odn = p["outlet_dn"]
    fx = ox + 2000 + idn + 2500
    _rect(msp, fx, oy + 2000 - odn / 2, fx + odn, oy + 2000 + odn / 2, "设备")
    _rect(msp, fx - 200, oy + 2000 - odn / 2 - 200, fx + odn + 200, oy + 2000 + odn / 2 + 200, "设备")
    _t(msp, f"出口法兰 {odn:.0f}×{odn:.0f}", (fx + odn / 2, oy + 2000 - odn / 2 - 5 * s),
       2.2 * s, align=MC, layer="文字", tracker=tracker)
    if label:
        _t(msp, label, (ox + 4000, oy + 2000 + idn / 2 + 5 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (fx + odn, oy)


# ═══ 5. 减振基础详图 ═══
def draw_fan_base(msp, origin, p: dict, scale: float = 100.0,
                  label: str = "减振基础详图", tracker=None):
    s = scale
    ox, oy = _r(*origin)
    L = p["L"]
    # 风机底座
    _rect(msp, ox, oy + 1500, ox + L, oy + 1800, "设备")
    _t(msp, "风机钢底座", (ox + L / 2, oy + 1650), 2.0 * s, align=MC, layer="文字", tracker=tracker)
    # 减振器（4个弹簧）
    for i in range(4):
        dx = ox + L * (0.15 + 0.23 * i)
        _rect(msp, dx - 150, oy + 900, dx + 150, oy + 1500, "设备")
        for w_ in range(3):
            _ln(msp, (dx - 100, oy + 1050 + w_ * 150), (dx + 100, oy + 1120 + w_ * 150), "细实线")
    _t(msp, "弹簧减振器×4", (ox + L / 2, oy + 700), 2.0 * s, align=MC, layer="文字", tracker=tracker)
    # 混凝土基础
    _rect(msp, ox - 300, oy, ox + L + 300, oy + 600, "设备")
    for k in range(int((L + 600) / 300)):
        _ln(msp, (ox - 300 + k * 300, oy), (ox - 300 + k * 300 - 100, oy + 600), "细实线")
    _t(msp, "钢筋混凝土基础（惰性块，质量≥3倍风机）", (ox + L / 2, oy - 5 * s), 2.2 * s,
       align=MC, layer="文字", tracker=tracker)
    if label:
        _t(msp, label, (ox + L / 2, oy + 2200), 3.2 * s, align=MC, layer="文字-标题", tracker=tracker)
    return (ox + L, oy)


# ═══ 6. 安装系统图 ═══
def draw_fan_installation(msp, origin, p: dict, scale: float = 100.0,
                          label: str = "风机安装系统图", tracker=None):
    s = scale
    ox, oy = _r(*origin)
    W = p["W"]
    R = W / 2.0
    cx, cy = ox + 6000, oy + R + 1000
    # 进口软接 + 风管
    _ln(msp, (ox, cy), (cx - R - 800, cy), "设备")
    _rect(msp, cx - R - 800, cy - p["inlet_dn"] / 2, cx - R, cy + p["inlet_dn"] / 2, "细实线")
    _t(msp, "进口软接（帆布）", (cx - R - 400, cy + p["inlet_dn"] / 2 + 3 * s), 2.0 * s,
       align=MC, layer="文字", tracker=tracker)
    # 风机蜗壳
    _circle(msp, (cx, cy), R, "设备")
    _circle(msp, (cx, cy), p["inlet_dn"] / 2.0, "设备")
    # 电机 + 联轴器防护罩
    _motor(msp, cx + R + 400, cy - 400, 900, 800)
    _rect(msp, cx + R + 200, cy - 250, cx + R + 500, cy + 250, "细实线")
    _t(msp, "联轴器防护罩", (cx + R + 350, cy - 550), 2.0 * s, align=MC, layer="文字", tracker=tracker)
    # 出口软接 + 排气
    odn = p["outlet_dn"]
    _rect(msp, cx - odn / 2, cy + R, cx + odn / 2, cy + R + 600, "细实线")
    _ln(msp, (cx - odn / 2, cy + R + 600), (cx - odn / 2, cy + R + odn), "设备")
    _ln(msp, (cx + odn / 2, cy + R + 600), (cx + odn / 2, cy + R + odn), "设备")
    _tri(msp, (cx, cy + R + odn + 3 * s), (0, 1), s, "设备")
    _t(msp, "出口软接→排气筒", (cx + odn, cy + R + odn), 2.0 * s, align=ML, layer="文字", tracker=tracker)
    # 底座 + 减振器
    _rect(msp, ox + 2000, oy, ox + 6000 + p["L"] - 2000, oy + 300, "设备")
    for i in range(3):
        _rect(msp, ox + 2500 + i * 2000, oy + 300, ox + 2700 + i * 2000, oy + 600, "设备")
    _t(msp, "减振器+基础", (ox + 4000, oy - 4 * s), 2.0 * s, align=MC, layer="文字", tracker=tracker)
    _t(msp, f"离心风机 {p['air_flow']:.0f}m³/h {p['pressure']:.0f}Pa 电机{p['N_rated']}kW",
       (cx, oy - 9 * s), 2.4 * s, align=MC, layer="文字-标题", tracker=tracker)
    if label:
        _t(msp, label, (cx, cy + R + odn + 8 * s), 3.2 * s, align=MC, layer="文字-标题", tracker=tracker)
    return (cx, oy)
