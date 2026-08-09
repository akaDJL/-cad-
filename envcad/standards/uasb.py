# -*- coding: utf-8 -*-
"""UASB 厌氧反应器多视图制图 v1.0（HJ 2013、GB 50014、UASB 设计规范）。

升流式厌氧污泥床(UASB)反应器的成套视图：外形总图(正立面/平面)、纵剖面、
三相分离器、布水系统、出水堰及排泥。所有几何参数由
design.env_process.design_uasb_full 从输入条件(水量/COD/容积负荷)算出并以 dict
传入——本模块只负责"画"，实现"提示词给条件 → 自动出图"。

坐标单位 mm（design 返回的反应器主尺寸 m，此处统一 ×1000 转 mm）。
scale=出图比例倒数。图层沿用包内中文命名。
"""
from __future__ import annotations

import math

from ezdxf.enums import TextEntityAlignment

from ..utils import _r, _tri
from .annotate import _t

MC = TextEntityAlignment.MIDDLE_CENTER
ML = TextEntityAlignment.MIDDLE_LEFT
MR = TextEntityAlignment.MIDDLE_RIGHT


# ─── 内部辅助 ─────────────────────────────────────────────

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
    """竖向分区标高（相对罐底 oy 的 mm 偏移），供立面/剖面共用。"""
    H = lambda k: p[k] * 1000.0
    y0 = 0.0
    y_sludge = y0 + H("H_sludge")              # 污泥床顶
    y_react = y_sludge + H("H_suspend")        # 反应区顶=悬浮层顶
    y_tp = y_react + H("H_three_phase")        # 三相分离器顶
    y_settle = y_tp + H("H_settle")            # 沉淀区顶
    y_top = y_settle + H("H_freeboard")        # 罐顶
    return dict(y0=y0, y_sludge=y_sludge, y_react=y_react,
                y_tp=y_tp, y_settle=y_settle, y_top=y_top)


# ══════════════════════════════════════════════════════════
#  1. 外形总图 — 正立面
# ══════════════════════════════════════════════════════════

