# -*- coding: utf-8 -*-
"""MBR 膜生物反应器多视图制图 v1.0（HJ 2010、HJ 2028、GB 50014）。

浸没式 MBR 成套视图：膜箱外形(正立面/平面)、横剖面、帘式膜组件详图、
抽吸反洗系统、膜列布置。所有几何参数以 dict 传入（默认取
knowledge.mbr_data.MBR_DEFAULTS）——本模块只负责"画"，不负责"算"。

坐标单位 mm，scale=出图比例倒数(1:100 → 100)。图层沿用包内中文命名。
"""
from __future__ import annotations

import math

from ezdxf.enums import TextEntityAlignment

from ..utils import _r, _tri
from .annotate import _t
from ..knowledge.mbr_data import MBR_DEFAULTS

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
    d = dict(MBR_DEFAULTS)
    d.update(p or {})
    return d


# ══════════════════════════════════════════════════════════
#  1. 膜箱外形 — 正立面
# ══════════════════════════════════════════════════════════

def draw_mbr_elevation(msp, origin, p=None, scale=100.0,
                       label="MBR膜箱外形图", tracker=None):
    """正立面：箱体/膜组件(2列)/曝气管/产水母管/吊装架。"""
    p = _params(p)
    s = scale
    ox, oy = _r(*origin)
    L, H = p["tank_L"], p["tank_H"]
    wH = p["water_H"]
    cx = ox + L / 2.0

    # 箱体（U 形）
    _ln(msp, (ox, oy), (ox + L, oy), "池体-壁")
    _ln(msp, (ox, oy), (ox, oy + H), "池体-壁")
    _ln(msp, (ox + L, oy), (ox + L, oy + H), "池体-壁")
    _ln(msp, (ox, oy + H), (ox + L, oy + H), "细实线")

    # 水面线
    _ln(msp, (ox, oy + wH), (ox + L, oy + wH), "池体-水")
    _t(msp, "运行水位", (ox + L + 3 * s, oy + wH), 2.0 * s, align=ML,
       layer="文字", tracker=tracker)

    # 膜组件（2 列，每列 n_module_row 片帘式膜）
    ncol = p["n_module_col"]
    nrow = p["n_module_row"]
    mh = p["module_H"]
    col_w = (L - 600) / ncol
    for c in range(ncol):
        x0 = ox + 300 + c * col_w
        # 膜片组（竖线束）
        for i in range(nrow):
            mx = x0 + col_w * (i + 0.5) / nrow
            _ln(msp, (mx, oy + 700), (mx, oy + 700 + mh), "细实线")
        # 上下集水管
        _rect(msp, x0, oy + 700 + mh, x0 + col_w, oy + 800 + mh, "设备")
        _rect(msp, x0, oy + 600, x0 + col_w, oy + 700, "设备")
    _t(msp, f"帘式膜组件 {ncol} 列×{nrow} 片", (cx, oy + 700 + mh + 4 * s),
       2.0 * s, align=MC, layer="文字", tracker=tracker)

    # 曝气穿孔管（膜组件正下方）
    _ln(msp, (ox + 200, oy + 350), (ox + L - 200, oy + 350), "管道-加药")
    for j in range(10):
        ax = ox + 300 + (L - 600) * (j + 0.5) / 10.0
        _tri(msp, (ax, oy + 500), (0, 1), s * 0.35, "细实线")
    _t(msp, f"膜擦洗曝气管 DN{p['air_pipe_dn']:.0f}", (cx, oy + 200),
       2.0 * s, align=MC, layer="文字", tracker=tracker)

    # 产水母管（顶部引出）
    pdn = p["permeate_dn"]
    _rect(msp, ox + L, oy + 700 + mh - pdn / 2, ox + L + pdn,
          oy + 700 + mh + pdn / 2, "管道-给水")
    _tri(msp, (ox + L + pdn + 3 * s, oy + 700 + mh), (1, 0), s, "流向")
    _t(msp, f"产水 DN{pdn:.0f}", (ox + L + pdn / 2, oy + 700 + mh + 4 * s),
       2.0 * s, align=MC, layer="文字", tracker=tracker)

    # 吊装架（顶部横梁+吊钩）
    _ln(msp, (ox - 200, oy + H + 500), (ox + L + 200, oy + H + 500), "设备")
    for k in (0.25, 0.75):
        hx = ox + L * k
        _ln(msp, (hx, oy + H + 500), (hx, oy + H), "设备")
        _circle(msp, (hx, oy + H - 100), 80, "设备")
    _t(msp, "吊装架", (ox + L + 300, oy + H + 500), 2.0 * s, align=ML,
       layer="文字", tracker=tracker)

    if label:
        _t(msp, label, (cx, oy - 8 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (cx, oy, oy + H + 500)


# ══════════════════════════════════════════════════════════
#  2. 膜箱外形 — 平面（俯视）
# ══════════════════════════════════════════════════════════

def draw_mbr_plan(msp, origin, p=None, scale=100.0,
                  label="膜箱平面图", tracker=None):
    """俯视：膜箱分区 + 膜组件排列 + 曝气/产水管布置。"""
    p = _params(p)
    s = scale
    ox, oy = _r(*origin)
    L, W = p["tank_L"], p["tank_W"]
    cx, cy = ox + L / 2.0, oy + W / 2.0

    # 箱体轮廓
    _rect(msp, ox, oy, ox + L, oy + W, "池体-壁")

    # 膜组件（俯视：两列长条，每列 n_module_row 片）
    ncol = p["n_module_col"]
    nrow = p["n_module_row"]
    ml = p["module_L"]
    col_w = (L - 600) / ncol
    for c in range(ncol):
        x0 = ox + 300 + c * col_w + (col_w - ml) / 2.0
        for i in range(nrow):
            my = oy + 150 + (W - 300) * (i + 0.5) / nrow
            _rect(msp, x0, my - p["module_W"] / 2, x0 + ml,
                  my + p["module_W"] / 2, "细实线")

    # 曝气管（纵向 2 根）
    _ln(msp, (ox + 200, cy - W * 0.2), (ox + L - 200, cy - W * 0.2),
        "管道-加药")
    _ln(msp, (ox + 200, cy + W * 0.2), (ox + L - 200, cy + W * 0.2),
        "管道-加药")

    # 产水母管（右侧横向）
    _ln(msp, (ox + L - 400, oy + 150), (ox + L - 400, oy + W - 150),
        "管道-给水")
    _rect(msp, ox + L, cy - 75, ox + L + 300, cy + 75, "管道-给水")
    _t(msp, "产水母管", (ox + L - 400, oy - 4 * s), 2.0 * s, align=MC,
       layer="文字", tracker=tracker)

    # 中心线
    _ln(msp, (ox - 3 * s, cy), (ox + L + 3 * s, cy), "点画线",
        linetype="CENTER")
    _ln(msp, (cx, oy - 3 * s), (cx, oy + W + 3 * s), "点画线",
        linetype="CENTER")

    _t(msp, f"膜箱 {L:.0f}×{W:.0f}｜膜通量 {p['flux']} L/m²·h",
       (cx, oy - 9 * s), 2.3 * s, align=MC, layer="文字", tracker=tracker)

    if label:
        _t(msp, label, (cx, oy + W + 6 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (ox + L, oy)


# ══════════════════════════════════════════════════════════
#  3. 横剖面图
# ══════════════════════════════════════════════════════════

def draw_mbr_section(msp, origin, p=None, scale=100.0,
                     label="膜箱横剖面图", tracker=None):
    """横剖面：膜丝束断面/集水管/曝气穿孔管/气泡上浮路径。"""
    p = _params(p)
    s = scale
    ox, oy = _r(*origin)
    W = p["tank_W"]
    H = p["tank_H"]
    wH = p["water_H"]
    mh = p["module_H"]
    cx = ox + W / 2.0

    # 池壁剖切
    _ln(msp, (ox, oy), (ox + W, oy), "池体-壁")
    _ln(msp, (ox, oy), (ox, oy + H), "池体-壁")
    _ln(msp, (ox + W, oy), (ox + W, oy + H), "池体-壁")
    _ln(msp, (ox, oy + wH), (ox + W, oy + wH), "池体-水")

    # 膜片断面（并排圆角矩形 = 膜丝束断面）
    nrow = p["n_module_row"]
    span = W - 500
    for i in range(nrow):
        mx = ox + 250 + span * (i + 0.5) / nrow
        _rect(msp, mx - p["module_W"] / 2, oy + 700, mx + p["module_W"] / 2,
              oy + 700 + mh, "设备")
    # 集水管（上下）
    _rect(msp, ox + 200, oy + 700 + mh, ox + W - 200, oy + 800 + mh, "设备")
    _rect(msp, ox + 200, oy + 600, ox + W - 200, oy + 700, "设备")
    _t(msp, "上集水管", (ox + W + 3 * s, oy + 750 + mh), 2.0 * s, align=ML,
       layer="文字", tracker=tracker)

    # 曝气穿孔管（底部横管 + 向下开孔示意 + 气泡）
    _circle(msp, (cx, oy + 350), 70, "管道-加药")
    for j in range(8):
        bx = ox + 250 + (W - 500) * (j + 0.5) / 8.0
        for k in range(3):
            by = oy + 500 + k * (mh * 0.3)
            _circle(msp, (bx, by), 25, "细实线")
    _t(msp, "气泡上浮擦洗膜丝", (cx, oy + 700 + mh * 0.6), 2.0 * s, align=MC,
       layer="文字", tracker=tracker)

    if label:
        _t(msp, label, (cx, oy - 8 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (cx, oy, oy + H)


# ══════════════════════════════════════════════════════════
#  4. 帘式膜组件详图
# ══════════════════════════════════════════════════════════

def draw_mbr_module(msp, origin, p=None, scale=100.0,
                    label="帘式膜组件详图", tracker=None):
    """单片帘式膜：膜丝束/上下集水管/曝气盒/吊装杆。"""
    p = _params(p)
    s = scale
    ox, oy = _r(*origin)
    ml = p["module_L"]
    mh = p["module_H"]
    cx = ox + ml / 2.0

    # 上集水管（ABS 集水盒）
    _rect(msp, ox, oy + mh + 300, ox + ml, oy + mh + 550, "设备")
    _t(msp, "上集水管(产水口)", (ox + ml + 3 * s, oy + mh + 425), 2.0 * s,
       align=ML, layer="文字", tracker=tracker)
    # 产水接口
    _circle(msp, (ox + ml, oy + mh + 425), 60, "设备")

    # 下集水管
    _rect(msp, ox, oy, ox + ml, oy + 250, "设备")
    _t(msp, "下集水管", (ox + ml + 3 * s, oy + 125), 2.0 * s, align=ML,
       layer="文字", tracker=tracker)

    # 膜丝束（上下管间密排竖线）
    n = int(ml / 60)
    for i in range(n):
        fx = ox + ml * (i + 0.5) / n
        _ln(msp, (fx, oy + 250), (fx, oy + mh + 300), "细实线")
    _t(msp, f"中空纤维膜丝 PVDF｜{p['membrane_area']:.0f}m²/片",
       (cx, oy + mh * 0.55), 2.0 * s, align=MC, layer="文字", tracker=tracker)

    # 下部曝气盒（两侧）
    _rect(msp, ox - 150, oy - 250, ox + ml + 150, oy, "设备")
    for i in range(8):
        ax = ox + ml * (i + 0.5) / 8.0
        _circle(msp, (ax, oy - 125), 30, "细实线")
    _t(msp, "曝气盒(穿孔向上)", (cx, oy - 450), 2.0 * s, align=MC,
       layer="文字", tracker=tracker)

    # 吊装杆
    _ln(msp, (cx, oy + mh + 550), (cx, oy + mh + 950), "设备")
    _circle(msp, (cx, oy + mh + 1050), 80, "设备")

    _t(msp, f"组件 {ml:.0f}×{p['module_W']:.0f}×{mh+550:.0f}",
       (cx, oy - 8 * s), 2.3 * s, align=MC, layer="文字", tracker=tracker)

    if label:
        _t(msp, label, (cx, oy + mh + 1250), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (ox + ml, oy)


# ══════════════════════════════════════════════════════════
#  5. 抽吸反洗系统图
# ══════════════════════════════════════════════════════════

def draw_mbr_backwash(msp, origin, p=None, scale=100.0,
                      label="抽吸反洗及化学清洗系统图", tracker=None):
    """系统图：膜箱 → 抽吸泵 → 产水池；CIP 药箱 → 反洗注入。"""
    p = _params(p)
    s = scale
    ox, oy = _r(*origin)
    W = 10000.0
    H = 4500.0

    # 膜箱（左）
    _rect(msp, ox, oy + 1200, ox + 2000, oy + 3800, "设备")
    _t(msp, "MBR膜箱", (ox + 1000, oy + 2500), 2.2 * s, align=MC,
       layer="文字", tracker=tracker)

    # 抽吸泵（中部）
    px, py = ox + 4200, oy + 1500
    _circle(msp, (px, py), 280, "设备")
    _t(msp, "抽吸泵", (px, py - 4 * s), 2.0 * s, align=MC, layer="文字",
       tracker=tracker)
    # 膜箱 → 泵（负压抽吸）
    _ln(msp, (ox + 2000, oy + 2000), (px, oy + 2000), "管道-给水")
    _ln(msp, (px, oy + 2000), (px, py + 280), "管道-给水")
    # 真空表 + 压力表
    _circle(msp, (ox + 3000, oy + 2300), 120, "阀门")
    _t(msp, "真空表", (ox + 3000, oy + 2600), 1.8 * s, align=MC, layer="文字",
       tracker=tracker)
    # 泵 → 产水池（右）
    _rect(msp, ox + 7000, oy + 1000, ox + 9500, oy + 3000, "设备")
    _t(msp, "产水池", (ox + 8250, oy + 2000), 2.2 * s, align=MC, layer="文字",
       tracker=tracker)
    _ln(msp, (px + 280, py), (ox + 7000, py), "管道-给水")
    _tri(msp, (ox + 6900, py), (1, 0), s * 0.6, "流向")

    # CIP 加药（NaClO / 柠檬酸 两药箱）
    for k, name in ((0.0, "NaClO药箱"), (1.0, "柠檬酸药箱")):
        bx = ox + 4000 + k * 1600
        _rect(msp, bx, oy + 3200, bx + 1200, oy + 4200, "设备")
        _t(msp, name, (bx + 600, oy + 3700), 1.8 * s, align=MC, layer="文字",
           tracker=tracker)
        # 计量泵 → 反洗管
        _circle(msp, (bx + 600, oy + 3000), 120, "阀门")
        _ln(msp, (bx + 600, oy + 3200), (bx + 600, oy + 3120), "管道-加药")
        _ln(msp, (bx + 600, oy + 2880), (bx + 600, oy + 2600), "管道-加药")
    # 反洗总管 → 膜箱（逆向）
    _ln(msp, (ox + 4600, oy + 2600), (ox + 1000, oy + 2600), "管道-加药")
    _ln(msp, (ox + 1000, oy + 2600), (ox + 1000, oy + 3800), "管道-加药")
    _tri(msp, (ox + 1000, oy + 3700), (0, 1), s * 0.6, "流向")
    _t(msp, "CIP反洗注入", (ox + 2800, oy + 2850), 2.0 * s, align=MC,
       layer="文字", tracker=tracker)

    _t(msp, f"抽吸负压 {p['suction_p']:.0f} kPa｜CIP：{p['cip_conc']}",
       (ox + W / 2, oy - 4 * s), 2.3 * s, align=MC, layer="文字",
       tracker=tracker)

    if label:
        _t(msp, label, (ox + W / 2, oy + H + 5 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (ox + W, oy)


# ══════════════════════════════════════════════════════════
#  6. 膜列布置图（多箱组合）
# ══════════════════════════════════════════════════════════

def draw_mbr_train(msp, origin, p=None, scale=100.0,
                   label="膜列(多膜箱组合)布置图", tracker=None):
    """多膜箱并排：产水/曝气/反洗母管贯通连接。"""
    p = _params(p)
    s = scale
    ox, oy = _r(*origin)
    tl, tw = p["tank_L"], p["tank_W"]
    n = 4                        # 4 个膜箱一列
    gap = 800.0
    cx = ox + (n * tl + (n - 1) * gap) / 2.0

    # 膜箱阵列
    for i in range(n):
        x0 = ox + i * (tl + gap)
        _rect(msp, x0, oy, x0 + tl, oy + tw, "池体-壁")
        # 内部膜组件示意
        _rect(msp, x0 + 300, oy + 150, x0 + tl - 300, oy + tw - 150, "细实线")
        _t(msp, f"{i+1}#膜箱", (x0 + tl / 2, oy + tw / 2), 2.0 * s, align=MC,
           layer="文字", tracker=tracker)

    # 产水母管（上部贯通）
    y_perm = oy + tw + 800
    _ln(msp, (ox, y_perm), (ox + n * tl + (n - 1) * gap, y_perm), "管道-给水")
    for i in range(n):
        x0 = ox + i * (tl + gap) + tl / 2
        _ln(msp, (x0, oy + tw), (x0, y_perm), "管道-给水")
        _rect(msp, x0 - 100, y_perm - 250, x0 + 100, y_perm - 50, "阀门")
    _t(msp, f"产水母管 DN{p['permeate_dn']:.0f}（各箱设电动阀）",
       (cx, y_perm + 4 * s), 2.0 * s, align=MC, layer="文字", tracker=tracker)

    # 曝气母管（下部贯通）
    y_air = oy - 800
    _ln(msp, (ox, y_air), (ox + n * tl + (n - 1) * gap, y_air), "管道-加药")
    for i in range(n):
        x0 = ox + i * (tl + gap) + tl / 2
        _ln(msp, (x0, oy), (x0, y_air), "管道-加药")
    _t(msp, f"曝气母管 DN{p['air_main_dn']:.0f}", (cx, y_air - 4 * s),
       2.0 * s, align=MC, layer="文字", tracker=tracker)

    _t(msp, f"{n} 膜箱一列｜可独立离线清洗", (cx, oy - 12 * s), 2.3 * s,
       align=MC, layer="文字", tracker=tracker)

    if label:
        _t(msp, label, (cx, y_perm + 9 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (cx, oy)
