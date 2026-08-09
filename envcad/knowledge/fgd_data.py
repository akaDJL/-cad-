# -*- coding: utf-8 -*-
"""石灰石-石膏湿法脱硫（WFGD）设计数据速查 — HJ 2001、HJ/T 179、DL/T 5196。

数值为行业常用区间/典型默认，供绘图默认参数与 AI 取数参考；
实际工程应由入口 SO2/烟温/液气比 L/G 计算确定。
"""

FGD_DEFAULTS = {
    # 吸收塔（mm）
    "tower_D": 8000.0,          # 吸收塔直径
    "sump_H": 4500.0,           # 浆液池高度（塔底段）
    "inlet_H": 2500.0,          # 入口烟道中心标高（距浆池底）
    "inlet_W": 2600.0,          # 入口烟道宽
    "inlet_Hh": 1800.0,         # 入口烟道高
    "spray_zone_H": 6600.0,     # 喷淋区总高
    "n_spray": 3,               # 喷淋层数（常规 3~5）
    "spray_pitch": 2200.0,      # 喷淋层间距
    "demister_H": 1800.0,       # 两级除雾器段高
    "outlet_H": 2000.0,         # 出口段高（锥顶+出口烟道）
    "outlet_dn": 2200.0,        # 出口净烟道直径
    # 喷淋层
    "spray_main_dn": 700.0,     # 喷淋母管直径
    "spray_branch_dn": 150.0,   # 喷淋支管直径
    "nozzle_pitch": 1200.0,     # 喷嘴布置间距
    "nozzle_type": "空心锥/实心锥",
    # 循环浆液
    "n_pump": 3,                # 循环泵台数（每喷淋层 1 台）
    "circ_dn": 700.0,           # 循环浆液管直径
    "pump_room_L": 9000.0,      # 泵房示意长
}

FGD_NOTES = [
    "液气比 L/G 常规 12~25 L/m³，喷淋层宜交错布置覆盖率≥150%。",
    "浆池设侧进式搅拌器与氧化空气喷枪，pH 控制 5.2~5.8。",
    "除雾器两级屋脊式，带冲洗水系统，出口液滴≤75mg/m³。",
    "塔体碳钢衬玻璃鳞片或橡胶，防腐厚度≥2mm。",
]

FGD_CODES = ["HJ 2001", "HJ/T 179", "DL/T 5196", "GB 13223", "HJ 2052"]


def fgd_summary() -> str:
    return f"湿法脱硫塔数据：塔径 {FGD_DEFAULTS['tower_D']:.0f}，{FGD_DEFAULTS['n_spray']} 层喷淋，规范 {len(FGD_CODES)} 本"
