"""列管（管壳式）换热器装配图模块 —— 壳体 + 管板 + 折流板。

依据标准
--------
* GB/T 151—2014《热交换器》——管板、折流板、拉杆、换热管布置
* GB/T 150.1~150.4—2024《压力容器》——壳体与封头（2024版替代2011版）
* GB/T 25198—2023《压力容器封头》
* NB/T 47065.1—2018《容器支座 第 1 部分：鞍式支座》
* HG/T 20592—2009《钢制管法兰》

.. note::
   折流板缺口率、板间距、管间距等取值随工况变化，
   envcad standards_kb.json 未收录 GB/T 151 数表，
   默认值见 ``# TODO: verify`` 标记。

坐标约定
--------
``(x, y)`` = **鞍座底板底面中心**（基础顶面标高处）。
"""
from __future__ import annotations

import math
from typing import Optional

from ezdxf.enums import TextEntityAlignment

from envcad.standards import pid

from . import _common as C


def _baffle(msp, x: float, cy: float, Ri: float, cut_ratio: float,
            thickness: float, up: bool, layer: str = C.L_MID):
    """单弓形折流板（GB/T 151 单弓形，缺口朝上/朝下）。

    cut_ratio 为缺口高度 / 壳体内径。
    """
    D = Ri * 2.0
    cut = D * cut_ratio
    if up:
        y0, y1 = cy - Ri, cy + Ri - cut
    else:
        y0, y1 = cy - Ri + cut, cy + Ri
    C.rect(msp, x - thickness / 2, y0, x + thickness / 2, y1, layer=layer)
    return (y0, y1)


