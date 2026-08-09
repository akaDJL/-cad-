# -*- coding: utf-8 -*-
"""RTO 蓄热式焚烧炉多视图制图 v1.0（HJ 2000、HJ 1093、GB 37822）。

三室 RTO 成套视图：外形总图(正立面/平面)、纵剖面、切换阀系统、
蓄热-放热-吹扫工艺流程。所有几何参数以 dict 传入（默认取
knowledge.rto_data.RTO_DEFAULTS）——本模块只负责"画"，不负责"算"。

坐标单位 mm，scale=出图比例倒数(1:100 → 100)。图层沿用包内中文命名。
"""
from __future__ import annotations

import math

from ezdxf.enums import TextEntityAlignment

from ..utils import _r, _tri
from .annotate import _t
from ..knowledge.rto_data import RTO_DEFAULTS

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
    d = dict(RTO_DEFAULTS)
    d.update(p or {})
    return d


def _chamber_xs(p, ox):
    """各蓄热室的 x 范围列表 [(x0, x1), ...]。"""
    n = p["n_chamber"]
    W = p["chamber_W"]
    return [(ox + i * W, ox + (i + 1) * W) for i in range(n)]


# ══════════════════════════════════════════════════════════
#  1. 外形总图 — 正立面
# ══════════════════════════════════════════════════════════

