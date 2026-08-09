# -*- coding: utf-8 -*-
"""土木行业知识库：岩土参数 / 地基承载力修正 / 桥梁道路岩土规范。

对标探索者的岩土与基础设计能力：把土层物理力学指标、地基承载力
深宽修正系数、以及桥梁/道路/岩土专业规范作为第一类数据沉淀进插件，
供基础设计与文档自动化统一取数。数据为常用工程经验值，具体以勘察
报告与现行规范条文为准。

数据来源：
  - GB 50007  建筑地基基础设计规范（承载力深宽修正系数、变形）
  - GB 50021  岩土工程勘察规范
  - JTG D60   公路桥涵设计通用规范（汽车荷载）
  - JTG B01   公路工程技术标准（路线等级）
  - JTG D30   公路路基设计规范
"""
from __future__ import annotations

import math

# ══════════════════════════════════════════════════════════
#  常见土层物理力学参数（经验值范围的常用代表值）
#  gamma  天然重度 kN/m³ | phi 内摩擦角 ° | c 粘聚力 kPa
#  fak    承载力特征值 kPa | Es 压缩模量 MPa
# ══════════════════════════════════════════════════════════
SOIL = {
    "杂填土":   dict(gamma=17.0, phi=10, c=5,  fak=80,  Es=4.0),
    "素填土":   dict(gamma=18.0, phi=12, c=8,  fak=100, Es=5.0),
    "淤泥":     dict(gamma=16.0, phi=4,  c=10, fak=50,  Es=2.0),
    "淤泥质土": dict(gamma=17.5, phi=6,  c=12, fak=75,  Es=3.0),
    "粘土":     dict(gamma=19.5, phi=15, c=30, fak=180, Es=7.0),
    "粉质粘土": dict(gamma=19.0, phi=18, c=20, fak=160, Es=6.0),
    "粉土":     dict(gamma=19.0, phi=22, c=8,  fak=140, Es=8.0),
    "粉砂":     dict(gamma=19.0, phi=26, c=0,  fak=140, Es=10.0),
    "细砂":     dict(gamma=19.5, phi=28, c=0,  fak=160, Es=13.0),
    "中砂":     dict(gamma=20.0, phi=32, c=0,  fak=200, Es=18.0),
    "粗砂":     dict(gamma=20.0, phi=34, c=0,  fak=250, Es=22.0),
    "圆砾":     dict(gamma=21.0, phi=38, c=0,  fak=350, Es=30.0),
    "卵石":     dict(gamma=21.0, phi=40, c=0,  fak=500, Es=40.0),
    "强风化岩": dict(gamma=22.0, phi=35, c=50, fak=500, Es=50.0),
    "中风化岩": dict(gamma=24.0, phi=40, c=200, fak=1500, Es=None),
}

# ══════════════════════════════════════════════════════════
#  地基承载力深宽修正系数 ηb / ηd（GB 50007 表 5.2.4，常用节选）
#  key 为土类描述，值 dict(eta_b, eta_d)
# ══════════════════════════════════════════════════════════
BEARING_CORRECTION = {
    "淤泥及淤泥质土": dict(eta_b=0.0, eta_d=1.0),
    "人工填土/e≥0.85粘性土": dict(eta_b=0.0, eta_d=1.0),
    "红粘土":       dict(eta_b=0.15, eta_d=1.4),
    "大面积压实填土": dict(eta_b=0.0, eta_d=1.5),
    "粉土":         dict(eta_b=0.5, eta_d=2.0),
    "e<0.85粘性土": dict(eta_b=0.3, eta_d=1.6),
    "粉砂细砂":     dict(eta_b=2.0, eta_d=3.0),
    "中砂粗砂砾砂": dict(eta_b=3.0, eta_d=4.4),
}

