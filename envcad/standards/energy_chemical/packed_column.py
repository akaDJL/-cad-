"""填料塔（Packed Column）总图模块。

依据标准
--------
* GB/T 150.1~150.4—2024《压力容器》——塔体强度与开孔（2024版替代2011版）
* HG/T 21514—2014《钢制人孔和手孔》——塔体人孔
* GB/T 25198—2023《压力容器封头》——标准椭圆封头 2:1
* JB/T 4712.3—2007《容器支座 第 3 部分：耳式支座》/ 裙座
* HG/T 21556—1995《塔器填料支承装置及液体分布装置》——支承板/分布器

.. note::
   本模块的填料层高度、分布器液流点密度等 **工艺参数** 必须由
   工艺计算给定；envcad 内置知识库 (standards_kb.json) 未收录该类数值，
   相关默认值仅为绘图占位，见函数内 ``# TODO: verify`` 标记。

坐标约定
--------
``(x, y)`` = **裙座底面中心**（基础顶面标高处）。
"""
from __future__ import annotations

import math
from typing import List, Optional, Sequence

from ezdxf.enums import TextEntityAlignment

from envcad.standards import pid

from . import _common as C


def _packing_hatch(msp, x: float, y0: float, y1: float, R: float,
                   scale: float, density: float = 1.0):
    """填料层示意（细实线交叉网纹，不代表实际填料型式）。"""
    h = y1 - y0
    step = max(h / max(int(8 * density), 4), C.P(2.0, scale))
    n = max(int(h / step), 2)
    for i in range(n + 1):
        yy = y0 + h * i / n
        msp.add_line((x - R, yy), (x + R, yy), dxfattribs={"layer": C.L_THIN})
    m = max(int(2 * R / step), 2)
    for i in range(m + 1):
        xx = x - R + 2 * R * i / m
        msp.add_line((xx, y0), (xx, y1), dxfattribs={"layer": C.L_THIN})


def _liquid_distributor(msp, x: float, y: float, R: float, scale: float,
                        n_arms: int = 7, tag: str = ""):
    """槽盘式液体分布器（HG/T 21556）：横槽 + 下降滴淋管。"""
    th = max(R * 0.16, C.P(3, scale))
    C.rect(msp, x - R * 0.92, y, x + R * 0.92, y + th, layer=C.L_MID)
    for i in range(n_arms):
        dx = -R * 0.8 + (1.6 * R) * i / max(n_arms - 1, 1)
        msp.add_line((x + dx, y), (x + dx, y - th * 1.4),
                     dxfattribs={"layer": C.L_THIN})
    if tag:
        C.leader_note(msp, (x + R * 0.9, y + th / 2), tag, scale, dx=18, dy=10)


def _support_grid(msp, x: float, y: float, R: float, scale: float, tag: str = ""):
    """填料支承栅板（HG/T 21556 气液分流型支承板）。"""
    th = max(R * 0.12, C.P(2.5, scale))
    C.rect(msp, x - R, y - th, x + R, y, layer=C.L_MID)
    n = 9
    for i in range(1, n):
        dx = -R + 2 * R * i / n
        msp.add_line((x + dx, y - th), (x + dx, y),
                     dxfattribs={"layer": C.L_THIN})
    if tag:
        C.leader_note(msp, (x - R * 0.9, y - th / 2), tag, scale, dx=-18, dy=-10)


