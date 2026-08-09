# -*- coding: utf-8 -*-
"""溶气气浮机多视图制图 v1.0（HJ 2007、GB 50014、CECS 75）。

平流式溶气气浮成套视图：外形总图(正立面/平面)、横剖面、溶气系统、
刮渣系统。所有几何参数以 dict 传入（默认取
knowledge.daf_data.DAF_DEFAULTS）——本模块只负责"画"，不负责"算"。

坐标单位 mm，scale=出图比例倒数(1:100 → 100)。图层沿用包内中文命名。
"""
from __future__ import annotations

import math

from ezdxf.enums import TextEntityAlignment

from ..utils import _r, _tri
from .annotate import _t
from ..knowledge.daf_data import DAF_DEFAULTS

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
    d = dict(DAF_DEFAULTS)
    d.update(p or {})
    return d


# ══════════════════════════════════════════════════════════
#  1. 外形总图 — 正立面（侧视）
# ══════════════════════════════════════════════════════════

def draw_daf_elevation(msp, origin, p=None, scale=100.0,
                       label="溶气气浮机外形图", tracker=None):
    """侧视：接触区/分离区/刮渣机/集渣槽/进出水管/溶气罐(旁置)。"""
    p = _params(p)
    s = scale
    ox, oy = _r(*origin)
    cL, sL = p["contact_L"], p["sep_L"]
    H = p["pool_H"]
    L = cL + sL
    wH = p["water_H"]
    cx = ox + L / 2.0

    # 池体（U 形开口）
    _ln(msp, (ox, oy), (ox + L, oy), "池体-壁")
    _ln(msp, (ox, oy), (ox, oy + H), "池体-壁")
    _ln(msp, (ox + L, oy), (ox + L, oy + H), "池体-壁")
    _ln(msp, (ox, oy + H), (ox + L, oy + H), "细实线")   # 池顶走道

    # 接触区/分离区分隔整流板（水下开孔）
    bx = ox + cL
    _ln(msp, (bx, oy), (bx, oy + H * 0.8), "池体-壁")
    for j in range(4):
        hy = oy + H * 0.15 + H * 0.12 * j
        _circle(msp, (bx, hy), 60, "细实线")
    _t(msp, "整流板", (bx + 3 * s, oy + H * 0.85), 2.0 * s, align=ML,
       layer="文字", tracker=tracker)
    _t(msp, "接触区", (ox + cL / 2, oy + H + 3 * s), 2.2 * s, align=MC,
       layer="文字", tracker=tracker)
    _t(msp, "分离区", (ox + cL + sL / 2, oy + H + 3 * s), 2.2 * s, align=MC,
       layer="文字", tracker=tracker)

    # 水面线 + 浮渣层
    wy = oy + wH
    _ln(msp, (ox, wy), (ox + L, wy), "池体-水")
    _ln(msp, (ox + cL, wy + p["scum_t"]), (ox + L, wy + p["scum_t"]), "细实线")
    _t(msp, "浮渣层", (ox + cL + sL * 0.55, wy + p["scum_t"] + 3 * s),
       2.0 * s, align=MC, layer="文字", tracker=tracker)

    # 刮渣机（顶部链式：轨道+刮板）
    _ln(msp, (ox + cL, oy + H + 600), (ox + L, oy + H + 600), "设备")
    for k in (0.15, 0.5, 0.85):
        sx = ox + cL + sL * k
        _ln(msp, (sx, oy + H + 600), (sx, wy + p["scum_t"]), "设备")
    _t(msp, "链式刮渣机", (ox + cL + sL / 2, oy + H + 900), 2.0 * s,
       align=MC, layer="文字", tracker=tracker)

    # 集渣槽（分离区末端顶部）
    tw = p["scum_trough_W"]
    _rect(msp, ox + L - tw, wy, ox + L, wy + 500, "设备")
    _t(msp, "集渣槽", (ox + L - tw / 2, wy + 800), 2.0 * s, align=MC,
       layer="文字", tracker=tracker)

    # 进水管（接触区上部）
    idn = p["inlet_dn"]
    _rect(msp, ox - idn, wy - idn, ox, wy, "设备")
    _tri(msp, (ox - idn - 3 * s, wy - idn / 2), (1, 0), s, "流向")
    _t(msp, f"进水 DN{idn:.0f}+回流溶气水", (ox - idn / 2, wy + 3 * s),
       2.0 * s, align=MC, layer="文字", tracker=tracker)

    # 出水管（分离区末段下部，集水管）
    odn = p["outlet_dn"]
    _rect(msp, ox + L, oy + 300, ox + L + odn, oy + 300 + odn, "设备")
    _tri(msp, (ox + L + odn + 3 * s, oy + 300 + odn / 2), (1, 0), s, "流向")
    _t(msp, f"出水 DN{odn:.0f}", (ox + L + odn / 2, oy + 200), 2.0 * s,
       align=MC, layer="文字", tracker=tracker)

    # 溶气罐（旁置右侧）
    td, th = p["tank_D"], p["tank_H"]
    tx = ox + L + 2500
    _rect(msp, tx, oy, tx + td, oy + th, "设备")
    _circle(msp, (tx + td / 2, oy + th), td / 2, "设备")   # 顶部封头示意
    _t(msp, f"溶气罐 Φ{td:.0f}", (tx + td / 2, oy - 4 * s), 2.0 * s, align=MC,
       layer="文字", tracker=tracker)
    # 溶气水管：罐底 → 接触区释放器
    _ln(msp, (tx, oy + 400), (ox + cL / 2, oy + 400), "管道-给水")
    _ln(msp, (ox + cL / 2, oy + 400), (ox + cL / 2, oy + 900), "管道-给水")

    if label:
        _t(msp, label, (cx, oy - 8 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (cx, oy, oy + H + 900)


# ══════════════════════════════════════════════════════════
#  2. 外形总图 — 平面（俯视）
# ══════════════════════════════════════════════════════════

def draw_daf_plan(msp, origin, p=None, scale=100.0,
                  label="平面图", tracker=None):
    """俯视：接触/分离分区 + 刮渣轨道 + 释放器阵 + 进出水 + 集渣槽。"""
    p = _params(p)
    s = scale
    ox, oy = _r(*origin)
    cL, sL = p["contact_L"], p["sep_L"]
    W = p["pool_W"]
    L = cL + sL
    cx, cy = ox + L / 2.0, oy + W / 2.0

    # 池体轮廓 + 分隔
    _rect(msp, ox, oy, ox + L, oy + W, "池体-壁")
    _ln(msp, (ox + cL, oy), (ox + cL, oy + W), "池体-壁")
    _t(msp, "接触区", (ox + cL / 2, oy + W + 3 * s), 2.2 * s, align=MC,
       layer="文字", tracker=tracker)
    _t(msp, "分离区", (ox + cL + sL / 2, oy + W + 3 * s), 2.2 * s, align=MC,
       layer="文字", tracker=tracker)

    # 释放器阵（接触区内，梅花布置）
    n_r = 4
    for j in range(2):
        for i in range(n_r):
            rx = ox + cL * (i + 0.5) / n_r
            ry = oy + W * (j + 0.5) / 2.0
            _circle(msp, (rx, ry), 80, "设备")
            _circle(msp, (rx, ry), 30, "细实线")
    _t(msp, f"{p['releaser']}×{n_r*2}", (ox + cL / 2, oy - 5 * s), 2.0 * s,
       align=MC, layer="文字", tracker=tracker)

    # 刮渣轨道（分离区两缘纵线 + 刮板横线）
    _ln(msp, (ox + cL, oy + 150), (ox + L, oy + 150), "设备")
    _ln(msp, (ox + cL, oy + W - 150), (ox + L, oy + W - 150), "设备")
    for k in (0.2, 0.5, 0.8):
        bx = ox + cL + sL * k
        _ln(msp, (bx, oy + 150), (bx, oy + W - 150), "细实线")

    # 集渣槽（末端通长）
    tw = p["scum_trough_W"]
    _rect(msp, ox + L - tw, oy, ox + L, oy + W, "设备")
    _t(msp, "集渣槽", (ox + L - tw / 2, cy), 2.0 * s, align=MC, layer="文字",
       tracker=tracker)

    # 进水（左）/出水（右下）/排渣（右上）
    idn = p["inlet_dn"]
    _rect(msp, ox - idn, cy - idn / 2, ox, cy + idn / 2, "设备")
    _t(msp, "进", (ox - idn / 2, cy), 2.2 * s, align=MC, layer="文字",
       tracker=tracker)
    odn = p["outlet_dn"]
    _rect(msp, ox + L, oy + 300, ox + L + odn, oy + 300 + odn, "设备")
    _t(msp, "出", (ox + L + odn / 2, oy + 300 + odn / 2), 2.2 * s, align=MC,
       layer="文字", tracker=tracker)

    # 集水管（分离区底部纵管，虚线）
    _ln(msp, (ox + cL + 300, oy + 600), (ox + L, oy + 600), "虚线",
        linetype="DASHED")

    _t(msp, f"池体 {L:.0f}×{W:.0f}｜接触 {cL:.0f}+分离 {sL:.0f}",
       (cx, oy - 10 * s), 2.3 * s, align=MC, layer="文字", tracker=tracker)

    if label:
        _t(msp, label, (cx, oy + W + 8 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (ox + L, oy)


# ══════════════════════════════════════════════════════════
#  3. 横剖面图
# ══════════════════════════════════════════════════════════

def draw_daf_section(msp, origin, p=None, scale=100.0,
                     label="1-1 剖面图", tracker=None):
    """横剖面：池体断面/水位/浮渣/释放器(立面)/穿孔集水管。"""
    p = _params(p)
    s = scale
    ox, oy = _r(*origin)
    W = p["pool_W"]
    H = p["pool_H"]
    wH = p["water_H"]
    cx = ox + W / 2.0

    # 池体断面（U 形）
    _ln(msp, (ox, oy), (ox + W, oy), "池体-壁")
    _ln(msp, (ox, oy), (ox, oy + H), "池体-壁")
    _ln(msp, (ox + W, oy), (ox + W, oy + H), "池体-壁")
    _ln(msp, (ox, oy + H), (ox + W, oy + H), "细实线")

    # 水面 + 浮渣层
    wy = oy + wH
    _ln(msp, (ox, wy), (ox + W, wy), "池体-水")
    _ln(msp, (ox, wy + p["scum_t"]), (ox + W, wy + p["scum_t"]), "细实线")
    _t(msp, "浮渣", (ox + W + 3 * s, wy + p["scum_t"]), 2.0 * s, align=ML,
       layer="文字", tracker=tracker)
    _t(msp, "水面", (ox + W + 3 * s, wy), 2.0 * s, align=ML, layer="文字",
       tracker=tracker)

    # 释放器（剖面内 3 个，底部向上喷射气泡点阵）
    for k in (0.25, 0.5, 0.75):
        rx = ox + W * k
        _circle(msp, (rx, oy + 400), 90, "设备")
        for j in range(4):
            by = oy + 600 + j * (wH - 700) / 4.0
            _circle(msp, (rx, by), 25, "细实线")
    _t(msp, "溶气释放器↑微气泡", (cx, oy + wH * 0.55), 2.0 * s, align=MC,
       layer="文字", tracker=tracker)

    # 穿孔集水管（底部一侧）
    _circle(msp, (ox + 400, oy + 250), 120, "管道-给水")
    _t(msp, "穿孔集水管", (ox + 400, oy - 3 * s), 2.0 * s, align=MC,
       layer="文字", tracker=tracker)

    # 刮板（顶部水面上）
    _ln(msp, (cx, wy + p["scum_t"]), (cx, oy + H + 400), "设备")
    _t(msp, "刮板", (cx + 3 * s, oy + H + 250), 2.0 * s, align=ML,
       layer="文字", tracker=tracker)

    if label:
        _t(msp, label, (cx, oy - 8 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (cx, oy, oy + H)


# ══════════════════════════════════════════════════════════
#  4. 溶气系统图
# ══════════════════════════════════════════════════════════

def draw_daf_saturation(msp, origin, p=None, scale=100.0,
                        label="溶气系统图", tracker=None):
    """系统图：回流泵 → 溶气罐(射流吸气) → 释放器；空压机补气。"""
    p = _params(p)
    s = scale
    ox, oy = _r(*origin)
    td, th = p["tank_D"], p["tank_H"]

    # 溶气罐（中）
    tx = ox + 4500
    _rect(msp, tx, oy + 800, tx + td, oy + 800 + th, "设备")
    msp.add_arc(_r(tx + td / 2, oy + 800 + th), td / 2, 0, 180,
                dxfattribs={"layer": "设备"})
    # 罐内填料层（中部斜线填充示意）
    fy = oy + 800 + th * 0.5
    _ln(msp, (tx + 100, fy - 200), (tx + td - 100, fy + 200), "细实线")
    _ln(msp, (tx + 100, fy + 200), (tx + td - 100, fy - 200), "细实线")
    _t(msp, "填料层", (tx + td + 3 * s, fy), 2.0 * s, align=ML, layer="文字",
       tracker=tracker)
    # 液位计
    _ln(msp, (tx - 250, oy + 1000), (tx - 250, oy + 800 + th - 300), "细实线")
    for k in (0.3, 0.6):
        _ln(msp, (tx - 250, oy + 800 + th * k), (tx, oy + 800 + th * k), "细实线")
    _t(msp, "液位计", (tx - 300, oy + 800 + th * 0.8), 2.0 * s, align=MR,
       layer="文字", tracker=tracker)

    # 回流泵（左下）
    px, py = ox + 1200, oy + 600
    _circle(msp, (px, py), 280, "设备")
    _rect(msp, px - 450, py - 150, px - 280, py + 150, "设备")
    _t(msp, "回流泵", (px, py - 4 * s), 2.0 * s, align=MC, layer="文字",
       tracker=tracker)
    # 泵 → 罐（射流器在进口）
    _ln(msp, (px + 280, py), (tx + td / 2, py), "管道-给水")
    _ln(msp, (tx + td / 2, py), (tx + td / 2, oy + 800), "管道-给水")
    _rect(msp, tx + td / 2 - 300, py - 100, tx + td / 2 + 300, py + 100, "阀门")
    _t(msp, "射流器(吸气)", (tx + td / 2, py + 3 * s), 2.0 * s, align=MC,
       layer="文字", tracker=tracker)

    # 空压机（罐顶）
    ax = tx + td + 1500
    _rect(msp, ax, oy + 800 + th - 400, ax + 900, oy + 800 + th + 400, "设备")
    _t(msp, "空压机", (ax + 450, oy + 800 + th + 700), 2.0 * s, align=MC,
       layer="文字", tracker=tracker)
    _ln(msp, (ax, oy + 800 + th), (tx + td, oy + 800 + th * 0.75), "管道-加药")

    # 罐 → 释放器（右下出）
    rx = tx + td + 3500
    _ln(msp, (tx + td, oy + 1200), (rx, oy + 1200), "管道-给水")
    _circle(msp, (rx, oy + 1200), 120, "设备")
    _t(msp, f"至释放器（{p['tank_p']} MPa）", (rx + 3 * s, oy + 1200),
       2.0 * s, align=ML, layer="文字", tracker=tracker)
    # 安全阀（罐顶）
    _rect(msp, tx + td / 2 - 100, oy + 800 + th + td / 2, tx + td / 2 + 100,
          oy + 800 + th + td / 2 + 250, "阀门")
    _t(msp, "安全阀", (tx + td / 2 + 400, oy + 800 + th + td / 2 + 100),
       2.0 * s, align=ML, layer="文字", tracker=tracker)

    _t(msp, f"回流比 {p['reflux']*100:.0f}%｜溶气压力 {p['tank_p']} MPa",
       (tx + td / 2, oy - 5 * s), 2.3 * s, align=MC, layer="文字",
       tracker=tracker)

    if label:
        _t(msp, label, (tx + td / 2, oy + 800 + th + td / 2 + 8 * s), 3.2 * s,
           align=MC, layer="文字-标题", tracker=tracker)
    return (tx + td, oy)


# ══════════════════════════════════════════════════════════
#  5. 刮渣系统详图
# ══════════════════════════════════════════════════════════

def draw_daf_skimmer(msp, origin, p=None, scale=100.0,
                     label="刮渣系统详图", tracker=None):
    """链式刮渣机构：驱动链轮/链条/刮板/集渣槽/可调堰板。"""
    p = _params(p)
    s = scale
    ox, oy = _r(*origin)
    L = 7000.0
    W = p["pool_W"]
    cx = ox + L / 2.0

    # 两链轮（端部）
    _circle(msp, (ox + 400, oy + 600), 250, "设备")
    _circle(msp, (ox + L - 400, oy + 600), 250, "设备")
    _t(msp, "驱动链轮", (ox + 400, oy + 1000), 2.0 * s, align=MC, layer="文字",
       tracker=tracker)
    # 驱动电机
    _rect(msp, ox + 100, oy + 1250, ox + 700, oy + 1650, "设备")
    _t(msp, "减速电机", (ox + 400, oy + 1850), 2.0 * s, align=MC, layer="文字",
       tracker=tracker)

    # 上下链条
    _ln(msp, (ox + 400, oy + 850), (ox + L - 400, oy + 850), "设备")
    _ln(msp, (ox + 400, oy + 350), (ox + L - 400, oy + 350), "设备")

    # 刮板（挂链条间，3 块）
    for k in (0.2, 0.5, 0.8):
        bx = ox + 400 + (L - 800) * k
        _ln(msp, (bx, oy + 350), (bx, oy + 850), "设备")
        _rect(msp, bx - 60, oy + 200, bx + 60, oy + 350, "设备")
    _t(msp, f"刮板（行走速度 {p['skimmer_v']} m/min）", (cx, oy - 3 * s),
       2.0 * s, align=MC, layer="文字", tracker=tracker)

    # 集渣槽（末端）
    tw = p["scum_trough_W"]
    _rect(msp, ox + L, oy + 200, ox + L + tw, oy + 1100, "设备")
    _tri(msp, (ox + L + tw / 2, oy + 650), (1, 0), s * 0.6, "流向")
    _t(msp, "集渣槽", (ox + L + tw / 2, oy + 1300), 2.0 * s, align=MC,
       layer="文字", tracker=tracker)
    # 排渣管
    _ln(msp, (ox + L + tw / 2, oy + 200), (ox + L + tw / 2, oy - 400),
        "管道-污水")
    _t(msp, f"排渣 DN{p['sludge_dn']:.0f}", (ox + L + tw / 2 + 3 * s, oy - 200),
       2.0 * s, align=ML, layer="文字", tracker=tracker)

    # 可调堰板（出水端）
    _rect(msp, ox + L - 500, oy - 500, ox + L - 300, oy + 300, "设备")
    _t(msp, "可调堰板", (ox + L - 400, oy - 7 * s), 2.0 * s, align=MC,
       layer="文字", tracker=tracker)

    if label:
        _t(msp, label, (cx, oy + 1650 + 8 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (ox + L, oy)