def draw_rto_elevation(msp, origin, p=None, scale=100.0,
                       label="RTO蓄热焚烧炉外形图", tracker=None):
    """正立面：三蓄热室/顶部燃烧室/燃烧器/底部阀箱/进出口/烟囱。"""
    p = _params(p)
    s = scale
    ox, oy = _r(*origin)
    xs = _chamber_xs(p, ox)
    n = p["n_chamber"]
    W = p["chamber_W"]
    chH = p["chamber_H"]
    combH = p["comb_H"]
    vH = p["valve_H"]
    L = n * W
    cx = ox + L / 2.0

    y_valve_top = oy + vH
    y_bed_top = y_valve_top + chH
    y_top = y_bed_top + combH

    # 底部阀箱（通长）
    _rect(msp, ox, oy, ox + L, y_valve_top, "设备")
    _t(msp, "切换阀箱", (cx, oy + vH / 2), 2.2 * s, align=MC, layer="文字",
       tracker=tracker)

    # 蓄热室（n 个并排，室间隔板）
    for i, (x0, x1) in enumerate(xs):
        _rect(msp, x0, y_valve_top, x1, y_bed_top, "设备")
        # 蓄热体分层线
        for j in range(1, p["bed_layers"]):
            ly = y_valve_top + chH * j / (p["bed_layers"] + 1)
            _ln(msp, (x0, ly), (x1, ly), "细实线")
        _t(msp, f"{i+1}#蓄热室", ((x0 + x1) / 2, y_valve_top + 4 * s),
           2.0 * s, align=MC, layer="文字", tracker=tracker)
    _t(msp, "陶瓷蓄热体", (cx, y_valve_top + chH * 0.55), 2.2 * s, align=MC,
       layer="文字", tracker=tracker)

    # 顶部燃烧室（贯通）
    _rect(msp, ox - p["insulation_t"], y_bed_top, ox + L + p["insulation_t"],
          y_top, "设备")
    _rect(msp, ox, y_bed_top + 100, ox + L, y_top - 100, "细实线")
    _t(msp, f"燃烧室 {p['comb_t']:.0f}℃", (cx, (y_bed_top + y_top) / 2),
       2.5 * s, align=MC, layer="文字", tracker=tracker)

    # 燃烧器（顶部中央）
    bd = p["burner_dn"]
    _rect(msp, cx - bd / 2, y_top, cx + bd / 2, y_top + 800, "设备")
    _ln(msp, (cx, y_top), (cx, y_top + 800), "点画线", linetype="CENTER")
    _t(msp, "燃气燃烧器", (cx + bd, y_top + 400), 2.0 * s, align=ML,
       layer="文字", tracker=tracker)
    # 火焰示意
    _tri(msp, (cx, y_top - 300), (0, -1), s * 1.0, "细实线")

    # 进出口（阀箱两侧）
    idn = p["inlet_dn"]
    _rect(msp, ox - idn, oy + vH / 2 - idn / 2, ox, oy + vH / 2 + idn / 2,
          "设备")
    _tri(msp, (ox - idn - 3 * s, oy + vH / 2), (1, 0), s, "流向")
    _t(msp, f"废气进口 Φ{idn:.0f}", (ox - idn / 2, oy - 4 * s), 2.0 * s,
       align=MC, layer="文字", tracker=tracker)
    odn = p["outlet_dn"]
    _rect(msp, ox + L, oy + vH / 2 - odn / 2, ox + L + odn,
          oy + vH / 2 + odn / 2, "设备")
    _tri(msp, (ox + L + odn + 3 * s, oy + vH / 2), (1, 0), s, "流向")
    _t(msp, f"净化气出口 Φ{odn:.0f}", (ox + L + odn / 2, oy - 4 * s),
       2.0 * s, align=MC, layer="文字", tracker=tracker)

    # 烟囱（出口后接，右侧竖管）
    sd = p["stack_dn"]
    sx = ox + L + odn + 1500
    _rect(msp, sx, oy, sx + sd, oy + vH / 2 + 2000, "设备")
    _ln(msp, (ox + L + odn, oy + vH / 2), (sx + sd / 2, oy + vH / 2), "设备")
    _ln(msp, (sx + sd / 2, oy + vH / 2), (sx + sd / 2, oy + vH / 2), "设备")
    _t(msp, "烟囱", (sx + sd / 2, oy + vH / 2 + 2300), 2.0 * s, align=MC,
       layer="文字", tracker=tracker)

    # 泄爆片（燃烧室顶部一侧）
    _circle(msp, (ox + 600, y_top), 200, "设备")
    _t(msp, "泄爆片", (ox + 600, y_top + 400), 2.0 * s, align=MC, layer="文字",
       tracker=tracker)

    _t(msp, f"三室 RTO｜热回收率 {p['heat_recovery']*100:.0f}%｜去除率≥99%",
       (cx, oy - 9 * s), 2.3 * s, align=MC, layer="文字", tracker=tracker)

    if label:
        _t(msp, label, (cx, oy - 15 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (cx, oy, y_top + 800)


# ══════════════════════════════════════════════════════════
#  2. 外形总图 — 平面（俯视）
# ══════════════════════════════════════════════════════════

def draw_rto_plan(msp, origin, p=None, scale=100.0,
                  label="平面图", tracker=None):
    """俯视：三蓄热室 + 阀箱 + 进出口管道方位。"""
    p = _params(p)
    s = scale
    ox, oy = _r(*origin)
    xs = _chamber_xs(p, ox)
    n = p["n_chamber"]
    D = p["chamber_D"]
    L = n * p["chamber_W"]
    cx, cy = ox + L / 2.0, oy + D / 2.0

    # 炉体外轮廓
    _rect(msp, ox, oy, ox + L, oy + D, "设备")
    # 室间隔板
    for x0, x1 in xs[1:]:
        _ln(msp, (x0, oy), (x0, oy + D), "设备")
    # 蓄热体投影（每室斜纹示意）
    for i, (x0, x1) in enumerate(xs):
        for j in range(3):
            lx = x0 + (x1 - x0) * (j + 0.5) / 3.0
            _ln(msp, (lx, oy + 200), (lx, oy + D - 200), "细实线")

    # 燃烧室投影（点画线内框）
    _rect(msp, ox + 200, oy + 200, ox + L - 200, oy + D - 200, "点画线")

    # 阀箱（前侧长条）
    vH = p["valve_H"]
    _rect(msp, ox, oy - vH - 300, ox + L, oy - 300, "设备")
    _t(msp, "切换阀箱", (cx, oy - vH / 2 - 300), 2.0 * s, align=MC,
       layer="文字", tracker=tracker)
    # 每室对应 2 阀（进/排）
    for x0, x1 in xs:
        vx = (x0 + x1) / 2.0
        _circle(msp, (vx, oy - vH / 2 - 300), 150, "阀门")

    # 进出口（阀箱两端）
    idn = p["inlet_dn"]
    _rect(msp, ox - idn, oy - vH / 2 - 300 - idn / 2, ox,
          oy - vH / 2 - 300 + idn / 2, "设备")
    _t(msp, "进", (ox - idn / 2, oy - vH / 2 - 300), 2.2 * s, align=MC,
       layer="文字", tracker=tracker)
    odn = p["outlet_dn"]
    _rect(msp, ox + L, oy - vH / 2 - 300 - odn / 2, ox + L + odn,
          oy - vH / 2 - 300 + odn / 2, "设备")
    _t(msp, "出", (ox + L + odn / 2, oy - vH / 2 - 300), 2.2 * s, align=MC,
       layer="文字", tracker=tracker)

    # 中心线
    _ln(msp, (ox - 3 * s, cy), (ox + L + 3 * s, cy), "点画线",
        linetype="CENTER")

    if label:
        _t(msp, label, (cx, oy + D + 6 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (ox + L, oy)


# ══════════════════════════════════════════════════════════
#  3. 纵剖面图（单室）
# ══════════════════════════════════════════════════════════

def draw_rto_section(msp, origin, p=None, scale=100.0,
                     label="蓄热室纵剖面图", tracker=None):
    """单室纵剖面：切换阀/蓄热体分层/气流上升/燃烧室。"""
    p = _params(p)
    s = scale
    ox, oy = _r(*origin)
    W = p["chamber_W"]
    chH = p["chamber_H"]
    combH = p["comb_H"]
    vH = p["valve_H"]
    cx = ox + W / 2.0

    y_vt = oy + vH
    y_bt = y_vt + chH
    y_top = y_bt + combH

    # 阀箱（底部，进/排两阀）
    _rect(msp, ox, oy, ox + W, y_vt, "设备")
    for k, name in ((0.25, "进气阀"), (0.75, "排气阀")):
        vx = ox + W * k
        _circle(msp, (vx, oy + vH / 2), 150, "阀门")
        _ln(msp, (vx, oy + vH / 2 + 150), (vx, y_vt), "细实线")
        _t(msp, name, (vx, oy - 3 * s), 1.8 * s, align=MC, layer="文字",
           tracker=tracker)

    # 蓄热室壁 + 保温（双线）
    _rect(msp, ox, y_vt, ox + W, y_bt, "设备")
    _rect(msp, ox + 150, y_vt + 150, ox + W - 150, y_bt - 150, "细实线")

    # 蓄热体分层（蜂窝陶瓷，交叉线示意）
    nl = p["bed_layers"]
    for j in range(nl):
        ly0 = y_vt + 200 + (chH - 400) * j / nl
        ly1 = y_vt + 200 + (chH - 400) * (j + 1) / nl
        _ln(msp, (ox + 200, ly0), (ox + W - 200, ly1), "细实线")
        _ln(msp, (ox + 200, ly1), (ox + W - 200, ly0), "细实线")
    _t(msp, f"蓄热体 {p['bed_layers']} 层×{p['bed_H']/nl:.0f}",
       (ox + W + 3 * s, y_vt + chH / 2), 2.0 * s, align=ML, layer="文字",
       tracker=tracker)

    # 气流箭头（上升）
    for k in (0.3, 0.5, 0.7):
        ax = ox + W * k
        _tri(msp, (ax, y_bt - 400), (0, 1), s * 0.5, "流向")

    # 燃烧室
    _rect(msp, ox - 250, y_bt, ox + W + 250, y_top, "设备")
    _t(msp, f"燃烧室 {p['comb_t']:.0f}℃", (cx, (y_bt + y_top) / 2), 2.2 * s,
       align=MC, layer="文字", tracker=tracker)

    # 热电偶（燃烧室侧壁）
    _ln(msp, (ox + W + 250, y_bt + combH / 2), (ox + W + 700, y_bt + combH / 2),
        "细实线")
    _circle(msp, (ox + W + 750, y_bt + combH / 2), 100, "设备")
    _t(msp, "热电偶", (ox + W + 850, y_bt + combH / 2), 2.0 * s, align=ML,
       layer="文字", tracker=tracker)

    if label:
        _t(msp, label, (cx, oy - 8 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (cx, oy, y_top)


# ══════════════════════════════════════════════════════════
#  4. 切换阀系统图
# ══════════════════════════════════════════════════════════

def draw_rto_valve(msp, origin, p=None, scale=100.0,
                   label="切换阀系统图", tracker=None):
    """提升阀组：每室进/排/吹扫三阀 + 气缸驱动 + 时序表。"""
    p = _params(p)
    s = scale
    ox, oy = _r(*origin)
    n = p["n_chamber"]
    bay = 2400.0
    W = n * bay
    H = 4200.0
    cx = ox + W / 2.0

    # 每室一组阀（进/排/吹扫竖排）
    for i in range(n):
        x0 = ox + i * bay
        # 蓄热室（顶部方块）
        _rect(msp, x0 + 400, oy + H - 1000, x0 + bay - 400, oy + H, "设备")
        _t(msp, f"{i+1}#室", (x0 + bay / 2, oy + H - 500), 2.0 * s, align=MC,
           layer="文字", tracker=tracker)
        # 三个提升阀
        for k, (name, ln) in enumerate((("进气阀", "管道-污水"),
                                        ("排气阀", "管道-给水"),
                                        ("吹扫阀", "管道-加药"))):
            vy = oy + 600 + k * 900
            _rect(msp, x0 + 800, vy - 200, x0 + 1600, vy + 200, "阀门")
            _ln(msp, (x0 + 1200, vy + 200), (x0 + 1200, oy + H - 1000),
                "细实线")
            # 气缸（阀上方）
            _rect(msp, x0 + 1050, vy + 250, x0 + 1350, vy + 550, "设备")
            _t(msp, name, (x0 + 1750, vy), 1.8 * s, align=ML, layer="文字",
               tracker=tracker)
        # 进出口总管连接
        _ln(msp, (x0, oy + 600), (x0 + 800, oy + 600), "管道-污水")
        _ln(msp, (x0 + 1600, oy + 1500), (x0 + bay, oy + 1500), "管道-给水")

    # 总管标注
    _t(msp, "废气总管", (ox - 3 * s, oy + 600), 2.0 * s, align=MR,
       layer="文字", tracker=tracker)
    _t(msp, "净化气总管", (cx, oy + 1500 + 4 * s), 2.0 * s, align=MC,
       layer="文字", tracker=tracker)

    # 时序表（右下角）
    tx = ox + W + 800
    _t(msp, "切换时序", (tx, oy + H - 600), 2.2 * s, align=ML, layer="文字",
       tracker=tracker)
    rows = [("状态", "1#", "2#", "3#"), ("T1", "蓄热", "放热", "吹扫"),
            ("T2", "吹扫", "蓄热", "放热"), ("T3", "放热", "吹扫", "蓄热")]
    for r, row in enumerate(rows):
        for c, cell in enumerate(row):
            _t(msp, cell, (tx + c * 1400, oy + H - 1200 - r * 500), 1.8 * s,
               align=ML, layer="文字", tracker=tracker)

    if label:
        _t(msp, label, (cx, oy + H + 6 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (ox + W, oy)


# ══════════════════════════════════════════════════════════
#  5. 工艺流程图（蓄热-放热-吹扫）
# ══════════════════════════════════════════════════════════

def draw_rto_flow(msp, origin, p=None, scale=100.0,
                  label="RTO 工艺流程图", tracker=None):
    """流程框图：废气→阻火器→RTO(三态)→烟囱；余热→换热器回用。"""
    p = _params(p)
    s = scale
    ox, oy = _r(*origin)
    W = 12000.0
    H = 5000.0

    def _box(x, y, w, h, name, layer="设备"):
        _rect(msp, x, y, x + w, y + h, layer)
        _t(msp, name, (x + w / 2, y + h / 2), 2.2 * s, align=MC, layer="文字",
           tracker=tracker)

    def _arrow(x0, y0, x1, y1, layer="流向"):
        _ln(msp, (x0, y0), (x1, y1), layer)
        dx, dy = x1 - x0, y1 - y0
        ln = math.hypot(dx, dy) or 1.0
        _tri(msp, (x1, y1), (dx / ln, dy / ln), s * 0.6, layer)

    y_mid = oy + H / 2
    # 主流程链
    _box(ox, y_mid - 500, 1800, 1000, "废气收集", "设备")
    _box(ox + 2400, y_mid - 500, 1600, 1000, "阻火器", "设备")
    _box(ox + 4600, y_mid - 900, 2200, 1800, "RTO三室炉", "粗实线")
    _box(ox + 7400, y_mid - 500, 1600, 1000, "引风机", "设备")
    _box(ox + 9600, y_mid - 500, 1400, 1000, "烟囱", "设备")
    _arrow(ox + 1800, y_mid, ox + 2400, y_mid)
    _arrow(ox + 4000, y_mid, ox + 4600, y_mid)
    _arrow(ox + 6800, y_mid, ox + 7400, y_mid)
    _arrow(ox + 9000, y_mid, ox + 9600, y_mid)
    _t(msp, f"净化气(≤排放限值)", (ox + 10300, y_mid + 900), 2.0 * s,
       align=MC, layer="文字", tracker=tracker)

    # RTO 内部三态注记
    _t(msp, "蓄热/放热/吹扫循环", (ox + 5700, y_mid - 1400), 2.0 * s,
       align=MC, layer="文字", tracker=tracker)
    # 燃气支线
    _box(ox + 4600, oy + 300, 2200, 800, "燃气/助燃风", "设备")
    _arrow(ox + 5700, oy + 1100, ox + 5700, y_mid - 900, "管道-加药")
    # 余热回用支线
    _box(ox + 7400, oy + H - 1400, 2200, 900, "余热换热器(可选)", "设备")
    _arrow(ox + 7400, y_mid + 500, ox + 7900, oy + H - 1400, "管道-给水")

    _t(msp, f"燃烧 {p['comb_t']:.0f}℃｜停留 {p['residence']}s｜热回收 "
            f"{p['heat_recovery']*100:.0f}%", (ox + W / 2, oy - 4 * s),
       2.3 * s, align=MC, layer="文字", tracker=tracker)

    if label:
        _t(msp, label, (ox + W / 2, oy + H + 5 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (ox + W, oy)
