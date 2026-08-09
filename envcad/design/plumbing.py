# -*- coding: utf-8 -*-
"""给排水设计验算（知识驱动）。

从 knowledge.plumb_data 取用水定额/器具当量/管材流速/排水坡度，覆盖：
  1) 生活用水量计算（定额法）：人数/床位 → 最高日/最大时/设计秒流量
  2) 给水设计秒流量（当量法）+ 管径水力计算（流速校验）
  3) 排水设计流量 + 横管坡度选取
  4) 给水泵扬程估算
"""
from __future__ import annotations

import math

from ..knowledge import plumb_data


def design_water_demand(number: float, kind: str = "办公楼") -> dict:
    """生活用水量计算（定额法）。number 为用水单位数（人/床/学生）。"""
    q = plumb_data.water_quota(kind)
    Qd = q["q"] * number / 1000.0                 # 最高日用水量 m³/d
    Qh_avg = Qd / q["hours"]                       # 平均时 m³/h
    Qh_max = Qh_avg * q["Kh"]                      # 最大时 m³/h
    Qs = Qh_max * 1000.0 / 3600.0                  # 最大时秒流量 L/s
    return dict(
        kind=kind, number=number, quota=q["q"], unit=q["unit"],
        Qd=round(Qd, 1), Qh_avg=round(Qh_avg, 2), Qh_max=round(Qh_max, 2),
        Qs=round(Qs, 2), Kh=q["Kh"],
        note=(f"{kind}：用水定额 {q['q']}{q['unit']}，用水单位 {number}；"
              f"最高日 {Qd:.1f}m³/d，最大时 {Qh_max:.2f}m³/h(Kh={q['Kh']})，"
              f"最大时秒流量 {Qs:.2f}L/s"),
    )


def design_supply_flow(Ng: float, alpha: float = 2.5) -> dict:
    """给水设计秒流量（当量法，GB50015 概率法）。

    公式：qg = 0.2·α·√Ng   (L/s)
        Ng    给水当量总数
        alpha 建筑物系数（住宅≈2.0~2.5，办公取小）
    """
    qg = 0.2 * alpha * math.sqrt(Ng)
    return dict(
        Ng=Ng, alpha=alpha, qg=round(qg, 2),
        note=f"给水当量 Ng={Ng}，α={alpha}；设计秒流量 qg=0.2·α·√Ng={qg:.2f}L/s",
    )


def size_supply_pipe(qg: float, v_target: float = 1.2) -> dict:
    """按设计秒流量选给水管径，并校验实际流速 ≤ 允许值。

    参数：qg 设计秒流量 (L/s)，v_target 目标流速 (m/s)
    公式：d = √(4·Q/(π·v))，Q = qg/1000 (m³/s)
    """
    Q = qg / 1000.0                                # m³/s
    d_req = math.sqrt(4.0 * Q / (math.pi * v_target)) * 1000.0   # mm
    dn = plumb_data.next_dn(d_req)
    di = plumb_data.pipe_di(dn)
    v_actual = Q / (math.pi * (di / 1000.0) ** 2 / 4.0)
    vmax = plumb_data.PIPE_SPEC.get(dn, dict(vmax=2.0))["vmax"]
    return dict(
        qg=qg, d_req=round(d_req, 1), dn=dn, di=di,
        v_actual=round(v_actual, 2), vmax=vmax, ok=(v_actual <= vmax),
        note=(f"qg={qg}L/s，需要内径 {d_req:.1f}mm → 选 DN{dn}(内径{di}mm)，"
              f"实际流速 {v_actual:.2f}m/s {'≤' if v_actual <= vmax else '>'} {vmax}m/s"),
    )


def design_drainage(Np: float, alpha: float = 1.5,
                    qmax: float = 1.5) -> dict:
    """排水设计流量（GB50015）：qp = 0.12·α·√Np + qmax。

    参数：Np 排水当量总数，alpha 系数，qmax 最大一个卫生器具排水流量 (L/s)
    """
    qp = 0.12 * alpha * math.sqrt(Np) + qmax
    # 按排水流量粗选横管管径（塑料管，充满度控制，经验）
    if qp <= 1.5:
        dn = 75
    elif qp <= 4.0:
        dn = 110
    elif qp <= 8.0:
        dn = 125
    else:
        dn = 160
    std_slope, min_slope = plumb_data.drain_slope(dn)
    return dict(
        Np=Np, alpha=alpha, qp=round(qp, 2), dn=dn,
        slope=std_slope, min_slope=min_slope,
        note=(f"排水当量 Np={Np}；设计流量 qp=0.12·α·√Np+qmax={qp:.2f}L/s → "
              f"横管 DN{dn}，标准坡度 {std_slope*1000:.0f}‰(最小 {min_slope*1000:.1f}‰)"),
    )


def design_pump_head(static_lift: float, length: float = 30.0,
                     i: float = 0.05, residual: float = 10.0) -> dict:
    """给水泵扬程估算：H = Hst + hf + H0。

    参数：
        static_lift 几何提升高度 Hst (m)
        length      管路计算长度 (m)
        i           单位长度水头损失 (m/m，含局部当量，缺省 0.05)
        residual    流出水头/富余 H0 (m)
    """
    hf = i * length
    H = static_lift + hf + residual
    return dict(
        static=static_lift, length=length, hf=round(hf, 2),
        residual=residual, H=round(H, 1),
        note=(f"扬程 H=Hst+hf+H0={static_lift}+{hf:.1f}+{residual}={H:.1f}m"),
    )


def format_supply_result(demand: dict, flow: dict = None, pipe: dict = None) -> str:
    lines = ["【给水系统计算】", demand["note"]]
    if flow:
        lines.append("设计秒流量：" + flow["note"])
    if pipe:
        lines.append("管径水力：" + pipe["note"])
    return "\n".join(lines)


def format_drain_result(r: dict) -> str:
    return "【排水系统计算】\n" + r["note"]