def draw_uasb_elevation(msp, origin, p: dict, scale: float = 100.0,
                        label: str = "UASB反应器外形图", tracker=None):
    """正立面：圆柱罐体(矩形)+进出水管+沼气管+排泥管+爬梯。"""
    s = scale
    ox, oy = _r(*origin)
    D = p["D"] * 1000.0
    z = _zones(p)
    cx = ox + D / 2.0
    y0 = oy + z["y0"]
    y_top = oy + z["y_top"]

    # 罐体（圆柱正立面 = 矩形）
    _rect(msp, ox, y0, ox + D, y_top, "设备")
    # 罐顶（椭圆示意）
    msp.add_ellipse(_r(cx, y_top), major_axis=(D / 2.0, 0),
                    ratio=0.18, dxfattribs={"layer": "设备"})

    # 进水管（下部一侧，水平伸入）
    idn = p["inlet_dn"]
    iy = y0 + (z["y_sludge"]) * 0.4
    _rect(msp, ox - idn * 1.5, iy - idn / 2, ox, iy + idn / 2, "设备")
    _tri(msp, (ox - idn * 1.5 - 3 * s, iy), (1, 0), s, "设备")
    _t(msp, f"进水 DN{idn:.0f}", (ox - idn * 0.75, iy - idn / 2 - 4 * s),
       2.2 * s, align=MC, layer="文字", tracker=tracker)

    # 出水管（上部另一侧）
    odn = p["outlet_dn"]
    oy_ = oy + z["y_settle"] - 300
    _rect(msp, ox + D, oy_ - odn / 2, ox + D + odn * 1.5, oy_ + odn / 2, "设备")
    _tri(msp, (ox + D + odn * 1.5 + 3 * s, oy_), (1, 0), s, "设备")
    _t(msp, f"出水 DN{odn:.0f}", (ox + D + odn * 0.75, oy_ + odn / 2 + 4 * s),
       2.2 * s, align=MC, layer="文字", tracker=tracker)

    # 沼气管（罐顶）
    bdn = p["biogas_dn"]
    _rect(msp, cx - bdn / 2, y_top, cx + bdn / 2, y_top + bdn * 2, "设备")
    _tri(msp, (cx, y_top + bdn * 2 + 3 * s), (0, 1), s, "设备")
    _t(msp, f"沼气 DN{bdn:.0f}", (cx, y_top + bdn * 2 + 6 * s), 2.2 * s,
       align=MC, layer="文字", tracker=tracker)

    # 排泥管（罐底）
    sdn = p["sludge_dn"]
    _rect(msp, cx - sdn / 2, y0 - sdn, cx + sdn / 2, y0, "设备")
    _t(msp, f"排泥 DN{sdn:.0f}", (cx + sdn, y0 - sdn / 2), 2.0 * s,
       align=ML, layer="文字", tracker=tracker)

    # 爬梯（罐体一侧竖线 + 横档）
    lx = ox + D + 800
    _ln(msp, (lx, y0), (lx, y_top), "细实线")
    n_rung = int((y_top - y0) / 300)
    for i in range(0, n_rung + 1, 3):
        ry = y0 + (y_top - y0) * i / n_rung
        _ln(msp, (lx, ry), (lx - 250, ry), "细实线")
    _t(msp, "爬梯", (lx, y_top + 2 * s), 2.0 * s, align=MC, layer="文字", tracker=tracker)

    if label:
        _t(msp, label, (cx, y0 - 9 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (cx, y0, y_top)


# ══════════════════════════════════════════════════════════
#  2. 外形总图 — 平面（俯视）
# ══════════════════════════════════════════════════════════

def draw_uasb_plan(msp, origin, p: dict, scale: float = 100.0,
                   label: str = "平面图", tracker=None):
    """俯视：圆形罐体 + 布水点 + 出水堰(周边) + 沼气管。"""
    s = scale
    ox, oy = _r(*origin)      # origin = 罐体中心
    D = p["D"] * 1000.0
    R = D / 2.0

    # 罐体圆
    _circle(msp, (ox, oy), R, "设备")
    # 出水堰（周边内圈虚线）
    _circle(msp, (ox, oy), R - 300, "细实线")
    _t(msp, "周边出水堰", (ox, oy + R - 550), 2.0 * s, align=MC,
       layer="文字", tracker=tracker)

    # 布水点（罐内均布，同心圆环）
    n = p["n_dist_points"]
    import math as _m
    placed = 0
    ring = 0
    while placed < n:
        ring += 1
        rr = R * 0.75 * ring / max(1, (n // 6) + 1)
        cnt = 6 * ring
        for k in range(cnt):
            if placed >= n:
                break
            ang = 2 * _m.pi * k / cnt + ring * 0.3
            px = ox + rr * _m.cos(ang)
            py = oy + rr * _m.sin(ang)
            _circle(msp, (px, py), 90, "细实线")
            placed += 1
    # 中心布水点
    _circle(msp, (ox, oy), 90, "细实线")

    # 沼气管（中心）
    _circle(msp, (ox, oy), p["biogas_dn"] / 2.0, "设备")
    # 进水管（一侧）
    idn = p["inlet_dn"]
    _rect(msp, ox - R - idn * 1.5, oy - idn / 2, ox - R, oy + idn / 2, "设备")
    _t(msp, "进水", (ox - R - idn * 0.75, oy + idn), 2.0 * s, align=MC,
       layer="文字", tracker=tracker)

    if label:
        _t(msp, label, (ox, oy + R + 6 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (ox + R, oy)


# ══════════════════════════════════════════════════════════
#  3. 纵剖面图
# ══════════════════════════════════════════════════════════

def draw_uasb_section(msp, origin, p: dict, scale: float = 100.0,
                      label: str = "1-1 剖面图", tracker=None):
    """纵剖面：布水区/污泥床/悬浮层/三相分离器/沉淀区/出水堰/沼气室。"""
    s = scale
    ox, oy = _r(*origin)
    D = p["D"] * 1000.0
    z = _zones(p)
    cx = ox + D / 2.0
    y0 = oy + z["y0"]

    # 罐体外壳
    _rect(msp, ox, y0, ox + D, oy + z["y_top"], "设备")

    # 分区横线 + 标注
    def _zone(y, name):
        _ln(msp, (ox, y), (ox + D, y), "细实线", linetype="DASHED")
        _t(msp, name, (ox - 3 * s, y), 2.0 * s, align=MR, layer="文字", tracker=tracker)

    _zone(oy + z["y_sludge"], "污泥床")
    _zone(oy + z["y_react"], "悬浮层")
    _zone(oy + z["y_tp"], "三相分离器")
    _zone(oy + z["y_settle"], "沉淀区")

    # 污泥床阴影（底部密点）
    for i in range(1, 12):
        yy = y0 + z["y_sludge"] * i / 12.0
        _ln(msp, (ox + 100, yy), (ox + D - 100, yy), "细实线")

    # 三相分离器（集气罩三角，剖面）
    tp_base = oy + z["y_react"]
    n_hood = max(2, int(D / 1500))
    hw = D / n_hood
    for i in range(n_hood):
        hx = ox + i * hw
        apex_y = tp_base + p["H_three_phase"] * 1000.0 * 0.7
        _ln(msp, (hx, tp_base), (hx + hw / 2, apex_y), "设备")
        _ln(msp, (hx + hw / 2, apex_y), (hx + hw, tp_base), "设备")

    # 布水管（底部进水分配）
    _ln(msp, (ox - 500, y0 + 300), (ox + D + 500, y0 + 300), "设备")
    for i in range(1, int(D / 800) + 1):
        bx = ox + i * 800
        if bx < ox + D:
            _ln(msp, (bx, y0 + 300), (bx, y0 + 600), "细实线")
    _t(msp, "布水系统", (cx, y0 + 900), 2.0 * s, align=MC, layer="文字", tracker=tracker)

    # 出水堰（顶部周边三角）
    wy = oy + z["y_settle"]
    for i in range(int(D / 400)):
        wx = ox + 200 + i * 400
        if wx < ox + D - 200:
            _tri(msp, (wx, wy), (0, -1), s * 0.7, "设备")
    _t(msp, "出水堰", (cx, wy + 300), 2.0 * s, align=MC, layer="文字", tracker=tracker)

    # 沼气管（顶）
    bdn = p["biogas_dn"]
    _rect(msp, cx - bdn / 2, oy + z["y_top"], cx + bdn / 2, oy + z["y_top"] + bdn * 2, "设备")

    # 排泥管（底）
    sdn = p["sludge_dn"]
    _rect(msp, cx - sdn / 2, y0 - sdn, cx + sdn / 2, y0, "设备")

    if label:
        _t(msp, label, (cx, y0 - 9 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (cx, y0, oy + z["y_top"])


# ══════════════════════════════════════════════════════════
#  4. 三相分离器详图
# ══════════════════════════════════════════════════════════

def draw_uasb_three_phase(msp, origin, p: dict, scale: float = 100.0,
                          label: str = "三相分离器详图", tracker=None):
    """三相分离器：集气罩(倾角)+沉淀斜板+气室+三相流向。"""
    s = scale
    ox, oy = _r(*origin)
    ang = p.get("ts_angle", 55.0)
    hood_w = 1500.0
    hood_h = hood_w * 0.5 * math.tan(math.radians(ang))
    n = 3
    gap = 500.0

    for i in range(n):
        hx = ox + i * (hood_w + gap)
        # 集气罩（倒V）
        _ln(msp, (hx, oy), (hx + hood_w / 2, oy + hood_h), "设备")
        _ln(msp, (hx + hood_w / 2, oy + hood_h), (hx + hood_w, oy), "设备")
        # 气流箭头（向上入气室）
        _tri(msp, (hx + hood_w / 2, oy + hood_h + 4 * s), (0, 1), s, "设备")
        # 沉淀斜板（上方）
        _ln(msp, (hx + 100, oy + hood_h + 600), (hx + hood_w - 100, oy + hood_h + 1100), "细实线")
        # 污泥下滑箭头（沿罩面）
        _tri(msp, (hx + hood_w * 0.2, oy + hood_h * 0.35), (-0.5, -1), s * 0.7, "设备")
        # 水流上箭头（罩间）
        if i < n - 1:
            _tri(msp, (hx + hood_w + gap / 2, oy + hood_h * 0.8), (0, 1), s * 0.8, "设备")

    # 集气室（顶部横管）
    total_w = n * hood_w + (n - 1) * gap
    _rect(msp, ox, oy + hood_h + 1300, ox + total_w, oy + hood_h + 1300 + 400, "设备")
    _t(msp, "集气室→沼气", (ox + total_w / 2, oy + hood_h + 1500), 2.2 * s,
       align=MC, layer="文字", tracker=tracker)

    _t(msp, f"集气罩倾角{ang:.0f}°  缝隙流速按上升流速{p['upflow_v']}m/h设计",
       (ox + total_w / 2, oy - 5 * s), 2.3 * s, align=MC, layer="文字", tracker=tracker)

    if label:
        _t(msp, label, (ox + total_w / 2, oy - 11 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (ox + total_w, oy)


# ══════════════════════════════════════════════════════════
#  5. 布水系统图
# ══════════════════════════════════════════════════════════

def draw_uasb_distributor(msp, origin, p: dict, scale: float = 100.0,
                          label: str = "布水系统图", tracker=None):
    """布水系统：进水主管 + 环状分配 + 布水点(服务面积校核)。"""
    s = scale
    ox, oy = _r(*origin)      # origin = 罐体中心
    D = p["D"] * 1000.0
    R = D / 2.0

    # 罐体圆
    _circle(msp, (ox, oy), R, "设备")

    # 进水主管（穿中心）
    idn = p["inlet_dn"]
    _ln(msp, (ox - R - idn * 1.5, oy), (ox + R, oy), "设备")
    _t(msp, f"进水主管 DN{idn:.0f}", (ox, oy + 4 * s), 2.0 * s, align=MC,
       layer="文字", tracker=tracker)

    # 环状分配管（两圈）
    for rr in (R * 0.35, R * 0.7):
        _circle(msp, (ox, oy), rr, "细实线")

    # 布水点（放射均布）
    n = p["n_dist_points"]
    placed = 0
    ring = 0
    while placed < n:
        ring += 1
        rr = R * 0.7 * ring / max(1, (n // 6) + 1)
        cnt = 6 * ring
        for k in range(cnt):
            if placed >= n:
                break
            a = 2 * math.pi * k / cnt + ring * 0.3
            px, py = ox + rr * math.cos(a), oy + rr * math.sin(a)
            _circle(msp, (px, py), 100, "设备")
            _ln(msp, (ox, oy), (px, py), "细实线", linetype="DASHED")
            placed += 1

    _t(msp, f"布水点 {n} 个，每点服务 {p['serve_area']} m²，"
            f"反应器面积 {p['A_reactor']} m²",
       (ox, oy - R - 5 * s), 2.3 * s, align=MC, layer="文字", tracker=tracker)

    if label:
        _t(msp, label, (ox, oy + R + 6 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (ox + R, oy)


# ══════════════════════════════════════════════════════════
#  6. 出水堰及排泥详图
# ══════════════════════════════════════════════════════════

def draw_uasb_outlet_weir(msp, origin, p: dict, scale: float = 100.0,
                          label: str = "出水堰及排泥详图", tracker=None):
    """出水堰：三角堰板 + 集水槽 + 出水管（堰负荷校核）。"""
    s = scale
    ox, oy = _r(*origin)
    D = p["D"] * 1000.0
    R = D / 2.0

    # 罐壁（顶部一段）
    _ln(msp, (ox, oy), (ox, oy - 2000), "设备")
    _ln(msp, (ox + D, oy), (ox + D, oy - 2000), "设备")

    # 三角堰板（周边，剖面示意）
    n_tooth = int(D / 300)
    for i in range(n_tooth):
        wx = ox + 150 + i * 300
        if wx < ox + D - 150:
            _tri(msp, (wx, oy), (0, -1), s * 0.6, "设备")
    _t(msp, "三角堰板（90°齿形）", (ox + D / 2, oy + 3 * s), 2.0 * s,
       align=MC, layer="文字", tracker=tracker)

    # 集水槽（堰下环形槽）
    _rect(msp, ox + 200, oy - 800, ox + D - 200, oy - 400, "细实线")
    _t(msp, "环形集水槽", (ox + D / 2, oy - 600), 2.0 * s, align=MC,
       layer="文字", tracker=tracker)

    # 出水管
    odn = p["outlet_dn"]
    _rect(msp, ox + D, oy - 900, ox + D + odn * 1.5, oy - 900 + odn, "设备")
    _t(msp, f"出水 DN{odn:.0f}", (ox + D + odn * 0.75, oy - 900 + odn + 3 * s),
       2.0 * s, align=MC, layer="文字", tracker=tracker)

    # 堰负荷校核标注
    _t(msp, f"堰负荷 {p['weir_load']} L/s·m（≤1.7），所需堰长 {p['weir_len']} m",
       (ox + D / 2, oy - 1400), 2.3 * s, align=MC, layer="文字", tracker=tracker)

    if label:
        _t(msp, label, (ox + D / 2, oy - 2400), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (ox + D, oy - 2400)
