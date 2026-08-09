# -*- coding: utf-8 -*-
"""SCR 脱硝反应器多视图制图 v1.0（HJ 562、HJ 563、GB/T 21509）。

高灰布置 SCR 成套视图：外形总图(正立面)、纵剖面、催化剂层平面、
喷氨格栅(AIG)、吹灰系统。所有几何参数以 dict 传入（默认取
knowledge.scr_data.SCR_DEFAULTS）——本模块只负责"画"，不负责"算"。

坐标单位 mm，scale=出图比例倒数(1:100 → 100)。图层沿用包内中文命名。
"""
from __future__ import annotations

import math

from ezdxf.enums import TextEntityAlignment

from ..utils import _r, _tri
from .annotate import _t
from ..knowledge.scr_data import SCR_DEFAULTS

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
    d = dict(SCR_DEFAULTS)
    d.update(p or {})
    return d


def _vert(p):
    """竖向分段（相对 origin 底部 oy）：支腿 | 底部支撑 | 催化剂层组 | 导流段。"""
    leg = p["leg_H"]
    sup = p["support_H"]
    n_tot = p["n_catalyst"] + p["n_spare"]
    cat_H = n_tot * p["catalyst_H"] + (n_tot - 1) * p["catalyst_gap"]
    guide = p["guide_H"]
    y0 = 0.0
    y1 = y0 + leg            # 反应器壳体底
    y2 = y1 + sup            # 首层催化剂底
    y3 = y2 + cat_H          # 顶层催化剂顶
    y4 = y3 + guide          # 壳体顶
    return dict(y0=y0, y1=y1, y2=y2, y3=y3, y4=y4)


# ══════════════════════════════════════════════════════════
#  1. 外形总图 — 正立面
# ══════════════════════════════════════════════════════════

