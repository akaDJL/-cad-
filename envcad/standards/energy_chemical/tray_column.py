"""板式塔（Tray Column）总图模块 —— 塔板 + 降液管。

依据标准
--------
* HG/T 21514—2014《钢制人孔和手孔》
* GB/T 150.1~150.4—2024《压力容器》（2024版替代2011版）
* GB/T 25198—2023《压力容器封头》
* JB/T 4712.3—2007 裙座
* NB/T 10557—2021《板式塔内件技术规范》（浮阀塔盘、筛板塔盘；原误引 HG/T 21523 为水平吊盖带颈平焊法兰人孔标准）

.. note::
   板间距、堰高、降液管面积比等 **工艺参数** 由塔盘水力学计算确定；
   envcad standards_kb.json 未收录这些数值，本模块默认值仅供绘图占位，
   见 ``# TODO: verify`` 标记。

坐标约定
--------
``(x, y)`` = **裙座底面中心**（基础顶面标高处）。
"""
from __future__ import annotations

import math
from typing import Optional

from ezdxf.enums import TextEntityAlignment

from envcad.standards import pid

from . import _common as C


def _tray(msp, x: float, y: float, Ri: float, scale: float,
          side: int, weir_h: float, downcomer_w: float,
          tray_type: str = "valve", n_holes: int = 12):
    """单块塔板：板面 + 溢流堰 + 降液管（side=+1 降液管在右，-1 在左）。

    tray_type: ``valve`` 浮阀 / ``sieve`` 筛孔 / ``bubble`` 泡罩
    """
    dx = downcomer_w
    # 板面（不含降液管占位）
    if side > 0:
        x0, x1 = x - Ri, x + Ri - dx
    else:
        x0, x1 = x - Ri + dx, x + Ri
    th = max(Ri * 0.05, C.P(1.0, scale))
    C.rect(msp, x0, y, x1, y + th, layer=C.L_MID)

    # 塔板开孔/浮阀示意（细实线）
    for i in range(n_holes):
        hx = x0 + (x1 - x0) * (i + 0.5) / n_holes
        if tray_type == "valve":
            msp.add_arc((hx, y + th), max(Ri * 0.035, C.P(0.8, scale)),
                        start_angle=0, end_angle=180,
                        dxfattribs={"layer": C.L_THIN})
        elif tray_type == "bubble":
            r = max(Ri * 0.04, C.P(0.9, scale))
            C.rect(msp, hx - r, y + th, hx + r, y + th + r * 1.6,
                   layer=C.L_THIN)
        else:  # sieve
            msp.add_line((hx, y), (hx, y + th),
                         dxfattribs={"layer": C.L_THIN})

    # 溢流堰（出口侧）
    wx = x1 if side > 0 else x0
    msp.add_line((wx, y + th), (wx, y + th + weir_h),
                 dxfattribs={"layer": C.L_THICK})
    # 降液管（竖直板，伸向下一块板）
    dcx = x + side * (Ri - dx)
    return dcx, th


