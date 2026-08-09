# -*- coding: utf-8 -*-
"""溶气气浮机（DAF）设计数据速查 — HJ 2007、GB 50014、CECS 75。

数值为行业常用区间/典型默认，供绘图默认参数与 AI 取数参考；
实际工程应由表面负荷/回流比/接触时间计算确定。
"""

DAF_DEFAULTS = {
    # 池体（mm）
    "contact_L": 1500.0,        # 接触区长度
    "sep_L": 6500.0,            # 分离区长度
    "pool_W": 3000.0,           # 池宽
    "pool_H": 2200.0,           # 池深（有效水深 1800~2500）
    "freeboard": 500.0,         # 超高
    "wall_t": 200.0,            # 壁厚（钢制 10/混凝土 200+）
    # 水位
    "water_H": 1800.0,          # 有效水深
    "scum_t": 150.0,            # 浮渣层厚
    # 溶气系统
    "tank_D": 800.0,            # 溶气罐直径
    "tank_H": 2500.0,           # 溶气罐高
    "tank_p": 0.4,              # 溶气压力 MPa（常规 0.3~0.5）
    "reflux": 0.30,             # 回流比（常规 20~40%）
    "releaser": "TS 溶气释放器",
    "releaser_dn": 50.0,        # 释放器直径
    # 刮渣
    "skimmer_v": 1.0,           # 刮渣机速度 m/min
    "scum_trough_W": 400.0,     # 集渣槽宽
    # 管口
    "inlet_dn": 300.0,          # 进水管
    "outlet_dn": 300.0,         # 出水管
    "sludge_dn": 150.0,         # 排泥/放空管
}

DAF_NOTES = [
    "表面负荷常规 5~10 m³/(m²·h)，分离区停留 15~30 min。",
    "溶气压力 0.3~0.5 MPa，回流比 20~40%，释放器均匀布置。",
    "接触区上升流速 10~20 mm/s，整流板保证气水充分接触。",
    "浮渣由链式刮渣机刮入集渣槽，出水设可调堰板。",
]

DAF_CODES = ["HJ 2007", "GB 50014", "CECS 75", "GB 8978"]


def daf_summary() -> str:
    return f"溶气气浮数据：接触 {DAF_DEFAULTS['contact_L']:.0f}+分离 {DAF_DEFAULTS['sep_L']:.0f}，溶气 {DAF_DEFAULTS['tank_p']} MPa，规范 {len(DAF_CODES)} 本"
