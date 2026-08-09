"""卧式储罐（Horizontal Tank）装配图模块。

依据标准
--------
* GB/T 150.1~150.4—2024《压力容器》——筒体、封头、开孔补强（2024版替代2011版，2025-02-01实施）
* GB/T 25198—2023《压力容器封头》——标准椭圆封头 2:1
* NB/T 47065.1—2018《容器支座 第 1 部分：鞍式支座》——包角 120°/150°
* HG/T 21514—2014《钢制人孔和手孔》
* HG/T 20592—2009《钢制管法兰》

坐标约定
--------
``(x, y)`` = 设备安装基准点，即 **鞍座底板底面中心**（基础顶面标高处）。
"""
from __future__ import annotations

import math
from typing import Optional, Sequence

from ezdxf.enums import TextEntityAlignment

from envcad.standards import pid

from . import _common as C

#: 默认管口配置
DEFAULT_NOZZLES: Sequence[dict] = (
    {"pos": "top", "dn": 150, "offset": -0.55, "tag": "a", "note": "进料口"},
    {"pos": "top", "dn": 80, "offset": 0.0, "tag": "b", "note": "放空口"},
    {"pos": "top", "dn": 500, "offset": 0.55, "tag": "M", "note": "人孔"},
    {"pos": "bottom", "dn": 150, "offset": 0.55, "tag": "c", "note": "出料口"},
    {"pos": "bottom", "dn": 50, "offset": -0.70, "tag": "d", "note": "排污口"},
)


