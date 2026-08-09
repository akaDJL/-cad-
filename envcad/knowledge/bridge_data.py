# -*- coding: utf-8 -*-
"""桥梁工程知识库：荷载等级 / 抗震设防 / 支座参数 / 伸缩缝规格 /
桥墩桥梁设计参数 + 规范。

把公路/城市桥梁设计常用数据作为第一类数据沉淀进插件，供梁体截面
估算与桥梁设计说明书自动生成统一取数。数据为常用工程节选，具体设计
以现行规范与地质勘察报告为准。

数据来源：
  - JTG D60  公路桥涵设计通用规范
  - JTG 3362 公路钢筋混凝土及预应力混凝土桥涵设计规范
  - GB 50011 建筑抗震设计规范（桥梁抗震参照）
  - JT/T 4    公路桥梁板式橡胶支座
  - JT/T 327 公路桥梁伸缩装置
  - CJJ 11    城市桥梁设计规范
"""
from __future__ import annotations

import math

# ══════════════════════════════════════════════════════════
#  公路荷载等级  JTG D60
# ══════════════════════════════════════════════════════════
# 车道荷载：qk 均布(kN/m) + Pk 集中(kN)
# 车辆荷载：总重/轴重/轴距
ROAD_LOAD = {
    "公路-Ⅰ级": dict(qk=10.5, Pk_base=360, vehicle_550=550, note="高速公路/一级公路"),
    "公路-Ⅱ级": dict(qk=7.875, Pk_base=270, vehicle_550=410, note="二级公路"),
    "城市-A级": dict(qk=10.5, Pk_base=360, vehicle_550=550, note="城市快速路/主干路"),
    "城市-B级": dict(qk=7.875, Pk_base=270, vehicle_550=410, note="城市次干路/支路"),
}

def pk_value(load_grade: str, L: float) -> float:
    """计算集中荷载 Pk(kN)，L 为计算跨径(m)。
    L≤5m 时 Pk 取基数；L≥50m 时 Pk=基数×1.6；中间线性内插。"""
    base = ROAD_LOAD[load_grade]["Pk_base"]
    if L <= 5:
        return base
    if L >= 50:
        return base * 1.6
    return base * (1 + (L - 5) / (50 - 5) * 0.6)

# ══════════════════════════════════════════════════════════
#  桥梁设计车道数折减系数
# ══════════════════════════════════════════════════════════
LANE_FACTOR = {      # 横向折减系数
    1: 1.20, 2: 1.00, 3: 0.78, 4: 0.67,
    5: 0.60, 6: 0.55, 7: 0.52, 8: 0.50,
}

# ══════════════════════════════════════════════════════════
#  桥梁抗震设防  GB 50011 / JTG/T 2231-01
# ══════════════════════════════════════════════════════════
# 地震动峰值加速度 (g)
SEISMIC_INTENSITY = {
    "6度":  0.05,
    "7度":  0.10,
    "7.5度": 0.15,
    "8度":  0.20,
    "8.5度": 0.30,
    "9度":  0.40,
}

# 桥梁抗震设防类别
BRIDGE_SEISMIC_CLASS = {
    "A类": "单跨跨径>150m的特大桥，抗震救灾关键桥梁",
    "B类": "高速公路/一级公路上的大桥、特大桥，城市快速路",
    "C类": "二级公路上的大桥/特大桥，其他等级公路上的基本桥梁",
    "D类": "三四级公路上的中小桥",
}

# ══════════════════════════════════════════════════════════
#  桥梁支座参数  JT/T 4 板式橡胶支座
# ══════════════════════════════════════════════════════════
# 矩形板式橡胶支座：平面尺寸(mm) × 承载力(kN)
BEARING_RECT = {
    "150×200": dict(area=(150, 200), capacity=300,  shear=10,  thickness=28),
    "200×250": dict(area=(200, 250), capacity=500,  shear=10,  thickness=35),
    "250×300": dict(area=(250, 300), capacity=750,  shear=10,  thickness=42),
    "300×350": dict(area=(300, 350), capacity=1050, shear=10,  thickness=49),
    "350×400": dict(area=(350, 400), capacity=1400, shear=10,  thickness=56),
    "400×450": dict(area=(400, 450), capacity=1800, shear=10,  thickness=63),
}
# 圆形板式橡胶支座
BEARING_ROUND = {
    "D200": dict(d=200, capacity=310,  shear=10, thickness=28),
    "D250": dict(d=250, capacity=490,  shear=10, thickness=35),
    "D300": dict(d=300, capacity=700,  shear=10, thickness=42),
    "D350": dict(d=350, capacity=960,  shear=10, thickness=49),
    "D400": dict(d=400, capacity=1250, shear=10, thickness=56),
}

