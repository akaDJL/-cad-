# -*- coding: utf-8 -*-
"""SCR 选择性催化还原脱硝设计数据速查 — HJ 562、HJ 563、GB/T 21509、DL/T 5480。

数值为行业常用区间/典型默认，供绘图默认参数与 AI 取数参考；
实际工程应由 NOx 浓度/烟温/空速 SV/催化剂体积计算确定。
"""

SCR_DEFAULTS = {
    # 反应器（mm）
    "reactor_W": 6000.0,        # 反应器宽（垂直气流）
    "reactor_D": 4000.0,        # 反应器深（沿气流）
    "inlet_flue_L": 5000.0,     # 进口烟道/渐扩段长
    "outlet_flue_L": 4000.0,    # 出口烟道/渐缩段长
    "guide_H": 1500.0,          # 顶部导流/均流段高
    "n_catalyst": 2,            # 初装催化剂层数（2+1 备用）
    "n_spare": 1,               # 备用层数
    "catalyst_H": 1200.0,       # 单层催化剂模块高
    "catalyst_gap": 900.0,      # 层间距（含吹灰器空间）
    "support_H": 1200.0,        # 底部支撑/检修空间
    "leg_H": 4500.0,            # 反应器支腿高
    # 催化剂布置
    "module_L": 1910.0,         # 催化剂模块长（标准 1910×970）
    "module_W": 970.0,          # 催化剂模块宽
    "module_gap": 10.0,         # 模块间隙
    # 喷氨格栅 AIG
    "aig_main_dn": 400.0,       # 喷氨母管直径
    "aig_branch_dn": 80.0,      # 喷氨支管直径
    "aig_nozzle_pitch": 1000.0, # 喷氨喷嘴间距
    "aig_nozzle_dn": 25.0,      # 喷嘴直径
    # 吹灰
    "sootblower": "蒸汽吹灰+声波吹灰",
}

SCR_NOTES = [
    "催化剂层按 2+1 配置，预留备用层，空速 SV 常规 2500~3500 h⁻¹。",
    "喷氨格栅距首层催化剂入口宜≥3m，保证氨氮摩尔比均匀（偏差≤5%）。",
    "反应器入口设导流板与整流格栅，烟温窗口 300~420℃。",
    "脱硝效率≥80% 时宜设声波+蒸汽联合吹灰。",
]

SCR_CODES = ["HJ 562", "HJ 563", "GB/T 21509", "DL/T 5480", "GB 13223"]


def scr_summary() -> str:
    return f"SCR 脱硝数据：{SCR_DEFAULTS['n_catalyst']}+{SCR_DEFAULTS['n_spare']} 层催化剂，规范 {len(SCR_CODES)} 本"
