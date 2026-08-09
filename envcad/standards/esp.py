# -*- coding: utf-8 -*-
"""静电除尘器多视图制图 v1.0（GB 16297、HJ/T 75、JB/T 5910）。

卧式电除尘器成套视图：外形总图(正立面/平面)、纵剖面、阴阳极系统、
振打清灰、灰斗及输灰装置。所有几何参数以 dict 传入（默认取
knowledge.esp_data.ESP_DEFAULTS）——本模块只负责"画"，不负责"算"。

坐标单位 mm，scale=出图比例倒数(1:100 → 100)。图层沿用包内中文命名。
"""
from __future__ import annotations

import math

from ezdxf.enums import TextEntityAlignment

from ..utils import _r, _tri
from .annotate import _t
from ..knowledge.esp_data import ESP_DEFAULTS

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
    d = dict(ESP_DEFAULTS)
    d.update(p or {})
    return d


def _lengths(p):
    """沿气流方向分段：进口喇叭 | 电场区 | 出口喇叭。"""
    in_L = p["inlet_horn_L"]
    field_L = p["n_field"] * p["field_L"]
    out_L = p["outlet_horn_L"]
    return in_L, field_L, out_L


def _vert(p):
    """竖向关键标高（相对 origin 底部 oy 的偏移）。"""
    leg = p["leg_H"]
    hop = p["hopper_H"]
    body = p["box_H"]
    roof = p["roof_H"]
    y0 = 0.0                # 支腿底（地面）
    y1 = y0 + leg           # 灰斗下口
    y2 = y1 + hop           # 箱体底（灰斗上口）
    y3 = y2 + body          # 电场顶
    y4 = y3 + roof          # 吊挂室顶
    return dict(y0=y0, y1=y1, y2=y2, y3=y3, y4=y4)


# ══════════════════════════════════════════════════════════
#  1. 外形总图 — 正立面
# ══════════════════════════════════════════════════════════

