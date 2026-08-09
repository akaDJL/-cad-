"""反应釜（Reactor Vessel）装配图模块 —— 搅拌器 + 夹套。

依据标准
--------
* GB/T 150.1~150.4—2024《压力容器》——釜体与夹套强度（2024版替代2011版）
* GB/T 25198—2023《压力容器封头》——标准椭圆封头 2:1
* HG/T 20569—2013《机械搅拌设备》——搅拌轴、桨叶、机架
* HG/T 3796 系列《搅拌器型式及基本参数》——桨型代号
* JB/T 4712.3—2007《容器支座 第 3 部分：耳式支座》
* HG/T 21514—2014《钢制人孔和手孔》

.. note::
   桨径比 d/D、桨叶层数、挡板宽度等属工艺/搅拌功率计算结果，
   envcad standards_kb.json 未收录，默认值见 ``# TODO: verify`` 标记。

坐标约定
--------
``(x, y)`` = **支座底面中心**（基础/平台顶面标高处）。
"""
from __future__ import annotations

import math
from typing import Optional, Sequence

from ezdxf.enums import TextEntityAlignment

from envcad.standards import pid

from . import _common as C


def _impeller(msp, x: float, y: float, d: float, itype: str, scale: float,
              layer: str = C.L_THICK):
    """搅拌桨叶正视图（HG/T 3796 系列）。

    itype: ``paddle`` 桨式 / ``turbine`` 涡轮式 / ``anchor`` 锚式 /
           ``propeller`` 推进式
    """
    r = d / 2.0
    h = max(d * 0.18, C.P(1.5, scale))
    if itype == "anchor":
        msp.add_lwpolyline([(x - r, y + d * 0.9), (x - r, y + h),
                            (x + r, y + h), (x + r, y + d * 0.9)],
                           dxfattribs={"layer": layer})
        msp.add_arc((x, y + h), r, start_angle=180, end_angle=360,
                    dxfattribs={"layer": layer})
    elif itype == "turbine":
        # 圆盘涡轮：中心圆盘 + 两侧直叶片
        C.rect(msp, x - r * 0.45, y - h * 0.3, x + r * 0.45, y + h * 0.3,
               layer=layer)
        for sgn in (-1, 1):
            C.rect(msp, x + sgn * r * 0.45, y - h, x + sgn * r, y + h,
                   layer=layer)
    elif itype == "propeller":
        for sgn in (-1, 1):
            msp.add_lwpolyline([(x, y), (x + sgn * r, y + h * 1.2),
                                (x + sgn * r, y - h * 0.4)],
                               close=True, dxfattribs={"layer": layer})
    else:  # paddle 桨式
        C.rect(msp, x - r, y - h, x + r, y + h, layer=layer)
    return r


