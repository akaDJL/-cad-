# -*- coding: utf-8 -*-
"""袋式除尘器多视图制图 v1.0（HJ 2020、HJ/T 75、GB 16297）。

脉冲袋式除尘器的成套视图：外形总图(正立面/平面)、纵剖面、花板布置、
喷吹系统、灰斗及卸料装置。所有几何参数由 design.env_process.design_baghouse_full
从输入条件(风量/过滤风速/袋径/袋长)算出并以 dict 传入——本模块只负责"画"，
不负责"算"，实现"提示词给条件 → 自动出图"。

坐标单位 mm，scale=出图比例倒数(1:100 → 100)。图层沿用包内中文命名。
"""
from __future__ import annotations

import math
from typing import Optional

from ezdxf.enums import TextEntityAlignment

from ..utils import _r, _tri
from .annotate import _t, draw_elevation

MC = TextEntityAlignment.MIDDLE_CENTER
ML = TextEntityAlignment.MIDDLE_LEFT


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


def _vertical_dims(p):
    """竖向关键标高（相对 origin 底部 oy 的偏移），供立面/剖面共用。"""
    leg = p["leg_H"]
    outlet = p["hopper_outlet"]
    neck = 150.0                     # 卸灰口短节高
    hop = p["hopper_H"]
    bag = p["bag_room_H"]
    cg = p["clean_gas_H"]
    y0 = 0.0                          # 支腿底（地面）
    y1 = y0 + leg                     # 卸灰口短节底
    y1n = y1 + neck                   # 灰斗锥底
    y2 = y1n + hop                    # 袋室底 = 灰斗顶
    y3 = y2 + bag                     # 花板 = 净气室底
    y4 = y3 + cg                      # 净气室顶
    return dict(y0=y0, y1=y1, y1n=y1n, y2=y2, y3=y3, y4=y4,
                leg=leg, neck=neck, hop=hop, bag=bag, cg=cg, outlet=outlet)


# ══════════════════════════════════════════════════════════
#  1. 外形总图 — 正立面
# ══════════════════════════════════════════════════════════

