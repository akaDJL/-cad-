# -*- coding: utf-8 -*-
"""RTO 蓄热式焚烧炉设计数据速查 — HJ 2000、HJ 1093、GB 37822。

数值为行业常用区间/典型默认，供绘图默认参数与 AI 取数参考；
实际工程应由废气量/VOCs 浓度/热回收效率(≥95%)计算确定。
"""

RTO_DEFAULTS = {
    # 炉体（mm）——三室结构
    "n_chamber": 3,             # 蓄热室数（三室 RTO）
    "chamber_W": 2500.0,        # 单室宽
    "chamber_D": 2000.0,        # 单室深
    "chamber_H": 5000.0,        # 蓄热室高
    "bed_H": 1800.0,            # 蓄热体层厚（陶瓷蜂窝/鞍环）
    "bed_layers": 3,            # 蓄热体分层数
    "comb_H": 2000.0,           # 顶部燃烧室高
    "insulation_t": 250.0,      # 保温层厚
    # 燃烧器
    "burner_dn": 300.0,         # 燃气烧嘴接口
    "burner_pos": "顶部",        # 燃烧器位置
    # 切换阀
    "valve_dn": 800.0,          # 提升阀通径
    "valve_H": 600.0,           # 阀箱高
    # 进出口
    "inlet_dn": 900.0,          # 废气进口
    "outlet_dn": 900.0,         # 净化气出口
    "purge_dn": 400.0,          # 吹扫口
    "stack_dn": 900.0,          # 烟囱直径
    "stack_H": 15000.0,         # 烟囱高（示意）
    # 工艺参数
    "comb_t": 850.0,            # 燃烧温度 ℃（常规 760~900）
    "residence": 1.2,           # 停留时间 s（≥1.0）
    "heat_recovery": 0.95,      # 热回收率
}

RTO_NOTES = [
    "三室 RTO：一室进气蓄热、一室出气放热、一室吹扫，循环切换。",
    "燃烧温度 760~900℃，停留时间≥1.0s，VOCs 去除率≥99%。",
    "蓄热体用陶瓷蜂窝/马鞍环，热回收率≥95%。",
    "入口浓度低于爆炸下限 25%LEL，设阻火器与泄爆片。",
]

RTO_CODES = ["HJ 2000", "HJ 1093", "GB 37822", "GB 16297"]


def rto_summary() -> str:
    return f"RTO 数据：{RTO_DEFAULTS['n_chamber']} 室，燃烧 {RTO_DEFAULTS['comb_t']:.0f}℃，热回收 {RTO_DEFAULTS['heat_recovery']*100:.0f}%，规范 {len(RTO_CODES)} 本"
