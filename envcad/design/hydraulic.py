# -*- coding: utf-8 -*-
"""液压系统设计验算（知识驱动）。

从 knowledge.hyd_data 取标准缸径/活塞杆/压力等级/管路流速，覆盖：
  1) 液压缸设计：所需推力 → 缸径（标准化）+ 流量
  2) 液压泵选择：流量 + 压力 → 排量/驱动功率
  3) 管路管径：流量 + 推荐流速 → 管径
"""
from __future__ import annotations

import math

from ..knowledge import hyd_data


def design_cylinder(F: float, p: float = 16.0, v: float = 0.1,
                    eta: float = None) -> dict:
    """液压缸设计（无杆腔驱动）。

    参数：
        F    工作负载 (kN)
        p    工作压力 (MPa)
        v    活塞运动速度 (m/s)
        eta  缸机械效率（缺省取知识层 0.95）

    公式：
        A = F/(p·η)              需要有效面积
        D = √(4A/π)              缸径 → 标准化
        Q = A·v                  流量
    """
    eta = hyd_data.EFFICIENCY["缸"] if eta is None else eta
    p_grade = hyd_data.next_pressure(p)
    F_N = F * 1000.0
    p_pa = p * 1e6
    A_req = F_N / (p_pa * eta)                     # m²
    D_req = math.sqrt(4.0 * A_req / math.pi) * 1000.0   # mm
    D = hyd_data.next_bore(D_req)
    A = math.pi * (D / 1000.0) ** 2 / 4.0          # m²
    F_actual = A * p_pa * eta / 1000.0             # kN
    d_rod = hyd_data.next_rod(0.5 * D)             # 活塞杆≈0.5D
    Q = A * v * 60000.0                             # L/min (m³/s×60000)
    return dict(
        F=F, p=p, p_grade=p_grade, v=v, eta=eta,
        D_req=round(D_req, 1), D=D, d_rod=d_rod,
        F_actual=round(F_actual, 1), Q=round(Q, 1),
        note=(f"负载 {F}kN、压力 {p}MPa：需缸径 {D_req:.1f}mm → 标准 Φ{D}mm"
              f"（活塞杆 Φ{d_rod}mm），可提供推力 {F_actual:.1f}kN；"
              f"速度 {v}m/s 对应流量 {Q:.1f}L/min"),
    )


def select_pump(Q: float, p: float = 16.0, eta: float = None) -> dict:
    """液压泵选择：流量 + 压力 → 驱动功率。

    参数：Q 系统流量 (L/min)，p 工作压力 (MPa)
    公式：P = p·Q/(60·η)   (kW)
    """
    eta = hyd_data.EFFICIENCY["泵"] if eta is None else eta
    p_grade = hyd_data.next_pressure(p)
    P = p * Q / (60.0 * eta)                        # kW
    # 按 1000rpm 估算泵排量 mL/r
    disp = Q * 1000.0 / 1000.0                      # L/min / (rpm/1000) → mL/r @1000rpm
    return dict(
        Q=Q, p=p, p_grade=p_grade, eta=eta,
        P=round(P, 2), disp=round(disp, 1),
        note=(f"流量 {Q}L/min、压力 {p}MPa（等级 {p_grade}MPa）：驱动功率 "
              f"P=p·Q/60η={P:.2f}kW，泵排量约 {disp:.1f}mL/r(@1000rpm)"),
    )


def size_hyd_pipe(Q: float, kind: str = "压油管", p: float = 16.0) -> dict:
    """液压管径：流量 + 推荐流速 → 内径。

    参数：Q 流量 (L/min)，kind ∈ {吸油管,压油管,回油管}
    公式：d = √(4Q/(π·v))
    """
    if kind == "压油管":
        v = hyd_data.pressure_velocity(p)
    else:
        lo, hi = hyd_data.PIPE_VELOCITY.get(kind, (1.5, 2.5))
        v = (lo + hi) / 2.0
    Qs = Q / 1000.0 / 60.0                          # m³/s
    d = math.sqrt(4.0 * Qs / (math.pi * v)) * 1000.0   # mm
    return dict(
        Q=Q, kind=kind, v=round(v, 1), d=round(d, 1),
        note=(f"{kind}：流量 {Q}L/min，推荐流速 {v:.1f}m/s；"
              f"需要内径 d=√(4Q/πv)={d:.1f}mm"),
    )


def format_cylinder_result(r: dict) -> str:
    return "【液压缸设计】\n" + r["note"]


def format_pump_result(r: dict, pipe: dict = None) -> str:
    lines = ["【液压泵选择】", r["note"]]
    if pipe:
        lines.append("管径：" + pipe["note"])
    return "\n".join(lines)
