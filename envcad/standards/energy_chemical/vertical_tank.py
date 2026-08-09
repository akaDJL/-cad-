"""立式储罐（Vertical Tank）装配图模块。

依据标准
--------
* GB/T 150.1~150.4—2024《压力容器》——筒体、封头、开孔补强（2024版替代2011版）
* SH/T 3049—2018《石油化工立式圆筒形储罐地基基础设计规范》——基础与裙座
* GB/T 25198—2023《压力容器封头》——标准椭圆封头 2:1
* HG/T 21514—2014《钢制人孔和手孔》——人孔选型
* HG/T 20592—2009《钢制管法兰》——接管法兰

坐标约定
--------
``(x, y)`` = 设备安装基准点，即 **支座底面中心**（基础顶面标高处）。
所有尺寸参数均为 *实物 mm*，字高等制图要素为 *图纸 mm*。
"""
from __future__ import annotations

import math
from typing import List, Optional, Sequence

from ezdxf.enums import TextEntityAlignment

from envcad.standards import pid

from . import _common as C


def _head_rise(dx: float, D: float) -> float:
    """标准椭圆封头在偏离轴线 dx 处的曲面高度（GB/T 25198，h = D/4）。"""
    R = D / 2.0
    dx = max(-R, min(R, dx))
    return (D / 4.0) * math.sqrt(max(0.0, 1.0 - (dx / R) ** 2))


#: 默认管口配置：(位置, DN, 相对位置, 管口号, 说明)
DEFAULT_NOZZLES: Sequence[dict] = (
    {"pos": "top", "dn": 150, "offset": -0.45, "tag": "a", "note": "进料口"},
    {"pos": "top", "dn": 80, "offset": 0.45, "tag": "b", "note": "放空口"},
    {"pos": "bottom", "dn": 150, "offset": 0.0, "tag": "c", "note": "出料口"},
    {"pos": "right", "dn": 80, "offset": 0.80, "tag": "d", "note": "温度计口"},
    {"pos": "left", "dn": 50, "offset": 0.20, "tag": "e", "note": "排污口"},
)


