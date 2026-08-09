# -*- coding: utf-8 -*-
"""土壤修复设计验算：修复目标判定 / 注入井影响半径 / 抽提井群设计。

从 knowledge.remediation_data 取土壤筛选值、井参数等，完成污染
达标判定、注入井间距估算与抽提井影响半径计算。
"""
from __future__ import annotations

import math
from ..knowledge import remediation_data as rd


# ══════════════════════════════════════════════════════════
#  土壤污染达标判定
# ══════════════════════════════════════════════════════════
def soil_check(pollutant: str, concentration: float,
               land_type: str = "I") -> dict:
    """土壤污染物达标判定。

    参数：
        pollutant     污染物名称
        concentration 实测浓度 mg/kg
        land_type     用地类型 I=第一类(敏感) II=第二类(非敏感)
    返回：筛选值、超标倍数、达标判定。
    """
    limit = rd.soil_limit(pollutant, land_type)
    if limit == 0:
        return dict(pollutant=pollutant, concentration=concentration,
                    limit="未知", ok=None,
                    note=f"{pollutant} 未收录在知识库中")

    exceeded = concentration > limit
    ratio = concentration / limit if limit > 0 else 0
    return dict(
        pollutant=pollutant, land_type=land_type,
        concentration=concentration, limit=limit,
        ratio=round(ratio, 2), ok=(not exceeded),
        note=(f"{pollutant} 实测 {concentration}mg/kg，"
              f"{'第' + land_type + '类'}用地筛选值 {limit}mg/kg，"
              f"{'未超标 √' if not exceeded else f'超标 {ratio:.1f}倍 ×'}"),
    )


# ══════════════════════════════════════════════════════════
#  注入井影响半径与间距估算（简化）
# ══════════════════════════════════════════════════════════
def injection_well_spacing(k: float, porosity: float = 0.30,
                           inject_rate: float = 30) -> dict:
    """原位注入井间距估算。

    参数：
        k           渗透系数 m/d
        porosity    有效孔隙度
        inject_rate 单井注入流量 L/min
    返回：影响半径、推荐井间距。
    """
    # 简化：影响半径 R ≈ sqrt(Q/(π×n×b×k)) 量级估计
    # 此处用经验公式 R ≈ 2×sqrt(k×t/n)，取 t=1d
    # 实际注入流量以水力梯度驱动，简化估计
    Q_m3d = inject_rate * 60 * 24 / 1000           # m³/d

    # 影响半径经验公式 R ≈ 2√(Qt/(πn))  取 t=1d
    R = 2 * math.sqrt(Q_m3d / (math.pi * porosity * 1.0))

    spacing = R * 1.5                             # 井间距取 1.5×R（重叠30%）

    return dict(
        k=k, porosity=porosity, inject_rate=inject_rate,
        Q_m3d=round(Q_m3d, 2),
        R_m=round(R, 1), spacing_m=round(spacing, 1),
        note=(f"k={k}m/d n={porosity} 注入{inject_rate}L/min，"
              f"影响半径约 {R:.1f}m，建议井间距 {spacing:.1f}m"),
    )


# ══════════════════════════════════════════════════════════
#  热脱附温度-停留时间校核
# ══════════════════════════════════════════════════════════
def thermal_check(pollutant_type: str = "石油烃",
                  operating_temp: float = 350,
                  dwell_time: float = 15) -> dict:
    """热脱附温度与停留时间校核。

    参数：
        pollutant_type  污染物大类
        operating_temp  操作温度 ℃
        dwell_time      停留时间 min
    返回：推荐参数范围与达标判定。
    """
    # 根据污染物类型匹配脱附等级
    level_map = {"VOC": "低温热脱附", "石油烃": "中温热脱附",
                 "SVOC": "中温热脱附", "PAHs": "高温热脱附",
                 "PCBs": "中温热脱附", "二噁英": "高温热脱附"}
    level = level_map.get(pollutant_type, "中温热脱附")
    param = rd.thermal_param(level)

    temp_ok = param["temp"][0] <= operating_temp <= param["temp"][1]
    dwell_ok = param["dwell"][0] <= dwell_time <= param["dwell"][1]

    return dict(
        pollutant_type=pollutant_type, level=level,
        temp_range=param["temp"], dwell_range=param["dwell"],
        operating_temp=operating_temp, dwell_time=dwell_time,
        temp_ok=temp_ok, dwell_ok=dwell_ok,
        note=(f"{pollutant_type} → {level}，温度{param['temp']}℃ "
              f"停留{param['dwell']}min，"
              f"操作 {operating_temp}℃/{dwell_time}min "
              f"{'√' if (temp_ok and dwell_ok) else '×'}"),
    )
