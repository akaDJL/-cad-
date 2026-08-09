# -*- coding: utf-8 -*-
"""曝气生物滤池多视图制图 v1.0（HJ 2014、GB 50014、CECS 265）。

上向流 BAF 成套视图：外形总图(正立面)、纵剖面、滤板滤头平面、
反冲洗系统、曝气系统平面。所有几何参数以 dict 传入（默认取
knowledge.baf_data.BAF_DEFAULTS）——本模块只负责"画"，不负责"算"。

坐标单位 mm，scale=出图比例倒数(1:100 → 100)。图层沿用包内中文命名。
"""
from __future__ import annotations

import math

from ezdxf.enums import TextEntityAlignment

from ..utils import _r, _tri
from .annotate import _t
from ..knowledge.baf_data import BAF_DEFAULTS

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
    d = dict(BAF_DEFAULTS)
    d.update(p or {})
    return d


def _layers(p, oy):
    """构造分层标高（自池底 oy）：配水区/滤板/承托层/滤料/清水区。"""
    y0 = oy
    y1 = y0 + p["bottom_H"]                     # 配水区顶
    y2 = y1 + p["floor_t"]                      # 滤板顶
    y3 = y2 + p["gravel_H"]                     # 承托层顶
    y4 = y3 + p["media_H"]                      # 滤料顶
    y5 = y4 + p["clear_H"]                      # 清水区顶（水面）
    y6 = oy + p["pool_H"]                       # 池顶
    return dict(y0=y0, y1=y1, y2=y2, y3=y3, y4=y4, y5=y5, y6=y6)


# ══════════════════════════════════════════════════════════
#  1. 外形总图 — 正立面
# ══════════════════════════════════════════════════════════

