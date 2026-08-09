# -*- coding: utf-8 -*-
"""轴的强度设计与校核（知识驱动，机械）。

两步法，对标机械设计手册：
  1) 按扭转强度初估最小轴径 d ≥ A0·(P/n)^(1/3)，圆整到标准直径
  2) 按弯扭合成强度校核危险截面 σca = √(M² + (αT)²)/W ≤ [σ-1b]

材料许用弯曲应力 [σ-1b] 按抗拉强度插值取值（濮良贵《机械设计》常用表）。
"""
from __future__ import annotations

import math

from ..knowledge import mech_data

# 按扭转强度初估的系数 A0（与许用扭剪应力对应）
_A0 = {
    "Q235": 158.0, "35钢": 126.0, "45钢": 112.0,
    "45钢(表面淬火)": 112.0, "40Cr": 103.0, "40Cr(表面淬火)": 103.0,
    "20CrMnTi": 100.0, "QT600-3": 125.0, "HT200": 160.0, "2A12铝": 150.0,
}

# 对称循环许用弯曲应力 [σ-1b] 随 σb 变化 (N/mm²)
_SIGMA_1B = {400: 40, 500: 45, 600: 55, 700: 60, 800: 65, 1000: 70, 1200: 75}


def allowable_sigma_1b(sb: float) -> float:
    """按抗拉强度插值取对称循环许用弯曲应力 [σ-1b]。"""
    keys = sorted(_SIGMA_1B)
    if sb <= keys[0]:
        return _SIGMA_1B[keys[0]]
    if sb >= keys[-1]:
        return _SIGMA_1B[keys[-1]]
    for i in range(len(keys) - 1):
        a, b = keys[i], keys[i + 1]
        if a <= sb <= b:
            t = (sb - a) / (b - a)
            return _SIGMA_1B[a] + t * (_SIGMA_1B[b] - _SIGMA_1B[a])
    return _SIGMA_1B[keys[-1]]


def estimate_diameter(power: float, n: float, material: str = "45钢",
                      A0: float = None, keyway: bool = True) -> dict:
    """按扭转强度初估最小轴径。

    参数：
        power    传递功率 (kW)
        n        轴转速 (rpm)
        material 轴材料
        keyway   有单键槽时轴径放大 5%
    """
    A0 = _A0.get(material, 112.0) if A0 is None else A0
    d0 = A0 * (power / n) ** (1.0 / 3.0)         # mm
    if keyway:
        d0 *= 1.05
    d_std = mech_data.round_to_std_diameter(d0)
    return dict(
        power=power, n=n, material=material, A0=A0,
        d_calc=round(d0, 2), d=d_std,
        note=(f"{material} 轴：P={power}kW，n={n}rpm，A0={A0}；"
              f"初估 d≥{d0:.1f}mm{'(含键槽放大)' if keyway else ''} → 取标准 d={d_std}mm"),
    )


def check_strength(d: float, M: float, T: float, material: str = "45钢",
                   alpha: float = 0.6) -> dict:
    """弯扭合成强度校核。

    参数：
        d        校核截面直径 (mm)
        M        该截面合成弯矩 (N·mm)
        T        扭矩 (N·mm)
        alpha    扭转切应力循环特性折合系数（脉动 0.6，对称 1.0，静 0.3）
    """
    mat = mech_data.material_props(material)
    sb = mat["sb"]
    W = math.pi * d ** 3 / 32.0                   # 抗弯截面系数
    sigma_ca = math.sqrt(M * M + (alpha * T) ** 2) / W
    allow = allowable_sigma_1b(sb)
    return dict(
        d=d, M=M, T=T, alpha=alpha, W=round(W, 1),
        sigma_ca=round(sigma_ca, 1), allow=round(allow, 1),
        safety=round(allow / sigma_ca, 2) if sigma_ca > 0 else float("inf"),
        ok=(sigma_ca <= allow),
        note=(f"截面 d={d}mm，M={M:.0f}、T={T:.0f} N·mm；"
              f"σca={sigma_ca:.1f} ≤ [σ-1b]={allow:.0f} N/mm² "
              f"{'√满足' if sigma_ca <= allow else '×不足'}"),
    )


def design_shaft(power: float, n: float, M: float = None, T: float = None,
                 material: str = "45钢") -> dict:
    """一步到位：初估轴径 + 用估得直径做弯扭合成校核。

    若未给 M/T，则按传递扭矩 T=9.55e6·P/n 估算，弯矩按 T 的 0.6 倍粗估。
    """
    est = estimate_diameter(power, n, material)
    if T is None:
        T = 9.55e6 * power / n
    if M is None:
        M = 0.6 * T
    chk = check_strength(est["d"], M, T, material)
    return dict(estimate=est, check=chk,
                all_ok=chk["ok"],
                d=est["d"])


def format_shaft_result(r: dict) -> str:
    lines = ["【轴的强度设计】"]
    lines.append(r["estimate"]["note"])
    lines.append(r["check"]["note"])
    lines.append("结论：" + ("轴径满足强度" if r["all_ok"] else "需增大轴径或提高材料"))
    return "\n".join(lines)
