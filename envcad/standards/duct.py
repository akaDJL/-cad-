# -*- coding: utf-8 -*-
"""风管系统多视图制图 v1.0（GB 50243、通风与空调工程施工质量验收规范）。

废气风管系统的成套视图：平面布置、立面、弯头、三通、变径、支吊架。
几何参数由 design.env_process.design_duct_full 算出并以 dict 传入。

坐标单位 mm。风管以双线（间距=管径）表示。图层沿用包内中文命名。
"""
from __future__ import annotations

import math

from ezdxf.enums import TextEntityAlignment

from ..utils import _r, _tri
from .annotate import _t, draw_elevation

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


def _duct_h(msp, x0, x1, y, dn, layer="设备"):
    """水平风管（双线，间距 dn）。"""
    _ln(msp, (x0, y - dn / 2), (x1, y - dn / 2), layer)
    _ln(msp, (x0, y + dn / 2), (x1, y + dn / 2), layer)


def _duct_v(msp, y0, y1, x, dn, layer="设备"):
    """竖直风管（双线）。"""
    _ln(msp, (x - dn / 2, y0), (x - dn / 2, y1), layer)
    _ln(msp, (x + dn / 2, y0), (x + dn / 2, y1), layer)


def _flange(msp, x, y, dn, orient="v", layer="细实线"):
    """法兰（管上一道线）。"""
    if orient == "v":
        _ln(msp, (x, y - dn / 2 - 100), (x, y + dn / 2 + 100), layer)
    else:
        _ln(msp, (x - dn / 2 - 100, y), (x + dn / 2 + 100, y), layer)


def _damper(msp, x, y, dn, layer="设备"):
    """风阀（蝶阀符号）。"""
    _circle(msp, (x, y), dn / 2.0, layer)
    _ln(msp, (x - dn / 2, y - dn / 2), (x + dn / 2, y + dn / 2), "细实线")


# ═══ 1. 平面布置图 ═══
def draw_duct_plan(msp, origin, p: dict, scale: float = 100.0,
                   label: str = "风管平面布置图", tracker=None):
    s = scale
    ox, oy = _r(*origin)
    dn = p["dn"]
    R = p["elbow_r"]

    # 主管（水平段1）
    y1 = oy + 12000
    _duct_h(msp, ox, ox + 9000, y1, dn)
    _flange(msp, ox + 3000, y1, dn)
    _damper(msp, ox + 5000, y1, dn)
    _t(msp, f"主管 Φ{dn:.0f}", (ox + 2000, y1 + dn / 2 + 3 * s), 2.2 * s,
       align=MC, layer="文字", tracker=tracker)
    _t(msp, "风阀", (ox + 5000, y1 - dn / 2 - 3 * s), 2.0 * s, align=MC, layer="文字", tracker=tracker)

    # 90° 弯头（向右转下）
    ecx = ox + 9000
    ecy = y1
    msp.add_arc(_r(ecx, ecy - R), R, 0, 90, dxfattribs={"layer": "设备"})
    _t(msp, f"弯头 R={R:.0f}", (ecx + R * 0.7, ecy - R * 0.7 + 3 * s), 2.0 * s,
       align=ML, layer="文字", tracker=tracker)

    # 竖直段（向下）
    vx = ecx + R
    _duct_v(msp, ecy - R, ecy - R - 6000, vx, dn)

    # 三通（支管向右）
    ty = ecy - R - 6000
    _duct_h(msp, vx, vx + 6000, ty, dn)
    _t(msp, "三通", (vx + 1000, ty + dn / 2 + 3 * s), 2.0 * s, align=MC, layer="文字", tracker=tracker)

    # 变径（主管继续向下，dn→0.7dn）
    dn2 = dn * 0.7
    _ln(msp, (vx - dn / 2, ty - 500), (vx - dn2 / 2, ty - 500 - p["reducer_len"]), "设备")
    _ln(msp, (vx + dn / 2, ty - 500), (vx + dn2 / 2, ty - 500 - p["reducer_len"]), "设备")
    _t(msp, f"变径 Φ{dn:.0f}→Φ{dn2:.0f}", (vx + 800, ty - 500 - p["reducer_len"] / 2),
       2.0 * s, align=ML, layer="文字", tracker=tracker)
    _duct_v(msp, ty - 500 - p["reducer_len"], ty - 500 - p["reducer_len"] - 3000, vx, dn2)

    # 设备连接标记
    _t(msp, "至除尘器", (ox, y1 + 3 * s), 2.2 * s, align=ML, layer="文字", tracker=tracker)
    _t(msp, "至风机", (vx + 6000, ty + 3 * s), 2.2 * s, align=ML, layer="文字", tracker=tracker)

    if label:
        _t(msp, label, (ox + 8000, oy + 20000), 3.2 * s, align=MC, layer="文字-标题", tracker=tracker)
    return (ox + 16000, oy)


