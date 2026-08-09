# -*- coding: utf-8 -*-
"""桥梁工程设计验算：荷载组合 / 支座选型 / 伸缩缝选型。

从 knowledge.bridge_data 取荷载等级、支座/伸缩缝参数，完成车道荷载
计算、支座承载力选型与伸缩缝位移规格推荐。
"""
from __future__ import annotations

import math
from ..knowledge import bridge_data as bd


# ══════════════════════════════════════════════════════════
#  车道荷载计算
# ══════════════════════════════════════════════════════════
def lane_load(grade: str = "公路-Ⅰ级", L: float = 30,
              n_lanes: int = 2) -> dict:
    """公路车道荷载计算。

    参数：
        grade     荷载等级
        L         计算跨径 m
        n_lanes   车道数
    返回：均布荷载 qk(kN/m)、集中荷载 Pk(kN)、折减后总荷载。
    """
    load = bd.road_load(grade)
    qk = load["qk"]
    Pk = bd.pk_value(grade, L)
    factor = bd.lane_factor(n_lanes)

    q_total = qk * n_lanes * factor               # 折减后均布总荷载 kN/m
    P_total = Pk * n_lanes * factor                # 折减后集中总荷载 kN

    return dict(
        grade=grade, L=L, n_lanes=n_lanes,
        qk=qk, Pk=round(Pk, 1),
        lane_factor=factor,
        q_total=round(q_total, 2), P_total=round(P_total, 1),
        note=(f"{grade} 跨径{L}m {n_lanes}车道：qk={qk}kN/m Pk={Pk:.1f}kN，"
              f"折减后 q={q_total:.2f}kN/m P={P_total:.1f}kN"),
    )


# ══════════════════════════════════════════════════════════
#  板式橡胶支座选型
# ══════════════════════════════════════════════════════════
def bearing_selection(vertical_load: float, shape: str = "矩形") -> dict:
    """桥梁支座承载力选型。

    参数：
        vertical_load  支座竖向力 kN
        shape          矩形/圆形
    返回：推荐支座规格与承载力利用率。
    """
    if shape == "矩形":
        bearings = bd.BEARING_RECT
    else:
        bearings = bd.BEARING_ROUND

    selected = None
    for spec, prop in bearings.items():
        if prop["capacity"] >= vertical_load:
            selected = (spec, prop)
            break

    if selected is None:
        last_spec = list(bearings.items())[-1]
        selected = (last_spec[0], last_spec[1])
        note_extra = "（超出标准范围，建议定制）"
    else:
        note_extra = ""

    spec, prop = selected
    util = vertical_load / prop["capacity"] * 100

    return dict(
        vertical_load=vertical_load, shape=shape,
        bearing_spec=spec, capacity=prop["capacity"],
        utilization=round(util, 1),
        thickness=prop["thickness"],
        ok=(util <= 100),
        note=(f"竖向力 {vertical_load}kN → 推荐 {spec}，"
              f"承载力 {prop['capacity']}kN，利用率 {util:.1f}%{note_extra}"),
    )


# ══════════════════════════════════════════════════════════
#  伸缩缝选型
# ══════════════════════════════════════════════════════════
def expansion_joint_selection(total_displacement: float) -> dict:
    """桥梁伸缩缝规格推荐。

    参数：
        total_displacement  总伸缩量 mm
    返回：推荐型号。
    """
    ej = bd.expansion_joint(total_displacement)
    return dict(
        total_displacement=total_displacement,
        joint_spec=ej["spec"], displacement=ej["displacement"],
        joint_type=ej["type"],
        ok=(total_displacement <= ej["displacement"]),
        note=(f"总伸缩量 {total_displacement}mm → 推荐 {ej['spec']} "
              f"({ej['type']}，允许 {ej['displacement']}mm)"),
    )


# ══════════════════════════════════════════════════════════
#  箱梁高跨比校核
# ══════════════════════════════════════════════════════════
def box_girder_hd_check(beam_type: str = "等截面连续梁",
                        span: float = 30, height: float = 1.6) -> dict:
    """箱梁高跨比范围校核。

    参数：
        beam_type  梁型
        span       跨径 m
        height     梁高 m
    返回：实际高跨比与推荐范围比较。
    """
    hd_low, hd_high = bd.BOX_GIRDER_HD.get(beam_type, (1/18, 1/25))
    actual_hd = height / span
    ok = hd_low <= actual_hd <= hd_high
    return dict(
        beam_type=beam_type, span=span, height=height,
        hd_actual=round(actual_hd, 4),
        hd_low=round(hd_low, 4), hd_high=round(hd_high, 4),
        ok=ok,
        note=(f"{beam_type} 跨径{span}m 梁高{height}m，"
              f"高跨比 {actual_hd:.4f}，推荐 {hd_low:.3f}~{hd_high:.3f} "
              f"{'√' if ok else '×'}"),
    )
