# -*- coding: utf-8 -*-
"""MBR 膜生物反应器设计数据速查 — HJ 2010、GB 50014、HJ 2028。

数值为行业常用区间/典型默认，供绘图默认参数与 AI 取数参考；
实际工程应由膜通量/产水量/曝气强度计算确定。
"""

MBR_DEFAULTS = {
    # 膜箱（mm）
    "tank_L": 3000.0,           # 膜箱长
    "tank_W": 1500.0,           # 膜箱宽
    "tank_H": 3500.0,           # 膜箱总高（含超高）
    "water_H": 3000.0,          # 运行水深
    "n_module_col": 2,          # 膜组件列数
    "n_module_row": 8,          # 每列帘式膜片数
    # 膜组件（帘式中空纤维）
    "module_L": 1250.0,         # 单片膜长
    "module_W": 50.0,           # 单片膜厚
    "module_H": 2000.0,         # 单片膜高（有效膜丝长）
    "module_pitch": 90.0,       # 膜片间距
    "membrane_area": 25.0,      # 单片膜面积 m²
    "flux": 15.0,               # 设计膜通量 L/(m²·h)（常规 12~25）
    # 曝气（膜擦洗）
    "air_pipe_dn": 100.0,       # 曝气支管
    "air_main_dn": 150.0,       # 曝气母管
    "aeration_rate": 0.25,      # 曝气强度 Nm³/(m²·min)（常规 0.2~0.4）
    # 抽吸/产水
    "suction_dn": 80.0,         # 抽吸支管
    "permeate_dn": 150.0,       # 产水母管
    "suction_p": -30.0,         # 抽吸负压 kPa（常规 -10~-50）
    # 化学清洗
    "cip_dn": 50.0,             # CIP 加药管
    "cip_conc": "NaClO 300~500mg/L / 柠檬酸 0.2%",
}

MBR_NOTES = [
    "膜通量常规 12~25 L/(m²·h)，按产水 8min 停 2min 间歇抽吸运行。",
    "膜擦洗曝气强度 0.2~0.4 Nm³/(m²·min)，穿孔管向下开孔双排 45°。",
    "跨膜压差 TMP≥35kPa 时启动化学清洗（维护性/恢复性）。",
    "出水浊度≤1NTU，可直接回用或进 RO 深度处理。",
]

MBR_CODES = ["HJ 2010", "HJ 2028", "GB 50014", "GB/T 18920"]


def mbr_summary() -> str:
    return f"MBR 数据：膜箱 {MBR_DEFAULTS['tank_L']:.0f}×{MBR_DEFAULTS['tank_W']:.0f}，通量 {MBR_DEFAULTS['flux']} L/m²·h，规范 {len(MBR_CODES)} 本"