def draw_packed_column(msp, x: float, y: float, scale: float = 50.0,
                       diameter: float = 1600.0,
                       shell_height: float = 12000.0,
                       straight_flange: float = 40.0,
                       wall_thickness: float = 10.0,
                       n_beds: int = 2,
                       bed_heights: Optional[Sequence[float]] = None,
                       bed_gap: float = 1500.0,
                       bottom_space: float = 2000.0,
                       packing_type: str = "250Y 规整填料",
                       skirt_height: float = 2500.0,
                       manhole_dn: float = 500.0,
                       tag: str = "T-301",
                       name: str = "填料塔",
                       design_pressure: str = "0.3 MPa",
                       design_temp: str = "120 ℃",
                       material: str = "S30408",
                       with_dims: bool = True,
                       with_table: bool = True,
                       **params):
    """绘制填料塔正视总图（GB/T 150 / HG/T 21514 / HG/T 21556）。

    参数
    ----
    diameter     塔体内直径 DN，mm
    shell_height 塔体直段总高（两切线间距），mm
    n_beds       填料层数
    bed_heights  各层填料高度列表 mm；缺省时按可用高度均分
                 # TODO: verify against 工艺计算（HETP × 理论板数），
                 #       GB/T 150 与 envcad standards_kb.json 均未规定该值
    bed_gap      层间空间（含再分布器）高度，mm
    bottom_space 塔釜液空间高度，mm
    packing_type 填料型号说明文字（随工艺给定）

    返回 ``dict``：各填料层标高区间。
    """
    s = scale
    R = diameter / 2.0

    y_base = y
    y_bot_tan = y_base + skirt_height
    y_top_tan = y_bot_tan + shell_height
    head_h = R / 2.0
    y_top = y_top_tan + straight_flange + head_h
    y_bot = y_bot_tan - straight_flange - head_h

    # ── 轴线 ──
    C.centerline(msp, (x, y_bot - C.P(8, s)), (x, y_top + C.P(14, s)))

    # ── 塔体 ──
    for sgn in (-1, 1):
        msp.add_line((x + sgn * R, y_bot_tan), (x + sgn * R, y_top_tan),
                     dxfattribs={"layer": C.L_THICK})
        xi = x + sgn * (R - wall_thickness)
        msp.add_line((xi, y_bot_tan), (xi, y_top_tan),
                     dxfattribs={"layer": C.L_THIN})
    C.ellipsoidal_head(msp, x, y_top_tan, diameter, "up", straight_flange)
    C.ellipsoidal_head(msp, x, y_bot_tan, diameter, "down", straight_flange)

    # ── 填料层布置 ──
    usable = shell_height - bottom_space - bed_gap * n_beds
    if bed_heights is None:
        bed_heights = [max(usable / max(n_beds, 1), diameter)] * n_beds
    bed_heights = list(bed_heights)[:n_beds]

    beds = []
    cur = y_bot_tan + bottom_space
    for i, bh in enumerate(bed_heights):
        _support_grid(msp, x, cur, R - wall_thickness, s,
                      tag="填料支承板" if i == 0 else "")
        y0 = cur
        y1 = cur + bh
        _packing_hatch(msp, x, y0, y1, R - wall_thickness, s)
        # 压紧栅板
        C.rect(msp, x - (R - wall_thickness), y1,
               x + (R - wall_thickness), y1 + max(R * 0.08, C.P(2, s)),
               layer=C.L_MID)
        # 分布器（每层顶部之上）
        _liquid_distributor(msp, x, y1 + bed_gap * 0.45, R - wall_thickness, s,
                            tag=("液体分布器 HG/T 21556" if i == len(bed_heights) - 1
                                 else "液体再分布器"))
        beds.append((y0, y1))
        if with_dims:
            C.dim_linear(msp, (x + R, y0), (x + R, y1), offset=-20, scale=s,
                         label=f"填料层{i + 1} {int(bh)}")
        cur = y1 + bed_gap

    # ── 塔釜液位 ──
    y_liq = y_bot_tan + bottom_space * 0.45
    msp.add_line((x - R + wall_thickness, y_liq), (x + R - wall_thickness, y_liq),
                 dxfattribs={"layer": C.L_PHANTOM})
    C.eng_text(msp, "NLL", (x + R - C.P(6, s), y_liq + C.P(2, s)), 2.5, s,
               layer=C.L_TEXT, align=TextEntityAlignment.MIDDLE_RIGHT)

    # ── 裙座与基础（JB/T 4712.3）──
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
             max(diameter * 0.25, 200), nl, s, tag="a")       # 塔顶气相出口
    C.nozzle(msp, (x + R, y_top_tan - shell_height * 0.06), "right",
             max(diameter * 0.10, 80), nl, s, tag="b")        # 回流入口
    C.nozzle(msp, (x - R, y_bot_tan + bottom_space * 1.15), "left",
             max(diameter * 0.12, 100), nl, s, tag="c")       # 进料口
    C.nozzle(msp, (x, y_bot_tan - straight_flange - head_h), "down",
             max(diameter * 0.12, 100), nl, s, tag="d")       # 塔釜出料
    C.nozzle(msp, (x + R, y_bot_tan + bottom_space * 0.75), "right",
             max(diameter * 0.15, 125), nl, s, tag="e")       # 气相入口

    if manhole_dn:
        for frac in (0.10, 0.92):
            C.manhole(msp, (x + R, y_bot_tan + shell_height * frac), "right",
                      manhole_dn, max(manhole_dn * 0.5, 250.0), s, tag="M")

    # ── 标注 ──
    if with_dims:
        C.dim_linear(msp, (x - R, y_bot_tan), (x + R, y_bot_tan),
                     offset=-8, scale=s, label=f"DN{int(diameter)}")
        C.dim_linear(msp, (x - R, y_bot_tan), (x - R, y_top_tan),
                     offset=30, scale=s, label=f"{int(shell_height)}")
        C.dim_linear(msp, (x - R, y_base), (x - R, y_top),
                     offset=46, scale=s, label=f"总高 {int(y_top - y_base)}")
        C.leader_note(msp, (x, (beds[0][0] + beds[0][1]) / 2 if beds else y_bot_tan),
                      packing_type, s, dx=-30, dy=10)
        C.elevation_mark(msp, (x + R * 1.5, y_base), "±0.000", s)

    C.eng_text(msp, tag, (x, y_top + C.P(11, s)), 5.0, s, layer=C.L_TITLE)
    C.text(msp, name, (x, y_top + C.P(5, s)), 3.5, s, layer=C.L_TITLE)

    if with_table:
        C.spec_table(msp, (x + R + C.P(58, s), y_top), [
            ["设计压力", design_pressure],
            ["设计温度", design_temp],
            ["塔体材质", material],
            ["公称直径", f"DN{int(diameter)}"],
            ["填料层数", f"{n_beds}"],
            ["填料型式", packing_type],
        ], s, title="塔器数据表")

    return {"tag": tag, "beds": beds, "base": y_base,
            "bottom_tangent": y_bot_tan, "top_tangent": y_top_tan,
            "top": y_top, "radius": R}


def draw_packed_column_symbol(msp, x: float, y: float, scale: float = 50.0,
                              width: float = 18.0, height: float = 70.0,
                              tag: str = "T-301", name: str = "填料塔",
                              **params):
    """填料塔 P&ID 简化符号，复用 ``pid.draw_vessel(v_type="column")``。"""
    return pid.draw_vessel(msp, (x, y), v_type="column", width=width,
                           height=height, scale=scale, tag=tag, label=name,
                           layer=C.L_EQUIP)