def draw_vertical_tank(msp, x: float, y: float, scale: float = 50.0,
                       diameter: float = 2400.0,
                       shell_height: float = 5000.0,
                       head_type: str = "ellipsoidal",
                       straight_flange: float = 40.0,
                       wall_thickness: float = 10.0,
                       support: str = "skirt",
                       support_height: float = 1500.0,
                       nozzles: Optional[Sequence[dict]] = None,
                       manhole_dn: float = 500.0,
                       manhole_elev: float = 0.75,
                       with_level_gauge: bool = True,
                       liquid_level: float = 0.60,
                       tag: str = "V-101",
                       name: str = "立式储罐",
                       design_pressure: str = "0.6 MPa",
                       design_temp: str = "80 ℃",
                       material: str = "Q345R",
                       medium: str = "工艺物料",
                       volume: str = "",
                       with_dims: bool = True,
                       with_table: bool = True,
                       **params):
    """绘制立式储罐正视装配图（GB/T 150 / SH/T 3049）。

    参数
    ----
    diameter        筒体内直径 DN，mm
    shell_height    筒体直段高度，mm
    head_type       ``ellipsoidal`` 标准椭圆封头 / ``flat`` 平盖
    straight_flange 封头直边段高度，mm（GB/T 25198 按壁厚取 25/40/50）
    wall_thickness  筒体名义壁厚，mm（仅用于双线表达与标注）
    support         ``skirt`` 裙座 / ``leg`` 支腿 / ``lug`` 耳式支座
    support_height  支座高度，mm
    nozzles         管口列表 ``[{"pos","dn","offset","tag","note"}, ...]``
                    pos ∈ top/bottom/left/right；offset 为归一化位置
                    （top/bottom 相对半径，left/right 相对筒体高度）
    manhole_elev    人孔中心相对筒体高度的归一化位置（0~1）
    liquid_level    正常液位相对筒体高度的归一化位置（0~1）

    返回 ``dict``：关键几何标高，便于上层继续拼装管系。
    """
    s = scale
    R = diameter / 2.0
    nozzles = list(nozzles) if nozzles is not None else list(DEFAULT_NOZZLES)

    # ── 竖向定位 ──
    y_base = y                              # 支座底面（基础顶面）
    y_bot_tan = y_base + support_height     # 下封头与筒体切线
    y_top_tan = y_bot_tan + shell_height    # 上封头切线
    head_h = (R / 2.0 if head_type == "ellipsoidal" else wall_thickness * 2)
    y_top = y_top_tan + straight_flange + head_h
    y_bot = y_bot_tan - straight_flange - head_h

    # ── 轴线 ──
    C.centerline(msp, (x, y_bot - C.P(10, s)), (x, y_top + C.P(14, s)))

    # ── 筒体（双线表示壁厚）──
    msp.add_line((x - R, y_bot_tan), (x - R, y_top_tan),
                 dxfattribs={"layer": C.L_THICK})
    msp.add_line((x + R, y_bot_tan), (x + R, y_top_tan),
                 dxfattribs={"layer": C.L_THICK})
    for sgn in (-1, 1):
        xi = x + sgn * (R - wall_thickness)
        msp.add_line((xi, y_bot_tan), (xi, y_top_tan),
                     dxfattribs={"layer": C.L_THIN})

    # ── 封头（复用 _common 的 GB/T 25198 椭圆封头）──
    if head_type == "ellipsoidal":
        C.ellipsoidal_head(msp, x, y_top_tan, diameter, "up", straight_flange)
        C.ellipsoidal_head(msp, x, y_bot_tan, diameter, "down", straight_flange)
    else:
        C.flat_head(msp, x, y_top_tan, diameter, wall_thickness * 2, "up")
        C.flat_head(msp, x, y_bot_tan, diameter, wall_thickness * 2, "down")

    # ── 液位线（双点画线表示假想液面）──
    if liquid_level and 0 < liquid_level < 1:
        y_liq = y_bot_tan + shell_height * liquid_level
        msp.add_line((x - R + wall_thickness, y_liq),
                     (x + R - wall_thickness, y_liq),
                     dxfattribs={"layer": C.L_PHANTOM})
        C.eng_text(msp, "NLL", (x + R - C.P(6, s), y_liq + C.P(2, s)),
                   2.5, s, layer=C.L_TEXT,
                   align=TextEntityAlignment.MIDDLE_RIGHT)

    # ── 支座 ──
    if support == "skirt":
        C.skirt_support(msp, x, y_bot_tan - straight_flange - head_h * 0.35,
                        diameter, support_height - head_h * 0.65, scale=s)
    elif support == "leg":
        C.support_legs(msp, x, y_bot_tan, diameter, support_height, scale=s)
    else:
        C.lug_support(msp, x, y_bot_tan + shell_height * 0.55, R, scale=s)

    # ── 基础地面线 ──
    msp.add_line((x - R * 2.0, y_base), (x + R * 2.0, y_base),
                 dxfattribs={"layer": C.L_THICK})
    for i in range(9):
        gx = x - R * 1.9 + (R * 3.8) * i / 8.0
        msp.add_line((gx, y_base), (gx - C.P(3, s), y_base - C.P(3, s)),
                     dxfattribs={"layer": C.L_THIN})

    # ── 管口 ──
    noz_len = max(diameter * 0.13, 250.0)
    for nz in nozzles:
        pos = nz.get("pos", "top")
        dn = float(nz.get("dn", 100))
        off = float(nz.get("offset", 0.0))
        ntag = nz.get("tag", "")
        if pos == "top":
            bx = x + off * R * 0.9
            by = y_top_tan + straight_flange + _head_rise(bx - x, diameter)
            C.nozzle(msp, (bx, by), "up", dn, noz_len, s, tag=ntag)
        elif pos == "bottom":
            bx = x + off * R * 0.9
            by = y_bot_tan - straight_flange - _head_rise(bx - x, diameter)
            C.nozzle(msp, (bx, by), "down", dn, noz_len, s, tag=ntag)
        elif pos == "left":
            by = y_bot_tan + shell_height * min(max(off, 0.05), 0.95)
            C.nozzle(msp, (x - R, by), "left", dn, noz_len, s, tag=ntag)
        else:
            by = y_bot_tan + shell_height * min(max(off, 0.05), 0.95)
            C.nozzle(msp, (x + R, by), "right", dn, noz_len, s, tag=ntag)

    # ── 人孔（HG/T 21514）──
    if manhole_dn:
        y_mh = y_bot_tan + shell_height * manhole_elev
        C.manhole(msp, (x + R, y_mh), "right", manhole_dn,
                  max(manhole_dn * 0.5, 250.0), s, tag="M")

    # ── 液位计（HG 21592-1995）──
    if with_level_gauge:
        C.level_gauge(msp, x - R,
                      y_bot_tan + shell_height * 0.25,
                      y_bot_tan + shell_height * 0.85,
                      scale=s, dn=max(diameter * 0.012, 25.0), tag="LG")

    # ── 尺寸标注 ──
    if with_dims:
        C.dim_linear(msp, (x - R, y_bot_tan), (x + R, y_bot_tan),
                     offset=-6, scale=s, label=f"DN{int(diameter)}")
        C.dim_linear(msp, (x - R, y_bot_tan), (x - R, y_top_tan),
                     offset=26, scale=s, label=f"{int(shell_height)}")
        C.dim_linear(msp, (x - R, y_base), (x - R, y_top),
                     offset=42, scale=s, label=f"H={int(y_top - y_base)}")
        C.leader_note(msp, (x + R, y_bot_tan + shell_height * 0.35),
                      f"筒体 {material} δ={int(wall_thickness)}", s,
                      dx=26, dy=14)
        C.elevation_mark(msp, (x + R * 1.35, y_base), "±0.000", s)

    # ── 位号与图名 ──
    C.eng_text(msp, tag, (x, y_top + C.P(11, s)), 5.0, s, layer=C.L_TITLE)
    C.text(msp, name, (x, y_top + C.P(5, s)), 3.5, s, layer=C.L_TITLE)

    # ── 设备数据表 ──
    if with_table:
        rows = [
            ["设计压力", design_pressure],
            ["设计温度", design_temp],
            ["筒体材质", material],
            ["公称直径", f"DN{int(diameter)}"],
            ["介质", medium],
        ]
        if volume:
            rows.append(["公称容积", volume])
        C.spec_table(msp, (x + R + C.P(52, s), y_top),
                     rows, s, title="设备数据表")

    return {
        "tag": tag, "base": y_base,
        "bottom_tangent": y_bot_tan, "top_tangent": y_top_tan,
        "top": y_top, "bottom": y_bot, "radius": R,
    }


def draw_vertical_tank_symbol(msp, x: float, y: float, scale: float = 50.0,
                              width: float = 26.0, height: float = 42.0,
                              tag: str = "V-101", name: str = "立式储罐",
                              **params):
    """立式储罐的 P&ID 简化符号。

    直接复用 :func:`envcad.standards.pid.draw_vessel` （``v_type="tank"``），
    width/height 为 *图纸 mm*。依据 GB/T 2625—1981 / ISA S5.1。
    """
    return pid.draw_vessel(msp, (x, y), v_type="tank", width=width,
                           height=height, scale=scale, tag=tag, label=name,
                           layer=C.L_EQUIP)
