# -*- coding: utf-8 -*-
"""环境应急设计验算：风险物质 Q 值计算 / 应急池容积 / 围堰校核 /
大气风险扩散估算。

从 knowledge.emergency_data 取风险物质临界量、应急池参数等，
完成Q值累计判定、应急池容积计算、围堰容积校核与烟团扩散距离估算。
"""
from __future__ import annotations

import math
from ..knowledge import emergency_data as em


# ══════════════════════════════════════════════════════════
#  环境风险物质 Q 值累计
# ══════════════════════════════════════════════════════════
def risk_q_calc(substances: list) -> dict:
    """环境风险物质总量与临界量比值 Q 计算。

    参数：
        substances  [(名称, 在线量t), ...]
    返回：每种物质的 q/Q 比值、累计 Q、是否构成重大危险源。
    """
    details = []
    Q_total = 0
    for name, amount in substances:
        q_crit = em.substance_q(name)
        qi = amount / q_crit if q_crit > 0 else 0
        Q_total += qi
        details.append(dict(
            name=name, amount=amount, q_crit=q_crit, qi=round(qi, 4),
            note=f"{name} {amount}t / {q_crit}t = {qi:.4f}",
        ))

    major = Q_total >= 1.0
    return dict(
        substances=details, Q_total=round(Q_total, 4),
        major=major,
        level="重大" if Q_total >= 1 else "一般",
        note=(f"累计 Q={Q_total:.4f}，"
              f"{'≥1 构成重大危险源' if major else '<1 未构成重大危险源'}"),
    )


# ══════════════════════════════════════════════════════════
#  应急池容积计算
# ══════════════════════════════════════════════════════════
def emergency_pool_volume(V1: float, fire_flow: float = 30,
                          duration: float = 3,
                          rain_thickness: float = 20,
                          pool_area: float = 500,
                          V3: float = 0) -> dict:
    """事故应急池有效容积计算。

    参数：
        V1            最大单罐/装置泄漏量 m³
        fire_flow     室外消防流量 L/s
        duration      火灾延续时间 h
        rain_thickness 设计暴雨厚度 mm
        pool_area     汇水面积 m²
        V3            可转输量 m³
    返回：V1/V2/V3 分项与总容积。
    """
    ep = em.EMERGENCY_POOL
    # V2 = 消防废水 + 雨水量
    V2_fire = fire_flow * duration * 3600 / 1000 * ep["runoff_coeff"]
    V2_rain = rain_thickness / 1000 * pool_area * ep["rain_area_factor"]
    V2 = V2_fire + V2_rain

    V = em.calc_emergency_pool_v(V1=V1, V2_fire=V2, V3=V3)

    return dict(
        V1=round(V1, 1), V2_fire=round(V2_fire, 1),
        V2_rain=round(V2_rain, 1), V2=round(V2, 1),
        V3=V3, V_total=round(V, 1),
        note=(f"V1(泄漏)={V1:.0f} + V2(消防+雨水)={V2:.0f} - V3(转输)={V3:.0f} "
              f"→ 应急池 {V:.0f}m³（含安全系数{ep['safety_factor']}）"),
    )


# ══════════════════════════════════════════════════════════
#  围堰容积校核
# ══════════════════════════════════════════════════════════
def dike_check(tank_volume: float, dike_area: float,
               dike_height: float = 1.2) -> dict:
    """防火堤/围堰容积校核。

    参数：
        tank_volume   最大储罐容积 m³
        dike_area     围堰内底面积 m²
        dike_height   围堰有效高度 m
    返回：围堰有效容积与达标判定。
    """
    di = em.DIKE
    dike_volume = dike_area * dike_height
    ok = dike_volume >= tank_volume
    return dict(
        tank_volume=tank_volume, dike_area=dike_area,
        dike_height=dike_height, dike_volume=round(dike_volume, 1),
        capacity_factor=di["capacity_factor"],
        ok=ok,
        note=(f"储罐 {tank_volume}m³ 围堰 {dike_area}×{dike_height}m "
              f"= {dike_volume:.0f}m³ ≥ {tank_volume}m³ "
              f"{'√' if ok else '× 不满足'}"),
    )


# ══════════════════════════════════════════════════════════
#  大气风险烟团扩散距离估算（简化 Pasquill-Gifford）
# ══════════════════════════════════════════════════════════
def plume_distance(Q_leak: float, duration: float = 600,
                   wind_speed: float = 2.0,
                   stab_class: str = "D",
                   endpoint: float = 100,
                   release_height: float = 0) -> dict:
    """连续泄漏烟团扩散-最大落地浓度距离估算。

    参数：
        Q_leak          泄漏速率 g/s
        duration        泄漏持续时间 s
        wind_speed      风速 m/s
        stab_class      大气稳定度 A~F
        endpoint        毒性终点浓度 mg/m³
        release_height  释放高度 m
    返回：最大落地浓度距离、下风向风险距离。
    """
    sp = em.stability_param(stab_class)
    a = sp["a"]
    b = sp["b"]

    # 高斯烟团简化：σy = a × x^b, σz = c × x^d
    # 最大落地浓度发生在 σz = H/√2（地面源时 x→0 最大）
    # 简化为：C(x) = Q/(π·u·σy·σz)
    # 求 C(x) = endpoint 的 x（风险距离）
    # 取 c≈0.8a, d≈b（简化）

    c_val = 0.8 * a
    d_val = b

    # σy·σz = Q/(π·u·C)
    product = Q_leak * 1e-3 / (math.pi * wind_speed * endpoint * 1e-3)

    # 解 a·x^b · c·x^d = a·c·x^(b+d) = product
    # x = (product/(a*c))^(1/(b+d))
    x_risk = (product / (a * c_val)) ** (1.0 / (b + d_val))

    return dict(
        Q_leak=Q_leak, duration=duration, wind_speed=wind_speed,
        stab_class=stab_class, endpoint=endpoint,
        a=a, b=b,
        x_max_risk=round(x_risk, 1),
        note=(f"Q={Q_leak}g/s u={wind_speed}m/s {stab_class}类 "
              f"终点{endpoint}mg/m³ → 下风向风险距离约 {x_risk:.0f}m"),
    )
