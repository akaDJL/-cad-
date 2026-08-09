# -*- coding: utf-8 -*-
"""湿式静电除尘器多视图制图 v1.0（HJ 2020、JB/T 5910、DL/T 1821）。

立式 WESP 成套视图：外形总图(正立面)、纵剖面、阳极管束平面、
冲洗水系统、绝缘箱详图。所有几何参数以 dict 传入（默认取
knowledge.wesp_data.WESP_DEFAULTS）——本模块只负责"画"，不负责"算"。

坐标单位 mm，scale=出图比例倒数(1:100 → 100)。图层沿用包内中文命名。
"""
from __future__ import annotations

import math

from ezdxf.enums import TextEntityAlignment

from ..utils import _r, _tri
from .annotate import _t
from ..knowledge.wesp_data import WESP_DEFAULTS

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


def _hex(msp, cx, cy, R, layer="细实线"):
    """正六边形（平顶），R=外接圆半径。"""
    pts = []
    for i in range(6):
        a = math.radians(60 * i + 30)
        pts.append(_r(cx + R * math.cos(a), cy + R * math.sin(a)))
    msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": layer})


def _params(p):
    d = dict(WESP_DEFAULTS)
    d.update(p or {})
    return d


def _vert(p):
    """竖向分段（相对 origin 底部 oy）。"""
    y0 = 0.0
    y1 = y0 + p["inlet_H"]          # 进气扩散段顶
    y2 = y1 + p["field_H"]          # 电场区顶
    y3 = y2 + p["top_H"]            # 出口段顶
    y4 = y3 + p["insul_H"]          # 绝缘箱顶
    return dict(y0=y0, y1=y1, y2=y2, y3=y3, y4=y4)


# ══════════════════════════════════════════════════════════
#  1. 外形总图 — 正立面
# ══════════════════════════════════════════════════════════