def draw_tray_column(msp, x: float, y: float, scale: float = 50.0,
                     diameter: float = 1800.0,
                     n_trays: int = 12,
                     tray_spacing: float = 600.0,
                     tray_type: str = "valve",
                     weir_height: float = 50.0,
                     downcomer_ratio: float = 0.12,
                     straight_flange: float = 40.0,
                     wall_thickness: float = 10.0,
                     bottom_space: float = 2500.0,
                     top_space: float = 1800.0,
                     skirt_height: float = 2500.0,
                     feed_tray: int = 6,
                     manhole_dn: float = 500.0,
                     tag: str = "T-401",
                     name: str = "板式塔",
                     design_pressure: str = "0.4 MPa",
                     design_temp: str = "150 ℃",
                     material: str = "S30408",
                     with_dims: bool = True,
                     with_table: bool = True,
                     **params):
    """绘制板式塔正视总图（HG/T 21514 / NB/T 10557—2021《板式塔内件技术规范》/ GB/T 150）。

    参数
    ----
    n_trays         实际塔板数
    tray_spacing    板间距 mm
                    # TODO: verify against NB/T 10557—2021 与塔盘水力学计算，
                    #       常用 300~800mm，随塔径与操作工况变化
    tray_type       ``valve`` 浮阀 / ``sieve`` 筛板 / ``bubble`` 泡罩
    weir_height     出口堰高 mm（# TODO: verify，常用 25~80mm）
    downcomer_ratio 降液管宽度 / 塔内径，常用 0.10~0.15
    feed_tray       进料板序号（自下往上计数，1 起）

    返回 ``dict``：各塔板标高列表。
    """
    s = scale
    R = diameter / 2.0
    Ri = R - wall_thickness
    dc_w = diameter * downcomer_ratio

    shell_height = bottom_space + tray_spacing * (n_trays - 1) + top_space
    y_base = y
    y_bot_tan = y_base + skirt_height
    y_top_tan = y_bot_tan + shell_height
    head_h = R / 2.0
    y_top = y_top_tan + straight_flange + head_h
    y_bot = y_bot_tan - straight_flange - head_h

    C.centerline(msp, (x, y_bot - C.P(8, s)), (x, y_top + C.P(14, s)))

    # ── 塔体 ──
    for sgn in (-1, 1):
        msp.add_line((x + sgn * R, y_bot_tan), (x + sgn * R, y_top_tan),
                     dxfattribs={"layer": C.L_THICK})
        msp.add_line((x + sgn * Ri, y_bot_tan), (x + sgn * Ri, y_top_tan),
                     dxfattribs={"layer": C.L_THIN})
    C.ellipsoidal_head(msp, x, y_top_tan, diameter, "up", straight_flange)
    C.ellipsoidal_head(msp, x, y_bot_tan, diameter, "down", straight_flange)

    # ── 塔板（降液管左右交替，单溢流）──
    trays = []
    for i in range(n_trays):
        ty = y_bot_tan + bottom_space + tray_spacing * i
        side = 1 if i % 2 == 0 else -1
        dcx, th = _tray(msp, x, ty, Ri, s, side, weir_height, dc_w, tray_type)
        # 降液管板：从本板向下延伸到下一板上方（留出底隙）
        if i > 0:
            prev_y = y_bot_tan + bottom_space + tray_spacing * (i - 1)
            gap = weir_height * 0.7   # 降液管底隙 # TODO: verify (常取 20~40mm)
            msp.add_line((dcx, ty), (dcx, prev_y + th + gap),
                         dxfattribs={"layer": C.L_MID})
        trays.append(ty)

    # ── 塔釜液位 ──
    y_liq = y_bot_tan + bottom_space * 0.40
    msp.add_line((x - Ri, y_liq), (x + Ri, y_liq),
                 dxfattribs={"layer": C.L_PHANTOM})
    C.eng_text(msp, "NLL", (x + Ri - C.P(6, s), y_liq + C.P(2, s)), 2.5, s,
               layer=C.L_TEXT, align=TextEntityAlignment.MIDDLE_RIGHT)

    # ── 裙座 + 基础 ──
    C.skirt_support(msp, x, y_bot_tan - straight_flange - head_h * 0.35,
                    diameter, skirt_height - head_h * 0.65, scale=s)
    msp.add_line((x - R * 2.2, y_base), (x + R * 2.2, y_base),
                 dxfattribs={"layer": C.L_THICK})
    for i in range(11):
        gx = x - R * 2.1 + (R * 4.2) * i / 10.0
        msp.add_line((gx, y_base), (gx - C.P(3, s), y_base - C.P(3, s)),
                     dxfattribs={"layer": C.L_THIN})

    # ── 管口 ──
    nl = max(diameter * 0.18, 260.0)
    C.nozzle(msp, (x, y_top_tan + straight_flange + head_h), "up",
             max(diameter * 0.25, 200), nl, s, tag="a")   # 塔顶气相
    C.nozzle(msp, (x - R, y_top_tan - top_space * 0.4), "left",
             max(diameter * 0.09, 80), nl, s, tag="b")    # 回流
    if 1 <= feed_tray <= n_trays:
        fy = trays[feed_tray - 1] + tray_spacing * 0.35
        C.nozzle(msp, (x - R, fy), "left", max(diameter * 0.11, 100),
                 nl, s, tag="c")                          # 进料
    C.nozzle(msp, (x, y_bot_tan - straight_flange - head_h), "down",
             max(diameter * 0.11, 100), nl, s, tag="d")   # 塔釜采出
    C.nozzle(msp, (x + R, y_bot_tan + bottom_space * 0.72), "right",
             max(diameter * 0.15, 125), nl, s, tag="e")   # 再沸器返回

    if manhole_dn:
        for frac in (0.06, 0.55, 0.95):
            my = y_bot_tan + shell_height * frac
            C.manhole(msp, (x + R, my), "right", manhole_dn,
                      max(manhole_dn * 0.5, 250.0), s, tag="M")

    # ── 标注 ──
    if with_dims:
        C.dim_linear(msp, (x - R, y_bot_tan), (x + R, y_bot_tan),
                     offset=-8, scale=s, label=f"DN{int(diameter)}")
        if len(trays) >= 2:
            C.dim_linear(msp, (x - R, trays[0]), (x - R, trays[1]),
                         offset=24, scale=s, label=f"HT={int(tray_spacing)}")
            C.dim_linear(msp, (x - R, trays[0]), (x - R, trays[-1]),
                         offset=38, scale=s,
                         label=f"{n_trays - 1}×{int(tray_spacing)}"
                               f"={int(tray_spacing * (n_trays - 1))}")
        C.dim_linear(msp, (x - R, y_base), (x - R, y_top),
                     offset=54, scale=s, label=f"总高 {int(y_top - y_base)}")
        tt = {"valve": "浮阀塔盘", "sieve": "筛板塔盘",
              "bubble": "泡罩塔盘"}.get(tray_type, tray_type)
        C.leader_note(msp, (x, trays[len(trays) // 2] if trays else y_bot_tan),
                      f"{tt} 共{n_trays}块 堰高{int(weir_height)}",
                      s, dx=-32, dy=12)
        if 1 <= feed_tray <= n_trays:
            C.leader_note(msp, (x - R, trays[feed_tray - 1]),
                          f"第{feed_tray}块板 进料", s, dx=-24, dy=-10)
        C.elevation_mark(msp, (x + R * 1.6, y_base), "±0.000", s)

    C.eng_text(msp, tag, (x, y_top + C.P(11, s)), 5.0, s, layer=C.L_TITLE)
    C.text(msp, name, (x, y_top + C.P(5, s)), 3.5, s, layer=C.L_TITLE)

    if with_table:
        tt = {"valve": "F1 型浮阀", "sieve": "筛孔",
              "bubble": "泡罩"}.get(tray_type, tray_type)
        C.spec_table(msp, (x + R + C.P(58, s), y_top), [
            ["设计压力", design_pressure],
            ["设计温度", design_temp],
            ["塔体材质", material],
            ["公称直径", f"DN{int(diameter)}"],
            ["塔板数", f"{n_trays}"],
            ["板间距", f"{int(tray_spacing)} mm"],
            ["塔盘型式", tt],
        ], s, title="塔器数据表")

    return {"tag": tag, "trays": trays, "base": y_base,
            "bottom_tangent": y_bot_tan, "top_tangent": y_top_tan,
            "top": y_top, "radius": R}


def draw_tray_column_symbol(msp, x: float, y: float, scale: float = 50.0,
                            width: float = 18.0, height: float = 70.0,
                            tag: str = "T-401", name: str = "板式塔",
                            **params):
    """板式塔 P&ID 简化符号，复用 ``pid.draw_vessel(v_type="column")``。"""
    return pid.draw_vessel(msp, (x, y), v_type="column", width=width,
                           height=height, scale=scale, tag=tag, label=name,
                           layer=C.L_EQUIP)
