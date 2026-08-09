# -*- coding: utf-8 -*-
"""石灰石-石膏湿法脱硫塔多视图制图 v1.0（HJ 2001、HJ/T 179、DL/T 5196）。

喷淋空塔成套视图：外形总图(正立面)、纵剖面、喷淋层平面、除雾器详图、
循环浆液系统。所有几何参数以 dict 传入（默认取
knowledge.fgd_data.FGD_DEFAULTS）——本模块只负责"画"，不负责"算"。

坐标单位 mm，scale=出图比例倒数(1:100 → 100)。图层沿用包内中文命名。
"""
from __future__ import annotations

import math

from ezdxf.enums import TextEntityAlignment

from ..utils import _r, _tri
from .annotate import _t
from ..knowledge.fgd_data import FGD_DEFAULTS

MC = TextEntityAlignment.MIDDLE_CENTER
ML = TextEntityAlignment.MIDDLE_LEFT
MR = TextEntityAlignment.MIDDLE_RIGHT


# ─── 内部辅助 ─────────────────────────────────────────────

def _rect(msp, x0, y0, x1, y1, layer="设备"):
    x0, y0 = _r(x0, y0)
    msp.add_lwpolyline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)],
                       close=True, dxfattribs={"layer": layer})


def _ln(msp, p0, p1, layer="设备", linetype=None):
    a = _r(*p0)
    b = _r(*p1)
    attr = {"layer": layer}
    if linetype:
        attr["linetype"] = linetype
    msp.add_line(a, b, dxfattribs=attr)


def _circle(msp, c, r, layer="设备"):
    msp.add_circle(_r(*c), r, dxfattribs={"layer": layer})


def _params(p):
    d = dict(FGD_DEFAULTS)
    d.update(p or {})
    return d


def _vert(p):
    """竖向分段（相对 origin 底部 oy 的偏移）。"""
    sump = p["sump_H"]
    inlet_top = sump + p["inlet_H"] + p["inlet_Hh"] / 2.0
    spray0 = sump + p["inlet_H"] + p["inlet_Hh"]   # 喷淋区起
    spray_top = spray0 + p["spray_zone_H"]
    dem_top = spray_top + p["demister_H"]
    top = dem_top + p["outlet_H"]
    return dict(sump=sump, spray0=spray0, spray_top=spray_top,
                dem_top=dem_top, top=top)


# ══════════════════════════════════════════════════════════
#  1. 外形总图 — 正立面
# ══════════════════════════════════════════════════════════

