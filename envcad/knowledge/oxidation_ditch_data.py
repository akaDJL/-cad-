# -*- coding: utf-8 -*-
"""氧化沟设计数据速查 — HJ 578、GB 50014、CECS 112。

数值为行业常用区间/典型默认，供绘图默认参数与 AI 取数参考；
实际工程应由污泥负荷/泥龄/需氧量计算确定。
"""

OD_DEFAULTS = {
    # 沟体（mm）
    "ditch_L": 40000.0,         # 直段长
    "ditch_W": 8000.0,          # 单沟宽
    "n_lane": 2,                # 沟道数（环形）
    "ditch_H": 5000.0,          # 池深
    "water_H": 4200.0,          # 有效水深（常规 3.5~4.5m）
    "wall_t": 300.0,            # 壁厚
    "guide_wall_L": 30000.0,    # 中央导流墙长
    "guide_wall_t": 300.0,      # 导流墙厚
    "bend_R": 4000.0,           # 端部弯道半径
    # 曝气设备
    "n_brush": 4,               # 转刷曝气机台数
    "brush_L": 7000.0,          # 转刷单机长（跨沟）
    "brush_D": 1000.0,          # 转刷直径
    "brush_immersion": 300.0,   # 浸没深度 mm（可调）
    "brush_power": 30.0,        # 单机功率 kW
    # 推流
    "flow_v": 0.3,              # 沟内流速 m/s（≥0.25 防沉积）
    # 出水
    "weir_L": 4000.0,           # 出水堰长
    "outlet_dn": 600.0,         # 出水管
    # 工艺参数
    "sludge_age": 15.0,         # 泥龄 d（常规 12~25）
    "mlss": 4000.0,             # MLSS mg/L
}

OD_NOTES = [
    "Carrousel 氧化沟：环形沟道+表面转刷/转盘曝气，流速≥0.25m/s。",
    "转刷浸没深度可调（200~350mm），控制曝气与推流。",
    "泥龄 12~25d 实现同步硝化反硝化，出水可达一级 A。",
    "弯道设导流墙防偏流，出水可调堰门控制水位。",
]

OD_CODES = ["HJ 578", "GB 50014", "CECS 112", "GB 18918"]


def od_summary() -> str:
    return f"氧化沟数据：{OD_DEFAULTS['n_lane']} 沟×{OD_DEFAULTS['ditch_L']:.0f}，{OD_DEFAULTS['n_brush']} 台转刷，规范 {len(OD_CODES)} 本"
