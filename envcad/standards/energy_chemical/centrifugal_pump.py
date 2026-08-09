"""离心泵（Centrifugal Pump）机组布置图模块。

依据标准
--------
* GB/T 5656—2008《离心泵 技术条件（Ⅲ 类）》——总体技术要求
* GB/T 5657—2013《离心泵技术条件（Ⅱ 类）》
* GB/T 3216—2016《回转动力泵 水力性能验收试验》——性能参数表述
* HG/T 20592—2009《钢制管法兰》——进出口法兰
* GB/T 6556—2016《机械密封的型式、主要尺寸、材料和识别标志》
* API 610 / GB/T 3215（石化流程泵，供对照）

坐标约定
--------
``(x, y)`` = **底座底面中心**（基础顶面标高处）。
"""
from __future__ import annotations

import math
from typing import Optional

from ezdxf.enums import TextEntityAlignment

from envcad.standards import hydraulic, pid

from . import _common as C


def _volute(msp, cx: float, cy: float, r_out: float, scale: float,
            layer: str = C.L_THICK):
    """蜗壳外廓（阿基米德螺线近似：4 段递增圆弧）。"""
    steps = [(0, 90, 0.86), (90, 180, 0.92), (180, 270, 1.0), (270, 360, 0.80)]
    for a0, a1, k in steps:
        msp.add_arc((cx, cy), r_out * k, start_angle=a0, end_angle=a1,
                    dxfattribs={"layer": layer})