def draw_fgd_elevation(msp, origin, p=None, scale=100.0,
                       label="脱硫吸收塔外形图", tracker=None):
    """正立面：浆池段/入口烟道/喷淋段/除雾段/出口/循环泵组。"""
    p = _params(p)
    s = scale
    ox, oy = _r(*origin)
    D = p["tower_D"]
    v = _vert(p)
    cx = ox + D / 2.0

    y_sump = oy + v["sump"]
    y_sp0 = oy + v["spray0"]
    y_spt = oy + v["spray_top"]
    y_dem = oy + v["dem_top"]
    y_top = oy + v["top"]

    # 塔体外轮廓
    _rect(msp, ox, oy, ox + D, y_dem, "设备")
    # 锥顶 + 出口烟道
    _ln(msp, (ox, y_dem), (cx - p["outlet_dn"] / 2, y_top), "设备")
    _ln(msp, (ox + D, y_dem), (cx + p["outlet_dn"] / 2, y_top), "设备")
    _rect(msp, cx - p["outlet_dn"] / 2, y_top, cx + p["outlet_dn"] / 2,
          y_top + p["outlet_dn"] * 0.8, "设备")
    _tri(msp, (cx, y_top + p["outlet_dn"] * 0.8 + 3 * s), (0, 1), s, "设备")
    _t(msp, f"净烟气出口 Φ{p['outlet_dn']:.0f}", (cx + 8 * s, y_top + 200),
       2.2 * s, align=ML, layer="文字", tracker=tracker)

    # 浆池段
    _t(msp, "浆液池", (cx, oy + v["sump"] * 0.55), 2.5 * s, align=MC,
       layer="文字", tracker=tracker)
    # 搅拌器（侧进 2 台示意）
    for k in (0.3, 0.7):
        mx = ox + D * k
        _circle(msp, (mx, oy + sump_cy(p)), 250, "设备")
        _ln(msp, (mx, oy + sump_cy(p)), (mx, oy + sump_cy(p) - 800), "设备")
    _t(msp, "侧进搅拌器", (ox - 3 * s, oy + sump_cy(p)), 2.0 * s, align=MR,
       layer="文字", tracker=tracker)

    # 入口烟道（斜插入塔，向下倾 15° 示意）
    iw, ih = p["inlet_W"], p["inlet_Hh"]
    iy = oy + v["sump"] + p["inlet_H"]
    _rect(msp, ox - iw, iy - ih / 2, ox, iy + ih / 2, "设备")
    _tri(msp, (ox - iw - 3 * s, iy), (1, 0), s, "设备")
    _t(msp, f"原烟气入口 {iw:.0f}×{ih:.0f}", (ox - iw / 2, iy + ih / 2 + 4 * s),
       2.2 * s, align=MC, layer="文字", tracker=tracker)

    # 喷淋层（横线 + 喷嘴倒三角）
    n_sp = p["n_spray"]
    for i in range(n_sp):
        ly = y_sp0 + p["spray_pitch"] * (i + 0.5)
        _ln(msp, (ox, ly), (ox + D, ly), "设备")
        for j in range(7):
            nx = ox + D * (j + 0.5) / 7.0
            _tri(msp, (nx, ly - 120), (0, -1), s * 0.5, "细实线")
        _t(msp, f"{i+1}#喷淋层", (ox + D + 3 * s, ly), 2.0 * s, align=ML,
           layer="文字", tracker=tracker)

    # 除雾器（两级折线）
    for k in (0.35, 0.7):
        dy = y_spt + (y_dem - y_spt) * k
        _ln(msp, (ox, dy), (ox + D, dy), "设备")
        _ln(msp, (ox, dy + 150), (ox + D, dy + 150), "细实线")
    _t(msp, "两级除雾器", (ox + D + 3 * s, (y_spt + y_dem) / 2), 2.0 * s,
       align=ML, layer="文字", tracker=tracker)

    # 循环泵组（塔右侧 3 台）
    n_pump = p["n_pump"]
    for i in range(n_pump):
        px = ox + D + 4500
        py = oy + 600 + i * 900
        _circle(msp, (px, py), 300, "设备")
        _rect(msp, px - 450, py - 150, px - 300, py + 150, "设备")
        # 管线：泵出口 → 喷淋层
        ly = y_sp0 + p["spray_pitch"] * (i + 0.5)
        _ln(msp, (px + 300, py), (px + 300, ly), "管道-加药")
        _ln(msp, (px + 300, ly), (ox + D, ly), "管道-加药")
        # 泵进口 ← 浆池
        _ln(msp, (ox + D, oy + 800), (px - 450, py), "管道-加药")
    _t(msp, "循环泵组", (ox + D + 4500, oy - 3 * s), 2.2 * s, align=MC,
       layer="文字", tracker=tracker)

    if label:
        _t(msp, label, (cx, oy - 8 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (cx, oy, y_top + p["outlet_dn"] * 0.8)


def sump_cy(p):
    return p["sump_H"] * 0.4


# ══════════════════════════════════════════════════════════
#  2. 纵剖面图
# ══════════════════════════════════════════════════════════

def draw_fgd_section(msp, origin, p=None, scale=100.0,
                     label="1-1 剖面图", tracker=None):
    """纵剖面：浆池(氧化喷枪)/喷淋层/除雾器/支撑梁。"""
    p = _params(p)
    s = scale
    ox, oy = _r(*origin)
    D = p["tower_D"]
    v = _vert(p)
    cx = ox + D / 2.0
    y_sump = oy + v["sump"]
    y_sp0 = oy + v["spray0"]
    y_spt = oy + v["spray_top"]
    y_dem = oy + v["dem_top"]

    # 塔壁剖切
    _rect(msp, ox, oy, ox + D, y_dem, "设备")
    # 浆液面
    _ln(msp, (ox + 150, y_sump - 600), (ox + D - 150, y_sump - 600), "池体-水")
    _t(msp, "浆液面", (ox + D - 400, y_sump - 400), 2.0 * s, align=MR,
       layer="文字", tracker=tracker)
    # 氧化空气喷枪（2 支斜插）
    for k in (0.35, 0.65):
        gx = ox + D * k
        _ln(msp, (gx - 300, y_sump + 500), (gx, y_sump - 1000), "管道-加药")
    _t(msp, "氧化空气喷枪", (ox - 3 * s, y_sump - 800), 2.0 * s, align=MR,
       layer="文字", tracker=tracker)
    # 搅拌器剖面（桨叶）
    mx = ox + D * 0.3
    my = oy + sump_cy(p)
    _circle(msp, (mx, my), 200, "设备")
    for ang in (45, 135, 225, 315):
        a = math.radians(ang)
        _ln(msp, (mx, my), (mx + 380 * math.cos(a), my + 380 * math.sin(a)),
            "细实线")

    # 喷淋层剖面（母管+喷嘴）
    for i in range(p["n_spray"]):
        ly = y_sp0 + p["spray_pitch"] * (i + 0.5)
        _ln(msp, (ox, ly), (ox + D, ly), "设备")
        for j in range(5):
            nx = ox + D * (j + 0.5) / 5.0
            _tri(msp, (nx, ly - 150), (0, -1), s * 0.5, "细实线")
    # 支撑梁（除雾器下）
    _ln(msp, (ox, y_spt), (ox + D, y_spt), "设备")
    for k in (0.25, 0.5, 0.75):
        _rect(msp, ox + D * k - 75, y_spt - 150, ox + D * k + 75, y_spt, "设备")

    # 除雾器折流板（W 形）
    for k in (0.3, 0.65):
        dy = y_spt + (y_dem - y_spt) * k
        x = ox
        up = True
        pts = []
        while x <= ox + D:
            pts.append(_r(x, dy + (150 if up else 0)))
            x += D / 12.0
            up = not up
        msp.add_lwpolyline(pts, dxfattribs={"layer": "设备"})
    _t(msp, "屋脊式除雾器×2", (cx, y_dem - 3 * s), 2.2 * s, align=MC,
       layer="文字", tracker=tracker)

    if label:
        _t(msp, label, (cx, oy - 8 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (cx, oy, y_dem)


# ══════════════════════════════════════════════════════════
#  3. 喷淋层平面布置图
# ══════════════════════════════════════════════════════════

def draw_fgd_spray_layer(msp, origin, p=None, scale=100.0,
                         label="喷淋层平面布置图", tracker=None):
    """俯视单层：母管 + 鱼骨支管 + 喷嘴阵 + 覆盖率标注。"""
    p = _params(p)
    s = scale
    ox, oy = _r(*origin)
    D = p["tower_D"]
    cx, cy = ox + D / 2.0, oy + D / 2.0

    # 塔截面圆
    _circle(msp, (cx, cy), D / 2.0, "设备")
    # 中心十字线
    _ln(msp, (ox - 3 * s, cy), (ox + D + 3 * s, cy), "点画线", linetype="CENTER")
    _ln(msp, (cx, oy - 3 * s), (cx, oy + D + 3 * s), "点画线", linetype="CENTER")

    # 母管（穿心）
    _ln(msp, (ox - 800, cy), (ox + D, cy), "设备")
    _rect(msp, ox - 800, cy - 150, ox - 500, cy + 150, "设备")
    _t(msp, f"母管 Φ{p['spray_main_dn']:.0f}", (ox - 900, cy + 4 * s),
       2.0 * s, align=ML, layer="文字", tracker=tracker)

    # 支管（鱼骨，上下交替）+ 喷嘴
    pitch = p["nozzle_pitch"]
    n_branch = int(D / (pitch * 2))
    for i in range(n_branch):
        bx = ox + D * (i + 0.5) / n_branch
        for sgn in (-1, 1):
            half = (D / 2.0) * 0.86
            _ln(msp, (bx, cy), (bx, cy + sgn * half), "细实线")
            # 喷嘴沿支管
            n_nz = int(half / pitch)
            for j in range(1, n_nz + 1):
                ny = cy + sgn * j * pitch
                _circle(msp, (bx, ny), 90, "设备")
                _ln(msp, (bx, ny), (bx + 250, ny + 250), "细实线")

    _t(msp, f"喷嘴 Φ25 间距 {pitch:.0f}（覆盖率≥150%）",
       (cx, oy - 6 * s), 2.3 * s, align=MC, layer="文字", tracker=tracker)

    if label:
        _t(msp, label, (cx, oy + D + 6 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (ox + D, oy)


# ══════════════════════════════════════════════════════════
#  4. 除雾器详图
# ══════════════════════════════════════════════════════════

def draw_fgd_demister(msp, origin, p=None, scale=100.0,
                      label="除雾器详图", tracker=None):
    """两级屋脊式除雾器 + 上下冲洗水管（局部放大）。"""
    p = _params(p)
    s = scale
    ox, oy = _r(*origin)
    W = 4000.0
    level_H = 900.0
    gap = 700.0
    cx = ox + W / 2.0

    def _ridge(y0):
        x = ox
        up = True
        pts = []
        while x <= ox + W:
            pts.append(_r(x, y0 + (260 if up else 0)))
            x += W / 16.0
            up = not up
        msp.add_lwpolyline(pts, dxfattribs={"layer": "设备"})
        # 后排板（双线表厚度）
        pts2 = [(px, py + 90) for px, py in pts]
        msp.add_lwpolyline(pts2, dxfattribs={"layer": "细实线"})

    # 第一级 / 第二级
    _ridge(oy)
    _ridge(oy + level_H + gap)
    _t(msp, "第一级(粗除雾)", (ox + W + 3 * s, oy + 200), 2.0 * s, align=ML,
       layer="文字", tracker=tracker)
    _t(msp, "第二级(精除雾)", (ox + W + 3 * s, oy + level_H + gap + 200),
       2.0 * s, align=ML, layer="文字", tracker=tracker)

    # 冲洗水管（级下/级间/级上 3 排）
    for k, wy in enumerate((oy - 500, oy + level_H + gap / 2,
                            oy + 2 * level_H + gap + 400)):
        _ln(msp, (ox, wy), (ox + W, wy), "管道-给水")
        for j in range(6):
            nx = ox + W * (j + 0.5) / 6.0
            _tri(msp, (nx, wy + 120), (0, 1), s * 0.4, "细实线")
    _t(msp, "冲洗水（上/中/下 3 排）", (cx, oy - 9 * s), 2.0 * s, align=MC,
       layer="文字", tracker=tracker)

    # 支撑梁
    _rect(msp, ox - 150, oy - 260, ox + W + 150, oy - 60, "设备")

    if label:
        _t(msp, label, (cx, oy + 2 * level_H + gap + 8 * s), 3.2 * s,
           align=MC, layer="文字-标题", tracker=tracker)
    return (ox + W, oy)


# ══════════════════════════════════════════════════════════
#  5. 循环浆液系统图
# ══════════════════════════════════════════════════════════

def draw_fgd_circulation(msp, origin, p=None, scale=100.0,
                         label="循环浆液系统图", tracker=None):
    """系统图：浆池 → 循环泵 → 喷淋层 → 塔内回落，含阀门/流量计。"""
    p = _params(p)
    s = scale
    ox, oy = _r(*origin)
    W = 9000.0
    H = 6000.0

    # 塔（左侧简化方块）
    _rect(msp, ox, oy, ox + 2500, oy + H, "设备")
    _t(msp, "吸收塔", (ox + 1250, oy + H + 3 * s), 2.5 * s, align=MC,
       layer="文字", tracker=tracker)
    # 浆池液位
    _ln(msp, (ox + 200, oy + 1500), (ox + 2300, oy + 1500), "池体-水")
    _t(msp, "浆池", (ox + 1250, oy + 800), 2.2 * s, align=MC, layer="文字",
       tracker=tracker)
    # 喷淋层标记
    n_sp = p["n_spray"]
    for i in range(n_sp):
        ly = oy + H * 0.5 + i * 900
        _ln(msp, (ox + 300, ly), (ox + 2200, ly), "设备")
        _t(msp, f"{i+1}#喷淋", (ox + 1250, ly + 250), 1.8 * s, align=MC,
           layer="文字", tracker=tracker)

    # 循环泵（右侧对应每层一台）
    for i in range(n_sp):
        py = oy + H * 0.5 + i * 900
        px = ox + 5500
        _circle(msp, (px, py - 1800), 280, "设备")
        _t(msp, f"循环泵{chr(65+i)}", (px, py - 2300), 2.0 * s, align=MC,
           layer="文字", tracker=tracker)
        # 吸入管：浆池 → 泵
        _ln(msp, (ox + 2500, oy + 900), (px, oy + 900), "管道-加药")
        _ln(msp, (px, oy + 900), (px, py - 2080), "管道-加药")
        # 吸入阀
        _rect(msp, ox + 3500, oy + 750, ox + 3700, oy + 1050, "阀门")
        # 压出管：泵 → 喷淋层
        _ln(msp, (px, py - 1520), (px, py), "管道-加药")
        _ln(msp, (px, py), (ox + 2500, py), "管道-加药")
        _tri(msp, (ox + 2600, py), (1, 0), s * 0.6, "流向")
        # 出口阀 + 流量计
        _rect(msp, px - 180, py - 900, px + 180, py - 600, "阀门")
        _circle(msp, (ox + 4000, py), 150, "阀门")

    # 图注
    _t(msp, "□—阀门  ○—泵/流量计", (ox + 4500, oy - 3 * s), 2.0 * s,
       align=MC, layer="文字", tracker=tracker)

    if label:
        _t(msp, label, (ox + 4500, oy + H + 8 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (ox + W, oy)