def draw_wesp_elevation(msp, origin, p=None, scale=100.0,
                        label="湿式静电除尘器外形图", tracker=None):
    """正立面：进气扩散段/管束电场区/出口段/顶部绝缘箱/冲洗管/排水。"""
    p = _params(p)
    s = scale
    ox, oy = _r(*origin)
    D = p["body_D"]
    v = _vert(p)
    y0, y1, y2, y3, y4 = (oy + v[k] for k in ("y0", "y1", "y2", "y3", "y4"))
    cx = ox + D / 2.0
    idn = p["inlet_dn"]

    # 进气扩散段（下渐扩：小端 idn → 大端 D）
    _ln(msp, (cx - idn / 2, y0), (ox, y1), "设备")
    _ln(msp, (cx + idn / 2, y0), (ox + D, y1), "设备")
    _ln(msp, (cx - idn / 2, y0), (cx + idn / 2, y0), "设备")
    _tri(msp, (cx, y0 - 3 * s), (0, 1), s, "流向")
    _t(msp, f"烟气进口 Φ{idn:.0f}(下进)", (cx, y0 - 7 * s), 2.2 * s,
       align=MC, layer="文字", tracker=tracker)
    # 气流均布板（扩散段内 1 道）
    _ln(msp, (cx - D * 0.3, y0 + p["inlet_H"] * 0.5),
        (cx + D * 0.3, y0 + p["inlet_H"] * 0.5), "细实线", linetype="DASHED")

    # 电场区（管束）
    _rect(msp, ox, y1, ox + D, y2, "设备")
    # 管束示意（竖线密排）
    n_tube_col = 9
    for i in range(n_tube_col):
        tx = ox + D * (i + 0.5) / n_tube_col
        _ln(msp, (tx, y1 + 150), (tx, y2 - 150), "细实线")
    _t(msp, f"阳极管束 {p['n_tube']} 根（导电玻璃钢）", (cx, y1 + 4 * s),
       2.0 * s, align=MC, layer="文字", tracker=tracker)

    # 出口段（上渐缩 + 侧出/顶出）
    odn = p["outlet_dn"]
    _ln(msp, (ox, y2), (cx - odn / 2, y3), "设备")
    _ln(msp, (ox + D, y2), (cx + odn / 2, y3), "设备")
    _rect(msp, cx - odn / 2, y3, cx + odn / 2, y3 + 600, "设备")
    _tri(msp, (cx, y3 + 900), (0, 1), s, "流向")
    _t(msp, f"净气出口 Φ{odn:.0f}", (cx + odn / 2 + 3 * s, y3 + 300),
       2.0 * s, align=ML, layer="文字", tracker=tracker)

    # 顶部绝缘箱（两侧）
    iw = p["insul_box_W"]
    for k in (-1, 1):
        bx = cx + k * (D / 2.0 + iw / 2.0 + 200)
        _rect(msp, bx - iw / 2, y2 + 200, bx + iw / 2, y2 + 200 + p["insul_H"],
              "设备")
        _t(msp, "绝缘箱", (bx, y2 + 200 + p["insul_H"] + 3 * s), 2.0 * s,
           align=MC, layer="文字", tracker=tracker)
        # 热风管
        _ln(msp, (bx, y2 + 200 + p["insul_H"]),
            (bx, y2 + 200 + p["insul_H"] + 500), "管道-加药")

    # 冲洗水母管（电场区顶部环形）
    _ln(msp, (ox - 600, y2 - 400), (ox + D + 600, y2 - 400), "管道-给水")
    for i in range(5):
        nx = ox + D * (i + 0.5) / 5.0
        _ln(msp, (nx, y2 - 400), (nx, y2 - 700), "管道-给水")
        _tri(msp, (nx, y2 - 750), (0, -1), s * 0.4, "细实线")
    _t(msp, f"冲洗水母管 Φ{p['spray_dn']:.0f}", (ox - 700, y2 - 4 * s),
       2.0 * s, align=MR, layer="文字", tracker=tracker)

    # 排水（底部）
    ddn = p["drain_dn"]
    _rect(msp, cx - ddn / 2, y0 - 400, cx + ddn / 2, y0, "设备")
    _tri(msp, (cx, y0 - 700), (0, -1), s, "流向")
    _t(msp, f"排水 DN{ddn:.0f}", (cx + ddn / 2 + 3 * s, y0 - 200), 2.0 * s,
       align=ML, layer="文字", tracker=tracker)

    if label:
        _t(msp, label, (cx, y0 - 13 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (cx, y0, y4)


# ══════════════════════════════════════════════════════════
#  2. 纵剖面图
# ══════════════════════════════════════════════════════════

def draw_wesp_section(msp, origin, p=None, scale=100.0,
                      label="1-1 剖面图", tracker=None):
    """纵剖面：阳极管/阴极线/水膜下流/冲洗喷嘴/排污。"""
    p = _params(p)
    s = scale
    ox, oy = _r(*origin)
    D = p["body_D"]
    v = _vert(p)
    y1, y2, y3 = oy + v["y1"], oy + v["y2"], oy + v["y3"]
    cx = ox + D / 2.0

    # 壳体剖切
    _rect(msp, ox, y1, ox + D, y2, "设备")

    # 阳极管（剖面内 5 根竖管）
    n_col = 5
    for i in range(n_col):
        tx = ox + D * (i + 0.5) / n_col
        _rect(msp, tx - 100, y1 + 100, tx + 100, y2 - 100, "设备")
        # 阴极线（管中心）
        _ln(msp, (tx, y1 + 100), (tx, y2 - 100), "点画线", linetype="CENTER")
        # 水膜（管内壁细线）
        _ln(msp, (tx - 80, y1 + 200), (tx - 80, y2 - 200), "池体-水")
    _t(msp, "阳极管/阴极线/内壁水膜", (cx, y2 - 4 * s), 2.0 * s, align=MC,
       layer="文字", tracker=tracker)

    # 阴极吊挂（顶部框架）
    _ln(msp, (ox, y2 - 300), (ox + D, y2 - 300), "设备")
    _t(msp, "阴极吊挂框架", (ox + D + 3 * s, y2 - 300), 2.0 * s, align=ML,
       layer="文字", tracker=tracker)

    # 冲洗喷嘴（顶部向下）
    for i in range(4):
        nx = ox + D * (i + 0.5) / 4.0
        _tri(msp, (nx, y2 - 350), (0, -1), s * 0.5, "管道-给水")
    _t(msp, "间断冲洗喷嘴", (cx, y2 - 100), 2.0 * s, align=MC, layer="文字",
       tracker=tracker)

    # 底部排污斗（斜板）
    _ln(msp, (ox, y1), (cx - 300, oy), "设备")
    _ln(msp, (ox + D, y1), (cx + 300, oy), "设备")

    if label:
        _t(msp, label, (cx, oy - 8 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (cx, oy, y3)


# ══════════════════════════════════════════════════════════
#  3. 阳极管束平面布置图
# ══════════════════════════════════════════════════════════

def draw_wesp_tube(msp, origin, p=None, scale=100.0,
                   label="阳极管束平面布置图", tracker=None):
    """俯视：蜂窝正六边形管束 + 阴极线中心点 + 壳体圆。"""
    p = _params(p)
    s = scale
    ox, oy = _r(*origin)
    D = p["body_D"]
    cx, cy = ox + D / 2.0, oy + D / 2.0

    # 壳体圆
    _circle(msp, (cx, cy), D / 2.0, "设备")
    _ln(msp, (ox - 3 * s, cy), (ox + D + 3 * s, cy), "点画线",
        linetype="CENTER")
    _ln(msp, (cx, oy - 3 * s), (cx, oy + D + 3 * s), "点画线",
        linetype="CENTER")

    # 蜂窝管束（正六边形密排，限制在管束外接圆内）
    hex_d = p["tube_hex"]
    R = hex_d / math.sqrt(3) * 2.0 / 2.0   # 由内切圆推外接圆半径
    bundle_R = p["bundle_D"] / 2.0
    dx = R * 1.5
    dy = R * math.sqrt(3)
    j = 0
    yy = cy - bundle_R
    row = 0
    while yy <= cy + bundle_R:
        xoff = (row % 2) * dx
        xx = cx - bundle_R + xoff
        while xx <= cx + bundle_R:
            if (xx - cx) ** 2 + (yy - cy) ** 2 <= (bundle_R - R) ** 2:
                _hex(msp, xx, yy, R, "细实线")
                _circle(msp, (xx, yy), 20, "设备")   # 阴极线端点
            xx += dx * 2
        yy += dy / 2.0
        row += 1
        j += 1

    _t(msp, f"阳极管正六边形内切 Φ{hex_d:.0f}｜{p['n_tube']} 根",
       (cx, oy - 6 * s), 2.3 * s, align=MC, layer="文字", tracker=tracker)

    if label:
        _t(msp, label, (cx, oy + D + 6 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (ox + D, oy)


# ══════════════════════════════════════════════════════════
#  4. 冲洗水系统图
# ══════════════════════════════════════════════════════════

def draw_wesp_spray(msp, origin, p=None, scale=100.0,
                    label="冲洗水系统图", tracker=None):
    """系统图：水箱 → 冲洗泵 → 程控阀 → 喷嘴；电场排水回污水处理。"""
    p = _params(p)
    s = scale
    ox, oy = _r(*origin)
    W = 9500.0
    H = 4200.0

    # 除尘器（右，简化）
    _rect(msp, ox + 6800, oy + 800, ox + 8800, oy + 4000, "设备")
    _t(msp, "WESP", (ox + 7800, oy + 2400), 2.2 * s, align=MC, layer="文字",
       tracker=tracker)
    # 喷嘴（塔顶）
    _ln(msp, (ox + 6600, oy + 3600), (ox + 6800, oy + 3600), "管道-给水")
    _tri(msp, (ox + 6900, oy + 3600), (1, 0), s * 0.5, "流向")

    # 水箱（左下）
    _rect(msp, ox, oy + 400, ox + 2000, oy + 2000, "设备")
    _ln(msp, (ox + 150, oy + 1700), (ox + 1850, oy + 1700), "池体-水")
    _t(msp, "冲洗水箱", (ox + 1000, oy + 1200), 2.2 * s, align=MC,
       layer="文字", tracker=tracker)

    # 冲洗泵（中部 2 台，一用一备）
    for k in (0, 1):
        px = ox + 3400 + k * 900
        _circle(msp, (px, oy + 700), 260, "设备")
    _t(msp, "冲洗泵(1用1备)", (ox + 3850, oy + 300), 2.0 * s, align=MC,
       layer="文字", tracker=tracker)
    # 水箱 → 泵
    _ln(msp, (ox + 2000, oy + 700), (ox + 3140, oy + 700), "管道-给水")
    _ln(msp, (ox + 3400, oy + 700), (ox + 4300, oy + 700), "管道-给水")
    # 泵 → 程控阀组 → 塔
    _ln(msp, (ox + 4300, oy + 700), (ox + 4600, oy + 700), "管道-给水")
    _ln(msp, (ox + 4600, oy + 700), (ox + 4600, oy + 3600), "管道-给水")
    _rect(msp, ox + 4450, oy + 2500, ox + 4750, oy + 2700, "阀门")
    _t(msp, "程控阀", (ox + 4900, oy + 2600), 2.0 * s, align=ML, layer="文字",
       tracker=tracker)
    _ln(msp, (ox + 4600, oy + 3600), (ox + 6600, oy + 3600), "管道-给水")
    # 压力表
    _circle(msp, (ox + 4600, oy + 3200), 120, "阀门")

    # 塔底排水 → 污水处理（虚线去向）
    _ln(msp, (ox + 7800, oy + 800), (ox + 7800, oy + 300), "管道-污水")
    _ln(msp, (ox + 7800, oy + 300), (ox + 5200, oy + 300), "管道-污水")
    _tri(msp, (ox + 5000, oy + 300), (-1, 0), s * 0.5, "流向")
    _t(msp, "排水至脱硫废水/污水处理", (ox + 6400, oy - 3 * s), 2.0 * s,
       align=MC, layer="文字", tracker=tracker)

    _t(msp, f"冲洗方式：{p['spray_zone']}", (ox + W / 2, oy - 8 * s),
       2.3 * s, align=MC, layer="文字", tracker=tracker)

    if label:
        _t(msp, label, (ox + W / 2, oy + H + 5 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (ox + W, oy)


# ══════════════════════════════════════════════════════════
#  5. 绝缘箱详图
# ══════════════════════════════════════════════════════════

def draw_wesp_insulation(msp, origin, p=None, scale=100.0,
                         label="绝缘箱详图", tracker=None):
    """绝缘箱：瓷瓶/电加热器/热风密封/阴极吊杆穿过。"""
    p = _params(p)
    s = scale
    ox, oy = _r(*origin)
    W = p["insul_box_W"]
    H = p["insul_H"] + 1200
    cx = ox + W / 2.0

    # 箱体
    _rect(msp, ox, oy, ox + W, oy + H, "设备")
    _t(msp, "保温箱壳", (ox + W + 3 * s, oy + H - 300), 2.0 * s, align=ML,
       layer="文字", tracker=tracker)

    # 瓷瓶（中央，伞裙用 3 个台阶）
    for k in range(3):
        wy = oy + 500 + k * 350
        _rect(msp, cx - 180 - k * 40, wy, cx + 180 + k * 40, wy + 200, "设备")
    _t(msp, "支撑瓷瓶", (cx, oy + 350), 2.0 * s, align=MC, layer="文字",
       tracker=tracker)

    # 阴极吊杆（穿瓷瓶中心）
    _ln(msp, (cx, oy - 400), (cx, oy + H + 400), "点画线", linetype="CENTER")
    _t(msp, "阴极吊杆", (cx + 3 * s, oy + H + 200), 1.8 * s, align=ML,
       layer="文字", tracker=tracker)

    # 电加热器（箱内壁两侧）
    for k in (-1, 1):
        hx = cx + k * (W / 2.0 - 200)
        _rect(msp, hx - 100, oy + 300, hx + 100, oy + 900, "设备")
    _t(msp, "电加热器", (ox - 3 * s, oy + 600), 2.0 * s, align=MR,
       layer="文字", tracker=tracker)

    # 热风密封（顶部进风管）
    hd = p["hot_air_dn"]
    _rect(msp, cx - hd / 2, oy + H, cx + hd / 2, oy + H + 500, "管道-加药")
    _tri(msp, (cx, oy + H + 700), (0, 1), s * 0.5, "流向")
    _t(msp, f"热风密封 Φ{hd:.0f}(80~120℃)", (cx + hd, oy + H + 250),
       2.0 * s, align=ML, layer="文字", tracker=tracker)

    # 温度/压力测点
    _circle(msp, (ox + W - 200, oy + H - 400), 80, "阀门")
    _t(msp, "测温", (ox + W - 100, oy + H - 400), 1.8 * s, align=ML,
       layer="文字", tracker=tracker)

    if label:
        _t(msp, label, (cx, oy - 8 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (cx, oy, oy + H + 700)
