"""机械制造制图 v1.0（GB/T 4459.2 / 4459.3 / 4459.4 / 4459.5）。

齿轮、轴系、轴承、连接件、弹簧、工艺结构——核心机械零件简图。
纯 ezdxf，零新依赖。所有参数由 Agent 搜索后传入。

## 6 大类 15 函数：
  传动件: spur_gear / helical_gear / bevel_gear_pair / worm_gear_pair
  轴系:   stepped_shaft / spline_shaft
  轴承:   rolling_bearing
  连接件: key / thread / bolt_connection
  弹簧:   compression_spring / extension_spring
  附件:   circlip / oil_seal / center_hole
"""
from __future__ import annotations

import math
from typing import List, Optional, Tuple

from ezdxf.enums import TextEntityAlignment

from ..utils import _r, _tri


def _add_params_text(msp, items, ox, oy, s):
    """在指定位置添加参数文本。"""
    y = oy
    for k, v in (items or {}).items():
        t = msp.add_text(f"{k}: {v}", dxfattribs={
            "layer": "文字", "height": 2.0 * s, "style": "HZ"})
        t.set_placement((ox, y), align=TextEntityAlignment.TOP_LEFT)
        y -= 2.5 * s


def _center_line(msp, cx, cy, length, direction="h", s=100.0):
    """画中心线（点画线）。"""
    hl = length / 2
    if direction == "h":
        msp.add_line((cx - hl, cy), (cx + hl, cy),
                     dxfattribs={"layer": "中心线", "linetype": "CENTER"})
    else:
        msp.add_line((cx, cy - hl), (cx, cy + hl),
                     dxfattribs={"layer": "中心线", "linetype": "CENTER"})


# ═══════════════════════════════════════════════
# 齿轮 — GB/T 4459.2
# ═══════════════════════════════════════════════

