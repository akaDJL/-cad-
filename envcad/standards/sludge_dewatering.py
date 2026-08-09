# -*- coding: utf-8 -*-
"""污泥脱水机房多视图制图 v1.0（GB 50014、HJ 2024、CJ/T 221）。

成套视图：带式压滤机立面、板框压滤机(立面/平面)、加药调理系统、
机房平面布置。所有几何参数以 dict 传入（默认取
knowledge.sludge_dewatering_data.SD_DEFAULTS）——本模块只负责"画"，不负责"算"。

坐标单位 mm，scale=出图比例倒数(1:100 → 100)。图层沿用包内中文命名。
"""
from __future__ import annotations

import math

from ezdxf.enums import TextEntityAlignment

from ..utils import _r, _tri
from .annotate import _t
from ..knowledge.sludge_dewatering_data import SD_DEFAULTS

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
    d = dict(SD_DEFAULTS)
    d.update(p or {})
    return d


# ══════════════════════════════════════════════════════════
#  1. 带式压滤机立面图
# ══════════════════════════════════════════════════════════

def draw_sd_belt_press(msp, origin, p=None, scale=100.0,
                       label="带式压滤机立面图", tracker=None):
    """侧视：重力浓缩段/楔形区/压榨辊组(S形)/驱动辊/张紧/接液盘。"""
    p = _params(p)
    s = scale
    ox, oy = _r(*origin)
    L, H = p["bp_L"], p["bp_H"]
    cx = ox + L / 2.0

    # 机架（底梁 + 支腿）
    _ln(msp, (ox, oy + 400), (ox + L, oy + 400), "设备")
    for k in (0.05, 0.5, 0.95):
        _ln(msp, (ox + L * k, oy), (ox + L * k, oy + 400), "设备")
    _ln(msp, (ox - 3 * s, oy), (ox + L + 3 * s, oy), "细实线")   # 地面

    # 重力浓缩段（左部斜面，上滤带）
    gL = p["gravity_H"]
    _ln(msp, (ox, oy + H - 300), (ox + gL + 1500, oy + H - 300), "设备")
    # 滤带（上下两条包络压榨区）
    _ln(msp, (ox + gL + 1500, oy + H - 300), (ox + L - 800, oy + H - 900),
        "设备")
    _ln(msp, (ox + gL + 1500, oy + H - 800), (ox + L - 800, oy + H - 800),
        "设备")
    # 重力段犁耙（上带面小耙）
    for j in range(4):
        rx = ox + 500 + j * 400
        _ln(msp, (rx, oy + H - 300), (rx + 100, oy + H - 100), "细实线")
    _t(msp, "重力浓缩段(犁耙)", (ox + gL / 2 + 700, oy + H - 100), 2.0 * s,
       align=MC, layer="文字", tracker=tracker)

    # 压榨辊组（S 形绕行 4 辊）
    rollers = [(0.62, 0.55, 300), (0.72, 0.45, 260), (0.82, 0.60, 220),
               (0.90, 0.50, 180)]
    for kx, ky, rr in rollers:
        rx, ry = ox + L * kx, oy + H * ky
        _circle(msp, (rx, ry), rr, "设备")
        _circle(msp, (rx, ry), rr * 0.25, "细实线")
    _t(msp, "压榨辊组(S形)", (ox + L * 0.76, oy + H * 0.55 + 500), 2.0 * s,
       align=MC, layer="文字", tracker=tracker)

    # 驱动辊 + 电机（右端）
    _circle(msp, (ox + L - 500, oy + H - 400), 350, "设备")
    _rect(msp, ox + L - 350, oy + H - 250, ox + L + 350, oy + H + 150, "设备")
    _t(msp, "驱动电机", (ox + L, oy + H + 350), 2.0 * s, align=MC,
       layer="文字", tracker=tracker)

    # 进泥端（左上）与调理混合器
    _circle(msp, (ox + 300, oy + H + 200), 250, "设备")
    _t(msp, "调理混合器", (ox + 300, oy + H + 550), 2.0 * s, align=MC,
       layer="文字", tracker=tracker)
    _ln(msp, (ox + 300, oy + H - 50), (ox + 300, oy + H - 300), "管道-污水")
    _tri(msp, (ox + 300, oy + H - 350), (0, -1), s * 0.5, "流向")

    # 泥饼卸料（右下刮板）
    _ln(msp, (ox + L - 700, oy + H - 950), (ox + L - 500, oy + H - 800),
        "设备")
    _tri(msp, (ox + L - 600, oy + 700), (0, -1), s * 0.6, "流向")
    _t(msp, f"泥饼(含固 {p['cake_ds']*100:.0f}%)", (ox + L - 600, oy + 500),
       2.0 * s, align=MC, layer="文字", tracker=tracker)

    # 接液盘（底部通长）
    _rect(msp, ox + 400, oy + 100, ox + L - 400, oy + 350, "设备")
    _t(msp, "接液盘(滤液回前端)", (cx, oy - 3 * s), 2.0 * s, align=MC,
       layer="文字", tracker=tracker)

    # 张紧/纠偏（中部标注）
    _t(msp, "张紧+纠偏装置", (ox + L * 0.35, oy + H * 0.45), 2.0 * s,
       align=MC, layer="文字", tracker=tracker)

    if label:
        _t(msp, label, (cx, oy - 8 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (cx, oy, oy + H)


# ══════════════════════════════════════════════════════════
#  2. 板框压滤机立面图
# ══════════════════════════════════════════════════════════

def draw_sd_filter_press(msp, origin, p=None, scale=100.0,
                         label="板框压滤机立面图", tracker=None):
    """侧视：止推板/滤板组/压紧板/液压缸/拉板机构/接液翻板。"""
    p = _params(p)
    s = scale
    ox, oy = _r(*origin)
    L, H = p["fp_L"], p["fp_H"]
    n = p["n_plate"]
    cx = ox + L / 2.0

    # 地面 + 机座
    _ln(msp, (ox - 3 * s, oy), (ox + L + 3 * s, oy), "细实线")
    for k in (0.08, 0.92):
        _rect(msp, ox + L * k - 150, oy, ox + L * k + 150, oy + 300, "设备")

    # 主梁（上下两根贯通）
    _ln(msp, (ox, oy + H - 300), (ox + L, oy + H - 300), "设备")
    _ln(msp, (ox, oy + H - 700), (ox + L, oy + H - 700), "设备")

    # 止推板（左端固定）
    _rect(msp, ox + 100, oy + 400, ox + 400, oy + H - 200, "设备")
    _t(msp, "止推板", (ox + 250, oy + H + 3 * s), 2.0 * s, align=MC,
       layer="文字", tracker=tracker)

    # 滤板组（n 块，挂主梁间）
    plate_t = p["plate_t"]
    span = L - 1400
    step = span / n
    for i in range(n):
        bx = ox + 500 + step * i
        _rect(msp, bx, oy + 500, bx + plate_t, oy + H - 500, "细实线")
    _t(msp, f"滤板 {n} 块（{p['plate_size']:.0f}×{p['plate_size']:.0f}）",
       (cx, oy + H - 4 * s), 2.2 * s, align=MC, layer="文字", tracker=tracker)

    # 压紧板 + 液压缸（右端）
    _rect(msp, ox + L - 900, oy + 400, ox + L - 600, oy + H - 200, "设备")
    _rect(msp, ox + L - 600, oy + H / 2 - 150, ox + L - 100,
          oy + H / 2 + 150, "设备")
    _t(msp, f"液压缸(压榨 {p['press_p']} MPa)", (ox + L - 350, oy + H + 3 * s),
       2.0 * s, align=MC, layer="文字", tracker=tracker)

    # 拉板机构（顶部小车）
    _rect(msp, cx - 200, oy + H - 250, cx + 200, oy + H - 50, "设备")
    _t(msp, "自动拉板小车", (cx, oy + H + 3 * s), 2.0 * s, align=MC,
       layer="文字", tracker=tracker)

    # 进料口（止推板中心）
    _circle(msp, (ox + 250, oy + H / 2), 120, "管道-污水")
    _ln(msp, (ox - 600, oy + H / 2), (ox + 100, oy + H / 2), "管道-污水")
    _tri(msp, (ox - 700, oy + H / 2), (1, 0), s * 0.6, "流向")
    _t(msp, f"进泥 DN{p['pump_dn']:.0f}", (ox - 400, oy + H / 2 + 4 * s),
       2.0 * s, align=MC, layer="文字", tracker=tracker)

    # 接液翻板（底部）
    _ln(msp, (ox + 200, oy + 400), (ox + L - 700, oy + 400), "设备")
    _ln(msp, (ox + 200, oy + 400), (ox + 200, oy + 200), "设备")
    _t(msp, "接液翻板", (cx, oy + 200), 2.0 * s, align=MC, layer="文字",
       tracker=tracker)

    if label:
        _t(msp, label, (cx, oy - 8 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (cx, oy, oy + H)


# ══════════════════════════════════════════════════════════
#  3. 板框压滤机平面图
# ══════════════════════════════════════════════════════════

def draw_sd_filter_press_plan(msp, origin, p=None, scale=100.0,
                              label="板框压滤机平面图", tracker=None):
    """俯视：机长/滤板排列/进料与滤液管/液压站位置。"""
    p = _params(p)
    s = scale
    ox, oy = _r(*origin)
    L, W = p["fp_L"], p["fp_W"]
    n = p["n_plate"]
    cx, cy = ox + L / 2.0, oy + W / 2.0

    # 机身轮廓
    _rect(msp, ox, oy, ox + L, oy + W, "设备")

    # 滤板（俯视横线阵）
    plate_t = p["plate_t"]
    span = L - 1400
    step = span / n
    for i in range(n):
        bx = ox + 500 + step * i
        _ln(msp, (bx, oy + 150), (bx, oy + W - 150), "细实线")

    # 止推板/压紧板
    _rect(msp, ox + 100, oy + 100, ox + 400, oy + W - 100, "设备")
    _rect(msp, ox + L - 900, oy + 100, ox + L - 600, oy + W - 100, "设备")

    # 进料管（角进料，上部）
    _ln(msp, (ox - 800, oy + W - 300), (ox + L, oy + W - 300), "管道-污水")
    _t(msp, "进泥总管", (cx, oy + W - 100), 2.0 * s, align=MC, layer="文字",
       tracker=tracker)
    # 滤液明流（下部每板嘴）
    _ln(msp, (ox + 400, oy + 200), (ox + L - 900, oy + 200), "管道-给水")
    _t(msp, "滤液明流槽", (cx, oy - 4 * s), 2.0 * s, align=MC, layer="文字",
       tracker=tracker)

    # 液压站（机尾旁）
    _rect(msp, ox + L + 500, oy + 200, ox + L + 1500, oy + 1000, "设备")
    _t(msp, "液压站", (ox + L + 1000, oy + 600), 2.0 * s, align=MC,
       layer="文字", tracker=tracker)
    _ln(msp, (ox + L, oy + 600), (ox + L + 500, oy + 600), "细实线")

    # 中心线
    _ln(msp, (ox - 3 * s, cy), (ox + L + 3 * s, cy), "点画线",
        linetype="CENTER")

    if label:
        _t(msp, label, (cx, oy + W + 6 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (ox + L, oy)


# ══════════════════════════════════════════════════════════
#  4. 加药调理系统图
# ══════════════════════════════════════════════════════════

def draw_sd_conditioning(msp, origin, p=None, scale=100.0,
                         label="污泥加药调理系统图", tracker=None):
    """系统图：PAM 制备(三腔) → 计量泵 → 管道混合 → 压滤机进泥。"""
    p = _params(p)
    s = scale
    ox, oy = _r(*origin)
    W = 10000.0
    H = 4000.0

    # PAM 三腔制备罐（左：干粉投加/熟化/储存 三格）
    td = p["pam_tank_D"]
    _rect(msp, ox, oy + 1200, ox + 3 * td, oy + 1200 + p["pam_tank_H"],
          "设备")
    for k in (1, 2):
        _ln(msp, (ox + k * td, oy + 1200), (ox + k * td, oy + 1200 +
                                            p["pam_tank_H"]), "细实线")
    for k, name in enumerate(("溶解", "熟化", "储存")):
        _t(msp, name, (ox + (k + 0.5) * td, oy + 1200 + p["pam_tank_H"] / 2),
           2.0 * s, align=MC, layer="文字", tracker=tracker)
    # 搅拌器（每腔顶部）
    for k in range(3):
        mx = ox + (k + 0.5) * td
        _ln(msp, (mx, oy + 1200 + p["pam_tank_H"]),
            (mx, oy + 1200 + p["pam_tank_H"] + 300), "设备")
        _rect(msp, mx - 150, oy + 1200 + p["pam_tank_H"] + 300, mx + 150,
              oy + 1200 + p["pam_tank_H"] + 550, "设备")
    _t(msp, "PAM 三腔制备装置", (ox + 1.5 * td, oy + 1200 +
                                 p["pam_tank_H"] + 800), 2.2 * s, align=MC,
       layer="文字", tracker=tracker)
    # 干粉料斗（第一腔顶）
    _ln(msp, (ox + td * 0.2, oy + 1200 + p["pam_tank_H"] + 550),
        (ox + td * 0.5, oy + 1200 + p["pam_tank_H"] + 900), "设备")
    _ln(msp, (ox + td * 0.8, oy + 1200 + p["pam_tank_H"] + 550),
        (ox + td * 0.5, oy + 1200 + p["pam_tank_H"] + 900), "设备")

    # 计量泵（中部 2 台）
    for k in (0, 1):
        _circle(msp, (ox + 5200 + k * 800, oy + 1500), 220, "阀门")
    _t(msp, "加药计量泵(1用1备)", (ox + 5600, oy + 1100), 2.0 * s, align=MC,
       layer="文字", tracker=tracker)
    # 储存腔 → 计量泵
    _ln(msp, (ox + 3 * td, oy + 1500), (ox + 4980, oy + 1500), "管道-加药")

    # 污泥线：浓缩池来泥 → 螺杆泵 → 混合器 → 压滤机（下排）
    _t(msp, "浓缩污泥", (ox + 200, oy + 300), 2.0 * s, align=ML, layer="文字",
       tracker=tracker)
    _ln(msp, (ox + 100, oy + 500), (ox + 4900, oy + 500), "管道-污水")
    _circle(msp, (ox + 4500, oy + 500), 220, "设备")
    _t(msp, "进泥螺杆泵", (ox + 4500, oy + 100), 2.0 * s, align=MC,
       layer="文字", tracker=tracker)
    # 管道混合器（药泥交汇）
    hx = ox + 6800
    _rect(msp, hx - 300, oy + 350, hx + 300, oy + 650, "设备")
    _t(msp, "管道混合器", (hx, oy + 50), 2.0 * s, align=MC, layer="文字",
       tracker=tracker)
    _ln(msp, (ox + 4720, oy + 500), (hx - 300, oy + 500), "管道-污水")
    # 药 → 混合器
    _ln(msp, (ox + 6000, oy + 1500), (hx, oy + 1500), "管道-加药")
    _ln(msp, (hx, oy + 1500), (hx, oy + 650), "管道-加药")
    _tri(msp, (hx, oy + 750), (0, -1), s * 0.5, "流向")
    # 混合后 → 压滤机
    _ln(msp, (hx + 300, oy + 500), (ox + 9500, oy + 500), "管道-污水")
    _rect(msp, ox + 9500, oy + 200, ox + 9900, oy + 800, "设备")
    _t(msp, "压滤机", (ox + 9700, oy + 500), 1.8 * s, align=MC, layer="文字",
       tracker=tracker)

    _t(msp, f"投加量 {p['pam_dose']*1000:.0f}‰ DS｜熟化浓度 "
            f"{p['pam_conc']*100:.1f}%", (ox + W / 2, oy - 5 * s), 2.3 * s,
       align=MC, layer="文字", tracker=tracker)

    if label:
        _t(msp, label, (ox + W / 2, oy + H + 5 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (ox + W, oy)


# ══════════════════════════════════════════════════════════
#  5. 脱水机房平面布置图
# ══════════════════════════════════════════════════════════

def draw_sd_room_layout(msp, origin, p=None, scale=100.0,
                        label="脱水机房平面布置图", tracker=None):
    """平面：压滤机位/加药间/污泥泵区/泥饼间/通道/起重轨道。"""
    p = _params(p)
    s = scale
    ox, oy = _r(*origin)
    L, W = p["room_L"], p["room_W"]
    cx, cy = ox + L / 2.0, oy + W / 2.0

    # 房体外轮廓 + 大门
    _rect(msp, ox, oy, ox + L, oy + W, "粗实线")
    # 大门（右墙，泥饼外运）
    _ln(msp, (ox + L, oy + W * 0.3), (ox + L, oy + W * 0.7), "细实线")
    _t(msp, "大门(泥饼外运)", (ox + L + 3 * s, oy + W * 0.5), 2.0 * s,
       align=ML, layer="文字", tracker=tracker)

    # 压滤机（2 台并排，中部）
    for k in (0, 1):
        fx = ox + 3500 + k * (p["fp_L"] + 800)
        _rect(msp, fx, oy + W * 0.45, fx + p["fp_L"], oy + W * 0.45 +
              p["fp_W"], "设备")
        _t(msp, f"{k+1}#压滤机", (fx + p["fp_L"] / 2,
                                  oy + W * 0.45 + p["fp_W"] / 2), 2.0 * s,
           align=MC, layer="文字", tracker=tracker)

    # 加药间（左部隔间）
    _rect(msp, ox, oy + W * 0.55, ox + 2800, oy + W, "细实线")
    _t(msp, "加药间", (ox + 1400, oy + W * 0.8), 2.2 * s, align=MC,
       layer="文字", tracker=tracker)
    _rect(msp, ox + 300, oy + W * 0.62, ox + 1500, oy + W * 0.9, "设备")
    _t(msp, "PAM制备", (ox + 900, oy + W * 0.76), 1.8 * s, align=MC,
       layer="文字", tracker=tracker)

    # 污泥泵区（左下）
    _rect(msp, ox, oy, ox + 2800, oy + W * 0.45, "细实线")
    _t(msp, "污泥泵区", (ox + 1400, oy + W * 0.25), 2.2 * s, align=MC,
       layer="文字", tracker=tracker)
    for k in (0, 1):
        _circle(msp, (ox + 800 + k * 1200, oy + W * 0.22), 300, "设备")

    # 泥饼堆场（右部）
    _rect(msp, ox + L - 2500, oy + W * 0.2, ox + L, oy + W * 0.8, "虚线")
    _t(msp, "泥饼暂存", (ox + L - 1250, oy + W * 0.9), 2.0 * s, align=MC,
       layer="文字", tracker=tracker)

    # 起重轨道（顶部双梁）
    _ln(msp, (ox + 500, oy + W - 400), (ox + L - 500, oy + W - 400), "设备")
    _ln(msp, (ox + 500, oy + W - 700), (ox + L - 500, oy + W - 700), "设备")
    _t(msp, "起重机轨道", (cx, oy + W + 3 * s), 2.0 * s, align=MC,
       layer="文字", tracker=tracker)

    # 排水沟（沿压滤机前缘）
    _ln(msp, (ox + 3200, oy + W * 0.42), (ox + L - 2600, oy + W * 0.42),
        "管道-污水")
    _t(msp, "地沟排水", (cx, oy + W * 0.38), 1.8 * s, align=MC, layer="文字",
       tracker=tracker)

    _t(msp, f"机房 {L:.0f}×{W:.0f}×{p['room_H']:.0f}｜通风除臭≥6次/h",
       (cx, oy - 6 * s), 2.3 * s, align=MC, layer="文字", tracker=tracker)

    if label:
        _t(msp, label, (cx, oy - 12 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (ox + L, oy)