# ══════════════════════════════════════════════════════════
#  桥梁伸缩缝装置规格  JT/T 327
# ══════════════════════════════════════════════════════════
EXPANSION_JOINT = {
    "40型":  dict(displacement=40,  type="轻型"),
    "60型":  dict(displacement=60,  type="轻型"),
    "80型":  dict(displacement=80,  type="中型"),
    "120型": dict(displacement=120, type="中型"),
    "160型": dict(displacement=160, type="重型"),
    "240型": dict(displacement=240, type="重型"),
    "320型": dict(displacement=320, type="特重型"),
}

# ══════════════════════════════════════════════════════════
#  箱梁常用截面参数
# ══════════════════════════════════════════════════════════
# 单箱单室截面：梁高/跨径比
BOX_GIRDER_HD = {
    "等截面连续梁": (1/18, 1/25),
    "变截面连续梁(支点)": (1/15, 1/18),
    "变截面连续梁(跨中)": (1/30, 1/50),
    "简支梁": (1/16, 1/22),
}

# ══════════════════════════════════════════════════════════
#  桥梁常用跨径与结构形式参考
# ══════════════════════════════════════════════════════════
BRIDGE_SPAN_TYPE = {
    "小桥":  (8, 30,   "板梁/T梁/空心板"),
    "中桥":  (30, 100,  "T梁/小箱梁/连续梁"),
    "大桥":  (100, 500,  "连续梁/连续刚构/拱桥"),
    "特大桥": (500, None, "斜拉桥/悬索桥/拱桥"),
}

# ══════════════════════════════════════════════════════════
#  桥梁规范注册表
# ══════════════════════════════════════════════════════════
BRIDGE_CODES = {
    "JTG D60-2015": "公路桥涵设计通用规范",
    "JTG 3362-2018": "公路钢筋混凝土及预应力混凝土桥涵设计规范",
    "JTG D63-2007": "公路桥涵地基与基础设计规范",
    "JTG/T 2231-01-2020": "公路桥梁抗震设计规范",
    "JT/T 4-2019": "公路桥梁板式橡胶支座",
    "JT/T 327-2016": "公路桥梁伸缩装置",
    "CJJ 11-2011": "城市桥梁设计规范",
    "CJJ 166-2011": "城市桥梁抗震设计规范",
}


# ══════════════════════════════════════════════════════════
#  查询辅助
# ══════════════════════════════════════════════════════════
def road_load(grade: str = "公路-Ⅰ级") -> dict:
    return ROAD_LOAD.get(grade, ROAD_LOAD["公路-Ⅰ级"])


def lane_factor(n_lanes: int) -> float:
    return LANE_FACTOR.get(n_lanes, 0.5)


def seismic_pga(intensity: str = "7度") -> float:
    return SEISMIC_INTENSITY.get(intensity, 0.10)


def bearing_rect(spec: str = "200×250") -> dict:
    return BEARING_RECT.get(spec, BEARING_RECT["200×250"])


def bearing_round(d: int = 200) -> dict:
    key = f"D{d}"
    if key in BEARING_ROUND:
        return BEARING_ROUND[key]
    keys = sorted([int(k[1:]) for k in BEARING_ROUND])
    for k in keys:
        if k >= d:
            return BEARING_ROUND[f"D{k}"]
    return BEARING_ROUND[f"D{keys[-1]}"]


def expansion_joint(disp: float) -> dict:
    for name, p in EXPANSION_JOINT.items():
        if p["displacement"] >= disp:
            return {**p, "spec": name}
    last = list(EXPANSION_JOINT.items())[-1]
    return {**last[1], "spec": last[0]}


def bridge_code_list() -> list:
    return list(BRIDGE_CODES.items())


def bridge_summary() -> str:
    return (f"荷载等级 {len(ROAD_LOAD)} 级 | 支座矩形{len(BEARING_RECT)}/圆形{len(BEARING_ROUND)} 种 | "
            f"伸缩缝 {len(EXPANSION_JOINT)} 型 | 桥梁规范 {len(BRIDGE_CODES)} 本")