def draw_shell_tube_exchanger(msp, x: float, y: float, scale: float = 50.0,
                              shell_dn: float = 600.0,
                              tube_length: float = 4500.0,
                              n_tube_rows: int = 7,
                              tube_od: float = 25.0,
                              n_baffles: int = 6,
                              baffle_cut: float = 0.25,
                              baffle_thickness: float = 8.0,
                              tubesheet_thickness: float = 60.0,
                              head_length: float = 500.0,
                              exchanger_type: str = "BEM",
                              wall_thickness: float = 8.0,
                              saddle_height: float = 500.0,
                              saddle_span_ratio: float = 0.62,
                              tag: str = "E-501",
                              name: str = "固定管板式换热器",
                              design_pressure_shell: str = "1.0 MPa",
                              design_pressure_tube: str = "1.6 MPa",
                              design_temp: str = "200 ℃",
                              material: str = "Q345R / 换热管 S30408",
                              heat_area: str = "",
                              with_dims: bool = True,
                              with_table: bool = True,
                              **params):
    """绘制管壳式换热器纵剖装配图（GB/T 151—2014）。

    参数
    ----
    shell_dn            壳体公称内直径 mm
    tube_length         换热管有效长度 mm（GB/T 151 推荐 1.5/2/3/4.5/6/9m）
    n_tube_rows         纵剖面上显示的换热管排数（示意）
    tube_od             换热管外径 mm（GB/T 151 常用 19/25/32）
    n_baffles           折流板数量
    baffle_cut          折流板缺口率
                        # TODO: verify against GB/T 151—2014 附录（常用 20%~25%）
    tubesheet_thickness 管板厚度 mm
                        # TODO: verify against GB/T 151 管板强度计算
    exchanger_type      TEMA/GB 型号代号（如 BEM / AES / BIU），仅作标注

    返回 ``dict``：关键几何坐标。
    """
    s = scale
    R = shell_dn / 2.0
    Ri = R - wall_thickness
    cy = y + saddle_height + R

    # 纵向定位：左封头 | 左管板 | 壳程（管束） | 右管板 | 右封头
    x_ts_l = x - tube_length / 2.0
    x_ts_r = x + tube_length / 2.0
    x_sh_l = x_ts_l - tubesheet_thickness
    x_sh_r = x_ts_r + tubesheet_thickness
    x_hd_l = x_sh_l - head_length
    x_hd_r = x_sh_r + head_length

    C.centerline(msp, (x_hd_l, cy), (x_hd_r, cy), extend=C.P(10, s))

    # ── 壳体 ──
    for sgn in (-1, 1):
        msp.add_line((x_sh_l, cy + sgn * R), (x_sh_r, cy + sgn * R),
                     dxfattribs={"layer": C.L_THICK})
        msp.add_line((x_sh_l, cy + sgn * Ri), (x_sh_r, cy + sgn * Ri),
                     dxfattribs={"layer": C.L_THIN})

    # ── 管板（GB/T 151，兼作法兰，外径大于壳体）──
    C.rect(msp, x_sh_l, cy - R * 1.15, x_ts_l, cy + R * 1.15, layer=C.L_THICK)
    C.rect(msp, x_ts_r, cy - R * 1.15, x_sh_r, cy + R * 1.15, layer=C.L_THICK)
    for x0, x1 in ((x_sh_l, x_ts_l), (x_ts_r, x_sh_r)):
        C.hatch_area(msp, [(x0, cy - R * 1.15), (x1, cy - R * 1.15),
                           (x1, cy + R * 1.15), (x0, cy + R * 1.15)],
                     scale=s, pattern_scale=0.6)

    # ── 管箱封头（椭圆形）──
    C.rect(msp, x_hd_l + R / 2.0, cy - R, x_sh_l, cy + R, layer=C.L_THICK)
    C.rect(msp, x_sh_r, cy - R, x_hd_r - R / 2.0, cy + R, layer=C.L_THICK)
    C.ellipsoidal_head(msp, x_hd_l + R / 2.0, cy, shell_dn, "left", 0.0)
    C.ellipsoidal_head(msp, x_hd_r - R / 2.0, cy, shell_dn, "right", 0.0)

    # ── 管箱分程隔板（双管程）──
    msp.add_line((x_hd_l + R / 2.0, cy), (x_ts_l, cy),
                 dxfattribs={"layer": C.L_MID})

    # ── 换热管束 ──
    rows = max(int(n_tube_rows), 2)
    for i in range(rows):
        ty = cy - Ri * 0.82 + (Ri * 1.64) * i / (rows - 1)
        if abs(ty - cy) < tube_od * 0.6:
            continue
        for sgn in (-1, 1):
            msp.add_line((x_ts_l, ty + sgn * tube_od / 2),
                         (x_ts_r, ty + sgn * tube_od / 2),
                         dxfattribs={"layer": C.L_THIN})

    # ── 折流板（单弓形，缺口上下交替）──
    if n_baffles > 0:
        pitch = tube_length / (n_baffles + 1)
        for i in range(1, n_baffles + 1):
            bx = x_ts_l + pitch * i
            _baffle(msp, bx, cy, Ri, baffle_cut, baffle_thickness,
                    up=(i % 2 == 1))

    # ── 鞍座（NB/T 47065.1）──
    span = (x_sh_r - x_sh_l) * saddle_span_ratio
    for sx in (x - span / 2.0, x + span / 2.0):
        C.saddle_support(msp, sx, cy, R, saddle_height,
                         width=R * 1.9, scale=s, wrap_deg=120.0)

    # ── 基础地面线 ──
    gx0, gx1 = x_hd_l - C.P(6, s), x_hd_r + C.P(6, s)
    msp.add_line((gx0, y), (gx1, y), dxfattribs={"layer": C.L_THICK})
    for i in range(15):
        gx = gx0 + (gx1 - gx0) * i / 14.0
        msp.add_line((gx, y), (gx - C.P(3, s), y - C.P(3, s)),
                     dxfattribs={"layer": C.L_THIN})

    # ── 管口：壳程进出 + 管程进出 ──
    nl = max(shell_dn * 0.35, 240.0)
    dn_sh = max(shell_dn * 0.20, 80.0)
    dn_tb = max(shell_dn * 0.20, 80.0)
    C.nozzle(msp, (x_sh_r - tube_length * 0.12, cy + R), "up", dn_sh, nl, s,
             tag="a")   # 壳程入口
    C.nozzle(msp, (x_sh_l + tube_length * 0.12, cy - R), "down", dn_sh, nl, s,
             tag="b")   # 壳程出口
    C.nozzle(msp, (x_hd_l + R * 0.55, cy - R * 0.55), "down", dn_tb, nl, s,
             tag="c")   # 管程入口
    C.nozzle(msp, (x_hd_l + R * 0.55, cy + R * 0.55), "up", dn_tb, nl, s,
             tag="d")   # 管程出口

    # ── 标注 ──
    if with_dims:
        C.dim_linear(msp, (x_ts_l, cy - R), (x_ts_r, cy - R),
                     offset=26, scale=s, label=f"换热管长 {int(tube_length)}")
        C.dim_linear(msp, (x_hd_l, cy - R), (x_hd_r, cy - R),
                     offset=40, scale=s, label=f"总长 {int(x_hd_r - x_hd_l)}")
        C.dim_linear(msp, (x_hd_r, cy - R), (x_hd_r, cy + R),
                     offset=-24, scale=s, label=f"DN{int(shell_dn)}")
        C.leader_note(msp, (x_ts_r + tubesheet_thickness / 2, cy + R * 0.9),
                      f"管板 δ={int(tubesheet_thickness)} GB/T 151", s,
                      dx=20, dy=18)
        if n_baffles > 0:
            C.leader_note(msp, (x_ts_l + tube_length / (n_baffles + 1), cy - R * 0.5),
                          f"折流板 {n_baffles}块 缺口率{int(baffle_cut * 100)}%",
                          s, dx=-22, dy=-18)
        C.leader_note(msp, (x, cy + Ri * 0.5),
                      f"换热管 φ{int(tube_od)} 正三角形排列", s, dx=16, dy=22)
        C.elevation_mark(msp, (x_hd_l - C.P(3, s), y), "±0.000", s)

    C.eng_text(msp, f"{tag}  ({exchanger_type})", (x, cy + R + C.P(34, s)),
               5.0, s, layer=C.L_TITLE)
    C.text(msp, name, (x, cy + R + C.P(27, s)), 3.5, s, layer=C.L_TITLE)

    if with_table:
        rows_t = [
            ["壳程设计压力", design_pressure_shell],
            ["管程设计压力", design_pressure_tube],
            ["设计温度", design_temp],
            ["壳体公称直径", f"DN{int(shell_dn)}"],
            ["换热管", f"φ{int(tube_od)}×{int(tube_length)}"],
            ["材质", material],
        ]
        if heat_area:
            rows_t.append(["换热面积", heat_area])
        C.spec_table(msp, (x_hd_r + C.P(22, s), cy + R + C.P(22, s)),
                     rows_t, s, col_w=(34.0, 40.0), title="换热器数据表")

    return {"tag": tag, "axis_y": cy, "base": y,
            "shell_left": x_sh_l, "shell_right": x_sh_r,
            "head_left": x_hd_l, "head_right": x_hd_r, "radius": R}


def draw_shell_tube_exchanger_symbol(msp, x: float, y: float,
                                     scale: float = 50.0,
                                     width: float = 40.0, height: float = 18.0,
                                     tag: str = "E-501",
                                     name: str = "列管换热器", **params):
    """换热器 P&ID 简化符号，复用 ``pid.draw_vessel(v_type="heat_exchanger")``。"""
    return pid.draw_vessel(msp, (x, y), v_type="heat_exchanger", width=width,
                           height=height, scale=scale, tag=tag, label=name,
                           layer=C.L_EQUIP)