def draw_baf_elevation(msp, origin, p=None, scale=100.0,
                       label="曝气生物滤池外形图", tracker=None):
    """正立面：池体/分层标注/进出水/反洗管口/曝气母管。"""
    p = _params(p)
    s = scale
    ox, oy = _r(*origin)
    L = p["pool_L"]
    v = _layers(p, oy)
    cx = ox + L / 2.0

    # 池体（U 形 + 顶盖走道线）
    _ln(msp, (ox, v["y0"]), (ox + L, v["y0"]), "池体-壁")
    _ln(msp, (ox, v["y0"]), (ox, v["y6"]), "池体-壁")
    _ln(msp, (ox + L, v["y0"]), (ox + L, v["y6"]), "池体-壁")
    _ln(msp, (ox, v["y6"]), (ox + L, v["y6"]), "细实线")

    # 分层线
    for k in ("y1", "y2", "y3", "y4"):
        _ln(msp, (ox, v[k]), (ox + L, v[k]), "细实线")
    _ln(msp, (ox, v["y5"]), (ox + L, v["y5"]), "池体-水")

    # 分层文字（右侧引注）
    notes = [("y1", "y0", "配水区"), ("y2", "y1", "滤板+滤头"),
             ("y3", "y2", "承托层"), ("y4", "y3", "陶粒滤料"),
             ("y5", "y4", "清水区")]
    for hi, lo, name in notes:
        _t(msp, name, (ox + L + 3 * s, (v[hi] + v[lo]) / 2), 2.0 * s,
           align=ML, layer="文字", tracker=tracker)

    # 进水（底部，上向流）
    idn = p["inlet_dn"]
    _rect(msp, ox - idn, v["y0"] + 200, ox, v["y0"] + 200 + idn, "设备")
    _tri(msp, (ox - idn - 3 * s, v["y0"] + 200 + idn / 2), (1, 0), s, "流向")
    _t(msp, f"进水 DN{idn:.0f}(下进)", (ox - idn / 2, v["y0"] + 100),
       2.0 * s, align=MC, layer="文字", tracker=tracker)

    # 出水（清水区顶部）
    odn = p["outlet_dn"]
    _rect(msp, ox + L, v["y5"] - 500, ox + L + odn, v["y5"] - 500 + odn,
          "设备")
    _tri(msp, (ox + L + odn + 3 * s, v["y5"] - 500 + odn / 2), (1, 0), s,
         "流向")
    _t(msp, f"出水 DN{odn:.0f}", (ox + L + odn / 2, v["y5"] + 3 * s),
       2.0 * s, align=MC, layer="文字", tracker=tracker)

    # 反洗排水（顶部另一侧，反洗时溢流）
    bdn = p["backwash_out_dn"]
    _rect(msp, ox - bdn, v["y5"] - 300, ox, v["y5"] - 300 + bdn, "设备")
    _t(msp, f"反洗排水 DN{bdn:.0f}", (ox - bdn / 2, v["y5"] + 3 * s),
       2.0 * s, align=MC, layer="文字", tracker=tracker)

    # 曝气母管（池侧上部进入，下到承托层下）
    adn = p["air_main_dn"]
    ax = ox + L + 2500
    _rect(msp, ax, v["y6"] - 800, ax + adn, v["y6"] - 800 + adn, "管道-加药")
    _ln(msp, (ax + adn / 2, v["y6"] - 800), (ax + adn / 2, v["y2"] + 400),
        "管道-加药")
    _ln(msp, (ax + adn / 2, v["y2"] + 400), (ox + L, v["y2"] + 400),
        "管道-加药")
    _t(msp, f"曝气母管 DN{adn:.0f}", (ax + adn / 2 + 3 * s, v["y6"] - 900),
       2.0 * s, align=ML, layer="文字", tracker=tracker)

    # 反洗水/气管口（底部侧面）
    _rect(msp, ox - 2000, v["y0"] + 800, ox, v["y0"] + 800 + 300, "管道-给水")
    _t(msp, f"反洗水 DN{p['bw_water_dn']:.0f}", (ox - 1000, v["y0"] + 1300),
       2.0 * s, align=MC, layer="文字", tracker=tracker)
    _rect(msp, ox - 2000, v["y0"] + 1400, ox, v["y0"] + 1400 + 250,
          "管道-加药")
    _t(msp, f"反洗气 DN{p['bw_air_dn']:.0f}", (ox - 1000, v["y0"] + 1900),
       2.0 * s, align=MC, layer="文字", tracker=tracker)

    if label:
        _t(msp, label, (cx, v["y0"] - 8 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (cx, v["y0"], v["y6"])


# ══════════════════════════════════════════════════════════
#  2. 纵剖面图
# ══════════════════════════════════════════════════════════

def draw_baf_section(msp, origin, p=None, scale=100.0,
                     label="1-1 剖面图", tracker=None):
    """纵剖面：分层构造 + 长柄滤头 + 曝气器 + 上向水流。"""
    p = _params(p)
    s = scale
    ox, oy = _r(*origin)
    W = p["pool_W"]
    v = _layers(p, oy)
    cx = ox + W / 2.0

    # 池壁剖切
    _ln(msp, (ox, v["y0"]), (ox + W, v["y0"]), "池体-壁")
    _ln(msp, (ox, v["y0"]), (ox, v["y6"]), "池体-壁")
    _ln(msp, (ox + W, v["y0"]), (ox + W, v["y6"]), "池体-壁")

    # 滤板（剖面矩形带）+ 长柄滤头（均布）
    _rect(msp, ox, v["y1"], ox + W, v["y2"], "设备")
    n_nz = 7
    for i in range(n_nz):
        nx = ox + W * (i + 0.5) / n_nz
        _ln(msp, (nx, v["y1"] - 150), (nx, v["y2"] + 100), "设备")
        _rect(msp, nx - 60, v["y2"] + 100, nx + 60, v["y2"] + 220, "设备")
    _t(msp, "长柄滤头", (ox + W + 3 * s, v["y2"] + 150), 2.0 * s, align=ML,
       layer="文字", tracker=tracker)

    # 承托层（点阵）
    for j in range(2):
        for i in range(12):
            gx = ox + W * (i + 0.5) / 12.0
            gy = v["y2"] + p["gravel_H"] * (j + 0.5) / 2.0
            _circle(msp, (gx, gy), 40, "细实线")
    # 滤料层（密点阵）
    for j in range(4):
        for i in range(12):
            gx = ox + W * (i + 0.5) / 12.0
            gy = v["y3"] + p["media_H"] * (j + 0.5) / 4.0
            _circle(msp, (gx, gy), 30, "细实线")
    _t(msp, "陶粒滤料 Φ3~5", (cx, v["y3"] + p["media_H"] * 0.6), 2.0 * s,
       align=MC, layer="文字", tracker=tracker)

    # 曝气器（承托层下缘，3 个膜片曝气头）
    for k in (0.25, 0.5, 0.75):
        ax = ox + W * k
        _circle(msp, (ax, v["y2"] + 120), 90, "设备")
        for j in range(3):
            _circle(msp, (ax, v["y2"] + 350 + j * 300), 25, "细实线")
    _t(msp, "曝气器(承托层下)", (ox - 3 * s, v["y2"] + 250), 2.0 * s,
       align=MR, layer="文字", tracker=tracker)

    # 分层界线 + 水面
    for k in ("y1", "y3", "y4"):
        _ln(msp, (ox, v[k]), (ox + W, v[k]), "细实线")
    _ln(msp, (ox, v["y5"]), (ox + W, v["y5"]), "池体-水")

    # 上向水流箭头
    for k in (0.3, 0.7):
        _tri(msp, (ox + W * k, v["y4"] - 200), (0, 1), s * 0.5, "流向")

    if label:
        _t(msp, label, (cx, v["y0"] - 8 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (cx, v["y0"], v["y6"])


# ══════════════════════════════════════════════════════════
#  3. 滤板滤头平面布置图
# ══════════════════════════════════════════════════════════

def draw_baf_filter_floor(msp, origin, p=None, scale=100.0,
                          label="滤板滤头平面布置图", tracker=None):
    """俯视：滤板分格 + 长柄滤头阵 + 接缝。"""
    p = _params(p)
    s = scale
    ox, oy = _r(*origin)
    L, W = p["pool_L"], p["pool_W"]
    cx, cy = ox + L / 2.0, oy + W / 2.0

    # 池内轮廓
    _rect(msp, ox, oy, ox + L, oy + W, "池体-壁")

    # 滤板分格（980×980 预制板）
    board = 980.0
    nx = max(1, int(L / board))
    ny = max(1, int(W / board))
    for i in range(1, nx):
        _ln(msp, (ox + L * i / nx, oy), (ox + L * i / nx, oy + W), "细实线")
    for j in range(1, ny):
        _ln(msp, (ox, oy + W * j / ny), (ox + L, oy + W * j / ny), "细实线")

    # 滤头阵（每格内按间距布置，示意每格 3×3）
    pitch = p["nozzle_pitch"]
    step_x = L / nx / 3.0
    step_y = W / ny / 3.0
    for bi in range(nx):
        for bj in range(ny):
            bx0 = ox + L * bi / nx
            by0 = oy + W * bj / ny
            for i in range(3):
                for j in range(3):
                    hx = bx0 + step_x * (i + 0.5)
                    hy = by0 + step_y * (j + 0.5)
                    _circle(msp, (hx, hy), 30, "设备")

    # 中心线
    _ln(msp, (ox - 3 * s, cy), (ox + L + 3 * s, cy), "点画线",
        linetype="CENTER")
    _ln(msp, (cx, oy - 3 * s), (cx, oy + W + 3 * s), "点画线",
        linetype="CENTER")

    _t(msp, f"滤板 {nx}×{ny} 格｜长柄滤头 {pitch:.0f} 间距（49只/m²）",
       (cx, oy - 6 * s), 2.3 * s, align=MC, layer="文字", tracker=tracker)

    if label:
        _t(msp, label, (cx, oy + W + 6 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (ox + L, oy)


# ══════════════════════════════════════════════════════════
#  4. 反冲洗系统图
# ══════════════════════════════════════════════════════════

def draw_baf_backwash(msp, origin, p=None, scale=100.0,
                      label="反冲洗系统图", tracker=None):
    """系统图：反洗水泵/反洗风机 → 滤池底部；排水至前端。"""
    p = _params(p)
    s = scale
    ox, oy = _r(*origin)
    W = 10500.0
    H = 4200.0

    # 滤池（右）
    _rect(msp, ox + 7500, oy + 600, ox + 9500, oy + 3800, "设备")
    _t(msp, "BAF滤池", (ox + 8500, oy + 2200), 2.2 * s, align=MC,
       layer="文字", tracker=tracker)
    # 滤料层线
    _ln(msp, (ox + 7550, oy + 2600), (ox + 9450, oy + 2600), "细实线")
    _t(msp, "滤料", (ox + 8500, oy + 3000), 1.8 * s, align=MC, layer="文字",
       tracker=tracker)

    # 反洗水泵（左下，2 台）
    for k in (0, 1):
        _circle(msp, (ox + 1200 + k * 900, oy + 700), 260, "设备")
    _t(msp, "反洗水泵(1用1备)", (ox + 1650, oy + 300), 2.0 * s, align=MC,
       layer="文字", tracker=tracker)
    # 水源：清水池（最左）
    _rect(msp, ox - 600, oy + 1200, ox + 300, oy + 2600, "设备")
    _t(msp, "清水池", (ox - 150, oy + 1900), 1.8 * s, align=MC, layer="文字",
       tracker=tracker)
    _ln(msp, (ox + 300, oy + 700), (ox + 940, oy + 700), "管道-给水")
    _ln(msp, (ox + 2100, oy + 700), (ox + 2600, oy + 700), "管道-给水")
    # 水 → 滤池底部
    _ln(msp, (ox + 2600, oy + 700), (ox + 8500, oy + 700), "管道-给水")
    _ln(msp, (ox + 8500, oy + 700), (ox + 8500, oy + 600), "管道-给水")
    _rect(msp, ox + 5000, oy + 550, ox + 5300, oy + 850, "阀门")
    _t(msp, f"水洗 {p['bw_water_q']:.0f} L/m²·s", (ox + 5150, oy + 1100),
       2.0 * s, align=MC, layer="文字", tracker=tracker)

    # 反洗风机（中部，罗茨 2 台）
    for k in (0, 1):
        _rect(msp, ox + 3400 + k * 1100, oy + 1800, ox + 3400 + k * 1100 + 800,
              oy + 2600, "设备")
    _t(msp, "反洗罗茨风机(1用1备)", (ox + 3950, oy + 1500), 2.0 * s,
       align=MC, layer="文字", tracker=tracker)
    _ln(msp, (ox + 3950, oy + 2600), (ox + 3950, oy + 3300), "管道-加药")
    _ln(msp, (ox + 3950, oy + 3300), (ox + 8300, oy + 3300), "管道-加药")
    _ln(msp, (ox + 8300, oy + 3300), (ox + 8300, oy + 600), "管道-加药")
    _rect(msp, ox + 6000, oy + 3150, ox + 6300, oy + 3450, "阀门")
    _t(msp, f"气洗 {p['bw_air_q']:.0f} L/m²·s", (ox + 6150, oy + 3700),
       2.0 * s, align=MC, layer="文字", tracker=tracker)

    # 反洗排水（池顶 → 前端集水井，虚线）
    _ln(msp, (ox + 9500, oy + 3600), (ox + 10200, oy + 3600), "管道-污水")
    _tri(msp, (ox + 10300, oy + 3600), (1, 0), s * 0.5, "流向")
    _t(msp, "反洗排水回前端", (ox + 10150, oy + 3900), 2.0 * s, align=MC,
       layer="文字", tracker=tracker)

    _t(msp, "程序：气洗→气水联合→水洗，周期 24~48h",
       (ox + W / 2, oy - 4 * s), 2.3 * s, align=MC, layer="文字",
       tracker=tracker)

    if label:
        _t(msp, label, (ox + W / 2, oy + H + 5 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (ox + W, oy)


# ══════════════════════════════════════════════════════════
#  5. 曝气系统平面图
# ══════════════════════════════════════════════════════════

def draw_baf_aeration(msp, origin, p=None, scale=100.0,
                      label="曝气系统平面图", tracker=None):
    """俯视：曝气母管环廊 + 支管 + 曝气器阵列。"""
    p = _params(p)
    s = scale
    ox, oy = _r(*origin)
    L, W = p["pool_L"], p["pool_W"]
    cx, cy = ox + L / 2.0, oy + W / 2.0

    # 池轮廓
    _rect(msp, ox, oy, ox + L, oy + W, "池体-壁")

    # 曝气母管（左侧进入，沿短边）
    _ln(msp, (ox - 1500, cy), (ox, cy), "管道-加药")
    _t(msp, f"曝气母管 DN{p['air_main_dn']:.0f}", (ox - 1500, cy + 4 * s),
       2.0 * s, align=ML, layer="文字", tracker=tracker)
    _ln(msp, (ox, cy), (ox, oy + 300), "管道-加药")
    _ln(msp, (ox, cy), (ox, oy + W - 300), "管道-加药")

    # 支管（沿长边均布，鱼刺状）
    pitch = p["diffuser_pitch"]
    n_br = int(W / (pitch * 2))
    for i in range(n_br):
        by = oy + W * (i + 0.5) / n_br
        _ln(msp, (ox, by), (ox + L - 300, by), "管道-加药")
        # 曝气器（沿支管）
        n_df = int(L / pitch) - 1
        for j in range(1, n_df + 1):
            dx = ox + j * pitch
            _circle(msp, (dx, by), 60, "设备")
            _circle(msp, (dx, by), 20, "细实线")

    _t(msp, f"支管 {n_br} 根｜曝气器间距 {pitch:.0f}（膜片曝气头）",
       (cx, oy - 6 * s), 2.3 * s, align=MC, layer="文字", tracker=tracker)

    if label:
        _t(msp, label, (cx, oy + W + 6 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (ox + L, oy)
