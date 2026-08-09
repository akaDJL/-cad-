# -*- coding: utf-8 -*-
"""湿法脱硫塔（喷淋吸收塔）多视图制图 v1.0（HJ 2001、GB 16297、火电厂脱硫规范）。

石灰石-石膏湿法脱硫塔的成套视图：外形总图(正立面/平面)、纵剖面、喷淋层、
除雾器、浆池及循环系统。几何参数由 design.env_process.design_spray_tower_full
从输入条件(烟气量/SO2/液气比)算出并以 dict 传入——本模块只负责"画"。

坐标单位 mm（design 返回的塔径 m，此处 ×1000 转 mm）。图层沿用包内中文命名。
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
    """竖向关键标高（相对浆池底 oy 的 mm 偏移）。"""
    H_pool = p["H_pool"]
    inlet_H = p["inlet_H"]
    H_absorb = p["H_absorb"]            # = inlet_H + n_spray*layer_gap
    H_dem = p["H_demister"]
    y0 = 0.0
    y1 = y0 + H_pool                    # 浆池顶 = 塔身底
    y_sp0 = y1 + inlet_H                # 首层喷淋
    y_ab = y1 + H_absorb                # 吸收区顶（末层喷淋上）
    y_top = y_ab + H_dem                # 塔顶
    return dict(y0=y0, y1=y1, y_sp0=y_sp0, y_ab=y_ab, y_top=y_top)


# ═══ 1. 外形总图 — 正立面 ═══
def draw_spray_tower_elevation(msp, origin, p: dict, scale: float = 100.0,
                               label: str = "脱硫塔外形图", tracker=None):
    s = scale
    ox, oy = _r(*origin)      # origin = 浆池底左端（以浆池宽为基）
    D = p["D"] * 1000.0
    Dp = p["D_pool"] * 1000.0
    z = _zones(p)
    cx = ox + Dp / 2.0
    tx = cx - D / 2.0          # 塔身左界

    # 浆池段（粗）
    _rect(msp, ox, oy + z["y0"], ox + Dp, oy + z["y1"], "设备")
    # 塔身（细）
    _rect(msp, tx, oy + z["y1"], tx + D, oy + z["y_top"], "设备")
    # 塔顶椭圆
    msp.add_ellipse(_r(cx, oy + z["y_top"]), major_axis=(D / 2.0, 0),
                    ratio=0.18, dxfattribs={"layer": "设备"})

    # 搅拌器（浆池侧进式，斜线）
    for i in range(2):
        my = oy + z["y0"] + p["H_pool"] * (0.3 + 0.3 * i)
        _ln(msp, (ox + Dp, my), (ox + Dp - 600, my - 250), "细实线")
        _circle(msp, (ox + Dp - 600, my - 250), 120, "细实线")
    _t(msp, "侧进搅拌器", (ox + Dp + 200, oy + z["y0"] + p["H_pool"] * 0.45),
       2.0 * s, align=ML, layer="文字", tracker=tracker)

    # 进口烟道（塔身下部左侧，方形）
    idn = p["inlet_dn"]
    iy = oy + z["y1"] + p["inlet_H"] * 0.4
    _rect(msp, tx - idn, iy - idn / 2, tx, iy + idn / 2, "设备")
    _tri(msp, (tx - idn - 3 * s, iy), (1, 0), s, "设备")
    _t(msp, f"进口烟道 {idn:.0f}×{idn:.0f}", (tx - idn / 2, iy - idn / 2 - 4 * s),
       2.2 * s, align=MC, layer="文字", tracker=tracker)

    # 喷淋层（吸收区横线）
    for i in range(p["n_spray"]):
        sy = oy + z["y_sp0"] + i * p["layer_gap"]
        _ln(msp, (tx, sy), (tx + D, sy), "细实线")
    _t(msp, f"喷淋层×{p['n_spray']}", (cx, oy + z["y_sp0"] + p["n_spray"] * p["layer_gap"] / 2),
       2.0 * s, align=ML, layer="文字", tracker=tracker)

    # 除雾器（顶部 2 折线）
    for j in range(2):
        dy = oy + z["y_ab"] + p["H_demister"] * (0.3 + 0.35 * j)
        _ln(msp, (tx, dy), (cx, dy + 300), "设备")
        _ln(msp, (cx, dy + 300), (tx + D, dy), "设备")
    _t(msp, "除雾器", (tx + D + 200, oy + z["y_ab"] + p["H_demister"] * 0.5),
       2.0 * s, align=ML, layer="文字", tracker=tracker)

    # 出口烟道（塔顶）
    odn = p["outlet_dn"]
    _rect(msp, cx - odn / 2, oy + z["y_top"], cx + odn / 2, oy + z["y_top"] + odn, "设备")
    _tri(msp, (cx, oy + z["y_top"] + odn + 3 * s), (0, 1), s, "设备")
    _t(msp, f"出口 {odn:.0f}×{odn:.0f}", (cx, oy + z["y_top"] + odn + 6 * s),
       2.2 * s, align=MC, layer="文字", tracker=tracker)

    # 循环泵（浆池右侧竖排）
    for i in range(p["n_pump"]):
        py_ = oy + z["y0"] + 300 + i * 500
        _rect(msp, ox + Dp + 800, py_, ox + Dp + 1200, py_ + 300, "设备")
    _t(msp, f"循环泵×{p['n_pump']}", (ox + Dp + 1000, oy + z["y0"] - 3 * s),
       2.0 * s, align=MC, layer="文字", tracker=tracker)

    if label:
        _t(msp, label, (cx, oy - 9 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (cx, oy, oy + z["y_top"])


# ═══ 2. 外形总图 — 平面 ═══
def draw_spray_tower_plan(msp, origin, p: dict, scale: float = 100.0,
                          label: str = "平面图", tracker=None):
    s = scale
    ox, oy = _r(*origin)      # origin = 塔中心
    D = p["D"] * 1000.0
    Dp = p["D_pool"] * 1000.0

    _circle(msp, (ox, oy), Dp / 2.0, "设备")        # 浆池外圆
    _circle(msp, (ox, oy), D / 2.0, "细实线")        # 塔身内圆

    # 进口烟道（一侧）
    idn = p["inlet_dn"]
    _rect(msp, ox - Dp / 2 - idn, oy - idn / 2, ox - Dp / 2, oy + idn / 2, "设备")
    _t(msp, "进口", (ox - Dp / 2 - idn / 2, oy + idn), 2.0 * s, align=MC,
       layer="文字", tracker=tracker)
    # 循环泵（周边均布）
    for i in range(p["n_pump"]):
        a = math.pi / 4 + i * math.pi / 2
        px_ = ox + (Dp / 2 + 500) * math.cos(a)
        py_ = oy + (Dp / 2 + 500) * math.sin(a)
        _rect(msp, px_ - 250, py_ - 250, px_ + 250, py_ + 250, "设备")
    # 搅拌器（周边 2-3 个标记）
    for i in range(3):
        a = i * 2 * math.pi / 3 + math.pi / 6
        mx = ox + (Dp / 2) * math.cos(a)
        my = oy + (Dp / 2) * math.sin(a)
        _circle(msp, (mx, my), 200, "细实线")

    if label:
        _t(msp, label, (ox, oy + Dp / 2 + 6 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (ox + Dp / 2, oy)


# ═══ 3. 纵剖面图 ═══
def draw_spray_tower_section(msp, origin, p: dict, scale: float = 100.0,
                             label: str = "1-1 剖面图", tracker=None):
    s = scale
    ox, oy = _r(*origin)
    D = p["D"] * 1000.0
    Dp = p["D_pool"] * 1000.0
    z = _zones(p)
    cx = ox + Dp / 2.0
    tx = cx - D / 2.0

    # 浆池 + 塔身外壳
    _rect(msp, ox, oy + z["y0"], ox + Dp, oy + z["y1"], "设备")
    _rect(msp, tx, oy + z["y1"], tx + D, oy + z["y_top"], "设备")

    # 浆池：氧化空气管 + 液位线
    _ln(msp, (ox + 200, oy + z["y1"] * 0.4), (ox + Dp - 200, oy + z["y1"] * 0.4),
        "细实线", linetype="DASHED")
    _t(msp, "氧化空气管", (cx, oy + z["y1"] * 0.4 + 2.5 * s), 2.0 * s, align=MC,
       layer="文字", tracker=tracker)
    _ln(msp, (ox, oy + z["y1"] * 0.8), (ox + Dp, oy + z["y1"] * 0.8), "细实线")
    _t(msp, "浆液液位", (ox + Dp - 200, oy + z["y1"] * 0.8 + 2 * s), 2.0 * s,
       align=MR, layer="文字", tracker=tracker)

    # 进口烟道
    idn = p["inlet_dn"]
    iy = oy + z["y1"] + p["inlet_H"] * 0.4
    _rect(msp, tx - idn, iy - idn / 2, tx, iy + idn / 2, "设备")

    # 喷淋层：母管 + 喷嘴（向下）
    for i in range(p["n_spray"]):
        sy = oy + z["y_sp0"] + i * p["layer_gap"]
        _ln(msp, (tx, sy), (tx + D, sy), "设备")
        for k in range(1, int(D / 500) + 1):
            nx = tx + k * 500
            if nx < tx + D:
                _ln(msp, (nx, sy), (nx, sy - 150), "细实线")
    _t(msp, f"喷淋层×{p['n_spray']}（喷嘴向下）", (cx, oy + z["y_sp0"] + 4 * s),
       2.0 * s, align=MC, layer="文字", tracker=tracker)

    # 除雾器：2级屋脊折流板
    for j in range(2):
        dy = oy + z["y_ab"] + p["H_demister"] * (0.3 + 0.35 * j)
        n_plate = int(D / 300)
        for k in range(n_plate):
            px0 = tx + k * 300
            _ln(msp, (px0, dy), (px0 + 150, dy + 200), "细实线")
            _ln(msp, (px0 + 150, dy + 200), (px0 + 300, dy), "细实线")
    _t(msp, "屋脊式除雾器×2级", (cx, oy + z["y_ab"] + p["H_demister"] * 0.5),
       2.0 * s, align=ML, layer="文字", tracker=tracker)

    # 出口
    odn = p["outlet_dn"]
    _rect(msp, cx - odn / 2, oy + z["y_top"], cx + odn / 2, oy + z["y_top"] + odn, "设备")

    if label:
        _t(msp, label, (cx, oy - 9 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (cx, oy, oy + z["y_top"])


# ═══ 4. 喷淋层布置详图 ═══
def draw_spray_tower_spray_layer(msp, origin, p: dict, scale: float = 100.0,
                                 label: str = "喷淋层布置图", tracker=None):
    s = scale
    ox, oy = _r(*origin)      # origin = 塔截面中心
    D = p["D"] * 1000.0
    R = D / 2.0

    _circle(msp, (ox, oy), R, "设备")
    # 喷淋母管（直径方向）
    _ln(msp, (ox - R, oy), (ox + R, oy), "设备")
    _t(msp, "喷淋母管", (ox, oy + 3 * s), 2.0 * s, align=MC, layer="文字", tracker=tracker)
    # 支管（垂直母管，两侧均布）
    n_branch = int(D / 600)
    for i in range(1, n_branch + 1):
        bx = ox - R + D * i / (n_branch + 1)
        _ln(msp, (bx, oy - R * 0.85), (bx, oy + R * 0.85), "细实线")
        # 喷嘴（支管上）
        for j in range(-2, 3):
            ny = oy + j * R * 0.35
            if (bx - ox) ** 2 + (ny - oy) ** 2 < (R * 0.9) ** 2:
                _circle(msp, (bx, ny), 60, "设备")
    _t(msp, f"喷淋层（{p['n_spray']}层之一），喷嘴密布全截面",
       (ox, oy - R - 5 * s), 2.3 * s, align=MC, layer="文字", tracker=tracker)
    if label:
        _t(msp, label, (ox, oy + R + 6 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (ox + R, oy)


# ═══ 5. 除雾器详图 ═══
def draw_spray_tower_demister(msp, origin, p: dict, scale: float = 100.0,
                              label: str = "除雾器详图", tracker=None):
    s = scale
    ox, oy = _r(*origin)
    D = p["D"] * 1000.0
    plate_h = 400.0
    pitch = 300.0

    for lvl in range(2):
        y0 = oy + lvl * (plate_h + 600)
        n = int(D / pitch)
        for k in range(n):
            px0 = ox + k * pitch
            _ln(msp, (px0, y0), (px0 + pitch / 2, y0 + plate_h), "设备")
            _ln(msp, (px0 + pitch / 2, y0 + plate_h), (px0 + pitch, y0), "设备")
        # 冲洗水管（级上方）
        _ln(msp, (ox, y0 + plate_h + 350), (ox + D, y0 + plate_h + 350), "细实线")
        for k in range(n):
            _ln(msp, (ox + k * pitch + pitch / 2, y0 + plate_h + 350),
                (ox + k * pitch + pitch / 2, y0 + plate_h), "细实线")
        _t(msp, f"{'一' if lvl==0 else '二'}级除雾器+冲洗水",
           (ox + D + 200, y0 + plate_h / 2), 2.0 * s, align=ML, layer="文字", tracker=tracker)

    _t(msp, "屋脊式折流板除雾器（2级，带在线冲洗），出口雾滴≤75mg/m³",
       (ox + D / 2, oy - 6 * s), 2.3 * s, align=MC, layer="文字", tracker=tracker)
    if label:
        _t(msp, label, (ox + D / 2, oy + 2 * (plate_h + 600) + 5 * s), 3.2 * s,
           align=MC, layer="文字-标题", tracker=tracker)
    return (ox + D, oy)


# ═══ 6. 浆池及循环系统图 ═══
def draw_spray_tower_slurry_system(msp, origin, p: dict, scale: float = 100.0,
                                   label: str = "浆池及循环系统图", tracker=None):
    s = scale
    ox, oy = _r(*origin)      # origin = 浆池左下角
    Dp = p["D_pool"] * 1000.0
    H_pool = p["H_pool"]

    # 浆池
    _rect(msp, ox, oy, ox + Dp, oy + H_pool, "设备")
    _t(msp, f"浆池 Φ{p['D_pool']}m V={p['V_pool']}m³", (ox + Dp / 2, oy + H_pool / 2),
       2.5 * s, align=MC, layer="文字", tracker=tracker)

    # 搅拌器（侧壁 2-3 台）
    for i in range(3):
        my = oy + H_pool * (0.25 + 0.25 * i)
        _circle(msp, (ox, my), 150, "设备")
    _t(msp, "侧进式搅拌器×3", (ox - 300, oy + H_pool * 0.5), 2.0 * s,
       align=MR, layer="文字", tracker=tracker)

    # 氧化空气管（入浆池）
    _ln(msp, (ox + Dp / 2, oy + H_pool + 800), (ox + Dp / 2, oy + H_pool * 0.3), "设备")
    _t(msp, "氧化空气（氧化风机）", (ox + Dp / 2 + 300, oy + H_pool + 500),
       2.0 * s, align=ML, layer="文字", tracker=tracker)

    # 循环泵组（右侧，浆池→喷淋层）
    for i in range(p["n_pump"]):
        py_ = oy + 400 + i * 700
        _rect(msp, ox + Dp + 1500, py_, ox + Dp + 2000, py_ + 400, "设备")
        _ln(msp, (ox + Dp, py_ + 200), (ox + Dp + 1500, py_ + 200), "设备")
        _ln(msp, (ox + Dp + 1750, py_ + 400), (ox + Dp + 1750, oy + H_pool + 2000), "设备")
    _t(msp, f"浆液循环泵×{p['n_pump']}（{p['pump_q']:.0f}m³/h·台）",
       (ox + Dp + 1750, oy + H_pool + 2300), 2.0 * s, align=MC, layer="文字", tracker=tracker)

    # 石膏排出（底部）
    _ln(msp, (ox + Dp * 0.3, oy), (ox + Dp * 0.3, oy - 800), "设备")
    _tri(msp, (ox + Dp * 0.3, oy - 900), (0, -1), s, "设备")
    _t(msp, "石膏排出泵→脱水", (ox + Dp * 0.3 + 200, oy - 700), 2.0 * s,
       align=ML, layer="文字", tracker=tracker)

    if label:
        _t(msp, label, (ox + Dp / 2 + 750, oy - 8 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (ox + Dp + 2000, oy)
