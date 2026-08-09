# -*- coding: utf-8 -*-
"""IC 内循环厌氧反应器多视图制图 v1.0（HJ 2023、HJ 2013、GB 50014）。

IC 反应器成套视图：外形总图(正立面/平面)、纵剖面、旋流布水器、
三相分离器详图、沼气提升内循环系统。所有几何参数以 dict 传入（默认取
knowledge.ic_reactor_data.IC_DEFAULTS）——本模块只负责"画"，不负责"算"。

坐标单位 mm，scale=出图比例倒数(1:100 → 100)。图层沿用包内中文命名。
"""
from __future__ import annotations

import math

from ezdxf.enums import TextEntityAlignment

from ..utils import _r, _tri
from .annotate import _t
from ..knowledge.ic_reactor_data import IC_DEFAULTS

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
    d = dict(IC_DEFAULTS)
    d.update(p or {})
    return d


def _vert(p):
    """竖向分段（相对 origin 底部 oy）。"""
    y0 = 0.0
    y1 = y0 + p["distribute_H"]      # 布水区顶
    y2 = y1 + p["r1_H"]              # 第一反应室顶
    y3 = y2 + p["sep1_H"]            # 一级分离区顶
    y4 = y3 + p["r2_H"]              # 第二反应室顶
    y5 = y4 + p["sep2_H"]            # 二级分离/沉淀区顶
    y6 = y5 + p["top_H"]             # 罐顶
    return dict(y0=y0, y1=y1, y2=y2, y3=y3, y4=y4, y5=y5, y6=y6)


def _gas_sep_pos(p, ox, oy):
    """气液分离器中心（罐顶上方）。"""
    v = _vert(p)
    return ox + p["D"] / 2.0, oy + v["y6"] + p["gls_H"] + 800


# ══════════════════════════════════════════════════════════
#  1. 外形总图 — 正立面
# ══════════════════════════════════════════════════════════