def draw_esp_elevation(msp, origin, p=None, scale=100.0,
                       label="静电除尘器外形图", tracker=None):
    """正立面：支腿/灰斗/进口喇叭/电场箱体/出口喇叭/顶部吊挂室。"""
    p = _params(p)
    s = scale
    ox, oy = _r(*origin)
    in_L, field_L, out_L = _lengths(p)
    W = p["box_W"]
    v = _vert(p)
    y0, y1, y2, y3, y4 = (oy + v[k] for k in ("y0", "y1", "y2", "y3", "y4"))

    x_in0 = ox                       # 进口小端左
    x_in1 = ox + in_L                # 箱体左
    x_out0 = x_in1 + field_L         # 箱体右
    x_out1 = x_out0 + out_L          # 出口小端右
    cx = (x_in1 + x_out0) / 2.0

    # 地面线
    _ln(msp, (ox - 3 * s, y0), (x_out1 + 3 * s, y0), "细实线")

    # 支腿（均布 4 对，画 4 根示意）
    leg_off = 500.0
    n_leg = 4
    for i in range(n_leg):
        lx = x_in1 + leg_off + (field_L - 2 * leg_off) * i / (n_leg - 1)
        _ln(msp, (lx, y0), (lx, y1), "设备")

    # 灰斗（n_hopper 个锥斗，均布在电场区下部）
    n_hop = p["n_hopper"]
    outlet = p["hopper_outlet"]
    hop_span = field_L / n_hop
    for i in range(n_hop):
        hx0 = x_in1 + i * hop_span
        hcx = hx0 + hop_span / 2.0
        _ln(msp, (hx0, y2), (hcx - outlet / 2, y1), "设备")
        _ln(msp, (hx0 + hop_span, y2), (hcx + outlet / 2, y1), "设备")
        _rect(msp, hcx - outlet / 2, y1, hcx + outlet / 2, y1 + 200, "设备")

    # 电场箱体
    _rect(msp, x_in1, y2, x_out0, y3, "设备")
    # 电场分隔线（虚线示意分隔墙/框架）
    for i in range(1, p["n_field"]):
        fx = x_in1 + i * p["field_L"]
        _ln(msp, (fx, y2), (fx, y3), "虚线", linetype="DASHED")
    # 电场编号
    for i in range(p["n_field"]):
        fx = x_in1 + (i + 0.5) * p["field_L"]
        _t(msp, f"{i+1}#电场", (fx, y2 + 3 * s), 2.5 * s, align=MC,
           layer="文字", tracker=tracker)

    # 进口喇叭（渐扩：小端 inlet_dn → 大端 箱高）
    idn = p["inlet_dn"]
    iy_mid = (y2 + y3) / 2.0
    _ln(msp, (x_in0, iy_mid - idn / 2), (x_in1, y2), "设备")
    _ln(msp, (x_in0, iy_mid + idn / 2), (x_in1, y3), "设备")
    _ln(msp, (x_in0, iy_mid - idn / 2), (x_in0, iy_mid + idn / 2), "设备")
    _tri(msp, (x_in0 - 3 * s, iy_mid), (1, 0), s, "设备")
    _t(msp, f"进口 Φ{idn:.0f}", (x_in0 + in_L / 2, iy_mid + idn / 2 + 4 * s),
       2.2 * s, align=MC, layer="文字", tracker=tracker)
    # 气流分布板（喇叭内 2 道）
    for k in (0.35, 0.7):
        px = x_in0 + in_L * k
        half = idn / 2 + (p["box_H"] / 2 - idn / 2) * k
        _ln(msp, (px, iy_mid - half), (px, iy_mid + half), "细实线",
            linetype="DASHED")
    _t(msp, "气流分布板", (x_in0 + in_L * 0.5, y2 - 4 * s), 2.0 * s,
       align=MC, layer="文字", tracker=tracker)

    # 出口喇叭（渐缩）
    odn = p["outlet_dn"]
    _ln(msp, (x_out0, y2), (x_out1, iy_mid - odn / 2), "设备")
    _ln(msp, (x_out0, y3), (x_out1, iy_mid + odn / 2), "设备")
    _ln(msp, (x_out1, iy_mid - odn / 2), (x_out1, iy_mid + odn / 2), "设备")
    _tri(msp, (x_out1 + 3 * s, iy_mid), (1, 0), s, "设备")
    _t(msp, f"出口 Φ{odn:.0f}", (x_out0 + out_L / 2, iy_mid + odn / 2 + 4 * s),
       2.2 * s, align=MC, layer="文字", tracker=tracker)

    # 顶部阴极吊挂室
    _rect(msp, x_in1, y3, x_out0, y4, "设备")
    _t(msp, "阴极吊挂室", (cx, (y3 + y4) / 2), 2.2 * s, align=MC,
       layer="文字", tracker=tracker)
    # 高压进线套管（顶部 2 个）
    for k in (0.3, 0.7):
        bx = x_in1 + field_L * k
        _rect(msp, bx - 100, y4, bx + 100, y4 + 400, "设备")
    _t(msp, "高压进线", (x_in1 + field_L * 0.7, y4 + 700), 2.0 * s,
       align=MC, layer="文字", tracker=tracker)

    # 总宽标注文字
    _t(msp, f"电场区 {field_L:.0f}（{p['n_field']}电场×{p['field_L']:.0f}）",
       (cx, y0 - 6 * s), 2.3 * s, align=MC, layer="文字", tracker=tracker)

    if label:
        _t(msp, label, (cx, y0 - 12 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (cx, y0, y4 + 400)


# ══════════════════════════════════════════════════════════
#  2. 外形总图 — 平面（俯视）
# ══════════════════════════════════════════════════════════

def draw_esp_plan(msp, origin, p=None, scale=100.0,
                  label="平面图", tracker=None):
    """俯视：总宽(通道)轮廓 + 喇叭渐变 + 中心线 + 进出口烟道。"""
    p = _params(p)
    s = scale
    ox, oy = _r(*origin)
    in_L, field_L, out_L = _lengths(p)
    W = p["box_W"]
    idn, odn = p["inlet_dn"], p["outlet_dn"]

    x_in0 = ox
    x_in1 = ox + in_L
    x_out0 = x_in1 + field_L
    x_out1 = x_out0 + out_L
    cy = oy + W / 2.0

    # 电场区外框
    _rect(msp, x_in1, oy, x_out0, oy + W, "设备")
    # 进口喇叭（俯视渐扩）
    _ln(msp, (x_in0, cy - idn / 2), (x_in1, oy), "设备")
    _ln(msp, (x_in0, cy + idn / 2), (x_in1, oy + W), "设备")
    _ln(msp, (x_in0, cy - idn / 2), (x_in0, cy + idn / 2), "设备")
    _t(msp, "进", (x_in0 + 3 * s, cy), 2.2 * s, align=ML, layer="文字",
       tracker=tracker)
    # 出口喇叭（俯视渐缩）
    _ln(msp, (x_out0, oy), (x_out1, cy - odn / 2), "设备")
    _ln(msp, (x_out0, oy + W), (x_out1, cy + odn / 2), "设备")
    _ln(msp, (x_out1, cy - odn / 2), (x_out1, cy + odn / 2), "设备")
    _t(msp, "出", (x_out1 - 3 * s, cy), 2.2 * s, align=MR, layer="文字",
       tracker=tracker)

    # 通道分隔（点画线：阳极排中心）
    pitch = p["pitch"]
    n_ch = int(W / pitch)
    for i in range(1, n_ch):
        chy = oy + i * pitch
        _ln(msp, (x_in1, chy), (x_out0, chy), "点画线", linetype="CENTER")
    # 纵向中心线
    _ln(msp, (x_in0 - 4 * s, cy), (x_out1 + 4 * s, cy), "点画线",
        linetype="CENTER")

    # 灰斗投影（虚线矩形）
    n_hop = p["n_hopper"]
    hop_span = field_L / n_hop
    for i in range(n_hop):
        hx0 = x_in1 + i * hop_span
        _rect(msp, hx0, oy + W * 0.2, hx0 + hop_span, oy + W * 0.8, "虚线")

    _t(msp, f"总宽 {W:.0f}｜{n_ch} 通道（同极距 {pitch:.0f}）",
       ((x_in1 + x_out0) / 2.0, oy - 6 * s), 2.3 * s, align=MC,
       layer="文字", tracker=tracker)

    if label:
        _t(msp, label, ((x_in1 + x_out0) / 2.0, oy + W + 6 * s), 3.2 * s,
           align=MC, layer="文字-标题", tracker=tracker)
    return (x_out1, oy)


# ══════════════════════════════════════════════════════════
#  3. 纵剖面图（沿气流方向）
# ══════════════════════════════════════════════════════════

def draw_esp_section(msp, origin, p=None, scale=100.0,
                     label="1-1 剖面图", tracker=None):
    """纵剖面：分布板/各电场阴阳极(交替)/振打锤/灰斗内部。"""
    p = _params(p)
    s = scale
    ox, oy = _r(*origin)
    in_L, field_L, out_L = _lengths(p)
    v = _vert(p)
    y1, y2, y3, y4 = (oy + v[k] for k in ("y1", "y2", "y3", "y4"))

    x_in1 = ox + in_L
    x_out0 = x_in1 + field_L
    cx = (x_in1 + x_out0) / 2.0

    # 壳体剖切轮廓
    _rect(msp, x_in1, y2, x_out0, y3, "设备")
    _rect(msp, x_in1, y3, x_out0, y4, "设备")

    # 进口分布板（剖面内 2 道多孔板）
    iy_mid = (y2 + y3) / 2.0
    idn = p["inlet_dn"]
    for k in (0.35, 0.7):
        px = ox + in_L * k
        half = idn / 2 + (p["box_H"] / 2 - idn / 2) * k
        _ln(msp, (px, iy_mid - half), (px, iy_mid + half), "细实线")
        # 板孔示意
        for j in range(3):
            hy = iy_mid - half + (2 * half) * (j + 0.5) / 3
            _circle(msp, (px, hy), 80, "细实线")

    # 各电场：阴阳极交替竖线（奇阳极板/偶电晕线）
    pitch = p["pitch"]
    for i in range(p["n_field"]):
        fx0 = x_in1 + i * p["field_L"]
        n = int(p["field_L"] / pitch)
        for j in range(n):
            ex = fx0 + pitch * (j + 0.5)
            if j % 2 == 0:
                _ln(msp, (ex, y2 + 200), (ex, y3 - 200), "设备")   # 阳极板
            else:
                _ln(msp, (ex, y2 + 300), (ex, y3 - 300), "细实线") # 电晕线
        # 振打锤（每电场顶部 1 组）
        hx = fx0 + p["field_L"] / 2.0
        _circle(msp, (hx, y4 - 300), 150, "设备")
        _ln(msp, (hx, y4 - 450), (hx, y3), "细实线")
    _t(msp, "阳极板/电晕线交替布置", (cx, y3 - 4 * s), 2.0 * s, align=MC,
       layer="文字", tracker=tracker)
    _t(msp, "振打锤", (x_in1 + p["field_L"] / 2.0 + 3 * s, y4 - 300),
       2.0 * s, align=ML, layer="文字", tracker=tracker)

    # 灰斗剖面（1 个代表）
    n_hop = p["n_hopper"]
    hop_span = field_L / n_hop
    outlet = p["hopper_outlet"]
    hx0 = x_in1 + hop_span * (n_hop // 2)
    hcx = hx0 + hop_span / 2.0
    _ln(msp, (hx0, y2), (hcx - outlet / 2, y1), "设备")
    _ln(msp, (hx0 + hop_span, y2), (hcx + outlet / 2, y1), "设备")
    # 斗内阻流板
    _ln(msp, (hx0 + hop_span * 0.3, y1 + (y2 - y1) * 0.5),
        (hx0 + hop_span * 0.7, y1 + (y2 - y1) * 0.5), "细实线")

    if label:
        _t(msp, label, (cx, oy - 8 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (cx, oy, y4)


# ══════════════════════════════════════════════════════════
#  4. 阴阳极系统详图（电场横断面局部）
# ══════════════════════════════════════════════════════════

def draw_esp_electrode(msp, origin, p=None, scale=100.0,
                       label="阴阳极系统详图", tracker=None):
    """电场横断面局部：阳极板(C480 波折) + 电晕线(芒刺) + 同极距标注。"""
    p = _params(p)
    s = scale
    ox, oy = _r(*origin)
    pitch = p["pitch"]
    plate_H = 2400.0           # 详图示意高
    n_bay = 4                  # 画 4 个通道

    W = n_bay * pitch
    cx = ox + W / 2.0

    # 阳极板排（波折板示意：正弦折线）
    for i in range(n_bay + 1):
        px = ox + i * pitch
        amp, period = 25.0, 200.0
        pts = []
        yy = oy
        while yy <= oy + plate_H:
            pts.append(_r(px + amp * math.sin(yy / period * math.pi), yy))
            yy += period / 4.0
        msp.add_lwpolyline(pts, dxfattribs={"layer": "设备"})

    # 电晕线（每通道中心，圆杆+芒刺）
    for i in range(n_bay):
        wx = ox + (i + 0.5) * pitch
        _ln(msp, (wx, oy), (wx, oy + plate_H), "细实线")
        yy = oy + 150.0
        while yy < oy + plate_H:
            _ln(msp, (wx - 60, yy), (wx + 60, yy), "细实线")   # 芒刺横划
            yy += 300.0

    # 悬吊梁（顶部）
    _rect(msp, ox - 200, oy + plate_H, ox + W + 200, oy + plate_H + 300, "设备")
    _t(msp, "悬吊梁", (ox + W + 400, oy + plate_H + 150), 2.0 * s, align=ML,
       layer="文字", tracker=tracker)
    # 下部撞击杆
    _rect(msp, ox - 200, oy - 300, ox + W + 200, oy, "设备")
    _t(msp, "撞击杆(振打传力)", (ox + W + 400, oy - 150), 2.0 * s, align=ML,
       layer="文字", tracker=tracker)

    # 同极距标注
    _ln(msp, (ox, oy - 5 * s), (ox + pitch, oy - 5 * s), "细实线-尺寸")
    _t(msp, f"同极距 {pitch:.0f}", (ox + pitch / 2, oy - 8 * s), 2.2 * s,
       align=MC, layer="文字", tracker=tracker)
    _t(msp, f"阳极板 {p['plate_len']:.0f} 型｜电晕线 {p['discharge_wire']}",
       (cx, oy - 12 * s), 2.2 * s, align=MC, layer="文字", tracker=tracker)

    if label:
        _t(msp, label, (cx, oy + plate_H + 6 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (ox + W, oy)


# ══════════════════════════════════════════════════════════
#  5. 振打清灰系统图
# ══════════════════════════════════════════════════════════

def draw_esp_rapping(msp, origin, p=None, scale=100.0,
                     label="振打清灰系统图", tracker=None):
    """侧部机械振打：减速电机 + 传动轴 + 振打锤(砧) 布置。"""
    p = _params(p)
    s = scale
    ox, oy = _r(*origin)
    n_field = p["n_field"]
    bay_W = 2600.0
    W = n_field * bay_W
    H = 3200.0
    cx = ox + W / 2.0

    # 侧壁示意
    _rect(msp, ox, oy, ox + W, oy + H, "细实线")
    _t(msp, "电场侧壁", (ox + 200, oy + H + 3 * s), 2.0 * s, align=ML,
       layer="文字", tracker=tracker)

    # 每电场：传动轴(横贯通) + 振打锤 2 组
    shaft_y = oy + H * 0.55
    _ln(msp, (ox - 600, shaft_y), (ox + W, shaft_y), "设备")
    for i in range(n_field):
        fx = ox + i * bay_W
        for k in (0.3, 0.7):
            hx = fx + bay_W * k
            _circle(msp, (hx, shaft_y), 120, "设备")            # 锤头
            _ln(msp, (hx, shaft_y + 120), (hx + 250, shaft_y + 600), "设备")  # 锤臂
            _rect(msp, hx + 150, shaft_y + 550, hx + 450, shaft_y + 700, "设备")  # 砧座
        _t(msp, f"{i+1}#", (fx + bay_W / 2, oy + 3 * s), 2.2 * s,
           align=MC, layer="文字", tracker=tracker)

    # 减速电机（轴端）
    _rect(msp, ox - 1400, shaft_y - 300, ox - 600, shaft_y + 300, "设备")
    _t(msp, "减速电机", (ox - 1000, shaft_y - 4 * s), 2.0 * s, align=MC,
       layer="文字", tracker=tracker)

    _t(msp, f"振打方式：{p['rapping']}（每电场 1 轴 2 锤）",
       (cx, oy - 5 * s), 2.3 * s, align=MC, layer="文字", tracker=tracker)

    if label:
        _t(msp, label, (cx, oy + H + 8 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (ox + W, oy)


# ══════════════════════════════════════════════════════════
#  6. 灰斗及输灰装置详图
# ══════════════════════════════════════════════════════════

def draw_esp_hopper(msp, origin, p=None, scale=100.0,
                    label="灰斗及输灰装置详图", tracker=None):
    """灰斗放大 + 气化风管 + 插板阀 + 星型卸料器 + 料位计。"""
    p = _params(p)
    s = scale
    ox, oy = _r(*origin)          # origin = 灰斗上口左端
    hop = p["hopper_H"]
    outlet = p["hopper_outlet"]
    W = 2600.0                     # 详图斗口宽（示意）
    cx = ox + W / 2.0
    yb = oy - hop

    # 灰斗锥形
    _ln(msp, (ox, oy), (cx - outlet / 2, yb), "设备")
    _ln(msp, (ox + W, oy), (cx + outlet / 2, yb), "设备")
    _ln(msp, (ox, oy), (ox + W, oy), "设备")
    _rect(msp, cx - outlet / 2, yb, cx + outlet / 2, yb + 200, "设备")
    _t(msp, "斗壁倾角≥60°", (ox + W * 0.72, oy - hop * 0.45), 2.2 * s,
       align=ML, layer="文字", tracker=tracker)

    # 气化风管（斗壁下部两侧斜插）
    for sgn in (-1, 1):
        ax = cx + sgn * (W * 0.28)
        ay = oy - hop * 0.62
        _ln(msp, (ax + sgn * 500, ay + 250), (ax, ay), "管道-加药")
        _circle(msp, (ax + sgn * 550, ay + 280), 60, "设备")
    _t(msp, "气化风管", (ox - 4 * s, oy - hop * 0.55), 2.0 * s, align=MR,
       layer="文字", tracker=tracker)
    # 电加热器（斗壁外侧）
    _rect(msp, ox - 350, oy - hop * 0.35, ox, oy - hop * 0.15, "设备")
    _t(msp, "电加热器", (ox - 380, oy - hop * 0.25), 2.0 * s, align=MR,
       layer="文字", tracker=tracker)

    # 插板阀
    gv_y = yb - 200
    _rect(msp, cx - outlet / 2 - 100, gv_y, cx + outlet / 2 + 100, gv_y + 120, "设备")
    _ln(msp, (cx - outlet / 2 - 100, gv_y + 60), (cx + outlet / 2 + 100, gv_y + 60), "细实线")
    _t(msp, "插板阀", (cx + outlet / 2 + 250, gv_y + 60), 2.0 * s, align=ML,
       layer="文字", tracker=tracker)

    # 星型卸料器
    rl_cy = gv_y - 350
    _circle(msp, (cx, rl_cy), 250, "设备")
    for ang in range(0, 360, 45):
        a = math.radians(ang)
        _ln(msp, (cx, rl_cy), (cx + 250 * math.cos(a), rl_cy + 250 * math.sin(a)), "细实线")
    _t(msp, "星型卸料器", (cx + 350, rl_cy), 2.0 * s, align=ML,
       layer="文字", tracker=tracker)

    # 料位计（高低两支）
    for frac, name in ((0.3, "高料位计"), (0.55, "低料位计")):
        lx = ox + W * 0.15
        ly = oy - hop * frac
        _circle(msp, (lx, ly), 60, "设备")
        _ln(msp, (lx + 60, ly), (lx + 500, ly), "细实线")
        _t(msp, name, (lx + 560, ly), 2.0 * s, align=ML, layer="文字",
           tracker=tracker)

    if label:
        _t(msp, label, (cx, yb - 900), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (cx, yb - 900)
