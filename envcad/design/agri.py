# -*- coding: utf-8 -*-
"""农业食品机械设计验算：灌溉水力 / 螺旋输送机功率 / 包装速度。

从 knowledge.agri_data 取灌溉定额、输送机参数等，完成灌溉管网
水力计算、螺旋输送机轴功率与包装机生产节拍估算。
"""
from __future__ import annotations

import math
from ..knowledge import agri_data as ag


# ══════════════════════════════════════════════════════════
#  灌溉管网水力计算（滴灌/微喷主管）
# ══════════════════════════════════════════════════════════
def irrigation_main_pipe(area: float, crop: str = "蔬菜(露地)",
                         method: str = "滴灌",
                         daily_hours: float = 12) -> dict:
    """灌溉主管设计流量与管径估算。

    参数：
        area        灌溉面积 亩（=666.67 m²）
        crop        作物类型
        method      灌溉方式（滴灌/微喷/喷灌）
        daily_hours 日运行小时数 h
    返回：设计流量、推荐管径。
    """
    ET = ag.IRRIGATION_ET.get(crop, 5)              # mm/d
    Cu = ag.IRRIGATION_UNIFORMITY.get(method, 0.90)

    # 日需水量 m³/d
    Q_day = ET / 1000 * area * 666.67 / Cu
    # 系统流量 m³/h
    Q_sys = Q_day / daily_hours
    Q_Ls = Q_sys / 3.6                               # L/s

    # 按经济流速选管径
    v_low, v_high = ag.IRR_VELOCITY["主管"]
    v = (v_low + v_high) / 2                        # m/s
    d_calc = math.sqrt(4 * Q_Ls / (1000 * math.pi * v)) * 1000  # mm

    # 向上取标准管径
    d_select = ag.IRR_PIPE_DN[-1]
    for dn in ag.IRR_PIPE_DN:
        if dn >= d_calc:
            d_select = dn
            break

    return dict(
        area_mu=area, crop=crop, method=method,
        ET=ET, Cu=Cu, Q_day=round(Q_day, 2),
        daily_hours=daily_hours, Q_sys=round(Q_sys, 2),
        Q_Ls=round(Q_Ls, 2), v=v, d_calc=round(d_calc, 1),
        d_select=d_select,
        note=(f"{area}亩 {crop} {method}，日需水 {Q_day:.1f}m³，"
              f"设计流量 {Q_sys:.1f}m³/h({Q_Ls:.1f}L/s)，"
              f"建议管径 DN{d_select}"),
    )


# ══════════════════════════════════════════════════════════
#  螺旋输送机轴功率计算
# ══════════════════════════════════════════════════════════
def screw_conveyor_power(Q: float, L: float, H: float = 0,
                         material_type: str = "颗粒(化肥/饲料)",
                         D: float = None) -> dict:
    """螺旋输送机轴功率估算。

    参数：
        Q             输送量 t/h
        L             输送长度 m
        H             提升高度 m（水平输送H=0）
        material_type 物料类型
        D             螺旋直径 mm，缺省按填充系数 0.3 估算
    返回：轴功率、电机功率（含1.2裕量）。
    """
    psi = ag.SCREW_FILL.get(material_type, 0.30)
    omega = ag.SCREW_RESISTANCE.get(
        {"颗粒(化肥/饲料)": "谷物/面粉",
         "小块(煤/石子)": "煤粉",
         "磨琢性(砂/矿粉)": "灰渣"}.get(material_type, "谷物/面粉"), 1.9)

    if D is None:
        # D ≈ sqrt(Q/(47×ψ×ρ×n×C))  简化：ρ≈1t/m³ n≈50rpm C≈1 D单位m
        D_calc = math.sqrt(Q / (47 * psi * 1.0 * 50 * 1.0)) * 1000  # mm
        # 向上取标准螺旋直径
        D = ag.SCREW_DIAMETER[-1]
        for d in ag.SCREW_DIAMETER:
            if d >= D_calc:
                D = d
                break
    else:
        D_calc = D

    # 轴功率 P = Q×(ω×L±H)/367  (kW)
    P_axis = Q * (omega * L + H) / 367
    P_motor = P_axis * 1.2 / 0.85                  # 含传动效率0.85与1.2裕量

    return dict(
        Q=Q, L=L, H=H, material_type=material_type,
        psi=psi, omega=omega,
        D_calc=round(D_calc, 0) if isinstance(D_calc, float) else D_calc,
        D_selected=D,
        P_axis=round(P_axis, 2), P_motor=round(P_motor, 2),
        note=(f"Q={Q}t/h L={L}m H={H}m {material_type}，"
              f"螺旋直径 D{D}mm，轴功率 {P_axis:.2f}kW，"
              f"建议电机功率 {math.ceil(P_motor/0.5)*0.5:.1f}kW"),
    )


# ══════════════════════════════════════════════════════════
#  包装机节拍估算
# ══════════════════════════════════════════════════════════
def packaging_capacity(machine_type: str = "枕式包装机",
                       bag_length: float = 150) -> dict:
    """包装机产能估算。

    参数：
        machine_type  包装机类型
        bag_length    袋长 mm
    返回：理论产能范围。
    """
    p = ag.PACKAGING.get(machine_type)
    if p is None:
        raise ValueError(f"未知包装机类型: {machine_type}")
    spd_low, spd_high = p["speed"]
    return dict(
        machine_type=machine_type, bag_length=bag_length,
        speed_range=f"{spd_low}~{spd_high} {p['unit']}",
        note=f"{machine_type} 袋长{bag_length}mm，理论产能 {spd_low}~{spd_high} {p['unit']}",
    )