# ═══ 2. 立面图（标高+支吊架）═══
def draw_duct_elevation(msp, origin, p: dict, scale: float = 100.0,
                        label: str = "风管立面图", tracker=None):
    s = scale
    ox, oy = _r(*origin)
    dn = p["dn"]
    L = 18000.0

    # 风管（水平双线）
    _duct_h(msp, ox, ox + L, oy, dn)
    # 支吊架（竖吊杆）
    n = int(L / p["hanger_gap"]) + 1
    for i in range(n + 1):
        hx = ox + i * p["hanger_gap"]
        if hx <= ox + L:
            _ln(msp, (hx, oy + dn / 2), (hx, oy + dn / 2 + 1500), "设备")
            _rect(msp, hx - 150, oy + dn / 2 + 1500, hx + 150, oy + dn / 2 + 1700, "设备")
    _t(msp, f"支吊架间距 {p['hanger_gap']/1000:.0f}m", (ox + L / 2, oy + dn / 2 + 2200),
       2.0 * s, align=MC, layer="文字", tracker=tracker)
    # 标高
    draw_elevation(msp, (ox, oy - dn / 2), "+4.500", scale, side="left", level=0, tracker=tracker)
    draw_elevation(msp, (ox + L, oy - dn / 2), "+4.500", scale, side="right", level=0, tracker=tracker)
    _t(msp, f"风管 Φ{dn:.0f} 钢板厚 {p['plate_t']}mm", (ox + L / 2, oy - dn / 2 - 4 * s),
       2.2 * s, align=MC, layer="文字", tracker=tracker)

    if label:
        _t(msp, label, (ox + L / 2, oy + dn / 2 + 3500), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (ox + L, oy)


# ═══ 3. 弯头详图 ═══
def draw_duct_elbow(msp, origin, p: dict, scale: float = 100.0,
                    label: str = "弯头详图", tracker=None):
    s = scale
    ox, oy = _r(*origin)
    dn = p["dn"]
    R = p["elbow_r"]
    # 内外两弧（90°）
    msp.add_arc(_r(ox, oy), R + dn / 2, 0, 90, dxfattribs={"layer": "设备"})
    msp.add_arc(_r(ox, oy), R - dn / 2, 0, 90, dxfattribs={"layer": "设备"})
    msp.add_arc(_r(ox, oy), R, 0, 90, dxfattribs={"layer": "中心线", "linetype": "CENTER"})
    # 两端直段+法兰
    _duct_h(msp, ox + R, ox + R + 2000, oy + dn / 2 + (R - dn / 2) * 0, dn)  # 简化
    _ln(msp, (ox + R - dn / 2, oy), (ox + R - dn / 2, oy - 2000), "设备")
    _ln(msp, (ox + R + dn / 2, oy), (ox + R + dn / 2, oy - 2000), "设备")
    _ln(msp, (ox, oy + R - dn / 2), (ox - 2000, oy + R - dn / 2), "设备")
    _ln(msp, (ox, oy + R + dn / 2), (ox - 2000, oy + R + dn / 2), "设备")
    _flange(msp, ox + R, oy - 1500, dn, orient="v")
    _t(msp, f"90°弯头 Φ{dn:.0f} 曲率半径 R={R:.0f}（{p['elbow_r']/dn:.1f}D）",
       (ox + R / 2, oy - 8 * s), 2.2 * s, align=MC, layer="文字", tracker=tracker)
    if label:
        _t(msp, label, (ox + R / 2, oy + R + dn / 2 + 5 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (ox + R, oy)


# ═══ 4. 三通详图 ═══
def draw_duct_tee(msp, origin, p: dict, scale: float = 100.0,
                  label: str = "三通详图", tracker=None):
    s = scale
    ox, oy = _r(*origin)
    dn = p["dn"]
    dn_b = dn * 0.7          # 支管
    # 主管（水平双线）
    _duct_h(msp, ox, ox + 6000, oy, dn)
    _flange(msp, ox, oy, dn)
    _flange(msp, ox + 6000, oy, dn)
    # 支管（竖直双线，接主管中部）
    bx = ox + 3000
    _duct_v(msp, oy + dn / 2, oy + dn / 2 + 4000, bx, dn_b)
    _flange(msp, bx, oy + dn / 2 + 4000, dn_b, orient="h")
    _t(msp, f"主管 Φ{dn:.0f}", (ox + 1500, oy + dn / 2 + 3 * s), 2.0 * s, align=MC,
       layer="文字", tracker=tracker)
    _t(msp, f"支管 Φ{dn_b:.0f}", (bx + dn_b / 2 + 3 * s, oy + dn / 2 + 2000), 2.0 * s,
       align=ML, layer="文字", tracker=tracker)
    _t(msp, "三通（主管×支管，法兰连接）", (ox + 3000, oy - dn / 2 - 5 * s), 2.2 * s,
       align=MC, layer="文字", tracker=tracker)
    if label:
        _t(msp, label, (ox + 3000, oy + dn / 2 + 5500), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (ox + 6000, oy)


# ═══ 5. 变径详图 ═══
def draw_duct_reducer(msp, origin, p: dict, scale: float = 100.0,
                      label: str = "变径详图", tracker=None):
    s = scale
    ox, oy = _r(*origin)
    dn = p["dn"]
    dn2 = dn * 0.7
    rl = p["reducer_len"]
    # 大径直段
    _duct_h(msp, ox, ox + 1000, oy, dn)
    _flange(msp, ox, oy, dn)
    # 变径（同心渐缩）
    _ln(msp, (ox + 1000, oy - dn / 2), (ox + 1000 + rl, oy - dn2 / 2), "设备")
    _ln(msp, (ox + 1000, oy + dn / 2), (ox + 1000 + rl, oy + dn2 / 2), "设备")
    # 小径直段
    _duct_h(msp, ox + 1000 + rl, ox + 2000 + rl, oy, dn2)
    _flange(msp, ox + 2000 + rl, oy, dn2)
    _t(msp, f"Φ{dn:.0f}", (ox + 500, oy + dn / 2 + 3 * s), 2.0 * s, align=MC, layer="文字", tracker=tracker)
    _t(msp, f"Φ{dn2:.0f}", (ox + 1500 + rl, oy + dn2 / 2 + 3 * s), 2.0 * s, align=MC, layer="文字", tracker=tracker)
    _t(msp, f"同心变径 L={rl:.0f}mm", (ox + 1000 + rl / 2, oy - dn / 2 - 4 * s), 2.2 * s,
       align=MC, layer="文字", tracker=tracker)
    if label:
        _t(msp, label, (ox + 1000 + rl / 2, oy + dn / 2 + 6 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (ox + 2000 + rl, oy)


# ═══ 6. 支吊架详图 ═══
def draw_duct_hanger(msp, origin, p: dict, scale: float = 100.0,
                     label: str = "支吊架详图", tracker=None):
    s = scale
    ox, oy = _r(*origin)
    dn = p["dn"]
    # 楼板（顶部）
    _ln(msp, (ox - 1500, oy + 3000), (ox + 1500, oy + 3000), "设备")
    for k in range(-5, 6):
        _ln(msp, (ox + k * 300, oy + 3000), (ox + k * 300 - 150, oy + 3150), "细实线")
    _t(msp, "楼板", (ox + 1600, oy + 3050), 2.0 * s, align=ML, layer="文字", tracker=tracker)
    # 吊杆
    _ln(msp, (ox, oy + 3000), (ox, oy + dn / 2 + 500), "设备")
    # 膨胀螺栓
    _rect(msp, ox - 100, oy + 2900, ox + 100, oy + 3000, "设备")
    # 横担（槽钢）
    _rect(msp, ox - dn / 2 - 300, oy + dn / 2 + 300, ox + dn / 2 + 300, oy + dn / 2 + 500, "设备")
    # 风管（圆）
    _circle(msp, (ox, oy), dn / 2.0, "设备")
    # 抱箍
    _ln(msp, (ox - dn / 2 - 200, oy + dn / 2 + 300), (ox - dn / 2, oy), "设备")
    _ln(msp, (ox + dn / 2 + 200, oy + dn / 2 + 300), (ox + dn / 2, oy), "设备")
    _t(msp, f"吊杆Φ10  横担槽钢  抱箍", (ox + dn / 2 + 500, oy + dn / 2 + 400),
       2.0 * s, align=ML, layer="文字", tracker=tracker)
    _t(msp, f"风管 Φ{dn:.0f}  支吊架间距 {p['hanger_gap']/1000:.0f}m",
       (ox, oy - dn / 2 - 5 * s), 2.2 * s, align=MC, layer="文字", tracker=tracker)
    if label:
        _t(msp, label, (ox, oy + 3600), 3.2 * s, align=MC, layer="文字-标题", tracker=tracker)
    return (ox, oy)
