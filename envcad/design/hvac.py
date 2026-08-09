# -*- coding: utf-8 -*-
"""暖通空调设计验算（知识驱动）。

从 knowledge.hvac_data 取负荷指标/室内参数/换气次数/风管规格，覆盖：
  1) 冷/热负荷估算（面积指标法）
  2) 送风量计算（换气次数法 / 送风温差法）
  3) 新风量计算（人均新风法）
  4) 风管尺寸选择（假定流速法）
"""
from __future__ import annotations

import math

from ..knowledge import hvac_data


def design_load(area: float, place: str = "办公室") -> dict:
    """冷/热负荷估算（面积指标法）。"""
    idx = hvac_data.load_index(place)
    Qc = idx["cool"] * area / 1000.0              # kW
    Qh = idx["heat"] * area / 1000.0              # kW
    return dict(
        area=area, place=place, q_cool=idx["cool"], q_heat=idx["heat"],
        Qc=round(Qc, 2), Qh=round(Qh, 2),
        note=(f"{place}：面积 {area}m²，冷指标 {idx['cool']}W/m²、热指标 {idx['heat']}W/m²；"
              f"冷负荷 {Qc:.1f}kW，热负荷 {Qh:.1f}kW"),
    )


def design_air_volume(area: float, height: float = 3.0,
                      place: str = "办公室", method: str = "换气次数") -> dict:
    """送风量计算。

    method='换气次数'：L = n · A · H  (m³/h)
    method='温差'    ：需另给冷负荷，此处按换气次数法为主。
    """
    n = hvac_data.air_change(place)
    V = area * height
    L = n * V                                     # m³/h
    fresh_per = hvac_data.indoor_param(place)["fresh"]
    return dict(
        area=area, height=height, place=place, n=n, V=round(V, 1),
        L=round(L, 0), fresh_per=fresh_per,
        note=(f"{place}：换气次数 {n} 次/h，房间体积 {V:.0f}m³；"
              f"送风量 L=n·V={L:.0f}m³/h，人均新风参考 {fresh_per}m³/(h·人)"),
    )


def design_fresh_air(people: float, place: str = "办公室") -> dict:
    """新风量计算（人均新风法）。"""
    fresh_per = hvac_data.indoor_param(place)["fresh"]
    Lf = people * fresh_per
    return dict(
        people=people, place=place, fresh_per=fresh_per, Lf=round(Lf, 0),
        note=f"{place}：{people} 人 × {fresh_per}m³/(h·人) = 新风量 {Lf:.0f}m³/h",
    )


def size_duct(L: float, v_target: float = 6.0,
              aspect: float = 2.0) -> dict:
    """风管尺寸（假定流速法）。

    参数：
        L        风量 (m³/h)
        v_target 假定流速 (m/s，主干管 6~8)
        aspect   宽高比 w/h（缺省 2:1）
    公式：A = L/3600/v，w·h=A，w=aspect·h
    """
    A = L / 3600.0 / v_target                     # m²
    h = math.sqrt(A / aspect)                      # m
    w = aspect * h
    w_mm = hvac_data.next_duct(w * 1000.0)
    h_mm = hvac_data.next_duct(h * 1000.0)
    A_actual = (w_mm / 1000.0) * (h_mm / 1000.0)
    v_actual = L / 3600.0 / A_actual
    return dict(
        L=L, v_target=v_target, A_req=round(A, 4),
        w=w_mm, h=h_mm, v_actual=round(v_actual, 2),
        note=(f"风量 {L:.0f}m³/h，假定流速 {v_target}m/s，需截面 {A:.3f}m² → "
              f"风管 {w_mm}×{h_mm}mm，实际流速 {v_actual:.2f}m/s"),
    )


def format_hvac_result(load: dict, air: dict = None, duct: dict = None) -> str:
    lines = ["【暖通空调计算】", load["note"]]
    if air:
        lines.append("送风量：" + air["note"])
    if duct:
        lines.append("风管尺寸：" + duct["note"])
    return "\n".join(lines)
