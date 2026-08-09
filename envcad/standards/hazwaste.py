# -*- coding: utf-8 -*-
"""危险废物暂存间多视图制图 v1.0（GB 18597、HJ 2025、GB 15603）。

成套视图：平面分区、防渗构造剖面、导流沟收集池详图、通风系统、
标识布置。所有几何参数以 dict 传入（默认取
knowledge.hazwaste_data.HW_DEFAULTS）——本模块只负责"画"，不负责"算"。

坐标单位 mm，scale=出图比例倒数(1:100 → 100)。图层沿用包内中文命名。
"""
from __future__ import annotations

import math

from ezdxf.enums import TextEntityAlignment

from ..utils import _r, _tri
from .annotate import _t
from ..knowledge.hazwaste_data import HW_DEFAULTS

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
    d = dict(HW_DEFAULTS)
    d.update(p or {})
    return d


# ══════════════════════════════════════════════════════════
#  1. 平面分区图
# ══════════════════════════════════════════════════════════

def draw_hw_plan(msp, origin, p=None, scale=100.0,
                 label="危废暂存间平面分区图", tracker=None):
    """平面：分区货架/主通道/门口围堰/导流沟坡向收集池。"""
    p = _params(p)
    s = scale
    ox, oy = _r(*origin)
    L, W = p["room_L"], p["room_W"]
    cx, cy = ox + L / 2.0, oy + W / 2.0

    # 墙体轮廓（双线表墙厚）
    _rect(msp, ox, oy, ox + L, oy + W, "粗实线")
    t = p["wall_t"]
    _rect(msp, ox + t, oy + t, ox + L - t, oy + W - t, "细实线")

    # 大门（右墙）+ 门口围堰（门槛）
    _ln(msp, (ox + L, cy - 900), (ox + L, cy + 900), "细实线")
    _ln(msp, (ox + L - t, cy - 900), (ox + L - t - 300, cy - 900), "设备")
    _ln(msp, (ox + L - t, cy + 900), (ox + L - t - 300, cy + 900), "设备")
    _t(msp, f"大门+围堰高 {p['kerb_H']:.0f}", (ox + L + 3 * s, cy), 2.0 * s,
       align=ML, layer="文字", tracker=tracker)

    # 分区（n_zone 个，沿长边排）+ 货架
    nz = p["n_zone"]
    zone_L = (L - 2 * t - p["aisle_W"]) / nz
    for i in range(nz):
        zx0 = ox + t + i * (zone_L + p["aisle_W"] / (nz - 1) * 0) + \
              i * p["aisle_W"] * 0.5
        # 分区虚线框
        _rect(msp, zx0, oy + t + 300, zx0 + zone_L, oy + W - t - 300, "虚线")
        _t(msp, f"{i+1}#分区", (zx0 + zone_L / 2, oy + W - t - 800), 2.2 * s,
           align=MC, layer="文字", tracker=tracker)
        # 货架（区内 2 排）
        for r in range(2):
            ry = oy + t + 600 + r * (p["rack_W"] + 700)
            _rect(msp, zx0 + 300, ry, zx0 + 300 + p["rack_L"],
                  ry + p["rack_W"], "设备")
            # 危废桶（俯视圆）
            for b in range(3):
                _circle(msp, (zx0 + 300 + p["rack_L"] * (b + 0.5) / 3.0,
                              ry + p["rack_W"] / 2), 250, "细实线")
    _t(msp, "货架(桶装危废)", (ox + t + zone_L / 2, oy + t + 100), 2.0 * s,
       align=MC, layer="文字", tracker=tracker)

    # 导流沟（沿四周墙脚 + 主通道一侧）
    dw = p["ditch_W"]
    _ln(msp, (ox + t + dw, oy + t + dw), (ox + L - t - dw, oy + t + dw),
        "管道-污水")
    _ln(msp, (ox + t + dw, oy + t + dw), (ox + t + dw, oy + W - t - dw),
        "管道-污水")
    _t(msp, f"导流沟 {dw:.0f}×{p['ditch_D']:.0f} i={p['ditch_i']*100:.1f}%",
       (cx, oy + t + dw + 3 * s), 2.0 * s, align=MC, layer="文字",
       tracker=tracker)

    # 收集池（左下角，沟汇交处）
    sl, sw = p["sump_L"], p["sump_W"]
    _rect(msp, ox + t, oy + t, ox + t + sl, oy + t + sw, "设备")
    _ln(msp, (ox + t, oy + t), (ox + t + sl, oy + t + sw), "细实线")
    _ln(msp, (ox + t, oy + t + sw), (ox + t + sl, oy + t), "细实线")
    _t(msp, "收集池", (ox + t + sl / 2, oy + t + sw + 3 * s), 2.0 * s,
       align=MC, layer="文字", tracker=tracker)

    # 坡度箭头（沟向收集池）
    _tri(msp, (ox + t + dw + 800, oy + t + dw), (-1, 0), s * 0.5, "流向")

    _t(msp, f"{L:.0f}×{W:.0f}｜{nz} 分区｜渗透系数≤10⁻¹⁰cm/s",
       (cx, oy - 6 * s), 2.3 * s, align=MC, layer="文字", tracker=tracker)

    if label:
        _t(msp, label, (cx, oy + W + 6 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (ox + L, oy)


# ══════════════════════════════════════════════════════════
#  2. 防渗构造剖面图
# ══════════════════════════════════════════════════════════

def draw_hw_section(msp, origin, p=None, scale=100.0,
                    label="地坪防渗构造剖面图", tracker=None):
    """构造层（自上而下）：环氧面层/P8混凝土/HDPE膜/垫层/地基 + 导流沟断面。"""
    p = _params(p)
    s = scale
    ox, oy = _r(*origin)
    W = 7000.0

    # 构造层（自上而下绘制， exaggerate 厚度×100 便于出图）
    ep = p["epoxy_t"] * 100
    conc = p["concrete_t"] * 6
    hdpe = p["hdpe_t"] * 100
    base = p["base_t"] * 3
    y = oy + 2000

    layers = [
        (ep, "环氧地坪面层 3mm", "设备"),
        (conc, "P8 防渗混凝土 150mm", "粗实线"),
        (hdpe, "HDPE 膜 2mm", "设备"),
        (base, "级配碎石垫层 300mm", "细实线"),
    ]
    y_top = y + sum(h for h, _, _ in layers)
    yy = y_top
    for h, name, layer in layers:
        _rect(msp, ox, yy - h, ox + W, yy, layer)
        _t(msp, name, (ox + W + 3 * s, yy - h / 2), 2.0 * s, align=ML,
           layer="文字", tracker=tracker)
        yy -= h
    # 地基线
    _ln(msp, (ox, yy), (ox + W, yy), "细实线")
    for i in range(12):
        gx = ox + W * (i + 0.5) / 12.0
        _ln(msp, (gx - 150, yy), (gx + 150, yy - 200), "细实线")
    _t(msp, "夯实素土", (ox + W + 3 * s, yy - 100), 2.0 * s, align=ML,
       layer="文字", tracker=tracker)

    # 导流沟断面（左侧下凹）
    dw = p["ditch_W"] * 3
    dd = p["ditch_D"] * 3
    gx0 = ox + 600
    _rect(msp, gx0, y_top - dd, gx0 + dw, y_top - ep, "粗实线")
    _rect(msp, gx0 + 60, y_top - dd + 60, gx0 + dw - 60, y_top - ep,
          "细实线")
    _t(msp, f"导流沟 {p['ditch_W']:.0f}×{p['ditch_D']:.0f}(同防渗)",
       (gx0 + dw / 2, y_top + 4 * s), 2.0 * s, align=MC, layer="文字",
       tracker=tracker)
    # 沟篦子
    _ln(msp, (gx0, y_top - ep), (gx0 + dw, y_top - ep), "设备")

    # 墙角翻边（右侧上翻 150）
    _rect(msp, ox + W - 400, y_top, ox + W, y_top + 300, "设备")
    _t(msp, "墙角防渗翻边150", (ox + W - 200, y_top + 500), 2.0 * s, align=MC,
       layer="文字", tracker=tracker)

    if label:
        _t(msp, label, (ox + W / 2, yy - 8 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (ox + W, oy)


# ══════════════════════════════════════════════════════════
#  3. 收集池详图
# ══════════════════════════════════════════════════════════

def draw_hw_sump(msp, origin, p=None, scale=100.0,
                 label="导流沟及收集池详图", tracker=None):
    """收集池：围堰/导流沟汇入/液位/排污泵/防渗。"""
    p = _params(p)
    s = scale
    ox, oy = _r(*origin)
    sl, sw, sd = p["sump_L"], p["sump_W"], p["sump_D"]
    cx = ox + sl / 2.0

    # 池体剖面（下凹）
    _rect(msp, ox, oy, ox + sl, oy + sd, "粗实线")
    _rect(msp, ox + 150, oy + 150, ox + sl - 150, oy + sd - 100, "细实线")
    _t(msp, "防渗同地坪", (ox + sl + 3 * s, oy + sd * 0.6), 2.0 * s, align=ML,
       layer="文字", tracker=tracker)

    # 地坪线（池口两侧）
    _ln(msp, (ox - 2000, oy + sd), (ox, oy + sd), "粗实线")
    _ln(msp, (ox + sl, oy + sd), (ox + sl + 2000, oy + sd), "粗实线")

    # 导流沟（两侧汇入）
    dw = p["ditch_W"]
    for k in (-1, 1):
        gx = cx + k * (sl / 2.0 + 1200)
        _rect(msp, gx - dw / 2, oy + sd - p["ditch_D"], gx + dw / 2, oy + sd,
              "设备")
        _tri(msp, (gx - k * dw, oy + sd - p["ditch_D"] / 2), (-k, 0), s * 0.4,
             "流向")
    _t(msp, "导流沟汇入", (ox + sl + 3 * s, oy + sd - 100), 2.0 * s, align=ML,
       layer="文字", tracker=tracker)

    # 篦子盖板（池口）
    _ln(msp, (ox, oy + sd), (ox + sl, oy + sd), "设备")
    for i in range(6):
        gx = ox + sl * (i + 0.5) / 6.0
        _ln(msp, (gx, oy + sd), (gx, oy + sd - 80), "细实线")
    _t(msp, "钢篦盖板", (cx, oy + sd + 3 * s), 2.0 * s, align=MC, layer="文字",
       tracker=tracker)

    # 液位计（池壁）
    _ln(msp, (ox + 100, oy + 200), (ox + 100, oy + sd - 300), "细实线")
    _t(msp, "液位", (ox - 3 * s, oy + sd * 0.5), 2.0 * s, align=MR,
       layer="文字", tracker=tracker)

    # 排污泵（池底潜水泵）
    _circle(msp, (cx, oy + 350), 200, "设备")
    _ln(msp, (cx, oy + 550), (cx, oy + sd), "管道-污水")
    _ln(msp, (cx, oy + sd), (cx, oy + sd + 700), "管道-污水")
    _tri(msp, (cx, oy + sd + 900), (0, 1), s * 0.5, "流向")
    _t(msp, "潜污泵(事故转移)", (cx + 3 * s, oy + 400), 2.0 * s, align=ML,
       layer="文字", tracker=tracker)

    _t(msp, f"收集池 {sl:.0f}×{sw:.0f}×{sd:.0f}", (cx, oy - 5 * s), 2.3 * s,
       align=MC, layer="文字", tracker=tracker)

    if label:
        _t(msp, label, (cx, oy + sd + 11 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (cx, oy)


# ══════════════════════════════════════════════════════════
#  4. 通风系统图
# ══════════════════════════════════════════════════════════

def draw_hw_ventilation(msp, origin, p=None, scale=100.0,
                        label="通风净化系统图", tracker=None):
    """立面：下部百叶进风 → 上部排风 → 活性炭吸附 → 排气筒。"""
    p = _params(p)
    s = scale
    ox, oy = _r(*origin)
    L, H = p["room_L"], p["room_H"]
    cx = ox + L / 2.0

    # 房间立面
    _rect(msp, ox, oy, ox + L, oy + H, "粗实线")
    _t(msp, "危废暂存间", (cx, oy + H / 2), 2.5 * s, align=MC, layer="文字",
       tracker=tracker)

    # 下部进风百叶（左墙下部）
    _rect(msp, ox - 300, oy + 400, ox, oy + 1400, "设备")
    for j in range(4):
        _ln(msp, (ox - 300, oy + 500 + j * 220), (ox, oy + 500 + j * 220 + 100),
            "细实线")
    _tri(msp, (ox - 800, oy + 900), (1, 0), s * 0.6, "流向")
    _t(msp, "防雨百叶进风", (ox - 500, oy + 300), 2.0 * s, align=MC,
       layer="文字", tracker=tracker)

    # 室内气流（下进上出箭头）
    for k in (0.3, 0.7):
        _tri(msp, (ox + L * k, oy + H * 0.6), (0, 1), s * 0.5, "流向")

    # 排风口（右上部）→ 风管
    fd = p["vent_fan_dn"]
    _rect(msp, ox + L, oy + H - 1200, ox + L + 1500, oy + H - 1200 + fd,
          "管道-加药")
    _t(msp, f"排风管 Φ{fd:.0f}", (ox + L + 750, oy + H - 900), 2.0 * s,
       align=MC, layer="文字", tracker=tracker)

    # 活性炭吸附箱（屋顶）
    ax = ox + L + 1800
    _rect(msp, ax, oy + H - 1500, ax + 1200, oy + H - 500, "设备")
    for j in range(3):
        _ln(msp, (ax + 200, oy + H - 1300 + j * 250),
            (ax + 1000, oy + H - 1300 + j * 250), "细实线")
    _t(msp, "活性炭吸附箱", (ax + 600, oy + H - 300), 2.0 * s, align=MC,
       layer="文字", tracker=tracker)

    # 离心风机（吸附箱后）
    fx = ax + 2000
    _circle(msp, (fx, oy + H - 1000), 400, "设备")
    _circle(msp, (fx, oy + H - 1000), 150, "细实线")
    _t(msp, "离心风机(防爆)", (fx, oy + H - 500), 2.0 * s, align=MC,
       layer="文字", tracker=tracker)
    _ln(msp, (ax + 1200, oy + H - 1000), (fx - 400, oy + H - 1000),
        "管道-加药")

    # 排气筒（高出屋面）
    _rect(msp, fx + 500, oy + H - 1050, fx + 500 + fd, oy + H + 1200, "设备")
    _tri(msp, (fx + 500 + fd / 2, oy + H + 1500), (0, 1), s, "流向")
    _t(msp, "排气筒(高出屋面2m)", (fx + 500 + fd / 2, oy + H + 1700),
       2.0 * s, align=MC, layer="文字", tracker=tracker)

    _t(msp, f"换气次数≥{p['vent_rate']:.0f} 次/h｜负压运行",
       (cx, oy - 5 * s), 2.3 * s, align=MC, layer="文字", tracker=tracker)

    if label:
        _t(msp, label, (cx, oy - 11 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (cx, oy, oy + H + 1700)


# ══════════════════════════════════════════════════════════
#  5. 标识布置图
# ══════════════════════════════════════════════════════════

def draw_hw_signage(msp, origin, p=None, scale=100.0,
                    label="标识标牌布置图", tracker=None):
    """外墙：危废标志牌(门口)/分区牌/责任制度牌 + 图例。"""
    p = _params(p)
    s = scale
    ox, oy = _r(*origin)
    L, H = 9000.0, 3600.0
    cx = ox + L / 2.0

    # 外墙立面（门口面）
    _rect(msp, ox, oy, ox + L, oy + H, "细实线")
    # 大门
    _rect(msp, cx - 1200, oy, cx + 1200, oy + 2400, "设备")
    _ln(msp, (cx, oy), (cx, oy + 2400), "细实线")
    _t(msp, "大门", (cx, oy + 1200), 2.0 * s, align=MC, layer="文字",
       tracker=tracker)

    sw, sh = p["sign_W"], p["sign_H"]

    def _sign(x, y, name, warn=False):
        _rect(msp, x, y, x + sw, y + sh, "设备")
        if warn:
            # 警示三角
            _tri(msp, (x + sw / 2, y + sh * 0.7), (0, 1), s * 0.8, "设备")
        _t(msp, name, (x + sw / 2, y - 3 * s), 1.8 * s, align=MC,
           layer="文字", tracker=tracker)

    # 门左侧：危废警示标志（黄底黑图，三角）
    _sign(ox + 500, oy + 1200, "危险废物警示标志", warn=True)
    # 门右侧：贮存设施标志 + 责任牌
    _sign(cx + 1500, oy + 1200, "贮存设施标志牌")
    _sign(cx + 1500 + sw + 400, oy + 1200, "责任制度/台账")
    # 分区牌（左墙 3 块竖排）
    for i in range(p["n_zone"]):
        _sign(ox - 1200, oy + 600 + i * (sh + 400), f"{i+1}#分区标识")
    _t(msp, "分区牌(类别/代码)", (ox - 1200 + sw / 2, oy + 200), 2.0 * s,
       align=MC, layer="文字", tracker=tracker)

    # 底部说明
    _t(msp, "标识执行 GB 15562.2｜黄底黑字黑边框", (cx, oy - 6 * s),
       2.3 * s, align=MC, layer="文字", tracker=tracker)

    if label:
        _t(msp, label, (cx, oy + H + 5 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (cx, oy)
