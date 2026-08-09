# -*- coding: utf-8 -*-
"""曝气生物滤池（BAF）设计数据速查 — HJ 2014、GB 50014、CECS 265。

数值为行业常用区间/典型默认，供绘图默认参数与 AI 取数参考；
实际工程应由滤速/容积负荷/反冲洗强度计算确定。
"""

BAF_DEFAULTS = {
    # 池体（mm）
    "pool_L": 6000.0,           # 池长
    "pool_W": 5000.0,           # 池宽
    "pool_H": 5500.0,           # 池总深
    "bottom_H": 800.0,          # 底部配水区高
    "floor_t": 200.0,           # 滤板厚
    "gravel_H": 300.0,          # 承托层（砾石）
    "media_H": 2500.0,          # 滤料层（陶粒 Φ3~5）
    "clear_H": 1200.0,          # 清水区/缓冲区高
    "freeboard": 500.0,         # 超高
    # 滤板滤头
    "nozzle_pitch": 150.0,      # 长柄滤头间距（49 只/m²）
    "nozzle_dn": 25.0,          # 滤头缝宽 0.3
    # 曝气
    "air_pipe_dn": 80.0,        # 曝气支管
    "air_main_dn": 200.0,       # 曝气母管
    "diffuser_pitch": 600.0,    # 曝气器间距
    # 反冲洗（气水联合）
    "bw_air_dn": 250.0,         # 反洗气管
    "bw_water_dn": 400.0,       # 反洗水管
    "bw_air_q": 15.0,           # 气洗强度 L/(m²·s)
    "bw_water_q": 8.0,          # 水洗强度 L/(m²·s)
    # 进出水
    "inlet_dn": 400.0,          # 进水（上向流：底部进）
    "outlet_dn": 400.0,         # 出水
    "backwash_out_dn": 500.0,   # 反洗排水
}

BAF_NOTES = [
    "上向流 BAF：底部配水、承托层、陶粒滤料 2.5~4m、清水区。",
    "滤速 3~6 m/h，硝化容积负荷 0.6~1.2 kgNH3-N/(m³·d)。",
    "气水联合反冲洗：气 15、水 8 L/(m²·s)，周期 24~48h。",
    "长柄滤头均布 49 只/m²，滤板接缝密封防漏砂。",
]

BAF_CODES = ["HJ 2014", "GB 50014", "CECS 265", "GB 18918"]


def baf_summary() -> str:
    return f"BAF 数据：{BAF_DEFAULTS['pool_L']:.0f}×{BAF_DEFAULTS['pool_W']:.0f}×{BAF_DEFAULTS['pool_H']:.0f}，滤料 {BAF_DEFAULTS['media_H']:.0f}，规范 {len(BAF_CODES)} 本"