def draw_baghouse_elevation(msp, origin, p: dict, scale: float = 100.0,
                            label: str = "袋式除尘器外形图", tracker=None):
    """正立面：支腿/灰斗/袋室/净气室/进出风口/检修门/滤袋示意。"""
    s = scale
    ox, oy = _r(*origin)
    L = p["box_L"]
    v = _vertical_dims(p)
    cx = ox + L / 2.0

    y0, y1, y1n = oy + v["y0"], oy + v["y1"], oy + v["y1n"]
    y2, y3, y4 = oy + v["y2"], oy + v["y3"], oy + v["y4"]
    outlet = v["outlet"]

    # 支腿（两侧，撑到袋室底 y2）
    leg_off = 150.0
    for lx in (ox + leg_off, ox + L - leg_off):
        _ln(msp, (lx, y0), (lx, y2), "设备")
    _ln(msp, (ox + leg_off, y0), (ox + L - leg_off, y0), "细实线")  # 地面线

    # 卸灰口短节（300 宽，y1→y1n，居中）
    _rect(msp, cx - outlet / 2, y1, cx + outlet / 2, y1n, "设备")

    # 灰斗（锥形：下口 outlet@y1n，上口 L@y2）
    _ln(msp, (cx - outlet / 2, y1n), (ox, y2), "设备")
    _ln(msp, (cx + outlet / 2, y1n), (ox + L, y2), "设备")
    _ln(msp, (ox, y2), (ox + L, y2), "设备")

    # 袋室（y2→y3，宽 L）
    _rect(msp, ox, y2, ox + L, y3, "设备")
    # 滤袋示意（袋室内均布 5 条竖线）
    for i in range(1, 6):
        fx = ox + L * i / 6.0
        _ln(msp, (fx, y2 + 100), (fx, y3 - 150), "细实线")

    # 花板线（y3 加粗示意）
    _ln(msp, (ox, y3), (ox + L, y3), "设备")

    # 净气室（y3→y4，宽 L）
    _rect(msp, ox, y3, ox + L, y4, "设备")
    # 检修门（净气室正面，700×900）
    _rect(msp, cx - 350, y3 + 100, cx + 350, y3 + 1000, "细实线")
    _t(msp, "检修门", (cx, y3 + 550), 2.2 * s, align=MC, layer="文字", tracker=tracker)

    # 出风口（净气室顶，竖直向上）
    od = p["outlet_dn"]
    _rect(msp, cx - od / 2, y4, cx + od / 2, y4 + od, "设备")
    _tri(msp, (cx, y4 + od + 3 * s), (0, 1), s, "设备")
    _t(msp, f"出风口 Φ{od:.0f}", (cx, y4 + od + 6 * s), 2.2 * s,
       align=MC, layer="文字", tracker=tracker)

    # 进风口（袋室下部左侧，水平伸入）
    idn = p["inlet_dn"]
    iy = y2 + v["bag"] * 0.25
    _rect(msp, ox - idn, iy - idn / 2, ox, iy + idn / 2, "设备")
    _tri(msp, (ox - idn - 3 * s, iy), (1, 0), s, "设备")
    _t(msp, f"进风口 Φ{idn:.0f}", (ox - idn / 2, iy - idn / 2 - 4 * s), 2.2 * s,
       align=MC, layer="文字", tracker=tracker)

    # 气包（净气室右侧外，横放圆柱示意）
    _rect(msp, ox + L + 100, y3 + 100, ox + L + 350, y3 + 350, "设备")
    _t(msp, "气包", (ox + L + 225, y3 - 3 * s), 2.0 * s, align=MC,
       layer="文字", tracker=tracker)

    # 标题
    if label:
        _t(msp, label, (cx, y0 - 8 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)

    return (cx, y0, y4)   # 返回中心x、底y、顶y 供排版


# ══════════════════════════════════════════════════════════
#  2. 外形总图 — 平面（俯视）
# ══════════════════════════════════════════════════════════

def draw_baghouse_plan(msp, origin, p: dict, scale: float = 100.0,
                       label: str = "平面图", tracker=None):
    """俯视：箱体轮廓 + 花板孔阵 + 进出风口 + 气包。"""
    s = scale
    ox, oy = _r(*origin)
    L, W = p["box_L"], p["box_W"]
    rows, cols = p["rows"], p["cols"]
    spacing = p["spacing"]
    bag_r = p["bag_dia_mm"] / 2.0
    pl, pw = p["plate_L"], p["plate_W"]

    # 箱体轮廓
    _rect(msp, ox, oy, ox + L, oy + W, "设备")

    # 花板孔阵（居中布置）
    offx = ox + (L - pl) / 2.0 + (pl - cols * spacing) / 2.0
    offy = oy + (W - pw) / 2.0 + (pw - rows * spacing) / 2.0
    for j in range(rows):
        for i in range(cols):
            ccx = offx + spacing * (i + 0.5)
            ccy = offy + spacing * (j + 0.5)
            _circle(msp, (ccx, ccy), bag_r, "细实线")

    # 进风口（左侧中）
    idn = p["inlet_dn"]
    _rect(msp, ox - idn, oy + W / 2 - idn / 2, ox, oy + W / 2 + idn / 2, "设备")
    _t(msp, "进", (ox - idn / 2, oy + W / 2), 2.0 * s, align=MC, layer="文字", tracker=tracker)
    # 出风口（中心）
    _circle(msp, (ox + L / 2, oy + W / 2), p["outlet_dn"] / 2.0, "设备")
    # 气包（下侧长条）
    _rect(msp, ox, oy - 350, ox + L, oy - 100, "设备")
    _t(msp, "气包", (ox + L / 2, oy - 225), 2.0 * s, align=MC, layer="文字", tracker=tracker)

    if label:
        _t(msp, label, (ox + L / 2, oy + W + 6 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (ox + L, oy)


# ══════════════════════════════════════════════════════════
#  3. 纵剖面图
# ══════════════════════════════════════════════════════════

def draw_baghouse_section(msp, origin, p: dict, scale: float = 100.0,
                          label: str = "1-1 剖面图", tracker=None):
    """纵剖面：花板(带孔)+悬挂滤袋+喷吹管+灰斗内部。"""
    s = scale
    ox, oy = _r(*origin)
    L = p["box_L"]
    v = _vertical_dims(p)
    cols = p["cols"]
    spacing = p["spacing"]
    bag_len = p["bag_len_mm"]
    bag_r = p["bag_dia_mm"] / 2.0

    y1n, y2, y3, y4 = oy + v["y1n"], oy + v["y2"], oy + v["y3"], oy + v["y4"]
    outlet = v["outlet"]
    cx = ox + L / 2.0

    # 灰斗（锥形）
    _ln(msp, (cx - outlet / 2, y1n), (ox, y2), "设备")
    _ln(msp, (cx + outlet / 2, y1n), (ox + L, y2), "设备")

    # 袋室外壳
    _ln(msp, (ox, y2), (ox, y3), "设备")
    _ln(msp, (ox + L, y2), (ox + L, y3), "设备")

    # 花板（y3 横线，带孔标记）
    _ln(msp, (ox, y3), (ox + L, y3), "设备")

    # 净气室
    _ln(msp, (ox, y3), (ox, y4), "设备")
    _ln(msp, (ox + L, y3), (ox + L, y4), "设备")
    _ln(msp, (ox, y4), (ox + L, y4), "设备")

    # 悬挂滤袋（cols 个，从花板下垂 bag_len）
    offx = ox + (L - cols * spacing) / 2.0
    for i in range(cols):
        fx = offx + spacing * (i + 0.5)
        # 袋口（花板处小圆）
        _circle(msp, (fx, y3), bag_r, "细实线")
        # 袋身两竖线 + 底部半圆
        _ln(msp, (fx - bag_r, y3), (fx - bag_r, y3 - bag_len + bag_r), "细实线")
        _ln(msp, (fx + bag_r, y3), (fx + bag_r, y3 - bag_len + bag_r), "细实线")
        msp.add_arc(_r(fx, y3 - bag_len + bag_r), bag_r, 180, 360,
                    dxfattribs={"layer": "细实线"})

    # 喷吹管（净气室内，每列一根，对准袋口上方）
    for i in range(cols):
        fx = offx + spacing * (i + 0.5)
        _ln(msp, (fx, y3 + 120), (fx, y4 - 50), "细实线", linetype="CENTER")
    # 喷吹总管（贯通）
    _ln(msp, (ox - 300, y3 + 250), (ox + L, y3 + 250), "设备")
    _t(msp, "喷吹管", (ox + L / 2, y4 - 2.5 * s), 2.0 * s, align=MC,
       layer="文字", tracker=tracker)

    # 进出风口
    idn = p["inlet_dn"]
    iy = y2 + v["bag"] * 0.25
    _rect(msp, ox - idn, iy - idn / 2, ox, iy + idn / 2, "设备")
    od = p["outlet_dn"]
    _rect(msp, cx - od / 2, y4, cx + od / 2, y4 + od, "设备")

    if label:
        _t(msp, label, (cx, oy - 8 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (cx, oy, y4)


# ══════════════════════════════════════════════════════════
#  4. 花板布置图
# ══════════════════════════════════════════════════════════

def draw_baghouse_tube_sheet(msp, origin, p: dict, scale: float = 100.0,
                             label: str = "花板布置图", tracker=None):
    """花板：矩形 + 孔阵(直径=袋径) + 孔径/孔数/行列/中心距标注。"""
    s = scale
    ox, oy = _r(*origin)
    pl, pw = p["plate_L"], p["plate_W"]
    rows, cols = p["rows"], p["cols"]
    spacing = p["spacing"]
    bag_d = p["bag_dia_mm"]

    # 花板外框
    _rect(msp, ox, oy, ox + pl, oy + pw, "设备")

    # 孔阵
    offx = ox + (pl - cols * spacing) / 2.0
    offy = oy + (pw - rows * spacing) / 2.0
    for j in range(rows):
        for i in range(cols):
            ccx = offx + spacing * (i + 0.5)
            ccy = offy + spacing * (j + 0.5)
            _circle(msp, (ccx, ccy), bag_d / 2.0, "细实线")

    # 中心线（行列方向）
    _ln(msp, (ox + pl / 2, oy - 4 * s), (ox + pl / 2, oy + pw + 4 * s),
        "中心线", linetype="CENTER")
    _ln(msp, (ox - 4 * s, oy + pw / 2), (ox + pl + 4 * s, oy + pw / 2),
        "中心线", linetype="CENTER")

    # 标注
    _t(msp, f"孔径 Φ{bag_d:.0f}  共{p['n_bags']}孔（{rows}行×{cols}列）  中心距{spacing:.0f}",
       (ox + pl / 2, oy - 6 * s), 2.3 * s, align=MC, layer="文字", tracker=tracker)
    _t(msp, f"花板 {pl:.0f}×{pw:.0f}", (ox + pl / 2, oy + pw + 5 * s),
       2.3 * s, align=MC, layer="文字", tracker=tracker)

    if label:
        _t(msp, label, (ox + pl / 2, oy - 12 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (ox + pl, oy)


# ══════════════════════════════════════════════════════════
#  5. 喷吹系统图
# ══════════════════════════════════════════════════════════

def draw_baghouse_pulse(msp, origin, p: dict, scale: float = 100.0,
                        label: str = "喷吹系统图", tracker=None):
    """喷吹系统：气包 + 脉冲阀(每列) + 喷吹管 + 喷嘴。"""
    s = scale
    ox, oy = _r(*origin)
    L = p["box_L"]
    W = p["box_W"]
    cols = p["cols"]
    rows = p["rows"]
    tank_d = 250.0

    # 气包（横放，长贯通）
    _rect(msp, ox, oy, ox + p["air_tank_L"], oy + tank_d, "设备")
    _t(msp, f"气包 Φ{tank_d:.0f}", (ox - 3 * s, oy + tank_d / 2), 2.0 * s,
       align=TextEntityAlignment.MIDDLE_RIGHT, layer="文字", tracker=tracker)

    # 脉冲阀 + 喷吹管（沿气包，每列一组）
    span = p["air_tank_L"]
    for i in range(cols):
        vx = ox + span * (i + 0.5) / cols
        # 脉冲阀（小气方块）
        _rect(msp, vx - 60, oy + tank_d, vx + 60, oy + tank_d + 120, "设备")
        # 喷吹管（向上进入袋室方向，竖直示意）
        _ln(msp, (vx, oy + tank_d + 120), (vx, oy + tank_d + 120 + W), "设备")
        # 喷嘴（沿喷吹管，对准每行袋口）
        for j in range(rows):
            ny = oy + tank_d + 120 + W * (j + 0.5) / rows
            _ln(msp, (vx - 40, ny), (vx + 40, ny), "细实线")

    # 标注
    _t(msp, f"脉冲阀 {p['n_pulse_valve']}个（每列1个）  喷吹管{cols}根  每管{rows}喷嘴",
       (ox + span / 2, oy - 5 * s), 2.3 * s, align=MC, layer="文字", tracker=tracker)

    if label:
        _t(msp, label, (ox + span / 2, oy + tank_d + 120 + W + 6 * s), 3.2 * s,
           align=MC, layer="文字-标题", tracker=tracker)
    return (ox + span, oy)


# ══════════════════════════════════════════════════════════
#  6. 灰斗及卸料装置详图
# ══════════════════════════════════════════════════════════

def draw_baghouse_hopper(msp, origin, p: dict, scale: float = 100.0,
                         label: str = "灰斗及卸料装置详图", tracker=None):
    """灰斗放大 + 插板阀 + 星型卸料器 + 料位计。"""
    s = scale
    ox, oy = _r(*origin)          # origin = 灰斗上口左端
    W = p["box_W"]
    hop = p["hopper_H"]
    outlet = p["hopper_outlet"]
    cx = ox + W / 2.0
    yb = oy - hop                  # 灰斗下口标高

    # 灰斗锥形
    _ln(msp, (ox, oy), (cx - outlet / 2, yb), "设备")
    _ln(msp, (ox + W, oy), (cx + outlet / 2, yb), "设备")
    _ln(msp, (ox, oy), (ox + W, oy), "设备")
    _ln(msp, (cx - outlet / 2, yb), (cx + outlet / 2, yb), "设备")

    # 斗壁角度标注
    _t(msp, "斗壁倾角60°", (ox + W * 0.7, oy - hop * 0.45), 2.2 * s,
       align=ML, layer="文字", tracker=tracker)

    # 插板阀（卸灰口下方第一段）
    gv_y = yb - 200
    _rect(msp, cx - outlet / 2 - 100, gv_y, cx + outlet / 2 + 100, gv_y + 120, "设备")
    _ln(msp, (cx - outlet / 2 - 100, gv_y + 60), (cx + outlet / 2 + 100, gv_y + 60), "细实线")
    _t(msp, "插板阀", (cx + outlet / 2 + 250, gv_y + 60), 2.0 * s, align=ML,
       layer="文字", tracker=tracker)

    # 星型卸料器（插板阀下方，圆+叶片）
    rl_cy = gv_y - 350
    _circle(msp, (cx, rl_cy), 250, "设备")
    for ang in range(0, 360, 45):
        a = math.radians(ang)
        _ln(msp, (cx, rl_cy), (cx + 250 * math.cos(a), rl_cy + 250 * math.sin(a)), "细实线")
    _t(msp, "星型卸料器", (cx + 350, rl_cy), 2.0 * s, align=ML, layer="文字", tracker=tracker)

    # 料位计（灰斗侧壁）
    _circle(msp, (ox + W * 0.15, oy - hop * 0.3), 60, "设备")
    _ln(msp, (ox + W * 0.15 + 60, oy - hop * 0.3), (ox + W * 0.15 + 500, oy - hop * 0.3), "细实线")
    _t(msp, "料位计", (ox + W * 0.15 + 550, oy - hop * 0.3), 2.0 * s, align=ML,
       layer="文字", tracker=tracker)

    if label:
        _t(msp, label, (cx, yb - 900), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (cx, yb - 900)