def draw_spur_gear(msp, origin, m=5.0, z=20, b=25.0,
                   scale=100.0, label="", params=None,
                   layer="粗实线", tracker=None):
    """直齿圆柱齿轮简化画法（侧视图：分度圆+齿顶圆+齿根圆+键槽）。"""
    s = scale
    ox, oy = _r(*origin)
    d = m * z
    da = d + 2 * m
    df = d - 2.5 * m
    if params:
        da = params.get("da", da); df = params.get("df", df); d = params.get("d", d)

    r, ra, rf = d / 2 * s, da / 2 * s, df / 2 * s
    cx, cy = ox + ra + 5 * s, oy

    _center_line(msp, cx, cy, da * s + 4 * s, "h", s)
    _center_line(msp, cx, cy, da * s + 4 * s, "v", s)
    msp.add_circle((cx, cy), ra, dxfattribs={"layer": layer})
    msp.add_circle((cx, cy), r, dxfattribs={"layer": "中心线", "linetype": "CENTER"})
    # 齿根圆（细实线 3/4 圈）
    pts_f = [(cx + rf * math.cos(math.radians(a)),
              cy + rf * math.sin(math.radians(a))) for a in range(0, 271, 5)]
    msp.add_lwpolyline(pts_f, close=False, dxfattribs={"layer": "细实线"})
    # 键槽
    kw, kh = 0.06 * da * s, 0.04 * da * s
    msp.add_lwpolyline([
        (cx - kw, cy + ra - kh), (cx + kw, cy + ra - kh),
        (cx + kw, cy + ra), (cx - kw, cy + ra),
    ], close=True, dxfattribs={"layer": layer})

    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": 3 * s, "style": "HZ"})
        t.set_placement((cx, cy - ra - 4 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)
    _add_params_text(msp, params or {"m": str(m), "z": str(z)},
                     ox, oy + 7 * s, s)
    return (cx + ra + 5 * s, cy - ra - 10 * s)


def draw_helical_gear(msp, origin, m=5.0, z=20, beta=15.0,
                      scale=100.0, label="", params=None,
                      layer="粗实线", tracker=None):
    """斜齿圆柱齿轮简化画法（侧视图+三条螺旋角示意线）。beta=螺旋角(°)。"""
    s = scale
    ox, oy = _r(*origin)
    d = m * z; da = d + 2 * m
    if params: da = params.get("da", da); d = params.get("d", d)
    r, ra = d / 2 * s, da / 2 * s
    cx, cy = ox + ra + 5 * s, oy

    _center_line(msp, cx, cy, da * s + 4 * s, "h", s)
    _center_line(msp, cx, cy, da * s + 4 * s, "v", s)
    msp.add_circle((cx, cy), ra, dxfattribs={"layer": layer})
    msp.add_circle((cx, cy), r, dxfattribs={"layer": "中心线", "linetype": "CENTER"})
    # 三条螺旋斜线
    hl = ra * 0.6
    offset_x = math.sin(math.radians(beta)) * hl
    for sign in [-1, 0, 1]:
        x0 = cx + sign * r * 0.4
        msp.add_line((x0, cy - hl), (x0 + offset_x, cy + hl),
                     dxfattribs={"layer": "细实线"})

    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": 3 * s, "style": "HZ"})
        t.set_placement((cx, cy - ra - 4 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)
    return (cx + ra + 5 * s, cy - ra - 8 * s)


def draw_bevel_gear_pair(msp, origin, m=5.0, z1=20, z2=30,
                         scale=100.0, label="", params=None,
                         layer="粗实线", tracker=None):
    """锥齿轮副简化画法（正交轴）。"""
    s = scale
    ox, oy = _r(*origin)
    r1 = m * z1 / 2 * s; r2 = m * z2 / 2 * s
    cx1, cy1 = ox, oy; cx2, cy2 = ox + r1, oy + r1

    pts1 = [(cx1, cy1), (cx1 + r1, cy1 + r1 * 0.6), (cx1 + r1, cy1 - r1 * 0.6)]
    msp.add_lwpolyline(pts1 + [pts1[0]], close=True, dxfattribs={"layer": layer})
    pts2 = [(cx2, cy2), (cx2 + r2 * 0.6, cy2 - r2), (cx2 - r2 * 0.6, cy2 - r2)]
    msp.add_lwpolyline(pts2 + [pts2[0]], close=True, dxfattribs={"layer": layer})
    msp.add_line((cx1 - 2 * s, cy1), (cx2 + r2 * 0.8, cy2 - r2 * 0.5),
                 dxfattribs={"layer": "中心线", "linetype": "CENTER"})
    msp.add_line((cx2, cy2 + 2 * s), (cx2, cy2 - r2 - 3 * s),
                 dxfattribs={"layer": "中心线", "linetype": "CENTER"})

    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": 3 * s, "style": "HZ"})
        t.set_placement((cx2, cy2 - r2 - 6 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)
    return (cx2 + r2 + 5 * s, cy2 - r2 - 10 * s)


def draw_worm_gear_pair(msp, origin, m=4.0, z1=2, z2=30, q=10.0,
                        scale=100.0, label="", params=None,
                        layer="粗实线", tracker=None):
    """蜗轮蜗杆副简化画法。q=直径系数。"""
    s = scale
    ox, oy = _r(*origin)
    dw = m * q * s; dg = m * z2 * s; rw, rg = dw / 2, dg / 2
    cx_w, cy_w = ox + rg + rw + 5 * s, oy

    msp.add_lwpolyline([
        (cx_w - rw, cy_w - rw * 0.5), (cx_w + rw, cy_w - rw * 0.5),
        (cx_w + rw, cy_w + rw * 0.5), (cx_w - rw, cy_w + rw * 0.5),
    ], close=True, dxfattribs={"layer": layer})
    cx_g, cy_g = cx_w - rw, cy_w - rg - 2 * s
    msp.add_circle((cx_g, cy_g), rg, dxfattribs={"layer": layer})
    msp.add_arc((cx_g, cy_g), rg + rw * 0.3, 150, 210,
                dxfattribs={"layer": "细实线"})
    _center_line(msp, cx_w, cy_w, dw + 8 * s, "h", s)
    _center_line(msp, cx_g, cy_g, dg + 10 * s, "v", s)

    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": 3 * s, "style": "HZ"})
        t.set_placement((cx_g, cy_g - rg - 5 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)
    return (cx_w + rw + 5 * s, cy_g - rg - 10 * s)


# ═══════════════════════════════════════════════
# 轴 — GB/T 4459.3
# ═══════════════════════════════════════════════

def draw_stepped_shaft(msp, origin, diameters=None, lengths=None,
                       scale=100.0, label="", params=None,
                       layer="粗实线", tracker=None):
    """阶梯轴（多段圆柱 + 倒角/退刀槽 + 中心孔 + 键槽）。
    diameters=[40,55,40,30](mm), lengths=[60,35,45,25](mm)。"""
    s = scale
    ox, oy = _r(*origin)
    if diameters is None: diameters = [40, 55, 40, 30]
    if lengths is None: lengths = [60, 35, 45, 25]

    x = ox; y_mid = oy; half_w_max = max(diameters) / 2 * s
    pts_upper = [(x, y_mid)]
    for dia, length in zip(diameters, lengths):
        hw = dia / 2 * s
        pts_upper.append((x, y_mid + hw))
        x += length * s
        pts_upper.append((x, y_mid + hw))
    pts_upper.append((x, y_mid))
    pts_lower = [(px, 2 * y_mid - py) for px, py in reversed(pts_upper)]
    msp.add_lwpolyline(pts_upper + pts_lower[1:-1], close=True,
                       dxfattribs={"layer": layer})
    _center_line(msp, ox - 3 * s, y_mid, x - ox + 6 * s, "h", s)
    # 键槽
    x_kc = ox + lengths[0] * s + lengths[1] * s * 0.5
    hw2 = diameters[1] / 2 * s; kw = lengths[1] * s * 0.3; kh = hw2 * 0.15
    bh = hw2 + kh * 0.5
    msp.add_lwpolyline([
        (x_kc - kw, bh - kh), (x_kc + kw, bh - kh),
        (x_kc + kw, bh + kh), (x_kc - kw, bh + kh),
    ], close=True, dxfattribs={"layer": "细实线"})
    # 中心孔符号
    ch_r = 1.5 * s
    msp.add_lwpolyline([(ox, oy - ch_r), (ox - ch_r * 1.5, oy), (ox, oy + ch_r)],
                       close=False, dxfattribs={"layer": "细实线"})

    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": 3 * s, "style": "HZ"})
        t.set_placement((ox + (x - ox) / 2, y_mid - half_w_max - 5 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)
    return (x + 5 * s, y_mid - half_w_max - 12 * s)


def draw_spline_shaft(msp, origin, d=40.0, z=6, L=80.0,
                      scale=100.0, label="", params=None,
                      layer="粗实线", tracker=None):
    """花键轴（矩形花键简化画法：外径+内径+截面齿形）。"""
    s = scale
    ox, oy = _r(*origin)
    R = d / 2 * s; r_inner = R * 0.85; length = L * s

    msp.add_lwpolyline([
        (ox, oy - R), (ox + length, oy - R),
        (ox + length, oy + R), (ox, oy + R),
    ], close=True, dxfattribs={"layer": layer})
    msp.add_line((ox, oy - r_inner), (ox + length, oy - r_inner),
                 dxfattribs={"layer": "细实线"})
    msp.add_line((ox, oy + r_inner), (ox + length, oy + r_inner),
                 dxfattribs={"layer": "细实线"})
    _center_line(msp, ox - 3 * s, oy, length + 6 * s, "h", s)
    # 截面圆
    cx_s = ox + length + R + 8 * s
    msp.add_circle((cx_s, oy), R, dxfattribs={"layer": layer})
    msp.add_circle((cx_s, oy), r_inner, dxfattribs={"layer": "细实线"})
    _center_line(msp, cx_s, oy, d * s + 4 * s, "h", s)
    _center_line(msp, cx_s, oy, d * s + 4 * s, "v", s)
    for i in range(z):
        a = 2 * math.pi * i / z
        msp.add_line((cx_s + r_inner * math.cos(a), oy + r_inner * math.sin(a)),
                     (cx_s + R * math.cos(a), oy + R * math.sin(a)),
                     dxfattribs={"layer": "细实线"})

    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": 3 * s, "style": "HZ"})
        t.set_placement((cx_s, oy - R - 5 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)
    return (cx_s + R + 3 * s, oy - R - 10 * s)


# ═══════════════════════════════════════════════
# 滚动轴承
# ═══════════════════════════════════════════════

def draw_rolling_bearing(msp, origin, b_type="deep_groove",
                         d=40.0, D=80.0, B=18.0,
                         scale=100.0, label="", params=None,
                         layer="粗实线", tracker=None):
    """滚动轴承简化画法（深沟球/角接触/圆锥滚子）。d=内径 D=外径 B=宽度(mm)。"""
    s = scale
    ox, oy = _r(*origin)
    R_out = D / 2 * s; R_in = d / 2 * s; w = B * s
    cx, cy = ox + R_out + 5 * s, oy
    # 外圈
    msp.add_lwpolyline([
        (cx - w / 2, cy - R_out), (cx + w / 2, cy - R_out),
        (cx + w / 2, cy + R_out), (cx - w / 2, cy + R_out),
    ], close=True, dxfattribs={"layer": layer})
    # 内圈
    msp.add_lwpolyline([
        (cx - w / 2, cy - R_in), (cx + w / 2, cy - R_in),
        (cx + w / 2, cy + R_in), (cx - w / 2, cy + R_in),
    ], close=True, dxfattribs={"layer": layer})
    # 滚动体
    r_ball = (R_out - R_in) * 0.25; r_mid = (R_out + R_in) / 2
    for i in range(6):
        by = cy + r_mid * math.sin(2 * math.pi * i / 6 - math.pi / 2)
        msp.add_circle((cx, by), r_ball, dxfattribs={"layer": "细实线"})
    _center_line(msp, cx, cy, D * s + 5 * s, "h", s)

    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": 3 * s, "style": "HZ"})
        t.set_placement((cx, cy - R_out - 5 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)
    return (cx + w / 2 + 3 * s, cy - R_out - 10 * s)


# ═══════════════════════════════════════════════
# 连接件
# ═══════════════════════════════════════════════

def draw_key(msp, origin, k_type="A", b=10.0, h=8.0, L=40.0,
             scale=100.0, label="", params=None,
             layer="粗实线", tracker=None):
    """键（平键/半圆键）简图。k_type: A(圆头)/B(方头)/woodruff(半圆)。"""
    s = scale
    ox, oy = _r(*origin)
    bw, bh, bl = b * s, h * s, L * s

    if k_type == "woodruff":
        msp.add_lwpolyline([(ox, oy), (ox + bl, oy),
                            (ox + bl, oy + bh), (ox, oy + bh)],
                           close=True, dxfattribs={"layer": layer})
        msp.add_arc((ox + bl / 2, oy), bw * 0.8, 180, 0,
                    dxfattribs={"layer": "细实线"})
    else:
        shape = [(ox, oy)]
        if k_type == "A":
            shape += [(ox + bw * 0.2, oy - bh * 0.3)]
        shape += [(ox + bw * 0.2, oy), (ox + bl - bw * 0.2, oy)]
        if k_type in ("A", "C"):
            shape.append((ox + bl, oy - bh * 0.3))
        shape += [(ox + bl - bw * 0.2, oy + bh), (ox + bw * 0.2, oy + bh),
                  (ox + bw * 0.2, oy + bh), shape[0]]
        msp.add_lwpolyline(shape, close=True, dxfattribs={"layer": layer})

    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": 2.5 * s, "style": "HZ"})
        t.set_placement((ox + bl / 2, oy - bh - 3 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)
    return (ox + bl + 3 * s, oy - bh - 5 * s)


def draw_thread(msp, origin, t_type="external", d=20.0, L=40.0,
                pitch=2.5, scale=100.0, label="", params=None,
                layer="粗实线", tracker=None):
    """螺纹简化画法（GB/T 4459.1）。external(外螺纹)/internal(内螺纹)。"""
    s = scale
    ox, oy = _r(*origin)
    r = d / 2 * s; r_inner = (d - 1.0825 * pitch) / 2 * s; length = L * s

    if t_type == "external":
        msp.add_lwpolyline([(ox, oy - r), (ox + length, oy - r),
                            (ox + length, oy + r), (ox, oy + r)],
                           close=True, dxfattribs={"layer": layer})
        margin = length * 0.05
        for sign in [-1, 1]:
            msp.add_line((ox + margin, oy + sign * r_inner),
                         (ox + length - margin, oy + sign * r_inner),
                         dxfattribs={"layer": "细实线"})
    else:
        msp.add_lwpolyline([(ox, oy - r), (ox + length, oy - r),
                            (ox + length, oy + r), (ox, oy + r)],
                           close=True, dxfattribs={"layer": "细实线"})
        margin = length * 0.05
        for sign in [-1, 1]:
            msp.add_line((ox + margin, oy + sign * r_inner),
                         (ox + length - margin, oy + sign * r_inner),
                         dxfattribs={"layer": layer})
    _center_line(msp, ox - 3 * s, oy, length + 6 * s, "h", s)

    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": 2.5 * s, "style": "HZ"})
        t.set_placement((ox + length / 2, oy - r - 4 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)
    return (ox + length + 5 * s, oy - r - 8 * s)


def draw_bolt_connection(msp, origin, d=12.0, L=50.0, t1=15.0, t2=15.0,
                         scale=100.0, label="", params=None,
                         layer="粗实线", tracker=None):
    """螺栓连接装配图简化画法（GB/T 4459.1）。"""
    s = scale
    ox, oy = _r(*origin)
    r = d / 2 * s; r_head = r * 1.6; h_head = d * 0.7 * s
    h_nut = d * 0.8 * s; r_nut = r_head
    t1s, t2s = t1 * s, t2 * s
    thread_len = (L - t1 - t2) * s

    _center_line(msp, ox - 3 * s, oy, h_head + t1s + t2s + h_nut + thread_len + 10 * s, "v", s)
    # 被连接件
    for i, (thk, top_y) in enumerate([(t1s, h_head), (t2s, h_head + t1s)]):
        msp.add_lwpolyline([
            (ox - r * 2, oy + top_y), (ox + r * 2, oy + top_y),
            (ox + r * 2, oy + top_y + thk), (ox - r * 2, oy + top_y + thk),
        ], close=True, dxfattribs={"layer": "细实线"})
    # 螺栓头
    msp.add_lwpolyline([(ox - r_head, oy), (ox + r_head, oy),
                        (ox + r_head, oy + h_head), (ox - r_head, oy + h_head)],
                       close=True, dxfattribs={"layer": layer})
    # 螺杆
    top_bolt = oy + h_head + t1s + t2s + thread_len
    msp.add_lwpolyline([
        (ox - r, oy + h_head + t1s + t2s), (ox + r, oy + h_head + t1s + t2s),
        (ox + r, top_bolt), (ox - r, top_bolt),
    ], close=True, dxfattribs={"layer": layer})
    # 垫圈
    ws = r * 1.4; hs = d * 0.15 * s
    msp.add_lwpolyline([(ox - ws, top_bolt), (ox + ws, top_bolt),
                        (ox + ws, top_bolt - hs), (ox - ws, top_bolt - hs)],
                       close=True, dxfattribs={"layer": "细实线"})
    # 螺母
    msp.add_lwpolyline([
        (ox - r_nut, top_bolt), (ox + r_nut, top_bolt),
        (ox + r_nut, top_bolt + h_nut), (ox - r_nut, top_bolt + h_nut),
    ], close=True, dxfattribs={"layer": layer})

    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": 3 * s, "style": "HZ"})
        t.set_placement((ox, oy - 5 * s), align=TextEntityAlignment.MIDDLE_CENTER)
    return (ox + r_nut + 5 * s, oy - 8 * s)


# ═══════════════════════════════════════════════
# 弹簧 — GB/T 4459.4
# ═══════════════════════════════════════════════

def draw_compression_spring(msp, origin, d=20.0, D=60.0, n=6,
                            free_length=80.0, scale=100.0,
                            label="", params=None,
                            layer="粗实线", tracker=None):
    """压缩弹簧（特征画法）。d=簧丝直径 D=中径 n=圈数 free_length=自由高度(mm)。"""
    s = scale
    ox, oy = _r(*origin)
    half_D = D / 2 * s; half_d = d / 2 * s; h = free_length * s

    msp.add_lwpolyline([(ox, oy - half_D), (ox + h * 0.5, oy - half_D),
                        (ox + h * 0.5, oy + half_D), (ox, oy + half_D)],
                       close=True, dxfattribs={"layer": "细实线"})
    msp.add_lwpolyline([(ox + h * 0.5, oy - half_D), (ox + h, oy - half_D),
                        (ox + h, oy + half_D), (ox + h * 0.5, oy + half_D)],
                       close=True, dxfattribs={"layer": layer})
    for x_pos in [ox + half_d, ox + h * 0.25, ox + h * 0.5, ox + h * 0.75, ox + h - half_d]:
        for sign in [-1, 1]:
            msp.add_circle((x_pos, oy + sign * half_D), half_d,
                           dxfattribs={"layer": layer})
    for sign in [-1, 1]:
        msp.add_line((ox + half_d, oy + sign * half_D),
                     (ox + h - half_d, oy + sign * half_D),
                     dxfattribs={"layer": layer})
    _center_line(msp, ox - 3 * s, oy, h + 6 * s, "h", s)

    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": 3 * s, "style": "HZ"})
        t.set_placement((ox + h / 2, oy - half_D - 5 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)
    return (ox + h + 5 * s, oy - half_D - 10 * s)


def draw_extension_spring(msp, origin, d=15.0, D=40.0, n=10,
                          free_length=100.0, scale=100.0,
                          label="", params=None,
                          layer="粗实线", tracker=None):
    """拉伸弹簧（特征画法：密圈+两端拉钩）。"""
    s = scale
    ox, oy = _r(*origin)
    half_D = D / 2 * s; half_d = d / 2 * s; h = free_length * s
    hook_h = half_D * 0.7

    msp.add_lwpolyline([(ox, oy - half_D), (ox + h, oy - half_D),
                        (ox + h, oy + half_D), (ox, oy + half_D)],
                       close=True, dxfattribs={"layer": "细实线"})
    n_show = min(n, 10); spacing = h / (n_show + 1)
    for i in range(1, n_show + 1):
        x_pos = ox + i * spacing
        for sign in [-1, 1]:
            msp.add_circle((x_pos, oy + sign * half_D), half_d,
                           dxfattribs={"layer": layer})
    for side in [-1, 1]:
        x_hook = ox if side == -1 else ox + h
        pts_hk = [(x_hook, oy + side * half_D),
                  (x_hook - side * hook_h * 0.3, oy + side * (half_D + hook_h)),
                  (x_hook + side * hook_h * 0.2, oy + side * (half_D + hook_h * 0.6)),
                  (x_hook - side * hook_h * 0.2, oy + side * (half_D + hook_h * 0.2))]
        msp.add_lwpolyline(pts_hk, close=True, dxfattribs={"layer": layer})
    _center_line(msp, ox - 3 * s, oy, h + 6 * s, "h", s)

    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": 3 * s, "style": "HZ"})
        t.set_placement((ox + h / 2, oy - half_D - 8 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)
    return (ox + h + 5 * s, oy - half_D - 12 * s)


# ═══════════════════════════════════════════════
# 附件
# ═══════════════════════════════════════════════

def draw_circlip(msp, origin, d=30.0, c_type="external",
                 scale=100.0, label="", params=None,
                 layer="粗实线", tracker=None):
    """弹性挡圈简化画法。external(轴用)/internal(孔用)。"""
    s = scale
    ox, oy = _r(*origin)
    R = d / 2 * s; r_inner = R * 0.85
    cx, cy = ox + R + 2 * s, oy

    if c_type == "external":
        pts = [(cx + R * math.cos(math.radians(a)),
                cy + R * math.sin(math.radians(a))) for a in range(20, 341, 3)]
        msp.add_lwpolyline(pts, close=False, dxfattribs={"layer": layer})
        r_eye = R * 0.08
        for sign in [-1, 1]:
            msp.add_circle((cx + R * math.cos(math.radians(10 * sign)),
                            cy + R * math.sin(math.radians(10 * sign))),
                           r_eye, dxfattribs={"layer": layer})
    else:
        pts = [(cx + r_inner * math.cos(math.radians(a)),
                cy + r_inner * math.sin(math.radians(a))) for a in range(20, 341, 3)]
        msp.add_lwpolyline(pts, close=False, dxfattribs={"layer": layer})

    _center_line(msp, cx, cy, d * s + 5 * s, "h", s)
    _center_line(msp, cx, cy, d * s + 5 * s, "v", s)

    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": 2.5 * s, "style": "HZ"})
        t.set_placement((cx, cy - R - 4 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)
    return (cx + R + 3 * s, cy - R - 6 * s)


def draw_oil_seal(msp, origin, d=40.0, D=62.0, B=8.0,
                  scale=100.0, label="", params=None,
                  layer="粗实线", tracker=None):
    """骨架油封简化画法（半剖）。d=内径 D=外径 B=宽度(mm)。"""
    s = scale
    ox, oy = _r(*origin)
    R_out = D / 2 * s; R_in = d / 2 * s; w = B * s
    cx, cy = ox + R_out + 3 * s, oy

    msp.add_lwpolyline([
        (cx - w / 2, cy - R_out), (cx + w / 2, cy - R_out),
        (cx + w / 2, cy + R_out), (cx - w / 2, cy + R_out),
    ], close=True, dxfattribs={"layer": layer})
    lip_w = w * 0.4; lip_h = (R_out - R_in) * 0.6
    for sign in [-1, 1]:
        y_b = cy + sign * R_in
        msp.add_lwpolyline([(cx - lip_w / 2, y_b), (cx + lip_w / 2, y_b),
                            (cx + lip_w / 3, y_b + sign * lip_h),
                            (cx - lip_w / 3, y_b + sign * lip_h)],
                           close=True, dxfattribs={"layer": layer})
    for sign in [-1, 1]:
        msp.add_circle((cx, cy + sign * (R_in + lip_h * 0.7)),
                       w * 0.08, dxfattribs={"layer": "细实线"})
    _center_line(msp, cx, cy, D * s + 5 * s, "h", s)

    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": 2.5 * s, "style": "HZ"})
        t.set_placement((cx, cy - R_out - 4 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)
    return (cx + w / 2 + 3 * s, cy - R_out - 6 * s)


def draw_center_hole(msp, origin, h_type="A", d=4.0, D_ref=10.0,
                     scale=100.0, label="", params=None,
                     layer="粗实线", tracker=None):
    """中心孔简化画法（GB/T 145）。A(不带护锥)/B(带护锥)/C(带螺纹)/R(弧形)。"""
    s = scale
    ox, oy = _r(*origin)
    half_D = D_ref / 2 * s; half_d = d / 2 * s; depth = D_ref * 1.2 * s

    msp.add_lwpolyline([
        (ox, oy - half_D), (ox - depth, oy - half_D),
        (ox - depth, oy + half_D), (ox, oy + half_D),
    ], close=True, dxfattribs={"layer": layer})
    v_depth = depth * 0.5
    v_ao = v_depth * 0.5 * math.tan(math.radians(30))
    msp.add_lwpolyline([(ox, oy - half_d), (ox - v_depth, oy - v_ao),
                        (ox - v_depth, oy + v_ao), (ox, oy + half_d)],
                       close=False, dxfattribs={"layer": layer})
    if h_type == "B":
        cone_d = D_ref * 1.8 * s; cone_w = cone_d * 0.5
        msp.add_lwpolyline([(ox, oy - cone_d / 2), (ox + cone_w, oy - cone_d / 4),
                            (ox + cone_w, oy + cone_d / 4), (ox, oy + cone_d / 2)],
                           close=True, dxfattribs={"layer": "细实线"})
    _center_line(msp, ox - depth - 2 * s, oy, depth + 6 * s, "h", s)

    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": 2.5 * s, "style": "HZ"})
        t.set_placement((ox - depth / 2, oy - half_D - 4 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)
    cone_w = D_ref * 1.8 * s * 0.5 if h_type == "B" else 0
    return (ox + cone_w + 3 * s, oy - half_D - 6 * s)


# ═══════════════════════════════════════════════
# 凸轮 / 链轮 / 联轴器
# ═══════════════════════════════════════════════

def draw_cam_disk(msp, origin, r_base=30.0, r_lobe=45.0, n_lobes=1,
                  scale=100.0, label="", params=None,
                  layer="粗实线", tracker=None):
    """盘形凸轮简化画法（基圆+凸起段，n_lobes个凸轮面）。"""
    s=scale;ox,oy=_r(*origin)
    rb,rh,lh=r_base*s,r_lobe*s,3*s
    cx,cy=ox+rh+5*s,oy
    _center_line(msp,cx,cy,rh*2+5*s,"h",s)
    _center_line(msp,cx,cy,rh*2+5*s,"v",s)
    msp.add_circle((cx,cy),rb,dxfattribs={"layer":"中心线","linetype":"CENTER"})
    # 凸轮轮廓（简化为圆+凸起段）
    import math
    pts=[];n=48
    for i in range(n):
        ang=i*2*math.pi/n
        r=rh if ang<math.pi/3*n_lobes/n else rb
        pts.append((cx+r*math.cos(ang),cy+r*math.sin(ang)))
    pts.append(pts[0])
    msp.add_lwpolyline(pts,close=True,dxfattribs={"layer":layer})
    if label:
        t=msp.add_text(label,dxfattribs={"layer":"文字-标题","height":2.8*s,"style":"HZ"})
        t.set_placement((cx,cy-rh-4*s),align=TextEntityAlignment.MIDDLE_CENTER)
    return (ox+rh*2+10*s,oy)


def draw_chain_sprocket(msp, origin, z=16, p=12.7, scale=100.0,
                        label="", params=None, layer="粗实线", tracker=None):
    """链轮简化画法（分度圆+齿顶圆+齿根圆）。p=节距mm。"""
    s=scale;ox,oy=_r(*origin)
    import math
    d=p/math.sin(math.pi/z)*s;da=d+0.8*p*s;df=d-1.2*p*s
    cx,cy=ox+da/2+5*s,oy
    _center_line(msp,cx,cy,da+5*s,"h",s)
    _center_line(msp,cx,cy,da+5*s,"v",s)
    msp.add_circle((cx,cy),da/2,dxfattribs={"layer":layer})
    msp.add_circle((cx,cy),d/2,dxfattribs={"layer":"中心线","linetype":"CENTER"})
    msp.add_circle((cx,cy),df/2,dxfattribs={"layer":"细实线"})
    # 键槽
    kw,kh=0.06*da,0.04*da
    msp.add_lwpolyline([(cx-kw,cy+da/2-kh),(cx+kw,cy+da/2-kh),(cx+kw,cy+da/2),(cx-kw,cy+da/2)],close=True,dxfattribs={"layer":layer})
    if label:
        t=msp.add_text(label,dxfattribs={"layer":"文字-标题","height":2.5*s,"style":"HZ"})
        t.set_placement((cx,cy-da/2-4*s),align=TextEntityAlignment.MIDDLE_CENTER)
    return (ox+da+10*s,oy)


def draw_coupling(msp, origin, d=40.0, L=100.0, c_type="rigid",
                  scale=100.0, label="", params=None,
                  layer="粗实线", tracker=None):
    """联轴器简化画法（法兰式/弹性销式）。c_type: rigid/flexible。"""
    s=scale;ox,oy=_r(*origin)
    ds,ls=d*s,L*s
    r,hl=ds/2,ls/2
    cx,cy=ox+hl+5*s,oy
    _center_line(msp,cx,cy,ls+8*s,"h",s)
    # 左法兰
    msp.add_lwpolyline([(cx-hl,cy-r),(cx-hl+8*s,cy-r),(cx-hl+8*s,cy+r),(cx-hl,cy+r)],close=True,dxfattribs={"layer":layer})
    # 右法兰
    msp.add_lwpolyline([(cx+hl-8*s,cy-r),(cx+hl,cy-r),(cx+hl,cy+r),(cx+hl-8*s,cy+r)],close=True,dxfattribs={"layer":layer})
    # 中间段（弹性联轴器加橡胶标记）
    if c_type=="flexible":
        msp.add_lwpolyline([(cx-2*s,cy-r),(cx+2*s,cy-r),(cx+2*s,cy+r),(cx-2*s,cy+r)],close=True,dxfattribs={"layer":"细实线"})
        for i in range(5):
            msp.add_line((cx-2*s+i*s,cy-r),(cx-2*s+i*s,cy+r),dxfattribs={"layer":"细实线","linetype":"DASHED"})
    else:
        msp.add_lwpolyline([(cx-2*s,cy-r),(cx+2*s,cy-r),(cx+2*s,cy+r),(cx-2*s,cy+r)],close=True,dxfattribs={"layer":layer})
    if label:
        t=msp.add_text(label,dxfattribs={"layer":"文字-标题","height":2.5*s,"style":"HZ"})
        t.set_placement((cx,cy-r-4*s),align=TextEntityAlignment.MIDDLE_CENTER)
    return (cx+hl+5*s,oy+r+5*s)
