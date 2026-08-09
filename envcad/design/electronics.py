# -*- coding: utf-8 -*-
"""电子硬件设计验算：PCB 温升载流 / 散热器热阻 / 微带线阻抗。

从 knowledge.electronics_data 取铜厚/基材参数，输入 PCB 几何与
电参数即可完成走线载流校核、散热器热阻估算与微带线特性阻抗计算。
系数取常用工程值，精确设计以仿真与实测为准。
"""
from __future__ import annotations

import math
from ..knowledge import electronics_data as ed


# ══════════════════════════════════════════════════════════
#  PCB 走线载流估算（IPC-2221 简化）
# ══════════════════════════════════════════════════════════
def pcb_trace_current(width: float, copper_oz: str = "1oz",
                      delta_T: float = 10, layer: str = "outer") -> dict:
    """PCB 走线载流量估算。

    参数：
        width      走线宽度 mm
        copper_oz  铜厚 "0.5oz"/"1oz"/"2oz"
        delta_T    允许温升 ℃
        layer      "outer" 外层 / "inner" 内层
    返回：估算载流量、温升对应的最大允许电流。
    """
    ipc = ed.IPC_CURRENT[layer]
    thickness = ed.COPPER_WEIGHT[copper_oz]  # μm
    # 截面积 mil² (1mil=0.0254mm)
    area_mil2 = (width / 0.0254) * (thickness / 25.4)
    I = ipc["k"] * (delta_T ** ipc["b"]) * (area_mil2 ** ipc["c"])

    # 反向计算：该线宽在给定温升下的安全载流量
    return dict(
        width=width, copper_oz=copper_oz, thickness_um=thickness,
        delta_T=delta_T, layer=layer, I=round(I, 2),
        note=(f"{width}mm {copper_oz}铜 {layer}层，ΔT={delta_T}℃ 载流约 {I:.2f}A")
    )


# ══════════════════════════════════════════════════════════
#  散热器热阻估算
# ══════════════════════════════════════════════════════════
def heatsink_thermal(Pd: float, T_j_max: float = 125,
                     T_amb: float = 45,
                     R_jc: float = 1.5, R_cs: float = 0.5,
                     material: str = "铝6063",
                     h: float = 10) -> dict:
    """散热器热阻与所需面积估算。

    参数：
        Pd      耗散功率 W
        T_j_max 结温上限 ℃
        T_amb   环境温度 ℃
        R_jc    结到壳热阻 ℃/W
        R_cs    壳到散热器热阻 ℃/W
        material 散热器材料
        h       对流换热系数 W/(m²·K)，自然对流5~10，强制风冷15~50
    返回：允许热阻、所需散热面积。
    """
    delta_T = T_j_max - T_amb
    R_total = delta_T / Pd                        # 允许总热阻
    R_hs = R_total - R_jc - R_cs                  # 散热器允许热阻

    if R_hs <= 0:
        return dict(ok=False, R_total=round(R_total, 2),
                    R_hs=round(R_hs, 3),
                    note="允许热阻不足，需增大散热或降低环境温度")

    # 散热面积估算：A ≈ 1/(R_hs × h)  简化公式
    A = 1.0 / (R_hs * h) * 1000                  # 换算为 cm²
    k_mat = ed.HEATSINK_MATERIAL[material]

    return dict(
        Pd=Pd, T_j_max=T_j_max, T_amb=T_amb, delta_T=delta_T,
        R_jc=R_jc, R_cs=R_cs, R_hs=round(R_hs, 3), R_total=round(R_total, 2),
        A_cm2=round(A, 1), h=h, material=material, k_mat=k_mat,
        ok=True,
        note=(f"Pd={Pd}W，ΔT={delta_T}℃，允许热阻 R_hs≈{R_hs:.3f}℃/W，"
              f"所需散热面积约 {A:.1f}cm² (h={h} W/(m²·K))"),
    )


# ══════════════════════════════════════════════════════════
#  微带线特性阻抗估算（简化公式，适用于 FR-4）
# ══════════════════════════════════════════════════════════
def microstrip_impedance(w: float, h: float = 1.6,
                         t: float = 0.035, er: float = 4.5) -> dict:
    """微带线特性阻抗估算。

    参数：
        w     导线宽度 mm
        h     介质厚度 mm（板厚减去铜厚）
        t     铜箔厚度 mm（1oz≈0.035）
        er    基材相对介电常数
    返回：特性阻抗 Z0 Ω。
    """
    # 有效宽度修正
    if w / h > 1:
        we = w + t / math.pi * (1 + math.log(2 * h / t))
    else:
        we = w + t / math.pi * (1 + math.log(4 * math.pi * w / t))

    # Wheeler 公式
    if we / h <= 1:
        ee = (er + 1) / 2 + (er - 1) / 2 * (1 / math.sqrt(1 + 12 * h / we)
             + 0.04 * (1 - we / h)**2)
        Z0 = 60 / math.sqrt(ee) * math.log(8 * h / we + we / (4 * h))
    else:
        ee = (er + 1) / 2 + (er - 1) / 2 * (1 / math.sqrt(1 + 12 * h / we))
        Z0 = 120 * math.pi / (math.sqrt(ee)
             * (we / h + 1.393 + 0.667 * math.log(we / h + 1.444)))

    return dict(
        w=w, h=h, t=t, er=er, we=round(we, 4),
        ee=round(ee, 3), Z0=round(Z0, 1),
        note=f"w={w}mm h={h}mm t={t}mm εr={er} → Z0≈{Z0:.1f}Ω",
    )
