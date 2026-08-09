# -*- coding: utf-8 -*-
"""氧化沟多视图制图 v1.0（HJ 578、GB 50014、CECS 112）。

Carrousel 氧化沟成套视图：平面布置、横剖面、转刷曝气机详图、
出水可调堰门、潜水推流器布置。所有几何参数以 dict 传入（默认取
knowledge.oxidation_ditch_data.OD_DEFAULTS）——本模块只负责"画"，不负责"算"。

坐标单位 mm，scale=出图比例倒数(1:100 → 100)。图层沿用包内中文命名。
"""
from __future__ import annotations

import math

from ezdxf.enums import TextEntityAlignment

from ..utils import _r, _tri
from .annotate import _t
from ..knowledge.oxidation_ditch_data import OD_DEFAULTS

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
    d = dict(OD_DEFAULTS)
    d.update(p or {})
    return d


# ══════════════════════════════════════════════════════════
#  1. 平面布置图
# ══════════════════════════════════════════════════════════

def draw_od_plan(msp, origin, p=None, scale=100.0,
                 label="氧化沟平面布置图", tracker=None):
    """俯视：环形沟道(2沟)/中央导流墙/端部弯道/转刷位/出水堰/进出水。"""
    p = _params(p)
    s = scale
    ox, oy = _r(*origin)
    L = p["ditch_L"]
    W = p["ditch_W"]
    R = p["bend_R"]
    t = p["wall_t"]
    gt = p["guide_wall_t"]

    # 外轮廓（直段 + 两端半圆弯道，俯视）
    total_W = 2 * W + gt + 2 * t
    # 外墙
    _ln(msp, (ox, oy), (ox + L, oy), "池体-壁")
    _ln(msp, (ox, oy + total_W), (ox + L, oy + total_W), "池体-壁")
    msp.add_arc(_r(ox + L, oy + total_W / 2), total_W / 2, -90, 90,
                dxfattribs={"layer": "池体-壁"})
    msp.add_arc(_r(ox, oy + total_W / 2), total_W / 2, 90, 270,
                dxfattribs={"layer": "池体-壁"})
    # 中央导流墙（两端不闭合，留弯道过流）
    gl = p["guide_wall_L"]
    gx0 = ox + (L - gl) / 2.0
    gy = oy + W + t + gt / 2.0 - gt / 2.0
    _rect(msp, gx0, oy + W + t, gx0 + gl, oy + W + t + gt, "池体-壁")
    _t(msp, "中央导流墙", (ox + L / 2, oy + W + t + gt + 3 * s), 2.0 * s,
       align=MC, layer="文字", tracker=tracker)

    # 沟内水流方向（环形，上沟向右下沟向左）
    _tri(msp, (ox + L * 0.3, oy + W / 2 + t / 2), (1, 0), s, "流向")
    _tri(msp, (ox + L * 0.7, oy + total_W - W / 2 - t / 2), (-1, 0), s, "流向")
    _t(msp, "推流方向", (ox + L * 0.3 + 8 * s, oy + W / 2 + t / 2), 2.0 * s,
       align=ML, layer="文字", tracker=tracker)

    # 转刷曝气机（跨沟，每沟 2 台）
    n_b = p["n_brush"]
    for i in range(n_b):
        bx = ox + L * (0.2 + 0.6 * (i % 2))
        by = oy + t + (i // 2) * (W + gt + t) + W / 2.0
        _circle(msp, (bx, by), p["brush_D"] / 2.0, "设备")
        _ln(msp, (bx, by - W / 2.0), (bx, by + W / 2.0), "设备")
        _t(msp, f"转刷{i+1}#", (bx + p["brush_D"], by + 3 * s), 1.8 * s,
           align=ML, layer="文字", tracker=tracker)

    # 出水堰（下沟末端）+ 出水管
    wl = p["weir_L"]
    wx = ox + L - 3500
    _rect(msp, wx, oy + total_W - t - W, wx + wl, oy + total_W - t - W + 300,
          "设备")
    _t(msp, "出水可调堰门", (wx + wl / 2, oy + total_W - t - W - 4 * s),
       2.0 * s, align=MC, layer="文字", tracker=tracker)
    odn = p["outlet_dn"]
    _rect(msp, wx + wl / 2 - odn / 2, oy - odn, wx + wl / 2 + odn / 2, oy,
          "设备")
    _tri(msp, (wx + wl / 2, oy - odn - 3 * s), (0, -1), s, "流向")
    _t(msp, f"出水 DN{odn:.0f}", (wx + wl / 2 + odn, oy - odn / 2), 2.0 * s,
       align=ML, layer="文字", tracker=tracker)

    # 进水（上沟首端）
    _rect(msp, ox + 2500 - 250, oy + total_W, ox + 2500 + 250,
          oy + total_W + 500, "设备")
    _tri(msp, (ox + 2500, oy + total_W + 700), (0, 1), s * 0.8, "流向")
    _t(msp, "进水+回流污泥", (ox + 2500, oy + total_W + 10 * s), 2.0 * s,
       align=MC, layer="文字", tracker=tracker)

    _t(msp, f"2 沟×{L/1000:.0f}m×{W/1000:.1f}m｜泥龄 {p['sludge_age']:.0f}d",
       (ox + L / 2, oy - odn - 8 * s), 2.3 * s, align=MC, layer="文字",
       tracker=tracker)

    if label:
        _t(msp, label, (ox + L / 2, oy + total_W + 14 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (ox + L, oy)


# ══════════════════════════════════════════════════════════
#  2. 横剖面图
# ══════════════════════════════════════════════════════════

def draw_od_section(msp, origin, p=None, scale=100.0,
                    label="1-1 剖面图", tracker=None):
    """横剖面：沟断面/水深/转刷浸没/曝气水花。"""
    p = _params(p)
    s = scale
    ox, oy = _r(*origin)
    W = p["ditch_W"]
    H = p["ditch_H"]
    wH = p["water_H"]
    cx = ox + W / 2.0

    # 沟断面（U 形）
    _ln(msp, (ox, oy), (ox + W, oy), "池体-壁")
    _ln(msp, (ox, oy), (ox, oy + H), "池体-壁")
    _ln(msp, (ox + W, oy), (ox + W, oy + H), "池体-壁")
    _ln(msp, (ox, oy + H), (ox + W, oy + H), "细实线")

    # 水面线
    _ln(msp, (ox, oy + wH), (ox + W, oy + wH), "池体-水")
    _t(msp, f"水深 {wH/1000:.1f}m", (ox + W + 3 * s, oy + wH), 2.0 * s,
       align=ML, layer="文字", tracker=tracker)

    # 转刷（跨沟，轴在水面上方，刷片入水）
    bd = p["brush_D"]
    by = oy + wH + bd / 2.0 - p["brush_immersion"]
    _circle(msp, (cx, by), bd / 2.0, "设备")
    _circle(msp, (cx, by), bd / 2.0 * 0.3, "细实线")
    # 刷片（径向 8 片）
    for ang in range(0, 360, 45):
        a = math.radians(ang)
        _ln(msp, (cx + bd * 0.15 * math.cos(a), by + bd * 0.15 * math.sin(a)),
            (cx + bd * 0.55 * math.cos(a), by + bd * 0.55 * math.sin(a)),
            "细实线")
    # 浸没深度标注
    _ln(msp, (cx + bd / 2 + 200, oy + wH), (cx + bd / 2 + 200, by - bd / 2),
        "细实线-尺寸")
    _t(msp, f"浸没 {p['brush_immersion']:.0f}", (cx + bd / 2 + 400, oy + wH - 300),
       2.0 * s, align=ML, layer="文字", tracker=tracker)
    # 水花（入水侧）
    for j in range(3):
        _circle(msp, (cx - bd / 2 - 200 - j * 150, oy + wH + 100 + j * 80),
                60, "细实线")
    _t(msp, "曝气水花", (ox - 3 * s, oy + wH + 300), 2.0 * s, align=MR,
       layer="文字", tracker=tracker)

    # 轴承座（两端）
    _rect(msp, ox - 300, by - 200, ox, by + 200, "设备")
    _rect(msp, ox + W, by - 200, ox + W + 300, by + 200, "设备")

    if label:
        _t(msp, label, (cx, oy - 8 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (cx, oy, by + bd / 2)


# ══════════════════════════════════════════════════════════
#  3. 转刷曝气机详图
# ══════════════════════════════════════════════════════════

def draw_od_brush(msp, origin, p=None, scale=100.0,
                  label="转刷曝气机详图", tracker=None):
    """立面：主轴/刷片组/减速电机/联轴器/轴承座/防溅罩。"""
    p = _params(p)
    s = scale
    ox, oy = _r(*origin)
    L = p["brush_L"]
    bd = p["brush_D"]
    cy = oy + bd

    # 主轴（水平）
    _ln(msp, (ox, cy), (ox + L, cy), "设备")
    # 刷片组（沿轴均布，正视圆片）
    n_disc = int(L / 500)
    for i in range(n_disc):
        dx = ox + L * (i + 0.5) / n_disc
        _circle(msp, (dx, cy), 120, "设备")
        for ang in range(0, 360, 90):
            a = math.radians(ang)
            _ln(msp, (dx, cy), (dx + 120 * math.cos(a),
                                cy + 120 * math.sin(a)), "细实线")
    _t(msp, f"刷片组 Φ{bd:.0f}（{n_disc} 组）", (ox + L / 2, cy - bd),
       2.0 * s, align=MC, layer="文字", tracker=tracker)

    # 防溅罩（轴上方半圆罩）
    msp.add_arc(_r(ox + L / 2, cy), L * 0.45, 20, 160,
                dxfattribs={"layer": "细实线"})
    _t(msp, "防溅罩", (ox + L / 2, cy + L * 0.42), 2.0 * s, align=MC,
       layer="文字", tracker=tracker)

    # 减速电机（右端）
    _rect(msp, ox + L + 300, cy - 350, ox + L + 1100, cy + 350, "设备")
    _t(msp, f"减速电机 {p['brush_power']:.0f}kW", (ox + L + 700, cy + 500),
       2.0 * s, align=MC, layer="文字", tracker=tracker)
    # 联轴器
    _rect(msp, ox + L, cy - 150, ox + L + 300, cy + 150, "设备")

    # 轴承座（两端）
    _rect(msp, ox - 400, cy - 250, ox, cy + 250, "设备")
    _rect(msp, ox + L + 1100, cy - 250, ox + L + 1500, cy + 250, "设备")
    _t(msp, "轴承座", (ox - 200, cy - 4 * s), 2.0 * s, align=MC, layer="文字",
       tracker=tracker)

    # 水位参考线
    wy = cy - bd / 2 + p["brush_immersion"]
    _ln(msp, (ox - 600, wy), (ox + L + 2100, wy), "池体-水")
    _t(msp, "运行水位", (ox + L + 2200, wy + 3 * s), 2.0 * s, align=ML,
       layer="文字", tracker=tracker)

    _t(msp, f"单机长 {L:.0f}｜浸没深度可调 200~350mm",
       (ox + L / 2, oy - 5 * s), 2.3 * s, align=MC, layer="文字",
       tracker=tracker)

    if label:
        _t(msp, label, (ox + L / 2, cy + L * 0.45 + 6 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (ox + L, oy)


# ══════════════════════════════════════════════════════════
#  4. 出水可调堰门详图
# ══════════════════════════════════════════════════════════

def draw_od_weir(msp, origin, p=None, scale=100.0,
                 label="出水可调堰门详图", tracker=None):
    """剖面：堰门(手电两用启闭机) + 堰板 + 出水渠 + 水位。"""
    p = _params(p)
    s = scale
    ox, oy = _r(*origin)
    W = p["weir_L"]
    H = 2200.0
    wH = p["water_H"]
    cx = ox + W / 2.0

    # 渠断面（左氧化沟侧 / 右出水渠侧，中间堰门）
    _ln(msp, (ox, oy), (ox + W, oy), "池体-壁")
    _ln(msp, (ox, oy), (ox, oy + H), "池体-壁")
    _ln(msp, (ox + W, oy), (ox + W, oy + H), "池体-壁")
    # 中隔墙（堰门框）
    _rect(msp, cx - 150, oy, cx + 150, oy + H * 0.7, "池体-壁")

    # 堰板（可上下调节，当前位置）
    gate_y = oy + H * 0.45
    _rect(msp, cx - 130, gate_y, cx + 130, gate_y + H * 0.35, "设备")
    _t(msp, "可调堰板", (cx + 400, gate_y + H * 0.18), 2.0 * s, align=ML,
       layer="文字", tracker=tracker)

    # 启闭机（顶部丝杆）
    _ln(msp, (cx, gate_y + H * 0.35), (cx, oy + H + 500), "设备")
    _rect(msp, cx - 250, oy + H + 500, cx + 250, oy + H + 900, "设备")
    _t(msp, "手电两用启闭机", (cx, oy + H + 1100), 2.0 * s, align=MC,
       layer="文字", tracker=tracker)

    # 沟侧水位（高）/ 渠侧水位（低）
    _ln(msp, (ox + 100, oy + wH * 0.45), (cx - 150, oy + wH * 0.45), "池体-水")
    _ln(msp, (cx + 150, oy + wH * 0.38), (ox + W - 100, oy + wH * 0.38),
        "池体-水")
    _t(msp, "沟内水位", (ox + 200, oy + wH * 0.45 + 3 * s), 2.0 * s, align=ML,
       layer="文字", tracker=tracker)
    _t(msp, "出水渠", (ox + W - 200, oy + wH * 0.38 + 3 * s), 2.0 * s,
       align=MR, layer="文字", tracker=tracker)

    # 过堰水流
    _tri(msp, (cx, gate_y + H * 0.35 + 200), (0, -1), s * 0.6, "流向")
    _t(msp, "薄壁堰出流", (cx + 400, gate_y + H * 0.35 + 100), 2.0 * s,
       align=ML, layer="文字", tracker=tracker)

    _t(msp, f"堰长 {W:.0f}｜调节范围±150mm", (cx, oy - 6 * s), 2.3 * s,
       align=MC, layer="文字", tracker=tracker)

    if label:
        _t(msp, label, (cx, oy - 12 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (cx, oy)


# ══════════════════════════════════════════════════════════
#  5. 潜水推流器布置图
# ══════════════════════════════════════════════════════════

def draw_od_pusher(msp, origin, p=None, scale=100.0,
                   label="潜水推流器布置图", tracker=None):
    """平面局部：弯道段推流器位置/角度/导流墙。"""
    p = _params(p)
    s = scale
    ox, oy = _r(*origin)
    W = p["ditch_W"]
    L = 12000.0
    cx, cy = ox + L / 2.0, oy + W / 2.0

    # 沟道平面（局部直段 + 导流墙）
    _rect(msp, ox, oy, ox + L, oy + W, "池体-壁")
    _rect(msp, ox + L * 0.4, oy - 600, ox + L * 0.6, oy + W * 0.55,
          "池体-壁")
    _t(msp, "导流墙", (ox + L * 0.5, oy - 900), 2.0 * s, align=MC,
       layer="文字", tracker=tracker)

    # 潜水推流器（2 台，沿流向 30° 斜置）
    for k, frac in enumerate((0.25, 0.75)):
        px = ox + L * frac
        py = oy + W * 0.72
        # 叶轮（圆）+ 导杆（斜）
        _circle(msp, (px, py), 350, "设备")
        _circle(msp, (px, py), 120, "细实线")
        _ln(msp, (px, py), (px + 800, py + 1200), "设备")
        _rect(msp, px + 650, py + 1150, px + 950, py + 1450, "设备")
        # 推力方向箭头
        _tri(msp, (px + 600, py - 500), (1, 0), s * 0.6, "流向")
        _t(msp, f"推流器{k+1}#", (px - 3 * s, py - 500), 1.8 * s, align=MR,
           layer="文字", tracker=tracker)

    # 沟内流速标注
    _t(msp, f"沟内流速≥{p['flow_v']} m/s（推流器辅助防沉积）",
       (cx, oy + W + 5 * s), 2.2 * s, align=MC, layer="文字", tracker=tracker)

    # 中心线
    _ln(msp, (ox - 3 * s, cy), (ox + L + 3 * s, cy), "点画线",
        linetype="CENTER")

    if label:
        _t(msp, label, (cx, oy - 14 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (ox + L, oy)
