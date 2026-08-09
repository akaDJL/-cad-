# -*- coding: utf-8 -*-
"""化工工艺设计验算（知识驱动）。

从 knowledge.proc_data 取管道规格/经济流速/介质物性/换热系数，覆盖：
  1) 经济管径：流量 + 经济流速 → 管径（标准 DN）+ 雷诺数/流态
  2) 泵扬程/功率：流量 + 扬程 → 轴功率/电机功率
  3) 换热器面积：热负荷 + LMTD + 传热系数 → 换热面积
"""
from __future__ import annotations

import math

from ..knowledge import proc_data


def size_econ_pipe(Q: float, medium: str = "水_一般",
                   fluid: str = "水") -> dict:
    """经济管径计算。

    参数：
        Q       体积流量 (m³/h)
        medium  经济流速类别（见 proc_data.ECON_VELOCITY）
        fluid   介质名（取物性算雷诺数）

    公式：
        d = √(4Q/(π·v))          按经济流速取管径 → 标准 DN
        Re = ρ·v·d/μ             校核流态
    """
    lo, hi = proc_data.econ_velocity(medium)
    v = (lo + hi) / 2.0
    Qs = Q / 3600.0                                  # m³/s
    d_req = math.sqrt(4.0 * Qs / (math.pi * v)) * 1000.0   # mm
    dn = proc_data.next_dn(d_req)
    di = proc_data.pipe_di(dn)
    # 实际流速（按标准管内径）
    v_act = Qs / (math.pi * (di / 1000.0) ** 2 / 4.0)
    prop = proc_data.medium_prop(fluid)
    Re = prop["rho"] * v_act * (di / 1000.0) / prop["mu"]
    flow = "层流" if Re < 2300 else ("过渡流" if Re < 4000 else "湍流")
    return dict(
        Q=Q, medium=medium, fluid=fluid, v_econ=round(v, 2),
        d_req=round(d_req, 1), dn=dn, di=di,
        v_act=round(v_act, 2), Re=round(Re, 0), flow=flow,
        note=(f"流量 {Q}m³/h、经济流速 {v:.2f}m/s：需内径 {d_req:.1f}mm → "
              f"标准 DN{dn}(内径 {di}mm)，实际流速 {v_act:.2f}m/s，"
              f"Re={Re:.0f}({flow})"),
    )


def design_pump(Q: float, H: float, fluid: str = "水",
                pump: str = "离心泵", eta: float = None) -> dict:
    """工艺泵扬程/功率计算。

    参数：
        Q     流量 (m³/h)
        H     扬程 (m)
        fluid 介质名（取密度）
        pump  泵型（取效率）

    公式：
        Pa = ρ·g·Q·H/(3.6e6·η)   轴功率 (kW)
        Pm = Pa·k                 电机功率（安全系数 1.15）
    """
    eta = proc_data.PUMP_EFFICIENCY.get(pump, 0.75) if eta is None else eta
    rho = proc_data.medium_prop(fluid)["rho"]
    Qs = Q / 3600.0                                  # m³/s
    Pa = rho * proc_data.G * Qs * H / 1000.0 / eta   # kW (轴功率)
    k = 1.15
    Pm = Pa * k
    return dict(
        Q=Q, H=H, fluid=fluid, pump=pump, eta=eta, rho=rho,
        Pa=round(Pa, 2), Pm=round(Pm, 2), k=k,
        note=(f"流量 {Q}m³/h、扬程 {H}m（{fluid} ρ={rho}）：轴功率 "
              f"Pa=ρgQH/η={Pa:.2f}kW，电机功率(×{k})={Pm:.2f}kW"),
    )


def design_heat_exchanger(Qh: float, pair: str = "水-水",
                          dt_hot=(90.0, 60.0), dt_cold=(20.0, 45.0),
                          arrangement: str = "逆流") -> dict:
    """换热器面积计算（LMTD 法）。

    参数：
        Qh          热负荷 (kW)
        pair        介质配对（取传热系数 K）
        dt_hot      热流体(进,出) ℃
        dt_cold     冷流体(进,出) ℃
        arrangement 逆流/顺流

    公式：
        LMTD = (Δt1-Δt2)/ln(Δt1/Δt2)
        A = Q/(K·LMTD)
    """
    Klo, Khi = proc_data.k_value(pair)
    K = (Klo + Khi) / 2.0                             # W/(m²·K)
    th_in, th_out = dt_hot
    tc_in, tc_out = dt_cold
    if arrangement == "逆流":
        dt1 = th_in - tc_out
        dt2 = th_out - tc_in
    else:  # 顺流
        dt1 = th_in - tc_in
        dt2 = th_out - tc_out
    if dt1 <= 0 or dt2 <= 0:
        lmtd = max(dt1, dt2, 0.1)
    elif abs(dt1 - dt2) < 1e-6:
        lmtd = dt1
    else:
        lmtd = (dt1 - dt2) / math.log(dt1 / dt2)
    A = Qh * 1000.0 / (K * lmtd)                      # m²
    A_design = A * 1.15                               # 15% 裕量
    return dict(
        Qh=Qh, pair=pair, K=round(K, 0), arrangement=arrangement,
        lmtd=round(lmtd, 2), A=round(A, 2), A_design=round(A_design, 2),
        note=(f"热负荷 {Qh}kW、{pair}(K={K:.0f}W/m²K)、{arrangement}："
              f"LMTD={lmtd:.2f}℃，换热面积 A=Q/(K·LMTD)={A:.2f}m²，"
              f"计入 15% 裕量取 {A_design:.2f}m²"),
    )


def format_pipe_result(r: dict) -> str:
    return "【经济管径】\n" + r["note"]


def format_pump_result(r: dict) -> str:
    return "【工艺泵选择】\n" + r["note"]


def format_hx_result(r: dict) -> str:
    return "【换热器选型】\n" + r["note"]