def draw_ic_elevation(msp, origin, p=None, scale=100.0,
                      label="IC厌氧反应器外形图", tracker=None):
    """正立面：罐体分段/气液分离器/内循环管/进出水/沼气/取样口。"""
    p = _params(p)
    s = scale
    ox, oy = _r(*origin)
    D = p["D"]
    v = _vert(p)
    y0, y1, y2, y3, y4, y5, y6 = (oy + v[k] for k in
                                  ("y0", "y1", "y2", "y3", "y4", "y5", "y6"))
    cx = ox + D / 2.0

    # 罐体
    _rect(msp, ox, y0, ox + D, y6, "设备")
    # 分段线 + 区名
    segs = [(y1, "布水区"), (y2, "第一反应室"), (y3, "一级三相分离"),
            (y4, "第二反应室"), (y5, "沉淀区")]
    for yy, name in segs:
        _ln(msp, (ox, yy), (ox + D, yy), "细实线")
    _t(msp, "第一反应室", (ox - 3 * s, (y1 + y2) / 2), 2.2 * s, align=MR,
       layer="文字", tracker=tracker)
    _t(msp, "第二反应室", (ox - 3 * s, (y3 + y4) / 2), 2.2 * s, align=MR,
       layer="文字", tracker=tracker)
    _t(msp, "沉淀区", (ox - 3 * s, (y4 + y5) / 2), 2.2 * s, align=MR,
       layer="文字", tracker=tracker)

    # 顶部封头
    msp.add_arc(_r(cx, y6), D / 2.0, 0, 180, dxfattribs={"layer": "设备"})

    # 气液分离器（罐顶上方圆罐）
    gx, gy = _gas_sep_pos(p, ox, oy)
    _circle(msp, (gx, gy), p["gls_D"] / 2.0, "设备")
    _t(msp, "气液分离器", (gx, gy), 2.2 * s, align=MC, layer="文字",
       tracker=tracker)

    # 沼气提升管（第一反应室顶 → 分离器，2 根）
    rd = p["riser_dn"]
    for k in (-0.18, 0.18):
        rx = cx + D * k
        _ln(msp, (rx, y2 + p["sep1_H"] * 0.5), (rx, y6), "管道-污水")
        _ln(msp, (rx, y6), (rx, gy - p["gls_D"] / 2.0), "管道-污水")
    _t(msp, f"沼气提升管 2×Φ{rd:.0f}", (ox + D + 3 * s, (y2 + y6) / 2),
       2.0 * s, align=ML, layer="文字", tracker=tracker)

    # 下降管（分离器底 → 布水区，内循环）
    dd = p["downcomer_dn"]
    dx = cx - D * 0.35
    _ln(msp, (gx - p["gls_D"] * 0.3, gy - p["gls_D"] / 2.0), (dx, y6),
        "管道-给水")
    _ln(msp, (dx, y6), (dx, y1 - 200), "管道-给水")
    _t(msp, f"内循环下降管 Φ{dd:.0f}", (dx - 3 * s, (y1 + y6) / 2),
       2.0 * s, align=MR, layer="文字", tracker=tracker)

    # 沼气管（分离器顶）
    bd = p["biogas_dn"]
    _rect(msp, gx - bd / 2, gy + p["gls_D"] / 2.0, gx + bd / 2,
          gy + p["gls_D"] / 2.0 + bd, "设备")
    _tri(msp, (gx, gy + p["gls_D"] / 2.0 + bd + 3 * s), (0, 1), s, "流向")
    _t(msp, f"沼气 DN{bd:.0f}", (gx + bd, gy + p["gls_D"] / 2.0 + bd / 2),
       2.0 * s, align=ML, layer="文字", tracker=tracker)

    # 进水管（底部）
    idn = p["inlet_dn"]
    _rect(msp, ox - idn, oy + 200, ox, oy + 200 + idn, "设备")
    _tri(msp, (ox - idn - 3 * s, oy + 200 + idn / 2), (1, 0), s, "流向")
    _t(msp, f"进水 DN{idn:.0f}", (ox - idn / 2, oy + 100), 2.0 * s, align=MC,
       layer="文字", tracker=tracker)

    # 出水管（沉淀区侧壁）
    odn = p["outlet_dn"]
    _rect(msp, ox + D, y5 - 600, ox + D + odn, y5 - 600 + odn, "设备")
    _tri(msp, (ox + D + odn + 3 * s, y5 - 600 + odn / 2), (1, 0), s, "流向")
    _t(msp, f"出水 DN{odn:.0f}", (ox + D + odn / 2, y5 - 900), 2.0 * s,
       align=MC, layer="文字", tracker=tracker)

    _t(msp, f"Φ{D:.0f}×{p['H_total']:.0f}｜负荷 {p['Nv']} kgCOD/m³·d",
       (cx, oy - 6 * s), 2.3 * s, align=MC, layer="文字", tracker=tracker)

    if label:
        _t(msp, label, (cx, oy - 12 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (cx, oy, gy + p["gls_D"] / 2.0)


# ══════════════════════════════════════════════════════════
#  2. 外形总图 — 平面（俯视）
# ══════════════════════════════════════════════════════════

def draw_ic_plan(msp, origin, p=None, scale=100.0,
                 label="平面图", tracker=None):
    """俯视：圆罐 + 布水点环 + 内循环管位 + 进出水方位。"""
    p = _params(p)
    s = scale
    ox, oy = _r(*origin)
    D = p["D"]
    cx, cy = ox + D / 2.0, oy + D / 2.0

    # 罐体圆 + 中心十字
    _circle(msp, (cx, cy), D / 2.0, "设备")
    _ln(msp, (ox - 3 * s, cy), (ox + D + 3 * s, cy), "点画线", linetype="CENTER")
    _ln(msp, (cx, oy - 3 * s), (cx, oy + D + 3 * s), "点画线", linetype="CENTER")

    # 布水点（外环均布 n_nozzle 个）
    n = p["n_nozzle"]
    r_ring = D * 0.38
    for i in range(n):
        a = 2 * math.pi * i / n
        nx = cx + r_ring * math.cos(a)
        ny = cy + r_ring * math.sin(a)
        _circle(msp, (nx, ny), 100, "设备")
    _t(msp, f"布水点 {n} 个（外环均布）", (cx, cy - r_ring - 4 * s), 2.0 * s,
       align=MC, layer="文字", tracker=tracker)

    # 内循环管位（中心：下降管；两侧提升管）
    _circle(msp, (cx, cy), p["downcomer_dn"] / 2.0, "管道-给水")
    _t(msp, "下降管", (cx, cy), 1.8 * s, align=MC, layer="文字", tracker=tracker)
    for k in (-0.18, 0.18):
        _circle(msp, (cx + D * k, cy), p["riser_dn"] / 2.0, "管道-污水")
    _t(msp, "提升管", (cx + D * 0.18 + 3 * s, cy + 500), 1.8 * s, align=ML,
       layer="文字", tracker=tracker)

    # 进出水（切线进入示意）
    idn = p["inlet_dn"]
    _rect(msp, ox - idn, cy - idn / 2, ox, cy + idn / 2, "设备")
    _t(msp, "进", (ox - idn / 2, cy), 2.2 * s, align=MC, layer="文字",
       tracker=tracker)

    if label:
        _t(msp, label, (cx, oy + D + 6 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (ox + D, oy)


# ══════════════════════════════════════════════════════════
#  3. 纵剖面图
# ══════════════════════════════════════════════════════════

def draw_ic_section(msp, origin, p=None, scale=100.0,
                    label="1-1 剖面图", tracker=None):
    """纵剖面：布水器/颗粒污泥床/两级三相分离器/提升下降管/气液分离器。"""
    p = _params(p)
    s = scale
    ox, oy = _r(*origin)
    D = p["D"]
    v = _vert(p)
    y0, y1, y2, y3, y4, y5, y6 = (oy + v[k] for k in
                                  ("y0", "y1", "y2", "y3", "y4", "y5", "y6"))
    cx = ox + D / 2.0

    # 罐壁剖切
    _rect(msp, ox, y0, ox + D, y6, "设备")

    # 底部布水支管（剖面内 3 根辐射）
    for k in (-0.3, 0.0, 0.3):
        bx = cx + D * k
        _ln(msp, (bx, y0 + 200), (bx, y1 - 100), "管道-给水")
        _tri(msp, (bx, y1 - 50), (0, 1), s * 0.5, "流向")
    _t(msp, "旋流布水器", (cx, y0 + 500), 2.0 * s, align=MC, layer="文字",
       tracker=tracker)

    # 颗粒污泥床（第一反应室下部阴影点阵）
    for j in range(3):
        for i in range(10):
            fx = ox + D * (i + 0.5) / 10.0
            fy = y1 + p["r1_H"] * 0.1 + j * 350
            _circle(msp, (fx, fy), 40, "细实线")
    _t(msp, "颗粒污泥膨胀床", (cx, y1 + p["r1_H"] * 0.35), 2.0 * s, align=MC,
       layer="文字", tracker=tracker)

    # 一级三相分离器（三角罩 4 个）
    for i in range(4):
        tx = ox + D * (i + 0.5) / 4.0
        ty = y2 + p["sep1_H"] * 0.4
        _tri(msp, (tx, ty + 350), (0, 1), s * 1.2, "设备")
    _t(msp, "一级三相分离器", (cx, y2 + p["sep1_H"] * 0.8), 2.0 * s, align=MC,
       layer="文字", tracker=tracker)

    # 二级三相分离器（三角罩 3 个）
    for i in range(3):
        tx = ox + D * (i + 0.5) / 3.0
        ty = y4 + p["sep2_H"] * 0.4
        _tri(msp, (tx, ty + 350), (0, 1), s * 1.2, "设备")
    _t(msp, "二级三相分离器", (cx, y4 + p["sep2_H"] * 0.8), 2.0 * s, align=MC,
       layer="文字", tracker=tracker)

    # 出水堰（沉淀区顶部两侧）
    _ln(msp, (ox + 200, y5 - 300), (ox + D * 0.3, y5 - 300), "设备")
    _ln(msp, (ox + D - 200, y5 - 300), (ox + D * 0.7, y5 - 300), "设备")
    _t(msp, "出水堰", (ox + D * 0.3 + 3 * s, y5 - 150), 1.8 * s, align=ML,
       layer="文字", tracker=tracker)

    # 提升管（剖面中央 1 根贯通到顶）
    _ln(msp, (cx, y2 + p["sep1_H"] * 0.5), (cx, y6), "管道-污水")
    _tri(msp, (cx, y6 - 200), (0, 1), s * 0.6, "流向")

    if label:
        _t(msp, label, (cx, oy - 8 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (cx, oy, y6)


# ══════════════════════════════════════════════════════════
#  4. 旋流布水器平面图
# ══════════════════════════════════════════════════════════

def draw_ic_distributor(msp, origin, p=None, scale=100.0,
                        label="旋流布水器平面图", tracker=None):
    """布水器：进水中心管 + 辐射支管 + 切向布水嘴（旋流）。"""
    p = _params(p)
    s = scale
    ox, oy = _r(*origin)
    D = p["D"]
    cx, cy = ox + D / 2.0, oy + D / 2.0

    # 罐底圆
    _circle(msp, (cx, cy), D / 2.0, "设备")
    _ln(msp, (ox - 3 * s, cy), (ox + D + 3 * s, cy), "点画线", linetype="CENTER")
    _ln(msp, (cx, oy - 3 * s), (cx, oy + D + 3 * s), "点画线", linetype="CENTER")

    # 中心分配罐
    _circle(msp, (cx, cy), p["downcomer_dn"], "设备")
    _t(msp, "中心分配罐", (cx, cy - p["downcomer_dn"] - 3 * s), 2.0 * s,
       align=MC, layer="文字", tracker=tracker)

    # 辐射支管 + 切向水嘴（旋流方向统一逆时针）
    n = p["n_nozzle"]
    r_out = D * 0.42
    r_in = p["downcomer_dn"]
    for i in range(n):
        a = 2 * math.pi * i / n
        x0 = cx + r_in * math.cos(a)
        y0 = cy + r_in * math.sin(a)
        x1 = cx + r_out * math.cos(a)
        y1 = cy + r_out * math.sin(a)
        _ln(msp, (x0, y0), (x1, y1), "管道-给水")
        # 切向喷嘴（端部 90° 拐弯）
        ta = a + math.pi / 2.0
        _ln(msp, (x1, y1), (x1 + 500 * math.cos(ta), y1 + 500 * math.sin(ta)),
            "管道-给水")
        _tri(msp, (x1 + 700 * math.cos(ta), y1 + 700 * math.sin(ta)),
             (math.cos(ta), math.sin(ta)), s * 0.5, "流向")

    _t(msp, f"{n} 支管切向布水，形成旋流防短流", (cx, oy - 6 * s), 2.3 * s,
       align=MC, layer="文字", tracker=tracker)

    if label:
        _t(msp, label, (cx, oy + D + 6 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (ox + D, oy)


# ══════════════════════════════════════════════════════════
#  5. 三相分离器详图
# ══════════════════════════════════════════════════════════

def draw_ic_three_phase(msp, origin, p=None, scale=100.0,
                        label="三相分离器详图", tracker=None):
    """三角罩重叠布置：气封/沉淀缝/回流缝 + 重叠度标注。"""
    p = _params(p)
    s = scale
    ox, oy = _r(*origin)
    W = 6000.0
    hood_W = 1400.0
    hood_H = 900.0
    overlap = 200.0
    cx = ox + W / 2.0

    # 两层三角罩（上下错缝）
    ys = [oy, oy + hood_H * 0.75]
    for row, yy in enumerate(ys):
        n = 4 if row == 0 else 3
        x0 = ox + (W - (n * hood_W - (n - 1) * overlap)) / 2.0
        for i in range(n):
            hx = x0 + i * (hood_W - overlap)
            msp.add_lwpolyline(
                [_r(hx, yy), _r(hx + hood_W / 2, yy + hood_H),
                 _r(hx + hood_W, yy)],
                dxfattribs={"layer": "设备"})
    # 重叠度标注
    _ln(msp, (ox + W * 0.3, oy - 4 * s), (ox + W * 0.3 + overlap, oy - 4 * s),
        "细实线-尺寸")
    _t(msp, f"重叠度 {overlap}（≥15%罩宽）", (cx, oy - 7 * s), 2.0 * s,
       align=MC, layer="文字", tracker=tracker)

    # 沉淀缝/回流缝箭头
    _tri(msp, (ox + W * 0.15, oy + hood_H * 1.6), (0, 1), s * 0.5, "流向")
    _t(msp, "沉淀缝(水上行)", (ox + W * 0.15 + 3 * s, oy + hood_H * 1.5),
       2.0 * s, align=ML, layer="文字", tracker=tracker)
    _tri(msp, (ox + W * 0.85, oy + hood_H * 1.6), (0, -1), s * 0.5, "流向")
    _t(msp, "回流缝(泥下行)", (ox + W * 0.85 + 3 * s, oy + hood_H * 1.5),
       2.0 * s, align=ML, layer="文字", tracker=tracker)
    # 集气室
    _rect(msp, cx - 400, oy + hood_H * 1.75, cx + 400, oy + hood_H * 1.75 + 500,
          "设备")
    _t(msp, "集气室", (cx, oy + hood_H * 1.75 + 250), 2.0 * s, align=MC,
       layer="文字", tracker=tracker)

    if label:
        _t(msp, label, (cx, oy + hood_H * 1.75 + 8 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (ox + W, oy)


# ══════════════════════════════════════════════════════════
#  6. 沼气提升内循环系统图
# ══════════════════════════════════════════════════════════

def draw_ic_gas_riser(msp, origin, p=None, scale=100.0,
                      label="沼气提升内循环系统图", tracker=None):
    """系统图：第一反应室→提升管→气液分离器→下降管→布水区 循环路径。"""
    p = _params(p)
    s = scale
    ox, oy = _r(*origin)
    W = 7000.0
    H = 8000.0
    cx = ox + W / 2.0

    # 反应器（左，简化）
    _rect(msp, ox, oy, ox + 2600, oy + H - 2000, "设备")
    _t(msp, "第一反应室", (ox + 1300, oy + 2200), 2.0 * s, align=MC,
       layer="文字", tracker=tracker)
    _t(msp, "布水区", (ox + 1300, oy + 500), 2.0 * s, align=MC, layer="文字",
       tracker=tracker)

    # 气液分离器（右上）
    gx, gy = ox + 5200, oy + H - 1200
    _circle(msp, (gx, gy), p["gls_D"] / 2.0, "设备")
    _t(msp, "气液分离器", (gx, gy), 2.2 * s, align=MC, layer="文字",
       tracker=tracker)
    # 沼气出口
    _ln(msp, (gx, gy + p["gls_D"] / 2.0), (gx, gy + p["gls_D"] / 2.0 + 700),
        "管道-加药")
    _tri(msp, (gx, gy + p["gls_D"] / 2.0 + 900), (0, 1), s * 0.6, "流向")
    _t(msp, "沼气去利用/火炬", (gx + 3 * s, gy + p["gls_D"] / 2.0 + 400),
       2.0 * s, align=ML, layer="文字", tracker=tracker)

    # 提升管（反应器顶 → 分离器）
    _ln(msp, (ox + 1300, oy + H - 2000), (ox + 1300, oy + H - 600), "管道-污水")
    _ln(msp, (ox + 1300, oy + H - 600), (gx - p["gls_D"] / 2.0, oy + H - 600),
        "管道-污水")
    _ln(msp, (gx - p["gls_D"] / 2.0, oy + H - 600), (gx - p["gls_D"] / 2.0, gy),
        "管道-污水")
    _tri(msp, (ox + 1300, oy + H - 800), (0, 1), s * 0.6, "流向")
    _t(msp, "沼气+混合液提升", (ox + 1500, oy + H - 400), 2.0 * s, align=ML,
       layer="文字", tracker=tracker)

    # 下降管（分离器底 → 布水区）
    _ln(msp, (gx, gy - p["gls_D"] / 2.0), (gx, oy + 700), "管道-给水")
    _ln(msp, (gx, oy + 700), (ox + 2600, oy + 700), "管道-给水")
    _tri(msp, (ox + 2800, oy + 700), (1, 0), s * 0.6, "流向")
    _t(msp, "内循环回流", (gx - 3 * s, oy + 1200), 2.0 * s, align=MR,
       layer="文字", tracker=tracker)

    _t(msp, "靠产气自提升循环，无外加动力", (cx, oy - 5 * s), 2.3 * s,
       align=MC, layer="文字", tracker=tracker)

    if label:
        _t(msp, label, (cx, oy + H + 5 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (ox + W, oy)
