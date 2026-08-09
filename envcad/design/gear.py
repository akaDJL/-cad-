# -*- coding: utf-8 -*-
"""直齿圆柱齿轮强度校核（知识驱动，简化 GB/T 3480）。

从 knowledge.mech_data 取材料疲劳极限与标准模数，给定传动功率、
转速与齿数即可算出齿轮几何并完成接触/弯曲疲劳强度校核，给出安全
系数与结论。系数取常用工程值，精确设计以规范条文与工况系数为准。
"""
from __future__ import annotations

import math

from ..knowledge import mech_data

# 齿形系数 YFa 与应力校正系数 YSa（α=20°, ha*=1 外啮合标准直齿，节选）
_YFA = {17: 2.97, 18: 2.91, 19: 2.85, 20: 2.80, 22: 2.72, 25: 2.62,
        30: 2.52, 35: 2.45, 40: 2.40, 45: 2.35, 50: 2.32, 60: 2.28,
        80: 2.22, 100: 2.18}
_YSA = {17: 1.52, 18: 1.53, 19: 1.54, 20: 1.55, 22: 1.57, 25: 1.59,
        30: 1.625, 35: 1.65, 40: 1.67, 45: 1.68, 50: 1.70, 60: 1.73,
        80: 1.77, 100: 1.79}


def _interp(tbl: dict, z: int) -> float:
    keys = sorted(tbl)
    if z <= keys[0]:
        return tbl[keys[0]]
    if z >= keys[-1]:
        return tbl[keys[-1]]
    for i in range(len(keys) - 1):
        a, b = keys[i], keys[i + 1]
        if a <= z <= b:
            t = (z - a) / (b - a)
            return tbl[a] + t * (tbl[b] - tbl[a])
    return tbl[keys[-1]]


def check_spur_gear(power: float, n1: float, z1: int = 20, z2: int = 60,
                    mn: float = None, phi_d: float = 1.0,
                    material: str = "45钢",
                    K: float = 1.4, ZE: float = 189.8,
                    ZH: float = 2.5, Zeps: float = 0.88,
                    Yeps: float = 0.70, YST: float = 2.0,
                    SH: float = 1.0, SF: float = 1.4) -> dict:
    """直齿圆柱齿轮接触+弯曲强度校核。

    参数：
        power   传递功率 (kW)
        n1      小齿轮转速 (rpm)
        z1,z2   小/大齿轮齿数
        mn      模数 (mm)，缺省按弯曲强度初估并圆整到标准模数
        phi_d   齿宽系数 b/d1
        material 小齿轮材料（取 knowledge.mech_data）
    返回：几何、应力、许用应力与安全系数、结论。
    """
    mat = mech_data.material_props(material)
    if mat["sH_lim"] is None or mat["sF_lim"] is None:
        raise ValueError(f"材料 {material} 缺少齿轮疲劳极限数据，请选调质/淬火钢")

    T1 = 9.55e6 * power / n1                 # N·mm
    u = z2 / z1
    YFa = _interp(_YFA, z1)
    YSa = _interp(_YSA, z1)

    # 许用应力
    sHP = mat["sH_lim"] / SH
    sFP = mat["sF_lim"] * YST / SF

    # 缺省模数：分别按弯曲、接触强度设计式初估，取较大者圆整
    # 软齿面(HB≤350)通常接触强度控制，硬齿面弯曲强度控制——取大值可兼顾两者
    if mn is None:
        # 弯曲：m ≥ (2·K·T1·YFa·YSa·Yε / (φd·z1²·[σF]))^(1/3)
        m_bend = (2 * K * T1 * YFa * YSa * Yeps
                  / (phi_d * z1 * z1 * sFP)) ** (1.0 / 3.0)
        # 接触：d1 ≥ ((2·K·T1·(u+1)/(φd·u))·(ZE·ZH·Zε/[σH])²)^(1/3)，m = d1/z1
        d1_cont = ((2 * K * T1 * (u + 1) / (phi_d * u))
                   * (ZE * ZH * Zeps / sHP) ** 2) ** (1.0 / 3.0)
        m_cont = d1_cont / z1
        m_calc = max(m_bend, m_cont)
        mn = mech_data.round_to_module(m_calc)
    else:
        m_calc = mn

    d1 = mn * z1
    d2 = mn * z2
    a = (d1 + d2) / 2.0                      # 中心距
    b = phi_d * d1                           # 齿宽

    # 接触应力
    sH = ZE * ZH * Zeps * math.sqrt(
        2 * K * T1 * (u + 1) / (b * d1 * d1 * u))
    # 弯曲应力
    sF = 2 * K * T1 * YFa * YSa * Yeps / (b * d1 * mn)

    return dict(
        material=material, power=power, n1=n1, z1=z1, z2=z2, u=round(u, 3),
        T1=round(T1, 0), mn=mn, m_calc=round(m_calc, 3),
        d1=round(d1, 2), d2=round(d2, 2), a=round(a, 2), b=round(b, 1),
        sH=round(sH, 1), sHP=round(sHP, 1), SH_calc=round(sHP / sH, 2),
        sF=round(sF, 1), sFP=round(sFP, 1), SF_calc=round(sFP / sF, 2),
        sH_ok=(sH <= sHP), sF_ok=(sF <= sFP),
        all_ok=(sH <= sHP and sF <= sFP),
        note=(f"{material} 直齿轮 z1={z1}/z2={z2}(u={u:.2f})，m={mn}mm，"
              f"d1={d1:.1f}/d2={d2:.1f}mm，a={a:.1f}mm，b={b:.0f}mm；"
              f"σH={sH:.0f}≤[{sHP:.0f}] {'√' if sH <= sHP else '×'}，"
              f"σF={sF:.0f}≤[{sFP:.0f}] {'√' if sF <= sFP else '×'}"),
    )


def format_gear_result(r: dict) -> str:
    lines = ["【直齿圆柱齿轮强度校核】"]
    lines.append(f"材料 {r['material']}，功率 {r['power']} kW，转速 {r['n1']} rpm")
    lines.append(f"齿数 z1={r['z1']}/z2={r['z2']}（传动比 u={r['u']}），T1={r['T1']:.0f} N·mm")
    lines.append(f"模数 m={r['mn']} mm（计算 {r['m_calc']}），d1={r['d1']}/d2={r['d2']} mm，"
                 f"中心距 a={r['a']} mm，齿宽 b={r['b']} mm")
    lines.append(f"接触：σH={r['sH']} ≤ [σH]={r['sHP']}，安全系数 {r['SH_calc']}，"
                 f"{'满足' if r['sH_ok'] else '不满足'}")
    lines.append(f"弯曲：σF={r['sF']} ≤ [σF]={r['sFP']}，安全系数 {r['SF_calc']}，"
                 f"{'满足' if r['sF_ok'] else '不满足'}")
    lines.append("结论：" + ("强度满足" if r["all_ok"] else "强度不足，需增大模数/齿宽或提高材料"))
    return "\n".join(lines)