# ══════════════════════════════════════════════════════════
#  公路等级与设计车速（JTG B01）
# ══════════════════════════════════════════════════════════
ROAD_CLASS = {
    "高速公路":   dict(v=list([120, 100, 80]), lanes="双向4~8", unit="km/h"),
    "一级公路":   dict(v=list([100, 80, 60]),  lanes="双向4~6", unit="km/h"),
    "二级公路":   dict(v=list([80, 60]),       lanes="双向2",   unit="km/h"),
    "三级公路":   dict(v=list([40, 30]),       lanes="双向2",   unit="km/h"),
    "四级公路":   dict(v=list([20]),           lanes="单/双车道", unit="km/h"),
}

# 公路桥涵汽车荷载（JTG D60，标准值）
VEHICLE_LOAD = {
    "公路-Ⅰ级": dict(qk=10.5, Pk="集中2×|180+(L-5)/10×180|", unit="kN/m 均布 + 集中"),
    "公路-Ⅱ级": dict(qk=7.875, Pk="Ⅰ级的0.75倍", unit="kN/m 均布 + 集中"),
}

# ══════════════════════════════════════════════════════════
#  土木专业规范注册表（岩土/桥梁/道路，与 codes.GB_CODES 互补）
# ══════════════════════════════════════════════════════════
CIVIL_CODES = {
    "GB 50007-2011": "建筑地基基础设计规范",
    "GB 50021-2001(2009版)": "岩土工程勘察规范",
    "GB 50330-2013": "建筑边坡工程技术规范",
    "GB 50086-2015": "岩土锚杆与喷射混凝土支护工程技术规范",
    "JTG D60-2015": "公路桥涵设计通用规范",
    "JTG 3362-2018": "公路钢筋混凝土及预应力混凝土桥涵设计规范",
    "JTG D30-2015": "公路路基设计规范",
    "JTG B01-2014": "公路工程技术标准",
    "JTG D40-2011": "公路水泥混凝土路面设计规范",
}


# ══════════════════════════════════════════════════════════
#  查询与计算辅助
# ══════════════════════════════════════════════════════════
def soil_props(name: str) -> dict:
    """返回土层物理力学参数；未知土类抛 KeyError。"""
    return SOIL[name]


def active_earth_coef(phi_deg: float) -> float:
    """朗肯主动土压力系数 Ka = tan²(45° - φ/2)。"""
    return math.tan(math.radians(45.0 - phi_deg / 2.0)) ** 2


def passive_earth_coef(phi_deg: float) -> float:
    """朗肯被动土压力系数 Kp = tan²(45° + φ/2)。"""
    return math.tan(math.radians(45.0 + phi_deg / 2.0)) ** 2


def correct_bearing(fak: float, b: float, d: float, gamma: float,
                    gamma_m: float, eta_b: float, eta_d: float) -> dict:
    """地基承载力特征值深宽修正（GB 50007 式 5.2.4）。

    fa = fak + ηb·γ·(b-3) + ηd·γm·(d-0.5)
    b 取基础宽度(3~6m 内取值，<3 按3，>6 按6)，d 为基础埋深(m)。
    """
    b_use = min(max(b, 3.0), 6.0)
    fa = (fak
          + eta_b * gamma * (b_use - 3.0)
          + eta_d * gamma_m * (d - 0.5))
    return dict(fak=fak, fa=round(fa, 1), b_use=b_use, d=d,
                eta_b=eta_b, eta_d=eta_d,
                note=f"fa={fa:.1f} kPa（fak={fak}，b取{b_use}m，d={d}m）")


def civil_code_list() -> list:
    """返回 [(编号, 名称), ...] 供文档「设计依据」引用。"""
    return list(CIVIL_CODES.items())


def civil_summary() -> str:
    return (f"土层 {len(SOIL)} 类 | 承载力修正 {len(BEARING_CORRECTION)} 组 | "
            f"公路等级 {len(ROAD_CLASS)} 级 | 土木规范 {len(CIVIL_CODES)} 本")
