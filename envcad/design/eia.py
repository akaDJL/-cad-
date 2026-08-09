# -*- coding: utf-8 -*-
"""环境影响评价设计验算：评价等级自动判定 / 防护距离计算 /
敏感区缓冲校核。

从 knowledge.eia_data 取判定标准、防护距离级差、敏感区分级等，
完成大气/地表水/噪声评价等级自动判定与防护距离计算。
"""
from __future__ import annotations

import math
from ..knowledge import eia_data as ea


# ══════════════════════════════════════════════════════════
#  大气评价等级判定 + 估算浓度比
# ══════════════════════════════════════════════════════════
def air_eia_grade(pmax: float, d10: float = 0) -> dict:
    """大气环境影响评价等级判定。

    参数：
        pmax  最大地面浓度占标率 %
        d10   D10% 最远距离 m
    返回：评价等级与要求。
    """
    grade = ea.air_grade_judge(pmax, d10)
    info = ea.AIR_GRADE[grade]
    return dict(
        pmax=pmax, d10=d10, grade=grade,
        method=info["detail"],
        note=f"Pmax={pmax:.1f}% D10%={d10:.0f}m → 大气评价{grade}，{info['detail']}",
    )


# ══════════════════════════════════════════════════════════
#  地表水评价等级判定
# ══════════════════════════════════════════════════════════
def water_eia_grade(discharge_m3d: float, complexity: str = "简单") -> dict:
    """地表水环境影响评价等级判定。

    参数：
        discharge_m3d  废水排放量 m³/d
        complexity     废水复杂程度："简单"/"中等"/"复杂"
    返回：评价等级与方法。
    """
    grade = ea.water_grade_judge(discharge_m3d, complexity)
    info = ea.WATER_GRADE[grade]
    return dict(
        discharge_m3d=discharge_m3d, complexity=complexity,
        grade=grade, method=info["method"],
        note=f"排放量 {discharge_m3d:.0f}m³/d 废水{complexity} → 地表水评价{grade}，{info['method']}",
    )


# ══════════════════════════════════════════════════════════
#  噪声评价等级判定
# ══════════════════════════════════════════════════════════
def noise_eia_grade(zone: str = "3类", delta: float = 2.0) -> dict:
    """声环境影响评价等级判定。

    参数：
        zone   声功能区（0类/1类/2类/3类/4a类/4b类）
        delta  预测增量 dB(A)
    返回：评价等级与要求。
    """
    grade = ea.noise_grade_judge(zone, delta)
    info = ea.NOISE_GRADE[grade]
    return dict(
        zone=zone, delta=delta, grade=grade,
        condition=info["condition"], detail=info["detail"],
        note=f"{zone}区 增量{delta}dB(A) → 噪声评价{grade}，{info['detail']}",
    )


# ══════════════════════════════════════════════════════════
#  大气环境防护距离计算
# ══════════════════════════════════════════════════════════
def protection_distance(d_calc: float) -> dict:
    """大气环境防护距离-按级差取整。

    参数：
        d_calc  计算距离 m
    返回：取整后的防护距离。
    """
    d = ea.round_protection_distance(d_calc)
    return dict(
        d_calc=round(d_calc, 1), d_protection=d,
        note=f"计算防护距离 {d_calc:.1f}m → 取整 {d:.0f}m（按级差）",
    )


# ══════════════════════════════════════════════════════════
#  敏感区距离校核
# ══════════════════════════════════════════════════════════
def sensitive_area_check(area_name: str, actual_distance: float) -> dict:
    """项目厂界与敏感区距离校核。

    参数：
        area_name         敏感区类型
        actual_distance   实际最近距离 m
    返回：最小缓冲距离与达标判定。
    """
    sa = ea.sensitive_area(area_name)
    _, buf_high = sa["buffer"]
    ok = actual_distance >= buf_high
    return dict(
        area_name=area_name, level=sa["level"],
        buffer_range=f"{sa['buffer'][0]}~{sa['buffer'][1]}m",
        buffer_min=buf_high,
        actual_distance=actual_distance, ok=ok,
        note=(f"{area_name}({sa['level']}类敏感区) 缓冲 {buf_high}m，"
              f"实际 {actual_distance:.0f}m {'√' if ok else '× 不满足'}"),
    )
