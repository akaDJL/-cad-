# -*- coding: utf-8 -*-
"""钢烟囱（排气筒）多视图制图 v1.0（GB 50051、GB 16297、CEMS 采样规范）。

钢烟囱的成套视图：外形总图(正立面/平面)、纵剖面、采样孔、平台、基础。
高耸结构按工程惯例采用**折断画法**（底段+顶段，中间折断线省略锥体中段）。
几何参数由 design.env_process.design_chimney_full 算出并以 dict 传入。

坐标单位 mm（design 返回的直径 m，此处 ×1000 转 mm）。图层沿用包内中文命名。
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


def _break(msp, x0, x1, y, layer="细实线"):
    """折断线（Z 字省略号），表示中段省略。"""
    xm = (x0 + x1) / 2.0
    msp.add_lwpolyline([(x0, y), (xm - 300, y + 150), (xm + 300, y - 150), (x1, y)],
                       dxfattribs={"layer": layer})


def _cone(msp, cx, y0, y1, d0, d1, layer="设备"):
    """锥形筒体段：底 d0 顶 d1，从 y0 到 y1。"""
    _ln(msp, (cx - d0 / 2, y0), (cx - d1 / 2, y1), layer)
    _ln(msp, (cx + d0 / 2, y0), (cx + d1 / 2, y1), layer)


def _ladder(msp, x, y0, y1, layer="细实线"):
    """爬梯（一侧竖杆+横档）。"""
    _ln(msp, (x, y0), (x, y1), layer)
    n = int((y1 - y0) / 300)
    for i in range(n + 1):
        ry = y0 + (y1 - y0) * i / max(1, n)
        _ln(msp, (x, ry), (x - 250, ry), layer)


def _platform(msp, cx, y, d, layer="设备"):
    """休息平台（环形，剖面画横板+栏杆）。"""
    _ln(msp, (cx - d / 2 - 600, y), (cx + d / 2 + 600, y), layer)
    _ln(msp, (cx - d / 2 - 600, y), (cx - d / 2 - 600, y + 500), "细实线")
    _ln(msp, (cx + d / 2 + 600, y), (cx + d / 2 + 600, y + 500), "细实线")


# ═══ 1. 外形总图 — 正立面（折断画法）═══
def draw_chimney_elevation(msp, origin, p: dict, scale: float = 100.0,
                           label: str = "钢烟囱外形图", tracker=None):
    s = scale
    ox, oy = _r(*origin)
    D_out = p["D_out"] * 1000.0
    D_base = p["D_base"] * 1000.0
    cx = ox + D_base / 2.0 + 1000

    # ── 底段（基础+进口+一平台）──
    y0 = oy
    y_bot_top = oy + 6000
    _cone(msp, cx, y0, y_bot_top, D_base, D_base - 400)
    _ln(msp, (cx - D_base / 2, y0), (cx + D_base / 2, y0), "设备")   # 底板
    # 烟气进口（底部侧面）
    _rect(msp, cx - D_base / 2 - 800, y0 + 800, cx - D_base / 2, y0 + 1600, "设备")
    _t(msp, "烟气进口", (cx - D_base / 2 - 400, y0 + 400), 2.0 * s, align=MC,
       layer="文字", tracker=tracker)
    # 爬梯 + 一平台
    _ladder(msp, cx + D_base / 2 + 300, y0, y_bot_top)
    _platform(msp, cx, y0 + 5000, D_base - 400)

    # ── 折断线 ──
    _break(msp, cx - D_base / 2, cx + D_base / 2, y_bot_top + 400)
    _t(msp, f"中段省略（总高 {p['H']}m，平台 {p['n_platform']} 层）",
       (cx, y_bot_top + 1000), 2.2 * s, align=MC, layer="文字", tracker=tracker)

    # ── 顶段（出口+采样孔+顶平台+避雷）──
    y_top0 = y_bot_top + 1600
    y_top1 = y_top0 + 6000
    _cone(msp, cx, y_top0, y_top1, D_out + 400, D_out)
    _ln(msp, (cx - D_out / 2, y_top1), (cx + D_out / 2, y_top1), "设备")  # 出口
    # 采样孔（顶段下部，两侧）
    for sgn in (-1, 1):
        sx = cx + sgn * (D_out / 2 + 150)
        _circle(msp, (sx, y_top0 + 1000), p["sample_dn"] / 2.0, "设备")
    _t(msp, f"采样孔Φ{p['sample_dn']:.0f}", (cx + D_out / 2 + 500, y_top0 + 1300),
       2.0 * s, align=ML, layer="文字", tracker=tracker)
    # 顶平台 + 爬梯
    _platform(msp, cx, y_top0 + 2500, D_out + 200)
    _ladder(msp, cx + D_out / 2 + 300, y_top0, y_top1)
    # 避雷针
    _ln(msp, (cx, y_top1), (cx, y_top1 + 1200), "设备")
    _circle(msp, (cx, y_top1 + 1300), 120, "设备")
    _t(msp, "避雷针", (cx + 300, y_top1 + 900), 2.0 * s, align=ML, layer="文字", tracker=tracker)

    if label:
        _t(msp, label, (cx, oy - 8 * s), 3.2 * s, align=MC, layer="文字-标题", tracker=tracker)
    return (cx, oy, y_top1 + 1300)


# ═══ 2. 外形总图 — 平面 ═══
def draw_chimney_plan(msp, origin, p: dict, scale: float = 100.0,
                      label: str = "平面图", tracker=None):
    s = scale
    ox, oy = _r(*origin)      # origin = 筒体中心
    D_base = p["D_base"] * 1000.0
    _circle(msp, (ox, oy), D_base / 2.0, "设备")        # 底部外圆
    _circle(msp, (ox, oy), D_base / 2.0 - p["wall_t"], "细实线")  # 内圆
    # 爬梯方位（一侧）
    _rect(msp, ox + D_base / 2 - 100, oy - 300, ox + D_base / 2 + 400, oy + 300, "设备")
    _t(msp, "爬梯", (ox + D_base / 2 + 600, oy), 2.0 * s, align=ML, layer="文字", tracker=tracker)
    # 烟气进口（一侧）
    _rect(msp, ox - D_base / 2 - 800, oy - 400, ox - D_base / 2, oy + 400, "设备")
    _t(msp, "进口", (ox - D_base / 2 - 400, oy + 700), 2.0 * s, align=MC, layer="文字", tracker=tracker)
    if label:
        _t(msp, label, (ox, oy + D_base / 2 + 6 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (ox + D_base / 2, oy)


# ═══ 3. 纵剖面图（折断画法）═══
def draw_chimney_section(msp, origin, p: dict, scale: float = 100.0,
                         label: str = "1-1 剖面图", tracker=None):
    s = scale
    ox, oy = _r(*origin)
    D_out = p["D_out"] * 1000.0
    D_base = p["D_base"] * 1000.0
    wt = p["wall_t"]
    cx = ox + D_base / 2.0 + 1000

    # 底段剖面
    y0 = oy
    ybt = oy + 6000
    _cone(msp, cx, y0, ybt, D_base, D_base - 400)
    _cone(msp, cx, y0 + 200, ybt - 100, D_base - 2 * wt, D_base - 400 - 2 * wt, "细实线")  # 内衬
    _ln(msp, (cx - D_base / 2, y0), (cx + D_base / 2, y0), "设备")
    _t(msp, f"壁厚{wt:.0f}mm+内衬防腐", (cx, y0 + 1500), 2.0 * s, align=MC,
       layer="文字", tracker=tracker)
    _platform(msp, cx, y0 + 5000, D_base - 400)
    _break(msp, cx - D_base / 2, cx + D_base / 2, ybt + 400)
    _t(msp, f"中段省略（总高 {p['H']}m）", (cx, ybt + 1000), 2.2 * s, align=MC,
       layer="文字", tracker=tracker)
    # 顶段剖面
    y_t0 = ybt + 1600
    y_t1 = y_t0 + 6000
    _cone(msp, cx, y_t0, y_t1, D_out + 400, D_out)
    _ln(msp, (cx - D_out / 2, y_t1), (cx + D_out / 2, y_t1), "设备")
    for sgn in (-1, 1):
        sx = cx + sgn * (D_out / 2 + 150)
        _circle(msp, (sx, y_t0 + 1000), p["sample_dn"] / 2.0, "设备")
    _platform(msp, cx, y_t0 + 2500, D_out + 200)
    _ln(msp, (cx, y_t1), (cx, y_t1 + 1200), "设备")

    if label:
        _t(msp, label, (cx, oy - 8 * s), 3.2 * s, align=MC, layer="文字-标题", tracker=tracker)
    return (cx, oy, y_t1 + 1200)


# ═══ 4. 采样孔详图 ═══
def draw_chimney_sample_port(msp, origin, p: dict, scale: float = 100.0,
                             label: str = "采样孔详图", tracker=None):
    s = scale
    ox, oy = _r(*origin)
    D_out = p["D_out"] * 1000.0
    sdn = p["sample_dn"]
    # 筒体侧壁一段
    _ln(msp, (ox, oy), (ox, oy + 3000), "设备")
    _ln(msp, (ox + 200, oy), (ox + 200, oy + 3000), "细实线")
    _t(msp, f"烟囱筒体 Φ{D_out:.0f}", (ox - 200, oy + 1500), 2.0 * s, align=MR,
       layer="文字", tracker=tracker)
    # 采样管（穿出侧壁）
    _rect(msp, ox, oy + 1200, ox + 1200, oy + 1200 + sdn, "设备")
    # 闸阀/球阀
    _rect(msp, ox + 500, oy + 1150, ox + 700, oy + 1250 + sdn, "设备")
    _t(msp, "采样管+截止阀", (ox + 600, oy + 1500 + sdn), 2.0 * s, align=MC,
       layer="文字", tracker=tracker)
    # 采样平台
    _ln(msp, (ox, oy), (ox + 1500, oy), "设备")
    _ln(msp, (ox + 1500, oy), (ox + 1500, oy + 500), "细实线")
    _t(msp, "采样平台", (ox + 1300, oy - 4 * s), 2.0 * s, align=MC, layer="文字", tracker=tracker)
    _t(msp, f"采样孔 Φ{sdn:.0f}，设于直管段，上游≥4D、下游≥2D",
       (ox + 750, oy - 9 * s), 2.2 * s, align=MC, layer="文字", tracker=tracker)
    if label:
        _t(msp, label, (ox + 750, oy + 3500), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (ox + 1500, oy)


# ═══ 5. 平台详图 ═══
def draw_chimney_platform(msp, origin, p: dict, scale: float = 100.0,
                          label: str = "休息平台详图", tracker=None):
    s = scale
    ox, oy = _r(*origin)
    W = 4000.0
    # 平台板（格栅）
    _ln(msp, (ox, oy), (ox + W, oy), "设备")
    for k in range(int(W / 150)):
        _ln(msp, (ox + k * 150, oy), (ox + k * 150, oy - 100), "细实线")
    _t(msp, "钢格栅平台板", (ox + W / 2, oy - 5 * s), 2.0 * s, align=MC, layer="文字", tracker=tracker)
    # 栏杆（三横杆+立柱）
    for ry in (oy + 300, oy + 650, oy + 1000):
        _ln(msp, (ox, ry), (ox + W, ry), "细实线")
    for k in range(0, int(W / 1000) + 1):
        _ln(msp, (ox + k * 1000, oy), (ox + k * 1000, oy + 1000), "设备")
    _t(msp, "栏杆 H=1050mm", (ox + W + 200, oy + 500), 2.0 * s, align=ML, layer="文字", tracker=tracker)
    # 爬梯连接
    _ladder(msp, ox + 300, oy - 2000, oy)
    _t(msp, "爬梯（带护笼）", (ox + 600, oy - 1500), 2.0 * s, align=ML, layer="文字", tracker=tracker)
    _t(msp, f"全塔平台 {p['n_platform']} 层，竖向间距 {p['plat_gap']}m",
       (ox + W / 2, oy - 10 * s), 2.2 * s, align=MC, layer="文字", tracker=tracker)
    if label:
        _t(msp, label, (ox + W / 2, oy + 1500), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (ox + W, oy)


# ═══ 6. 基础详图 ═══
def draw_chimney_foundation(msp, origin, p: dict, scale: float = 100.0,
                            label: str = "烟囱基础详图", tracker=None):
    s = scale
    ox, oy = _r(*origin)
    D_base = p["D_base"] * 1000.0
    Df = D_base + 2000.0          # 基础直径
    cx = ox + Df / 2.0
    # 环形基础（剖面）
    _rect(msp, ox, oy, ox + Df, oy + 800, "设备")
    _ln(msp, (ox, oy + 800), (ox + Df, oy + 800), "设备")
    # 筒体（基础上）
    _ln(msp, (cx - D_base / 2, oy + 800), (cx - D_base / 2, oy + 2500), "设备")
    _ln(msp, (cx + D_base / 2, oy + 800), (cx + D_base / 2, oy + 2500), "设备")
    # 地脚螺栓（均布）
    for sgn in (-1, 1):
        bx = cx + sgn * (D_base / 2 - 150)
        _ln(msp, (bx, oy + 200), (bx, oy + 900), "设备")
        _circle(msp, (bx, oy + 900), 60, "设备")
    _t(msp, "地脚螺栓", (cx + D_base / 2 + 200, oy + 600), 2.0 * s, align=ML,
       layer="文字", tracker=tracker)
    # 配筋示意（基础内）
    for k in range(1, int(Df / 300)):
        _ln(msp, (ox + k * 300, oy + 100), (ox + k * 300, oy + 200), "细实线")
    _t(msp, f"环形钢筋混凝土基础 Φ{Df/1000:.1f}m，C30，配双层双向钢筋",
       (cx, oy - 5 * s), 2.2 * s, align=MC, layer="文字", tracker=tracker)
    if label:
        _t(msp, label, (cx, oy + 3200), 3.2 * s, align=MC, layer="文字-标题", tracker=tracker)
    return (cx, oy)