def draw_scr_elevation(msp, origin, p=None, scale=100.0,
                       label="SCR脱硝反应器外形图", tracker=None):
    """正立面：支腿/反应器本体/进出口烟道(竖进竖出)/吹灰器/检修门。"""
    p = _params(p)
    s = scale
    ox, oy = _r(*origin)
    W = p["reactor_W"]
    D = p["reactor_D"]
    v = _vert(p)
    y0, y1, y2, y3, y4 = (oy + v[k] for k in ("y0", "y1", "y2", "y3", "y4"))
    cx = ox + W / 2.0

    # 地面线 + 支腿
    _ln(msp, (ox - 3 * s, y0), (ox + W + 3 * s, y0), "细实线")
    leg_off = 400.0
    for lx in (ox + leg_off, ox + W - leg_off, cx):
        _ln(msp, (lx, y0), (lx, y1), "设备")

    # 反应器壳体
    _rect(msp, ox, y1, ox + W, y4, "设备")

    # 催化剂层（横线 + 层标记）
    n_tot = p["n_catalyst"] + p["n_spare"]
    yy = y2
    for i in range(n_tot):
        _ln(msp, (ox, yy), (ox + W, yy), "设备")
        name = f"催化剂层{i+1}" if i < p["n_catalyst"] else "备用层"
        _t(msp, name, (ox + W + 3 * s, yy + p["catalyst_H"] / 2), 2.0 * s,
           align=ML, layer="文字", tracker=tracker)
        # 层内模块示意（竖向密线）
        for j in range(8):
            mx = ox + W * (j + 0.5) / 8.0
            _ln(msp, (mx, yy + 100), (mx, yy + p["catalyst_H"] - 100), "细实线")
        yy += p["catalyst_H"]
        if i < n_tot - 1:
            _ln(msp, (ox, yy), (ox + W, yy), "细实线")  # 层间吹灰空间
            yy += p["catalyst_gap"]
    _ln(msp, (ox, y3), (ox + W, y3), "设备")

    # 整流格栅（导流段下部）
    _ln(msp, (ox, y3 + p["guide_H"] * 0.4), (ox + W, y3 + p["guide_H"] * 0.4),
        "细实线")
    _t(msp, "整流格栅", (ox - 3 * s, y3 + p["guide_H"] * 0.4), 2.0 * s,
       align=MR, layer="文字", tracker=tracker)

    # 进口烟道（顶部竖进，渐扩）
    iw = D * 0.6
    _rect(msp, cx - iw / 2, y4, cx + iw / 2, y4 + 1200, "设备")
    _rect(msp, cx - iw * 0.3, y4 + 1200, cx + iw * 0.3, y4 + 2400, "设备")
    _tri(msp, (cx, y4 + 2700), (0, -1), s, "流向")
    _t(msp, "烟气进口(竖进)", (cx + iw / 2 + 3 * s, y4 + 1500), 2.0 * s,
       align=ML, layer="文字", tracker=tracker)

    # 出口烟道（底部侧出，渐缩）
    oh = D * 0.5
    _rect(msp, ox - 1500, y1 + 200, ox, y1 + 200 + oh, "设备")
    _tri(msp, (ox - 1800, y1 + 200 + oh / 2), (-1, 0), s, "流向")
    _t(msp, "烟气出口", (ox - 900, y1 - 3 * s), 2.0 * s, align=MC,
       layer="文字", tracker=tracker)

    # 吹灰器（侧面，每层 1 台）
    for i in range(n_tot):
        by = y2 + i * (p["catalyst_H"] + p["catalyst_gap"]) + p["catalyst_H"] / 2
        _rect(msp, ox - 500, by - 150, ox, by + 150, "设备")
    _t(msp, "吹灰器", (ox - 550, y2 + p["catalyst_H"] / 2), 2.0 * s, align=MR,
       layer="文字", tracker=tracker)

    # 检修门（首层催化剂处）
    _rect(msp, cx - 350, y2 + 100, cx + 350, y2 + 1000, "细实线")
    _t(msp, "检修门", (cx, y2 + 550), 2.0 * s, align=MC, layer="文字",
       tracker=tracker)

    if label:
        _t(msp, label, (cx, y0 - 8 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (cx, y0, y4 + 2400)


# ══════════════════════════════════════════════════════════
#  2. 纵剖面图
# ══════════════════════════════════════════════════════════

def draw_scr_section(msp, origin, p=None, scale=100.0,
                     label="1-1 剖面图", tracker=None):
    """纵剖面：导流板/整流格栅/催化剂层内部/支撑格栅/灰斗。"""
    p = _params(p)
    s = scale
    ox, oy = _r(*origin)
    W = p["reactor_W"]
    v = _vert(p)
    y1, y2, y3, y4 = (oy + v[k] for k in ("y1", "y2", "y3", "y4"))
    cx = ox + W / 2.0

    # 壳体剖切轮廓
    _rect(msp, ox, y1, ox + W, y4, "设备")

    # 顶部导流板（斜置 3 块）
    for k in (0.25, 0.5, 0.75):
        gx = ox + W * k
        _ln(msp, (gx - 400, y4 - 100), (gx + 400, y4 - 700), "设备")
    _t(msp, "导流板", (ox + W * 0.75 + 600, y4 - 400), 2.0 * s, align=ML,
       layer="文字", tracker=tracker)

    # 整流格栅（网格示意）
    gy = y3 + p["guide_H"] * 0.4
    _rect(msp, ox, gy - 150, ox + W, gy + 150, "细实线")
    for j in range(12):
        mx = ox + W * (j + 0.5) / 12.0
        _ln(msp, (mx, gy - 150), (mx, gy + 150), "细实线")

    # 催化剂层（剖面内模块边框 + 蜂窝孔示意）
    n_tot = p["n_catalyst"] + p["n_spare"]
    yy = y2
    for i in range(n_tot):
        _rect(msp, ox, yy, ox + W, yy + p["catalyst_H"], "设备")
        # 支撑格栅
        _ln(msp, (ox, yy), (ox + W, yy), "设备")
        for j in range(10):
            mx = ox + W * (j + 0.5) / 10.0
            _ln(msp, (mx, yy), (mx, yy + 200), "细实线")
        yy += p["catalyst_H"] + (p["catalyst_gap"] if i < n_tot - 1 else 0)

    # 底部支撑梁
    for k in (0.2, 0.5, 0.8):
        _rect(msp, ox + W * k - 100, y1, ox + W * k + 100, y2, "设备")
    _t(msp, "支撑梁", (ox + W * 0.5, (y1 + y2) / 2), 2.0 * s, align=MC,
       layer="文字", tracker=tracker)

    if label:
        _t(msp, label, (cx, oy - 8 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (cx, oy, y4)


# ══════════════════════════════════════════════════════════
#  3. 催化剂层平面布置图
# ══════════════════════════════════════════════════════════

def draw_scr_catalyst(msp, origin, p=None, scale=100.0,
                      label="催化剂层平面布置图", tracker=None):
    """俯视单层：模块阵(1910×970) + 密封条 + 中心线 + 吊装孔。"""
    p = _params(p)
    s = scale
    ox, oy = _r(*origin)
    W = p["reactor_W"]
    D = p["reactor_D"]
    ml, mw = p["module_L"], p["module_W"]
    gap = p["module_gap"]

    # 反应器内壁
    _rect(msp, ox, oy, ox + W, oy + D, "设备")
    cx, cy = ox + W / 2.0, oy + D / 2.0
    _ln(msp, (ox - 3 * s, cy), (ox + W + 3 * s, cy), "点画线", linetype="CENTER")
    _ln(msp, (cx, oy - 3 * s), (cx, oy + D + 3 * s), "点画线", linetype="CENTER")

    # 模块阵（沿 W 方向排 ml，沿 D 方向排 mw）
    nx = max(1, int((W - 2 * gap) / (ml + gap)))
    ny = max(1, int((D - 2 * gap) / (mw + gap)))
    tot_w = nx * ml + (nx - 1) * gap
    tot_d = ny * mw + (ny - 1) * gap
    x0 = ox + (W - tot_w) / 2.0
    y0 = oy + (D - tot_d) / 2.0
    for j in range(ny):
        for i in range(nx):
            mx = x0 + i * (ml + gap)
            my = y0 + j * (mw + gap)
            _rect(msp, mx, my, mx + ml, my + mw, "细实线")
    # 周边密封条（双线）
    _rect(msp, x0 - gap * 2, y0 - gap * 2, x0 + tot_w + gap * 2,
          y0 + tot_d + gap * 2, "虚线")
    # 吊装孔（角落）
    _rect(msp, ox + 200, oy + D - 700, ox + 700, oy + D - 200, "设备")
    _t(msp, "吊装孔", (ox + 450, oy + D - 450), 1.8 * s, align=MC,
       layer="文字", tracker=tracker)

    _t(msp, f"模块 {ml:.0f}×{mw:.0f}｜{nx}×{ny}={nx*ny} 块｜周边密封",
       (cx, oy - 6 * s), 2.3 * s, align=MC, layer="文字", tracker=tracker)

    if label:
        _t(msp, label, (cx, oy + D + 6 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (ox + W, oy)


# ══════════════════════════════════════════════════════════
#  4. 喷氨格栅（AIG）平面图
# ══════════════════════════════════════════════════════════

def draw_scr_ammonia_grid(msp, origin, p=None, scale=100.0,
                          label="喷氨格栅平面布置图", tracker=None):
    """俯视：母管 + 分区支管 + 喷嘴阵 + 调节阀（每支管 1 只）。"""
    p = _params(p)
    s = scale
    ox, oy = _r(*origin)
    W = p["reactor_W"]
    D = p["reactor_D"]
    cx, cy = ox + W / 2.0, oy + D / 2.0

    # 烟道截面（矩形轮廓）
    _rect(msp, ox, oy, ox + W, oy + D, "设备")

    # 母管（左侧进入，沿 D 方向）
    _ln(msp, (ox - 1500, cy), (ox, cy), "管道-加药")
    _t(msp, f"氨/空混合气母管 Φ{p['aig_main_dn']:.0f}", (ox - 1500, cy + 4 * s),
       2.0 * s, align=ML, layer="文字", tracker=tracker)

    # 支管（垂直母管，沿 W 方向均布）+ 喷嘴
    pitch = p["aig_nozzle_pitch"]
    n_branch = max(2, int(D / pitch))
    for i in range(n_branch):
        by = oy + D * (i + 0.5) / n_branch
        _ln(msp, (ox, by), (ox + W, by), "管道-加药")
        # 调节阀（支管入口）
        _rect(msp, ox + 100, by - 120, ox + 340, by + 120, "阀门")
        # 喷嘴（向上 45° 短划示意）
        n_nz = int(W / pitch)
        for j in range(n_nz):
            nx = ox + W * (j + 0.5) / n_nz
            _ln(msp, (nx, by), (nx + 180, by + 180), "细实线")
    _t(msp, "每支管入口设调节阀", (ox + W + 3 * s, cy), 2.0 * s, align=ML,
       layer="文字", tracker=tracker)

    _t(msp, f"支管 {n_branch} 根｜喷嘴间距 {pitch:.0f}｜氨氮摩尔比偏差≤5%",
       (cx, oy - 6 * s), 2.3 * s, align=MC, layer="文字", tracker=tracker)

    if label:
        _t(msp, label, (cx, oy + D + 6 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (ox + W, oy)


# ══════════════════════════════════════════════════════════
#  5. 吹灰系统图
# ══════════════════════════════════════════════════════════

def draw_scr_sootblower(msp, origin, p=None, scale=100.0,
                        label="吹灰系统图", tracker=None):
    """蒸汽吹灰器(层间伸缩枪) + 声波吹灰器(顶部) 布置。"""
    p = _params(p)
    s = scale
    ox, oy = _r(*origin)
    W = 8000.0
    n_tot = p["n_catalyst"] + p["n_spare"]
    bay_H = 1400.0
    H = n_tot * bay_H + 1500.0
    cx = ox + W / 2.0

    # 反应器侧壁（简化）
    _rect(msp, ox, oy, ox + W, oy + H, "细实线")
    _t(msp, "反应器侧壁", (ox + 200, oy + H + 3 * s), 2.0 * s, align=ML,
       layer="文字", tracker=tracker)

    # 每层：蒸汽吹灰枪（左右对穿）+ 行程箭头
    for i in range(n_tot):
        by = oy + 800 + i * bay_H
        _ln(msp, (ox + 300, by), (ox + W - 300, by), "设备")
        _rect(msp, ox - 700, by - 150, ox + 300, by + 150, "设备")   # 左侧枪机
        _rect(msp, ox + W - 300, by - 150, ox + W + 700, by + 150, "设备")
        # 喷嘴（枪身）
        for j in range(6):
            nx = ox + 800 + j * (W - 1600) / 5.0
            _tri(msp, (nx, by + 120), (0, 1), s * 0.4, "细实线")
        _t(msp, f"{i+1}#层吹灰枪", (cx, by + 250), 1.8 * s, align=MC,
           layer="文字", tracker=tracker)

    # 声波吹灰器（顶部 2 台，喇叭朝下）
    for k in (0.3, 0.7):
        hx = ox + W * k
        hy = oy + H - 400
        _ln(msp, (hx - 250, hy), (hx - 100, hy - 500), "设备")
        _ln(msp, (hx + 250, hy), (hx + 100, hy - 500), "设备")
        _ln(msp, (hx - 250, hy), (hx + 250, hy), "设备")
    _t(msp, "声波吹灰器", (ox + W * 0.7 + 400, oy + H - 600), 2.0 * s,
       align=ML, layer="文字", tracker=tracker)

    _t(msp, f"吹灰方式：{p['sootblower']}",
       (cx, oy - 5 * s), 2.3 * s, align=MC, layer="文字", tracker=tracker)

    if label:
        _t(msp, label, (cx, oy + H + 8 * s), 3.2 * s, align=MC,
           layer="文字-标题", tracker=tracker)
    return (ox + W, oy)