def draw_reactor_vessel(msp, x: float, y: float, scale: float = 50.0,
                        diameter: float = 1600.0,
                        shell_height: float = 2000.0,
                        straight_flange: float = 40.0,
                        wall_thickness: float = 12.0,
                        jacket: bool = True,
                        jacket_gap: float = 60.0,
                        jacket_thickness: float = 8.0,
                        jacket_coverage: float = 0.85,
                        jacket_type: str = "整体夹套",
                        impeller_type: str = "turbine",
                        n_impellers: int = 2,
                        impeller_ratio: float = 0.45,
                        n_baffles: int = 4,
                        baffle_ratio: float = 0.10,
                        motor_power: str = "11 kW",
                        gearbox: bool = True,
                        support: str = "lug",
                        support_height: float = 900.0,
                        manhole_dn: float = 450.0,
                        tag: str = "R-601",
                        name: str = "搅拌反应釜",
                        design_pressure: str = "1.6 MPa",
                        jacket_pressure: str = "0.6 MPa",
                        design_temp: str = "180 ℃",
                        material: str = "S31603",
                        volume: str = "",
                        with_dims: bool = True,
                        with_table: bool = True,
                        **params):
    """绘制搅拌反应釜正视装配图（GB/T 150 / HG/T 20569）。

    参数
    ----
    jacket          是否绘制夹套
    jacket_gap      夹套环隙宽度 mm
                    # TODO: verify against GB/T 150.3 夹套设计（常用 25~100mm）
    jacket_coverage 夹套包覆筒体高度的比例
    impeller_type   ``turbine``/``paddle``/``anchor``/``propeller``
    impeller_ratio  桨径 d / 釜内径 D
                    # TODO: verify against HG/T 20569（涡轮式常用 0.3~0.5）
    baffle_ratio    挡板宽度 / 釜内径（# TODO: verify，常用 1/10~1/12）
    support         ``lug`` 耳式支座 / ``leg`` 支腿

    返回 ``dict``：关键几何标高。
    """
    s = scale
    R = diameter / 2.0
    Ri = R - wall_thickness

    y_base = y
    y_bot_tan = y_base + support_height
    y_top_tan = y_bot_tan + shell_height
    head_h = R / 2.0
    y_top = y_top_tan + straight_flange + head_h
    y_bot = y_bot_tan - straight_flange - head_h

    C.centerline(msp, (x, y_bot - C.P(8, s)), (x, y_top + C.P(46, s)))

    # ── 釜体筒节 ──
    for sgn in (-1, 1):
        msp.add_line((x + sgn * R, y_bot_tan), (x + sgn * R, y_top_tan),
                     dxfattribs={"layer": C.L_THICK})
        msp.add_line((x + sgn * Ri, y_bot_tan), (x + sgn * Ri, y_top_tan),
                     dxfattribs={"layer": C.L_THIN})
    C.ellipsoidal_head(msp, x, y_top_tan, diameter, "up", straight_flange)
    C.ellipsoidal_head(msp, x, y_bot_tan, diameter, "down", straight_flange)

    # ── 夹套（GB/T 150.3 整体夹套）──
    y_j_top = y_bot_tan + shell_height * jacket_coverage
    if jacket:
        Rj = R + jacket_gap
        Rjo = Rj + jacket_thickness
        for sgn in (-1, 1):
            msp.add_line((x + sgn * Rj, y_bot_tan), (x + sgn * Rj, y_j_top),
                         dxfattribs={"layer": C.L_DASH})
            msp.add_line((x + sgn * Rjo, y_bot_tan - head_h * 0.5),
                         (x + sgn * Rjo, y_j_top),
                         dxfattribs={"layer": C.L_THICK})
            # 夹套封口环
            msp.add_line((x + sgn * R, y_j_top), (x + sgn * Rjo, y_j_top),
                         dxfattribs={"layer": C.L_THICK})
        # 夹套下部包覆封头
        C.ellipsoidal_head(msp, x, y_bot_tan - head_h * 0.5, (Rjo) * 2,
                           "down", 0.0)
        # 夹套进出口
        C.nozzle(msp, (x + Rjo, y_j_top - shell_height * 0.08), "right",
                 max(diameter * 0.05, 50), max(diameter * 0.16, 220), s,
                 tag="j1")
        C.nozzle(msp, (x - Rjo, y_bot_tan + shell_height * 0.10), "left",
                 max(diameter * 0.05, 50), max(diameter * 0.16, 220), s,
                 tag="j2")

    # ── 挡板（HG/T 20569，竖直条，正视图画 2 块）──
    if n_baffles > 0:
        bw = diameter * baffle_ratio
        for sgn in (-1, 1):
            bx = x + sgn * (Ri - bw)
            C.rect(msp, bx, y_bot_tan + shell_height * 0.06,
                   bx + sgn * max(bw * 0.22, C.P(0.8, s)),
                   y_top_tan - shell_height * 0.06, layer=C.L_MID)

    # ── 搅拌轴 + 桨叶 ──
    shaft_d = max(diameter * 0.035, 40.0)
    y_shaft_top = y_top + C.P(22, s)
    y_shaft_bot = y_bot_tan + shell_height * 0.10
    for sgn in (-1, 1):
        msp.add_line((x + sgn * shaft_d / 2, y_shaft_bot),
                     (x + sgn * shaft_d / 2, y_shaft_top),
                     dxfattribs={"layer": C.L_THICK})
    d_imp = diameter * impeller_ratio
    for i in range(max(n_impellers, 1)):
        iy = y_bot_tan + shell_height * (0.16 + 0.36 * i)
        if iy > y_top_tan - shell_height * 0.08:
            break
        _impeller(msp, x, iy, d_imp, impeller_type, s)

    # ── 传动装置：机座 + 减速机 + 电机（HG/T 20569）──
    y_flange = y_top + C.P(2, s)
    C.rect(msp, x - R * 0.42, y_flange, x + R * 0.42, y_flange + C.P(3, s),
           layer=C.L_THICK)                                    # 安装法兰
    y_seal = y_flange + C.P(3, s)
    C.rect(msp, x - R * 0.26, y_seal, x + R * 0.26, y_seal + C.P(8, s),
           layer=C.L_MID)                                      # 机械密封
    C.leader_note(msp, (x + R * 0.26, y_seal + C.P(4, s)),
                  "机械密封 HG/T 21571-1995", s, dx=20, dy=6)
    y_g = y_seal + C.P(8, s)
    if gearbox:
        C.rect(msp, x - R * 0.55, y_g, x + R * 0.55, y_g + C.P(14, s),
               layer=C.L_THICK)                                # 减速机
        C.text(msp, "减速机", (x, y_g + C.P(7, s)), 3.0, s, layer=C.L_TEXT)
        y_g += C.P(14, s)
    C.rect(msp, x - R * 0.40, y_g, x + R * 0.40, y_g + C.P(16, s),
           layer=C.L_THICK)                                    # 电机
    msp.add_circle((x, y_g + C.P(8, s)), R * 0.22,
                   dxfattribs={"layer": C.L_MID})
    C.eng_text(msp, "M", (x, y_g + C.P(8, s)), 4.0, s, layer=C.L_TITLE)
    C.leader_note(msp, (x + R * 0.40, y_g + C.P(8, s)),
                  f"电机 {motor_power}", s, dx=18, dy=8)
    y_drive_top = y_g + C.P(16, s)

    # ── 支座 ──
    if support == "leg":
        C.support_legs(msp, x, y_bot_tan, diameter, support_height, scale=s)
    else:
        C.lug_support(msp, x, y_bot_tan + shell_height * 0.62, R, scale=s)
        # 支承梁
        for sgn in (-1, 1):
            bx = x + sgn * R * 1.35
            msp.add_line((bx, y_bot_tan + shell_height * 0.42),
                         (bx, y_base), dxfattribs={"layer": C.L_THICK})
    msp.add_line((x - R * 2.2, y_base), (x + R * 2.2, y_base),
                 dxfattribs={"layer": C.L_THICK})
    for i in range(11):
        gx = x - R * 2.1 + (R * 4.2) * i / 10.0
        msp.add_line((gx, y_base), (gx - C.P(3, s), y_base - C.P(3, s)),
                     dxfattribs={"layer": C.L_THIN})

    # ── 釜体管口 ──
    nl = max(diameter * 0.16, 240.0)
    hr = R / 2.0
    C.nozzle(msp, (x - R * 0.55, y_top_tan + straight_flange + hr * 0.83),
             "up", max(diameter * 0.07, 65), nl, s, tag="a")   # 进料
    C.nozzle(msp, (x + R * 0.55, y_top_tan + straight_flange + hr * 0.83),
             "up", max(diameter * 0.05, 50), nl, s, tag="b")   # 气相/回流
    C.nozzle(msp, (x, y_bot_tan - straight_flange - hr), "down",
             max(diameter * 0.07, 65), nl, s, tag="c")         # 出料
    if manhole_dn:
        C.manhole(msp, (x, y_top_tan + straight_flange + hr), "up",
                  manhole_dn, max(manhole_dn * 0.5, 220.0), s, tag="M")

    # ── 标注 ──
    if with_dims:
        C.dim_linear(msp, (x - R, y_bot_tan), (x + R, y_bot_tan),
                     offset=-8, scale=s, label=f"DN{int(diameter)}")
        C.dim_linear(msp, (x - R, y_bot_tan), (x - R, y_top_tan),
                     offset=34, scale=s, label=f"{int(shell_height)}")
        C.dim_linear(msp, (x - R, y_base), (x - R, y_drive_top),
                     offset=50, scale=s,
                     label=f"总高 {int(y_drive_top - y_base)}")
        it = {"turbine": "圆盘涡轮式", "paddle": "桨式", "anchor": "锚式",
              "propeller": "推进式"}.get(impeller_type, impeller_type)
        C.leader_note(msp, (x + d_imp / 2, y_bot_tan + shell_height * 0.16),
                      f"{it}搅拌器 d={int(d_imp)}", s, dx=26, dy=-14)
        if jacket:
            C.leader_note(msp, (x + R + jacket_gap / 2, y_bot_tan + shell_height * 0.5),
                          f"{jacket_type} 环隙{int(jacket_gap)}", s, dx=30, dy=10)
        C.elevation_mark(msp, (x + R * 1.7, y_base), "±0.000", s)

    C.eng_text(msp, tag, (x, y_drive_top + C.P(10, s)), 5.0, s, layer=C.L_TITLE)
    C.text(msp, name, (x, y_drive_top + C.P(4, s)), 3.5, s, layer=C.L_TITLE)

    if with_table:
        rows = [
            ["釜内设计压力", design_pressure],
            ["夹套设计压力", jacket_pressure if jacket else "—"],
            ["设计温度", design_temp],
            ["釜体材质", material],
            ["公称直径", f"DN{int(diameter)}"],
            ["电机功率", motor_power],
        ]
        if volume:
            rows.append(["公称容积", volume])
        C.spec_table(msp, (x + R + C.P(62, s), y_drive_top),
                     rows, s, col_w=(32.0, 36.0), title="反应釜数据表")

    return {"tag": tag, "base": y_base, "bottom_tangent": y_bot_tan,
            "top_tangent": y_top_tan, "top": y_top,
            "drive_top": y_drive_top, "radius": R}


def draw_reactor_vessel_symbol(msp, x: float, y: float, scale: float = 50.0,
                               width: float = 30.0, height: float = 36.0,
                               tag: str = "R-601", name: str = "反应釜",
                               jacket: bool = True, **params):
    """反应釜 P&ID 符号 —— 在 ``pid.draw_vessel(v_type="reactor")`` 基础上加夹套。

    ``pid.draw_vessel`` 的 reactor 型式已自带搅拌轴、桨叶与电机；
    此处仅补画夹套外廓（虚线），实现「扩展而非重写」。
    """
    res = pid.draw_vessel(msp, (x, y), v_type="reactor", width=width,
                          height=height, scale=scale, tag=tag, label=name,
                          layer=C.L_EQUIP)
    if jacket:
        s = scale
        w, h = width * s, height * s
        g = C.P(2.5, s)
        C.rect(msp, x - w / 2 - g, y - h / 2 - g, x + w / 2 + g,
               y + h / 2 - h * 0.12, layer=C.L_DASH)
    return res