def draw_horizontal_tank(msp, x: float, y: float, scale: float = 50.0,
                         diameter: float = 2000.0,
                         shell_length: float = 6000.0,
                         head_type: str = "ellipsoidal",
                         straight_flange: float = 40.0,
                         wall_thickness: float = 10.0,
                         saddle_height: float = 700.0,
                         saddle_span_ratio: float = 0.60,
                         saddle_wrap: float = 120.0,
                         nozzles: Optional[Sequence[dict]] = None,
                         with_level_gauge: bool = True,
                         liquid_level: float = 0.55,
                         tag: str = "V-201",
                         name: str = "卧式储罐",
                         design_pressure: str = "1.0 MPa",
                         design_temp: str = "100 ℃",
                         material: str = "Q345R",
                         medium: str = "工艺物料",
                         volume: str = "",
                         with_dims: bool = True,
                         with_table: bool = True,
                         **params):
    """绘制卧式储罐正视装配图（GB/T 150 / NB/T 47065.1）。

    参数
    ----
    diameter          筒体内直径 DN，mm
    shell_length      筒体直段长度（两切线间距），mm
    saddle_height     鞍座高度（筒体最低点到基础顶面），mm
    saddle_span_ratio 两鞍座中心距 / 筒体长度，工程常用 0.5~0.7
    saddle_wrap       鞍座包角，NB/T 47065.1 标准值 120°（重型 150°）
    nozzles           管口列表，``pos`` ∈ top/bottom/left/right，
                      top/bottom 的 ``offset`` 为相对筒体半长的归一化位置

    返回 ``dict``：关键几何坐标。
    """
    s = scale
    R = diameter / 2.0
    L = shell_length
    nozzles = list(nozzles) if nozzles is not None else list(DEFAULT_NOZZLES)

    y_base = y
    cy = y_base + saddle_height + R          # 筒体轴线标高
    x_l, x_r = x - L / 2.0, x + L / 2.0      # 两条切线

    head_d = (R / 2.0 if head_type == "ellipsoidal" else wall_thickness * 2)
    x_left_end = x_l - straight_flange - head_d
    x_right_end = x_r + straight_flange + head_d

    # ── 轴线 ──
    C.centerline(msp, (x_left_end, cy), (x_right_end, cy),
                 extend=C.P(10, s))

    # ── 筒体上下素线（双线表壁厚）──
    for sgn in (-1, 1):
        msp.add_line((x_l, cy + sgn * R), (x_r, cy + sgn * R),
                     dxfattribs={"layer": C.L_THICK})
        msp.add_line((x_l, cy + sgn * (R - wall_thickness)),
                     (x_r, cy + sgn * (R - wall_thickness)),
                     dxfattribs={"layer": C.L_THIN})

    # ── 封头 ──
    if head_type == "ellipsoidal":
        C.ellipsoidal_head(msp, x_r, cy, diameter, "right", straight_flange)
        C.ellipsoidal_head(msp, x_l, cy, diameter, "left", straight_flange)
    else:
        C.flat_head(msp, x_r, cy, diameter, wall_thickness * 2, "right")
        C.flat_head(msp, x_l, cy, diameter, wall_thickness * 2, "left")

    # ── 液位线 ──
    if liquid_level and 0 < liquid_level < 1:
        y_liq = cy - R + diameter * liquid_level
        half = math.sqrt(max(R * R - (y_liq - cy) ** 2, 0.0))
        msp.add_line((x_l - half * 0.0, y_liq), (x_r, y_liq),
                     dxfattribs={"layer": C.L_PHANTOM})
        C.eng_text(msp, "NLL", (x_r - C.P(6, s), y_liq + C.P(2, s)),
                   2.5, s, layer=C.L_TEXT,
                   align=TextEntityAlignment.MIDDLE_RIGHT)

    # ── 鞍座（NB/T 47065.1，两只，包角 120°）──
    span = L * saddle_span_ratio
    saddle_w = max(R * 1.8, diameter * 0.9)
    for sx in (x - span / 2.0, x + span / 2.0):
        C.saddle_support(msp, sx, cy, R, saddle_height, width=saddle_w,
                         scale=s, wrap_deg=saddle_wrap)

    # ── 基础地面线 ──
    gx0, gx1 = x_left_end - C.P(6, s), x_right_end + C.P(6, s)
    msp.add_line((gx0, y_base), (gx1, y_base), dxfattribs={"layer": C.L_THICK})
    n = 14
    for i in range(n + 1):
        gx = gx0 + (gx1 - gx0) * i / n
        msp.add_line((gx, y_base), (gx - C.P(3, s), y_base - C.P(3, s)),
                     dxfattribs={"layer": C.L_THIN})

    # ── 管口 ──
    noz_len = max(diameter * 0.15, 250.0)
    for nz in nozzles:
        pos = nz.get("pos", "top")
        dn = float(nz.get("dn", 100))
        off = float(nz.get("offset", 0.0))
        ntag = nz.get("tag", "")
        if pos in ("top", "bottom"):
            bx = x + off * (L / 2.0) * 0.9
            sgn = 1 if pos == "top" else -1
            by = cy + sgn * R
            if dn >= 400:   # 大口径按人孔画
                C.manhole(msp, (bx, by), pos, dn,
                          max(dn * 0.5, 250.0), s, tag=ntag)
            else:
                C.nozzle(msp, (bx, by), pos, dn, noz_len, s, tag=ntag)
        elif pos == "left":
            C.nozzle(msp, (x_left_end, cy + off * R * 0.6), "left", dn,
                     noz_len, s, tag=ntag)
        else:
            C.nozzle(msp, (x_right_end, cy + off * R * 0.6), "right", dn,
                     noz_len, s, tag=ntag)

    # ── 液位计 ──
    if with_level_gauge:
        C.level_gauge(msp, x_right_end, cy - R * 0.6, cy + R * 0.6,
                      scale=s, dn=max(diameter * 0.014, 25.0), tag="LG")

    # ── 标注 ──
    if with_dims:
        C.dim_linear(msp, (x_l, cy - R), (x_r, cy - R),
                     offset=30, scale=s, label=f"{int(L)}")
        C.dim_linear(msp, (x - span / 2, y_base), (x + span / 2, y_base),
                     offset=16, scale=s, label=f"鞍座中心距 {int(span)}")
        C.dim_linear(msp, (x_right_end, cy - R), (x_right_end, cy + R),
                     offset=-22, scale=s, label=f"DN{int(diameter)}")
        C.leader_note(msp, (x, cy + R), f"筒体 {material} δ={int(wall_thickness)}",
                      s, dx=22, dy=16)
        C.leader_note(msp, (x + span / 2, y_base + saddle_height * 0.4),
                      f"鞍座 包角{int(saddle_wrap)}° NB/T 47065.1",
                      s, dx=24, dy=-14)
        C.elevation_mark(msp, (x_left_end - C.P(4, s), y_base), "±0.000", s)

    # ── 位号与图名 ──
    C.eng_text(msp, tag, (x, cy + R + C.P(30, s)), 5.0, s, layer=C.L_TITLE)
    C.text(msp, name, (x, cy + R + C.P(24, s)), 3.5, s, layer=C.L_TITLE)

    if with_table:
        rows = [
            ["设计压力", design_pressure],
            ["设计温度", design_temp],
            ["筒体材质", material],
            ["公称直径", f"DN{int(diameter)}"],
            ["筒体长度", f"{int(L)}"],
            ["介质", medium],
        ]
        if volume:
            rows.append(["公称容积", volume])
        C.spec_table(msp, (x_right_end + C.P(30, s), cy + R + C.P(18, s)),
                     rows, s, title="设备数据表")

    return {
        "tag": tag, "axis_y": cy, "base": y_base,
        "left_tangent": x_l, "right_tangent": x_r,
        "left_end": x_left_end, "right_end": x_right_end, "radius": R,
    }


def draw_horizontal_tank_symbol(msp, x: float, y: float, scale: float = 50.0,
                                width: float = 46.0, height: float = 20.0,
                                tag: str = "V-201", name: str = "卧式储罐",
                                **params):
    """卧式储罐的 P&ID 简化符号。

    复用 :func:`envcad.standards.pid.draw_vessel` （``v_type="drum"``，卧式分离罐）。
    """
    return pid.draw_vessel(msp, (x, y), v_type="drum", width=width,
                           height=height, scale=scale, tag=tag, label=name,
                           layer=C.L_EQUIP)
