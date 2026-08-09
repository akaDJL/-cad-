# -*- coding: utf-8 -*-
"""噪声与振动治理多视图制图 v1.0（GB 12348、HJ 2034、HJ/T 90、GB/T 19887）。

成套视图：声屏障(立面/剖面)、片式阻性消声器、隔声罩、消声百叶。
所有几何参数以 dict 传入（默认取 knowledge.noise_control_data.NOISE_DEFAULTS）
——本模块只负责"画"，不负责"算"。

坐标单位 mm，scale=出图比例倒数(1:100 → 100)。图层沿用包内中文命名。
"""
from __future__ import annotations

import math

from ezdxf.enums import TextEntityAlignment

from ..utils import _r, _tri
from .annotate import _t
from ..knowledge.noise_control_data import NOISE_DEFAULTS

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
    d = dict(NOISE_DEFAULTS)
    d.update(p or {})
    return d


# ══════════════════════════════════════════════════════════
#  1. 声屏障立面图
# ══════════════════════════════════════════════════════════

def draw_noise_barrier_elevation(msp, origin, p=None, scale=100.0,
                                 label="声屏障立面图", tracker=None):
    """立面：H 钢立柱 + 吸声屏体(分跨) + 基础 + 顶部弧形挑臂。"""
    p = _params(p)
    s = scale
    ox, oy = _r(*origin)
    H = p["barrier_H"]
    pitch = p["post_pitch"]
    n_bay = 5
    L = n_bay * pitch
    cx = ox + L / 2.0

    # 地面线
    _ln(msp, (ox - 3 * s, oy), (ox + L + 3 * s, oy), "细实线")

    # 立柱（每跨端部）
    post_w = 150.0
    for i in range(n_bay + 1):
        px = ox + i * pitch
        _rect(msp, px - post_w / 2, oy, px + post_w / 2, oy + H, "设备")
        # 基础
        _rect(msp, px - p["base_W"] / 2, oy - p["base_H"],
              px + p["base_W"] / 2, oy, "粗实线")

    # 屏体（跨间，分上下两块板）
    for i in range(n_bay):
        x0 = ox + i * pitch + post_w / 2
        x1 = ox + (i + 1) * pitch - post_w / 2
        _ln(msp, (x0, oy + H * 0.5), (x1, oy + H * 0.5), "细实线")
    # 屏体填充线（斜纹示意吸声面）
    for i in range(n_bay * 4):
        fx = ox + L * (i + 0.5) / (n_bay * 4)
        _ln(msp, (fx, oy + 200), (fx + 150, oy + 500), "细实线")

    # 顶部弧形挑臂（朝声源侧）
    for i in range(n_bay + 1):
        px = ox + i * pitch
        msp.add_arc(_r(px, oy + H), p["top_arc"], 0, 90,
                    dxfattribs={"layer": "设备"})

    # 标注
    _t(msp, f"立柱 {p['post_type']} @ {pitch:.0f}", (cx, oy + H + 4 * s),
       2.2 * s, align=MC, layer="文字", tracker=tracker)
    _t(msp, f"吸声屏体 δ={p['panel_t']:.0f}", (cx, oy + H * 0.5 + 4 * s),
       2.0 * s, align=MC, layer="文字", tracker=tracker)
    _t(msp, f"H={H:.0f}｜基础 {p['base_W']:.0f}×{p['base_H']:.0f} 埋深 "
            f"{p['base_embed']:.0f}", (cx, oy - 6 * s), 2.3 * s, align=MC,
       layer="文字", tracker=tracker)

    if label:
        _t(msp, label, (cx, oy - 12 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (cx, oy - p["base_H"], oy + H + p["top_arc"])


# ══════════════════════════════════════════════════════════
#  2. 声屏障剖面图
# ══════════════════════════════════════════════════════════

def draw_noise_barrier_section(msp, origin, p=None, scale=100.0,
                               label="声屏障剖面图", tracker=None):
    """剖面：屏体构造(面板/吸声棉/空腔/背板) + 立柱 + 基础预埋。"""
    p = _params(p)
    s = scale
    ox, oy = _r(*origin)
    t = p["panel_t"]
    H = 1600.0                 # 剖面截取高

    # 屏体断面（左面板/吸声棉/空腔/背板）
    face = 1.5 * 100           # 面板折算示意厚
    cotton = t * 0.6
    cavity = t * 0.25
    x = ox
    _rect(msp, x, oy, x + face, oy + H, "设备")                      # 穿孔面板
    x += face
    _rect(msp, x, oy, x + cotton, oy + H, "细实线")                  # 吸声棉
    x += cotton
    _rect(msp, x, oy, x + cavity, oy + H, "虚线")                    # 空腔
    x += cavity
    _rect(msp, x, oy, x + face, oy + H, "设备")                      # 背板
    x += face
    # 层次引注
    labels = [("穿孔面板(声源侧)", ox + face / 2),
              ("离心玻璃棉", ox + face + cotton / 2),
              ("空腔", ox + face + cotton + cavity / 2),
              ("背板", ox + face + cotton + cavity + face / 2)]
    for name, lx in labels:
        _t(msp, name, (lx, oy + H + 3 * s), 1.8 * s, align=MC, layer="文字",
           tracker=tracker)
    # 面板穿孔示意
    for j in range(6):
        for i in range(2):
            _circle(msp, (ox + face * (i + 0.5) / 2.0, oy + H * (j + 0.5) / 6.0),
                    15, "细实线")

    # H 钢立柱（屏体右侧）
    col_x = x + 300
    _rect(msp, col_x, oy - 200, col_x + 150, oy + H + 200, "设备")
    _rect(msp, col_x - 75, oy + 100, col_x + 225, oy + 250, "设备")   # 翼缘示意
    _t(msp, p["post_type"], (col_x + 75, oy + H + 4 * s), 2.0 * s,
       align=MC, layer="文字", tracker=tracker)

    # 基础 + 预埋螺栓
    _rect(msp, col_x - p["base_W"] / 2 + 75, oy - 200 - p["base_H"],
          col_x + p["base_W"] / 2 + 75, oy - 200, "粗实线")
    for k in (-0.25, 0.25):
        bx = col_x + 75 + p["base_W"] * k
        _ln(msp, (bx, oy - 200), (bx, oy - 200 - p["base_H"] * 0.7), "设备")
    _t(msp, "预埋螺栓", (col_x + 75, oy - 200 - p["base_H"] - 3 * s),
       2.0 * s, align=MC, layer="文字", tracker=tracker)

    if label:
        _t(msp, label, (ox + t / 2, oy - 200 - p["base_H"] - 8 * s), 3.2 * s,
           align=MC, layer="文字-标题", tracker=tracker)
    return (x, oy)


# ══════════════════════════════════════════════════════════
#  3. 片式阻性消声器剖面图
# ══════════════════════════════════════════════════════════

def draw_muffler(msp, origin, p=None, scale=100.0,
                 label="片式阻性消声器剖面图", tracker=None):
    """纵剖面：外壳 + 消声片(玻璃棉+穿孔护面) + 气流通道 + 变径接管。"""
    p = _params(p)
    s = scale
    ox, oy = _r(*origin)
    L = p["muffler_L"]
    H = p["muffler_H"]
    n = p["n_splitter"]
    gap = p["splitter_gap"]
    t = p["splitter_t"]
    cx = ox + L / 2.0

    # 外壳
    _rect(msp, ox, oy, ox + L, oy + H, "设备")

    # 消声片（竖置，沿高均布，剖面中为水平片？此处画横剖：片竖向）
    span = n * t + (n + 1) * gap
    y0 = oy + (H - span) / 2.0
    for i in range(n):
        py = y0 + gap + i * (t + gap)
        _rect(msp, ox + 150, py, ox + L - 150, py + t, "细实线")
        # 穿孔护面（两端小圆点示意）
        for j in range(8):
            hx = ox + 150 + (L - 300) * (j + 0.5) / 8.0
            _circle(msp, (hx, py + t / 2), 20, "细实线")
    # 气流箭头（片间通道）
    for i in range(n + 1):
        ay = y0 + gap / 2.0 + i * (t + gap)
        _tri(msp, (ox + L * 0.45, ay), (1, 0), s * 0.5, "流向")
        _tri(msp, (ox + L * 0.55, ay), (1, 0), s * 0.5, "流向")
    _t(msp, f"气流通道 {gap:.0f}", (ox + L + 3 * s, y0 + gap / 2), 2.0 * s,
       align=ML, layer="文字", tracker=tracker)

    # 进出口变径（喇叭）
    _ln(msp, (ox, oy + H * 0.2), (ox - 800, oy + H * 0.35), "设备")
    _ln(msp, (ox, oy + H * 0.8), (ox - 800, oy + H * 0.65), "设备")
    _ln(msp, (ox - 800, oy + H * 0.35), (ox - 800, oy + H * 0.65), "设备")
    _ln(msp, (ox + L, oy + H * 0.2), (ox + L + 800, oy + H * 0.35), "设备")
    _ln(msp, (ox + L, oy + H * 0.8), (ox + L + 800, oy + H * 0.65), "设备")
    _ln(msp, (ox + L + 800, oy + H * 0.35), (ox + L + 800, oy + H * 0.65), "设备")

    _t(msp, f"{n} 片×δ{t:.0f}｜长 {L:.0f}｜消声量 15~25 dB(A)/m",
       (cx, oy - 6 * s), 2.3 * s, align=MC, layer="文字", tracker=tracker)

    if label:
        _t(msp, label, (cx, oy + H + 6 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (ox + L, oy)


# ══════════════════════════════════════════════════════════
#  4. 隔声罩外形图
# ══════════════════════════════════════════════════════════

def draw_acoustic_enclosure(msp, origin, p=None, scale=100.0,
                            label="隔声罩外形图", tracker=None):
    """立面：罩体(钢板+吸声内衬) + 观察窗 + 检修门 + 进排风消声 + 减振。"""
    p = _params(p)
    s = scale
    ox, oy = _r(*origin)
    L, H = p["hood_L"], p["hood_H"]
    cx = ox + L / 2.0

    # 罩体（双层线表罩板+内衬）
    _rect(msp, ox, oy, ox + L, oy + H, "设备")
    _rect(msp, ox + p["hood_t"], oy + p["hood_t"], ox + L - p["hood_t"],
          oy + H - p["hood_t"], "细实线")
    _t(msp, "罩板(钢板+吸声内衬)", (cx, oy + H + 3 * s), 2.2 * s, align=MC,
       layer="文字", tracker=tracker)

    # 观察窗（左上）
    ww, wh = p["window_W"], p["window_H"]
    _rect(msp, ox + 300, oy + H - 300 - wh, ox + 300 + ww, oy + H - 300, "设备")
    _ln(msp, (ox + 300, oy + H - 300 - wh), (ox + 300 + ww, oy + H - 300),
        "细实线", linetype="CENTER")
    _ln(msp, (ox + 300, oy + H - 300), (ox + 300 + ww, oy + H - 300 - wh),
        "细实线", linetype="CENTER")
    _t(msp, "双层观察窗", (ox + 300 + ww / 2, oy + H - 200), 2.0 * s, align=MC,
       layer="文字", tracker=tracker)

    # 检修门（右部）
    dw, dh = p["door_W"], p["door_H"]
    _rect(msp, ox + L - 300 - dw, oy, ox + L - 300, oy + dh, "设备")
    _circle(msp, (ox + L - 450, oy + dh / 2), 40, "设备")   # 把手
    _t(msp, "隔声检修门(密封条)", (ox + L - 300 - dw / 2, oy - 4 * s),
       2.0 * s, align=MC, layer="文字", tracker=tracker)

    # 进排风消声通道（顶部两侧，迷宫式）
    for k, name in ((0.2, "进风消声道"), (0.8, "排风消声道")):
        vx = ox + L * k
        _rect(msp, vx - 250, oy + H, vx + 250, oy + H + 600, "设备")
        _ln(msp, (vx - 150, oy + H + 100), (vx + 150, oy + H + 300), "细实线")
        _ln(msp, (vx - 150, oy + H + 300), (vx + 150, oy + H + 500), "细实线")
        _t(msp, name, (vx, oy + H + 800), 2.0 * s, align=MC, layer="文字",
           tracker=tracker)

    # 减振基础（底部橡胶垫）
    _rect(msp, ox - 100, oy - 250, ox + L + 100, oy, "粗实线")
    for i in range(6):
        dx = ox + L * (i + 0.5) / 6.0
        _rect(msp, dx - 100, oy - 250, dx + 100, oy - 100, "细实线")
    _t(msp, "橡胶减振垫", (cx, oy - 4 * s), 2.0 * s, align=MC, layer="文字",
       tracker=tracker)

    _t(msp, f"罩体 {L:.0f}×{p['hood_W']:.0f}×{H:.0f}｜隔声量≥25 dB",
       (cx, oy - 9 * s), 2.3 * s, align=MC, layer="文字", tracker=tracker)

    if label:
        _t(msp, label, (cx, oy - 15 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (cx, oy - 250, oy + H + 800)


# ══════════════════════════════════════════════════════════
#  5. 消声百叶剖面图
# ══════════════════════════════════════════════════════════

def draw_silencer_louver(msp, origin, p=None, scale=100.0,
                         label="消声百叶剖面图", tracker=None):
    """剖面：框架 + 斜置吸声叶片(穿孔板+玻璃棉) + 防雨沿。"""
    p = _params(p)
    s = scale
    ox, oy = _r(*origin)
    L = p["louver_L"]
    H = p["louver_H"]
    pitch = p["blade_pitch"]
    t = p["blade_t"]
    cx = ox + L / 2.0

    # 外框
    _rect(msp, ox, oy, ox + L, oy + H, "设备")

    # 吸声叶片（斜置 V 形，上下排列）
    n = int(H / pitch)
    for i in range(n):
        by = oy + pitch * (i + 0.5)
        msp.add_lwpolyline(
            [_r(ox + 100, by + pitch * 0.3), _r(cx, by - pitch * 0.2),
             _r(ox + L - 100, by + pitch * 0.3)],
            dxfattribs={"layer": "细实线"})
        # 叶片厚度（平行下线）
        msp.add_lwpolyline(
            [_r(ox + 100, by + pitch * 0.3 - t), _r(cx, by - pitch * 0.2 - t),
             _r(ox + L - 100, by + pitch * 0.3 - t)],
            dxfattribs={"layer": "细实线"})
    # 叶片内吸声棉（点画示意）
    for i in range(n):
        by = oy + pitch * (i + 0.5) - t / 2.0
        for j in range(5):
            fx = ox + L * (j + 0.5) / 5.0
            _circle(msp, (fx, by), 15, "细实线")

    # 防雨沿（进口侧顶部斜板）
    _ln(msp, (ox, oy + H), (ox - 400, oy + H - 300), "设备")
    _t(msp, "防雨沿", (ox - 350, oy + H + 3 * s), 2.0 * s, align=MC,
       layer="文字", tracker=tracker)

    # 气流方向
    _tri(msp, (ox - 3 * s, oy + H / 2), (1, 0), s, "流向")
    _t(msp, "气流", (ox - 6 * s, oy + H / 2 + 3 * s), 2.0 * s, align=MR,
       layer="文字", tracker=tracker)

    _t(msp, f"叶片 {n} 排×δ{t:.0f}｜间距 {pitch:.0f}｜片内填离心玻璃棉",
       (cx, oy - 6 * s), 2.3 * s, align=MC, layer="文字", tracker=tracker)

    if label:
        _t(msp, label, (cx, oy + H + 6 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (ox + L, oy)