def draw_centrifugal_pump(msp, x: float, y: float, scale: float = 50.0,
                          suction_dn: float = 150.0,
                          discharge_dn: float = 100.0,
                          impeller_diameter: float = 320.0,
                          shaft_height: float = 320.0,
                          baseplate_length: float = 1600.0,
                          baseplate_height: float = 120.0,
                          motor_length: float = 620.0,
                          motor_diameter: float = 400.0,
                          coupling_gap: float = 120.0,
                          seal_type: str = "机械密封",
                          orientation: str = "right",
                          tag: str = "P-701A",
                          name: str = "离心泵",
                          flow: str = "50 m³/h",
                          head: str = "32 m",
                          motor_power: str = "11 kW",
                          speed: str = "2900 r/min",
                          medium: str = "工艺物料",
                          material: str = "泵体 QT450 / 叶轮 S30408",
                          with_dims: bool = True,
                          with_table: bool = True,
                          **params):
    """绘制卧式单级离心泵机组正视图（GB/T 5656—2008）。

    参数
    ----
    suction_dn         吸入口公称直径 mm（通常大于排出口一档）
    discharge_dn       排出口公称直径 mm
    impeller_diameter  叶轮外径 mm（决定蜗壳外廓）
    shaft_height       泵轴中心线到底座顶面的高度 mm
    baseplate_length   公共底座长度 mm
    orientation        ``right`` 电机在右 / ``left`` 电机在左
    seal_type          ``机械密封`` / ``填料密封``（GB/T 6556）

    返回 ``dict``：吸入口/排出口/轴中心等坐标。
    """
    s = scale
    sgn = 1.0 if orientation == "right" else -1.0

    y_base = y
    y_bp_top = y_base + baseplate_height
    cy = y_bp_top + shaft_height                 # 泵轴中心线
    r_vol = impeller_diameter * 0.62             # 蜗壳外半径

    x_pump = x - sgn * baseplate_length * 0.27   # 泵中心
    x_motor = x + sgn * baseplate_length * 0.25  # 电机中心

    # ── 公共底座（GB/T 5656 附带底座）──
    C.rect(msp, x - baseplate_length / 2, y_base,
           x + baseplate_length / 2, y_bp_top, layer=C.L_THICK)
    C.hatch_area(msp, [(x - baseplate_length / 2, y_base),
                       (x + baseplate_length / 2, y_base),
                       (x + baseplate_length / 2, y_bp_top),
                       (x - baseplate_length / 2, y_bp_top)],
                 scale=s, pattern_scale=0.7)
    # 地脚螺栓
    for f in (-0.42, -0.14, 0.14, 0.42):
        bx = x + baseplate_length * f
        msp.add_line((bx, y_base - C.P(5, s)), (bx, y_bp_top + C.P(2, s)),
                     dxfattribs={"layer": C.L_THIN})

    # ── 基础地面线 ──
    gx0 = x - baseplate_length * 0.72
    gx1 = x + baseplate_length * 0.72
    msp.add_line((gx0, y_base), (gx1, y_base), dxfattribs={"layer": C.L_THICK})
    for i in range(13):
        gx = gx0 + (gx1 - gx0) * i / 12.0
        msp.add_line((gx, y_base), (gx - C.P(3, s), y_base - C.P(3, s)),
                     dxfattribs={"layer": C.L_THIN})

    # ── 泵轴中心线 ──
    C.centerline(msp, (x - baseplate_length * 0.58, cy),
                 (x + baseplate_length * 0.58, cy))

    # ── 蜗壳 + 叶轮 ──
    _volute(msp, x_pump, cy, r_vol, s)
    msp.add_circle((x_pump, cy), impeller_diameter / 2.0,
                   dxfattribs={"layer": C.L_DASH})     # 叶轮外圆（不可见）
    msp.add_circle((x_pump, cy), impeller_diameter * 0.18,
                   dxfattribs={"layer": C.L_MID})      # 轮毂
    for i in range(6):                                  # 叶片示意
        a = math.radians(i * 60.0)
        r0, r1 = impeller_diameter * 0.20, impeller_diameter * 0.48
        msp.add_line((x_pump + r0 * math.cos(a), cy + r0 * math.sin(a)),
                     (x_pump + r1 * math.cos(a + 0.55),
                      cy + r1 * math.sin(a + 0.55)),
                     dxfattribs={"layer": C.L_THIN})

    # ── 泵体支脚 ──
    C.rect(msp, x_pump - r_vol * 0.75, y_bp_top,
           x_pump + r_vol * 0.75, cy - r_vol * 0.72, layer=C.L_THICK)

    # ── 吸入口（轴向，水平进）与排出口（径向，垂直出）——GB/T 5656 单级悬臂式 ──
    nl = max(suction_dn * 1.4, C.P(8, s))
    p_suc = C.nozzle(msp, (x_pump - sgn * r_vol * 0.86, cy),
                     "left" if sgn > 0 else "right",
                     suction_dn, nl, s, tag="进口")
    p_dis = C.nozzle(msp, (x_pump, cy + r_vol), "up",
                     discharge_dn, max(discharge_dn * 1.6, C.P(8, s)), s,
                     tag="出口")

    # ── 密封腔 + 轴承箱 + 泵轴 ──
    shaft_d = max(impeller_diameter * 0.14, 30.0)
    x_seal = x_pump + sgn * r_vol * 0.80
    seal_len = r_vol * 0.45
    C.rect(msp, min(x_seal, x_seal + sgn * seal_len), cy - shaft_d * 1.5,
           max(x_seal, x_seal + sgn * seal_len), cy + shaft_d * 1.5,
           layer=C.L_MID)
    x_brg = x_seal + sgn * seal_len
    brg_len = r_vol * 0.95
    C.rect(msp, min(x_brg, x_brg + sgn * brg_len), cy - shaft_d * 1.9,
           max(x_brg, x_brg + sgn * brg_len), cy + shaft_d * 1.9,
           layer=C.L_THICK)
    C.rect(msp, min(x_brg, x_brg + sgn * brg_len), y_bp_top,
           max(x_brg, x_brg + sgn * brg_len), cy - shaft_d * 1.9,
           layer=C.L_THICK)                          # 轴承座支撑
    x_shaft_end = x_brg + sgn * (brg_len + coupling_gap)
    for d in (-1, 1):
        msp.add_line((x_brg + sgn * brg_len, cy + d * shaft_d / 2),
                     (x_shaft_end, cy + d * shaft_d / 2),
                     dxfattribs={"layer": C.L_THICK})

    # ── 联轴器（GB/T 5272 弹性柱销，带防护罩）──
    cpl_r = shaft_d * 1.7
    for k in (0.15, 0.85):
        cxk = x_brg + sgn * (brg_len + coupling_gap * k)
        C.rect(msp, cxk - C.P(0.8, s), cy - cpl_r, cxk + C.P(0.8, s), cy + cpl_r,
               layer=C.L_THICK)
    C.rect(msp, min(x_brg + sgn * brg_len, x_shaft_end),
           cy - cpl_r * 1.5, max(x_brg + sgn * brg_len, x_shaft_end),
           cy + cpl_r * 1.5, layer=C.L_THIN)          # 联轴器防护罩
    C.leader_note(msp, ((x_brg + sgn * brg_len + x_shaft_end) / 2, cy + cpl_r * 1.5),
                  "弹性柱销联轴器 + 防护罩", s, dx=10, dy=16)

    # ── 电机 ──
    mr = motor_diameter / 2.0
    C.rect(msp, x_motor - motor_length / 2, cy - mr,
           x_motor + motor_length / 2, cy + mr, layer=C.L_THICK)
    for i in range(7):                                 # 机壳散热筋
        fx = x_motor - motor_length * 0.40 + motor_length * 0.80 * i / 6.0
        msp.add_line((fx, cy + mr), (fx, cy + mr * 0.78),
                     dxfattribs={"layer": C.L_THIN})
    C.rect(msp, x_motor - motor_length * 0.30, y_bp_top,
           x_motor + motor_length * 0.30, cy - mr, layer=C.L_THICK)
    C.rect(msp, x_motor - motor_length * 0.16, cy + mr,
           x_motor + motor_length * 0.16, cy + mr * 1.28, layer=C.L_MID)
    C.eng_text(msp, "M", (x_motor, cy), 5.0, s, layer=C.L_TITLE)

    # ── 标注 ──
    if with_dims:
        C.dim_linear(msp, (x - baseplate_length / 2, y_base),
                     (x + baseplate_length / 2, y_base),
                     offset=24, scale=s, label=f"底座 {int(baseplate_length)}")
        C.dim_linear(msp, (x - baseplate_length / 2, y_bp_top),
                     (x - baseplate_length / 2, cy),
                     offset=20, scale=s, label=f"轴心高 {int(shaft_height)}")
        C.leader_note(msp, (x_pump, cy), f"叶轮 φ{int(impeller_diameter)}",
                      s, dx=-26, dy=-20)
        C.leader_note(msp, (x_seal + sgn * seal_len / 2, cy + shaft_d * 1.5),
                      f"{seal_type} GB/T 6556", s, dx=-6 * sgn, dy=22)
        C.leader_note(msp, p_suc, f"吸入口 DN{int(suction_dn)} HG/T 20592",
                      s, dx=-16, dy=-18)
        C.leader_note(msp, p_dis, f"排出口 DN{int(discharge_dn)}",
                      s, dx=14, dy=12)
        C.elevation_mark(msp, (gx0 + C.P(4, s), y_base), "±0.000", s)

    C.eng_text(msp, tag, (x, cy + mr + C.P(34, s)), 5.0, s, layer=C.L_TITLE)
    C.text(msp, name, (x, cy + mr + C.P(28, s)), 3.5, s, layer=C.L_TITLE)

    if with_table:
        C.spec_table(msp, (x + baseplate_length * 0.62, cy + mr + C.P(22, s)), [
            ["流量 Q", flow],
            ["扬程 H", head],
            ["转速 n", speed],
            ["电机功率", motor_power],
            ["输送介质", medium],
            ["材质", material],
            ["执行标准", "GB/T 5656-2008"],
        ], s, col_w=(28.0, 42.0), title="泵性能数据表")

    return {"tag": tag, "base": y_base, "shaft_y": cy,
            "suction": p_suc, "discharge": p_dis,
            "pump_x": x_pump, "motor_x": x_motor}


def draw_centrifugal_pump_symbol(msp, x: float, y: float, scale: float = 50.0,
                                 tag: str = "P-701A", name: str = "离心泵",
                                 flow: str = "", head: str = "", **params):
    """离心泵工艺流程符号 —— 复用 ``hydraulic.draw_pump`` 并补充化工参数标注。

    ``hydraulic.draw_pump`` 提供 GB/T 786.1 液压泵基圆 + 驱动三角；
    此处叠加 P&ID 常用的流量/扬程标注，实现「扩展而非重写」。
    """
    p = {}
    if flow:
        p["Q"] = flow
    if head:
        p["H"] = head
    res = hydraulic.draw_pump(msp, (x, y), p_type="fixed_uni", scale=scale,
                              label=f"{tag} {name}", params=p or None,
                              layer=C.L_EQUIP)
    return res
