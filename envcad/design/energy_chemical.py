# -*- coding: utf-8 -*-
"""能源化工设备设计验算：压力容器壁厚 / 换热器面积 / 塔器流体力学。

从 knowledge.energy_chem_data 取材料许用应力、腐蚀裕量、换热K值等，
输入工艺参数即可完成壁厚校核、换热面积估算与填料塔流体力学计算。
系数取常用工程值，精确设计以规范条文与设备计算书为准。
"""
from __future__ import annotations

import math
from ..knowledge import energy_chem_data as ec
from ..knowledge import proc_data


# ══════════════════════════════════════════════════════════
#  压力容器壁厚校核（GB/T 150 内压圆筒）
# ══════════════════════════════════════════════════════════
def vessel_thickness(p: float, Di: float, material: str = "Q245R",
                     weld_method: str = "双面焊100%RT",
                     corrosion: str = "轻微腐蚀",
                     C1: float = 0.3) -> dict:
    """内压圆筒计算厚度与校核。

    参数：
        p            设计压力 MPa
        Di           内径 mm
        material     材料（取 energy_chem_data.VESSEL_MATERIAL）
        weld_method  焊接接头系数方法
        corrosion    腐蚀裕量等级
        C1           钢板负偏差 mm
    返回：计算壁厚、名义壁厚、各应力分量与结论。
    """
    mat = ec.vessel_material(material)
    phi = ec.weld_factor(weld_method)
    C2 = ec.corrosion_allowance(corrosion)
    allow = mat["allow"]

    # 计算厚度 δ = p×Di / (2×[σ]×φ - p)
    delta = p * Di / (2 * allow * phi - p)       # mm
    delta_n = delta + C1 + C2                     # 名义壁厚
    # 向上圆整
    delta_n_rounded = math.ceil(delta_n * 2) / 2  # 0.5mm 进位

    # 应力校核
    sigma_t = p * (Di + delta) / (2 * delta)      # 计算应力
    ok = sigma_t <= allow * phi

    return dict(
        material=material, p=p, Di=Di, allow=allow, phi=phi,
        delta=round(delta, 2), C1=C1, C2=C2,
        delta_n=round(delta_n, 2), delta_n_rounded=delta_n_rounded,
        sigma_t=round(sigma_t, 1), allow_effective=round(allow * phi, 1),
        ok=ok,
        note=(f"{material} 设计压力 {p}MPa 内径 {Di}mm，计算壁厚 {delta:.2f}mm，"
              f"名义壁厚(含C1+C2) {delta_n:.2f}mm → 取整 {delta_n_rounded}mm，"
              f"σ={sigma_t:.1f}≤[σ]φ={allow*phi:.1f} {'√' if ok else '×'}")
    )


# ══════════════════════════════════════════════════════════
#  换热器面积估算（GB/T 151）
# ══════════════════════════════════════════════════════════
def heat_exchanger_area(Q: float, hot_in: float, hot_out: float,
                        cold_in: float, cold_out: float,
                        pair: str = "水-水(管壳式)") -> dict:
    """换热器传热面积估算。

    参数：
        Q        换热量 kW
        hot_in/out  热流体进出口温度 ℃
        cold_in/out 冷流体进出口温度 ℃
        pair     换热介质对（取 K_EXCHANGER_DETAIL）
    返回：对数平均温差、K值、估算面积。
    """
    # 对数平均温差（逆流）
    dt1 = hot_in - cold_out
    dt2 = hot_out - cold_in
    if dt1 <= 0 or dt2 <= 0:
        raise ValueError(f"温度交叉：ΔT1={dt1:.1f}℃, ΔT2={dt2:.1f}℃")
    if abs(dt1 - dt2) < 1e-6:
        dtm = (dt1 + dt2) / 2
    else:
        dtm = (dt1 - dt2) / math.log(dt1 / dt2)

    K_low, K_high = ec.exchanger_k(pair)
    K = (K_low + K_high) / 2                  # 取中值估算

    A = Q * 1000 / (K * dtm)                   # m²
    A_safety = A * 1.15                        # 加 15% 裕量

    return dict(
        Q=Q, hot_in=hot_in, hot_out=hot_out,
        cold_in=cold_in, cold_out=cold_out,
        dt1=round(dt1, 1), dt2=round(dt2, 1),
        dtm=round(dtm, 1), K=round(K, 0),
        A=round(A, 2), A_safety=round(A_safety, 2),
        note=(f"Q={Q}kW，Δtm={dtm:.1f}℃，K≈{K:.0f} W/(m²·K)，"
              f"估算面积 {A:.2f}m²（含裕量 {A_safety:.2f}m²）"),
    )


# ══════════════════════════════════════════════════════════
#  填料塔流体力学：泛点气速与塔径估算
# ══════════════════════════════════════════════════════════
def packing_tower_diameter(G: float, L: float,
                           rho_g: float = 1.2, rho_l: float = 1000,
                           mu_l: float = 1.0e-3,
                           packing_type: str = "DN38鲍尔环(金属)",
                           ff: float = 0.7) -> dict:
    """填料塔泛点气速与塔径估算（Eckert 关联简化）。

    参数：
        G      气体质量流量 kg/s
        L      液体质量流量 kg/s
        rho_g  气体密度 kg/m³
        rho_l  液体密度 kg/m³
        mu_l   液体黏度 Pa·s
        packing_type 填料类型
        ff     泛点率（操作气速/泛点气速）
    返回：泛点气速、塔径、压降估算。
    """
    pk = ec.packing_prop(packing_type)
    a = pk["a"]          # 比表面积
    eps = pk["eps"]      # 空隙率

    # 流动参数 Flv = (L/G) × √(ρg/ρl)
    if G <= 0:
        raise ValueError("气体流量 G 必须 > 0")
    Flv = (L / G) * math.sqrt(rho_g / rho_l)

    # Eckert 泛点关联系数（简化）：C = f(Flv)，此处用 Billet-Schultes 简化
    # 泛点压降取 ~1.2 kPa/m 对应
    # Cf = 0.5 ~ 0.6 量级，简化取 0.55
    Cf = 0.55
    uf = Cf * math.sqrt(eps**3 / a * (rho_l - rho_g) / rho_g
                        * (1 / (mu_l * 1000)**0.1))   # 泛点气速 m/s

    u_op = uf * ff                                    # 操作气速 m/s
    D = math.sqrt(4 * G / (math.pi * rho_g * u_op))   # 塔径 m

    # 压降估算（干填料+持液）
    dp_per_m = 300 + 800 * ff**2                      # 简化：Pa/m

    return dict(
        Flv=round(Flv, 4), uf=round(uf, 3), u_op=round(u_op, 3),
        D_calc=round(D, 3), D_rounded=math.ceil(D * 10) / 10,
        ff=ff, dp_per_m=round(dp_per_m, 0),
        packing=packing_type, a=a, eps=eps,
        note=(f"Flv={Flv:.4f}，泛点气速 {uf:.3f} m/s，操作气速 {u_op:.3f} m/s，"
              f"塔径 {D:.3f}m → 取整 {math.ceil(D*10)/10:.1f}m",
              f"G={G:.2f}kg/s L={L:.2f}kg/s"),
    )
