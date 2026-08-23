# -*- coding: utf-8 -*-
"""环保工艺设计验算（知识驱动）。

从 knowledge.env_data 取工艺参数与排放限值，覆盖三类常用工艺：
  1) 活性污泥法曝气池容积（污泥负荷法）
  2) 二次沉淀池表面积（表面负荷法）
  3) 除尘器选型（旋风/袋式，处理风量 → 尺寸/效率/阻力）
并给出出水/排放是否达标的判定。
"""
from __future__ import annotations

import math

from ..knowledge import env_data


def design_aeration_tank(Q: float, So: float, Se: float = None,
                         Ls: float = None, MLSS: float = None) -> dict:
    """曝气池容积设计（污泥负荷法）。

    参数：
        Q     设计流量 (m³/d)
        So    进水 BOD5 (mg/L)
        Se    出水 BOD5 (mg/L)，缺省取一级A 的 10
        Ls    污泥负荷 kgBOD/(kgMLSS·d)，缺省取知识层推荐 0.2
        MLSS  混合液悬浮固体 (mg/L)，缺省 3000

    公式：V = Q·So / (Ls·X)   [推导后单位可约为 m³]
         HRT = V / Q × 24     [h]
    """
    Se = env_data.WATER_GB18918["一级A"]["BOD5"] if Se is None else Se
    Ls = env_data.AERATION["Ls"] if Ls is None else Ls
    X = env_data.AERATION["MLSS"] if MLSS is None else MLSS

    V = Q * So / (Ls * X)                       # m³
    HRT = V / Q * 24.0                          # h
    G_bod = Q * So / 1000.0                     # kg/d 进水 BOD 负荷
    eff = (So - Se) / So if So > 0 else 0.0
    lo, hi = env_data.AERATION["HRT"]
    return dict(
        Q=Q, So=So, Se=Se, Ls=Ls, MLSS=X,
        V=round(V, 1), HRT=round(HRT, 2),
        bod_load=round(G_bod, 1), removal=round(eff * 100, 1),
        hrt_ok=(lo <= HRT <= hi + 4),          # 略放宽上限
        note=(f"Q={Q}m³/d，So={So}→Se={Se}mg/L；污泥负荷{Ls}、MLSS{X}mg/L；"
              f"曝气池容积 V={V:.1f}m³，HRT={HRT:.2f}h，去除率{eff*100:.1f}%"),
    )


def design_sed_tank(Q: float, q: float = None, n: int = 2) -> dict:
    """二次沉淀池表面积（表面负荷法），按圆形池给出直径。

    参数：
        Q  设计流量 (m³/d)
        q  表面负荷 m³/(m²·h)，缺省取知识层 1.0
        n  池数
    """
    q = env_data.SED_TANK["q"] if q is None else q
    Qh = Q / 24.0                               # m³/h
    A_total = Qh / q                            # m²
    A_each = A_total / n
    D = math.sqrt(4.0 * A_each / math.pi)
    D = math.ceil(D * 2) / 2.0                  # 上取整到 0.5m
    depth = env_data.SED_TANK["depth"][0]
    return dict(
        Q=Q, Qh=round(Qh, 1), q=q, n=n,
        A_total=round(A_total, 1), A_each=round(A_each, 1),
        D=round(D, 2), depth=depth,
        note=(f"Q={Q}m³/d(={Qh:.1f}m³/h)，表面负荷{q}；总沉淀面积{A_total:.1f}m²，"
              f"{n}座每座Φ{D:.1f}m，有效水深{depth}m"),
    )


def design_dust_collector(air_flow: float, kind: str = "baghouse",
                          pollutant_in: float = 5000.0,
                          limit_std: str = "颗粒物") -> dict:
    """除尘器选型（air_flow: m³/h）。kind ∈ {baghouse 袋式, cyclone 旋风}。

    返回过滤面积/筒体直径、效率、阻力与排放达标判定。
    """
    if kind == "cyclone":
        v = env_data.CYCLONE["v"]               # 进口气速 m/s
        eff = env_data.CYCLONE["eff"][1]        # 取上限效率
        dp = env_data.CYCLONE["dp"][1]
        Qs = air_flow / 3600.0                   # m³/s
        A_inlet = Qs / v                          # m² 进口截面
        # 简化：进口为筒径 0.25D×0.5D 矩形，反推筒体直径
        D = math.sqrt(A_inlet / 0.125)
        D = math.ceil(D * 10) / 10.0
        geom = dict(type="旋风除尘器", inlet_area=round(A_inlet, 3),
                    body_D=round(D, 2), inlet_v=v)
    else:
        v = env_data.BAGHOUSE["v"]               # 过滤风速 m/min
        eff = env_data.BAGHOUSE["eff"][1]
        dp = env_data.BAGHOUSE["dp"][1]
        A_filter = air_flow / 60.0 / v            # m² (air_flow m³/h → m³/min /v)
        geom = dict(type="袋式除尘器", filter_area=round(A_filter, 1),
                    filter_v=v)

    out_conc = pollutant_in * (1 - eff)
    limit = env_data.AIR_GB16297.get(limit_std, dict(conc=120))["conc"]
    return dict(
        kind=kind, air_flow=air_flow, eff=round(eff, 4),
        dp=dp, geom=geom,
        conc_in=pollutant_in, conc_out=round(out_conc, 1),
        limit=limit, ok=(out_conc <= limit),
        note=(f"{geom['type']}：处理风量{air_flow}m³/h，效率{eff*100:.2f}%，"
              f"阻力{dp}Pa；出口浓度{out_conc:.1f}mg/m³ "
              f"{'≤' if out_conc <= limit else '>'} 限值{limit}mg/m³"),
    )


def format_wwtp_result(aer: dict, sed: dict) -> str:
    lines = ["【污水处理主要构筑物】"]
    lines.append("曝气池：" + aer["note"])
    lines.append("二沉池：" + sed["note"])
    return "\n".join(lines)


def format_dust_result(r: dict) -> str:
    lines = ["【除尘器选型】", r["note"]]
    lines.append("达标结论：" + ("满足排放限值" if r["ok"] else "超标，需提高效率/更换工艺"))
    return "\n".join(lines)


# ══════════════════════════════════════════════════════════
#  全参数设备设计（提示词输入条件 → 成套绘图几何参数）
#  返回的所有长度统一为 mm（工程图单位），供 drawings/ 模板直接消费。
# ══════════════════════════════════════════════════════════

def design_baghouse_full(air_flow: float = 20000.0,
                         filter_v: float = None,
                         bag_dia_mm: float = 130.0,
                         bag_len_mm: float = 3000.0,
                         pollutant_in: float = 5000.0,
                         limit_std: str = "颗粒物") -> dict:
    """脉冲袋式除尘器全参数设计。

    输入提示词可给的条件：
        air_flow     处理风量 (m³/h)，默认 20000
        filter_v     过滤风速 (m/min)，缺省取知识层 1.0
        bag_dia_mm   滤袋直径 (mm)，默认 130
        bag_len_mm   滤袋长度 (mm)，默认 3000
        pollutant_in 入口粉尘浓度 (mg/m³)，默认 5000

    返回：过滤面积→袋数→排列→花板→箱体→灰斗→喷吹→管口的全套几何参数（mm）。
    供 drawings/t7_baghouse.py 按 A/B/C 级别直接取参绘图。
    """
    v = (env_data.BAGHOUSE["v"] if filter_v is None else filter_v)
    eff = env_data.BAGHOUSE["eff"][1]
    dp = env_data.BAGHOUSE["dp"][1]

    # ── 过滤面积与袋数 ─────────────────────────────
    A_filter = air_flow / 60.0 / v                       # m² 总过滤面积
    a_bag = math.pi * (bag_dia_mm / 1000.0) * (bag_len_mm / 1000.0)  # m² 单袋
    n0 = A_filter / a_bag if a_bag > 0 else 0

    # ── 排列（中心距 = 袋径 + 40mm 净距）─────────────
    spacing = bag_dia_mm + 40.0                          # mm 袋中心距
    cols = max(2, round(math.sqrt(n0) * 1.25))           # 长度方向袋数（偏长形）
    rows = max(1, math.ceil(n0 / cols))                  # 宽度方向袋数
    n_bags = rows * cols

    # ── 花板与箱体 ─────────────────────────────────
    edge = 100.0                                         # mm 花板边距
    plate_L = cols * spacing + 2 * edge                  # mm 花板长
    plate_W = rows * spacing + 2 * edge                  # mm 花板宽
    box_L = plate_L + 100.0                              # mm 箱体长（壁板内净）
    box_W = plate_W + 100.0                              # mm 箱体宽
    clean_gas_H = 900.0                                  # mm 净气室（上箱体）高
    bag_room_H = bag_len_mm + 250.0                      # mm 袋室高（袋长+花板下空间）
    # 灰斗：四棱锥，斗壁与水平夹角 60°，卸灰口 300
    hopper_outlet = 300.0                                # mm 卸灰口边长
    half_span = (min(box_L, box_W) - hopper_outlet) / 2.0
    hopper_H = half_span * math.tan(math.radians(60.0))
    leg_H = 1400.0                                       # mm 支腿高（灰斗下卸料空间）
    total_H = clean_gas_H + bag_room_H + hopper_H        # mm 设备本体总高

    # ── 进出风口管径（管内风速 13 m/s）──────────────
    Q_s = air_flow / 3600.0                              # m³/s
    v_wind = 13.0
    dn = math.sqrt(4.0 * Q_s / (math.pi * v_wind)) * 1000.0  # mm
    inlet_dn = math.ceil(dn / 50.0) * 50                 # 上取整到 50
    outlet_dn = inlet_dn

    # ── 喷吹系统（每列一个脉冲阀）──────────────────
    n_pulse_valve = cols
    air_tank_L = box_L + 200.0                           # mm 气包长（贯通箱体）

    # ── 达标判定 ───────────────────────────────────
    conc_out = pollutant_in * (1 - eff)
    limit = env_data.AIR_GB16297.get(limit_std, dict(conc=120))["conc"]

    return dict(
        air_flow=air_flow, filter_v=v,
        bag_dia_mm=bag_dia_mm, bag_len_mm=bag_len_mm,
        filter_area=round(A_filter, 1), bag_area=round(a_bag, 3),
        n_bags=n_bags, rows=rows, cols=cols, spacing=spacing,
        plate_L=plate_L, plate_W=plate_W,
        box_L=box_L, box_W=box_W,
        clean_gas_H=clean_gas_H, bag_room_H=bag_room_H,
        hopper_H=round(hopper_H, 0), hopper_outlet=hopper_outlet,
        leg_H=leg_H, total_H=round(total_H, 0),
        inlet_dn=inlet_dn, outlet_dn=outlet_dn,
        n_pulse_valve=n_pulse_valve, air_tank_L=air_tank_L,
        eff=round(eff, 4), dp=dp,
        conc_in=pollutant_in, conc_out=round(conc_out, 1),
        limit=limit, ok=(conc_out <= limit),
        note=(f"袋式除尘器：风量{air_flow}m³/h，过滤风速{v}m/min，"
              f"过滤面积{A_filter:.1f}m²；滤袋Φ{bag_dia_mm:.0f}×{bag_len_mm:.0f}，"
              f"共{n_bags}条（{rows}行×{cols}列）；箱体{box_L:.0f}×{box_W:.0f}，"
              f"总高{total_H:.0f}mm；出口{conc_out:.1f}mg/m³"
              f"{'≤' if conc_out<=limit else '>'}限值{limit}"),
    )


def design_uasb_full(Q: float = 500.0,
                     cod_in: float = 3000.0,
                     Nv: float = 8.0,
                     H_reactor: float = 6.0,
                     cod_out_ratio: float = 0.85) -> dict:
    """UASB 厌氧反应器全参数设计。

    输入提示词可给的条件：
        Q          处理水量 (m³/d)，默认 500
        cod_in     进水 COD (mg/L)，默认 3000
        Nv         容积负荷 (kgCOD/m³·d)，默认 8（知识层范围 5~15）
        H_reactor  反应区高度 (m)，默认 6
        cod_out_ratio COD 去除率，默认 0.85

    返回：容积→直径→分区高度→三相分离器→布水→出水堰→沼气的全套几何参数。
    长度单位：反应器主尺寸 m，管口 mm。供 drawings/t8_uasb.py 取参绘图。
    """
    # ── 容积与负荷 ─────────────────────────────────
    cod_load = Q * cod_in / 1000.0                       # kgCOD/d
    V_eff = cod_load / Nv                                # m³ 有效容积
    HRT = V_eff / Q * 24.0                               # h

    # ── 反应器直径（圆柱）───────────────────────────
    A_reactor = V_eff / H_reactor                        # m² 截面积
    D = math.sqrt(4.0 * A_reactor / math.pi)
    D = math.ceil(D * 2.0) / 2.0                         # 上取整 0.5m
    # 校核上升流速
    Qh = Q / 24.0                                        # m³/h
    A_real = math.pi * D * D / 4.0
    upflow_v = Qh / A_real                               # m/h

    # ── 竖向分区（自下而上）─────────────────────────
    H_sludge = H_reactor * 0.5                           # m 污泥床
    H_suspend = H_reactor * 0.5                          # m 悬浮层
    H_three_phase = 1.5                                  # m 三相分离器
    H_settle = 1.5                                       # m 沉淀区
    H_freeboard = 0.5                                    # m 超高
    H_total = H_reactor + H_three_phase + H_settle + H_freeboard

    # ── 布水系统（每点服务 2~3 m²）──────────────────
    serve = 2.5                                          # m²/点
    n_dist_points = max(4, math.ceil(A_real / serve))
    # ── 出水堰（堰负荷 ≤1.7 L/s·m）──────────────────
    Q_peak = Q * 1.5 / 24.0 / 3600.0 * 1000.0            # L/s（时变化系数1.5）
    weir_len = Q_peak / 1.7                              # m 所需堰长
    weir_load = Q_peak / (math.pi * D)                   # 按周边堰校核 L/s·m

    # ── 沼气（产率 0.35 m³/kgCOD去除）───────────────
    cod_removed = cod_load * cod_out_ratio               # kg/d
    biogas_yield = cod_removed * 0.35                    # m³/d
    bg_q = biogas_yield / 86400.0                        # m³/s
    bg_dn = math.sqrt(4.0 * bg_q / (math.pi * 8.0)) * 1000.0  # 管内8m/s
    biogas_dn = max(50.0, math.ceil(bg_dn / 25.0) * 25.0)

    # ── 管口（mm）──────────────────────────────────
    def _dn(flow_m3h, vv):
        d = math.sqrt(4.0 * (flow_m3h / 3600.0) / (math.pi * vv)) * 1000.0
        return max(50.0, math.ceil(d / 25.0) * 25.0)
    inlet_dn = _dn(Qh, 1.0)                              # 进水管 1.0 m/s
    outlet_dn = _dn(Qh, 0.8)                             # 出水管
    sludge_dn = 150.0                                    # 排泥管

    _uasb = env_data.BIO_REACTOR["UASB"]
    lo_v, hi_v = _uasb["上升流速_m_h"]
    lo_h, hi_h = _uasb["HRT_h"]

    return dict(
        Q=Q, cod_in=cod_in, Nv=Nv, H_reactor=H_reactor,
        cod_load=round(cod_load, 1), V_eff=round(V_eff, 1), HRT=round(HRT, 1),
        D=D, A_reactor=round(A_real, 1), upflow_v=round(upflow_v, 2),
        H_sludge=round(H_sludge, 2), H_suspend=round(H_suspend, 2),
        H_three_phase=H_three_phase, H_settle=H_settle,
        H_freeboard=H_freeboard, H_total=round(H_total, 2),
        ts_angle=55.0,
        n_dist_points=n_dist_points, serve_area=serve,
        weir_len=round(weir_len, 2), weir_load=round(weir_load, 3),
        biogas_yield=round(biogas_yield, 1), biogas_dn=biogas_dn,
        inlet_dn=inlet_dn, outlet_dn=outlet_dn, sludge_dn=sludge_dn,
        hrt_ok=(lo_h <= HRT <= hi_h + 10), v_ok=(lo_v <= upflow_v <= hi_v),
        note=(f"UASB：水量{Q}m³/d，COD {cod_in}mg/L，容积负荷{Nv}kgCOD/m³·d；"
              f"有效容积{V_eff:.1f}m³，HRT {HRT:.1f}h；反应器Φ{D:.1f}m，"
              f"上升流速{upflow_v:.2f}m/h，总高{H_total:.1f}m；"
              f"布水点{n_dist_points}个，沼气{biogas_yield:.0f}m³/d"),
    )


def design_spray_tower_full(air_flow: float = 50000.0,
                            so2_in: float = 2000.0,
                            eff: float = None,
                            lg: float = None,
                            v_tower: float = None,
                            n_spray: int = 3) -> dict:
    """石灰石-石膏湿法脱硫塔（喷淋吸收塔）全参数设计。

    输入提示词可给的条件：
        air_flow   烟气量 (m³/h)，默认 50000
        so2_in     入口 SO2 浓度 (mg/m³)，默认 2000
        eff        脱硫效率，缺省取知识层 0.98
        lg         液气比 (L/m³)，缺省 15
        v_tower    空塔气速 (m/s)，缺省 3.3
        n_spray    喷淋层数，默认 3

    返回：塔径→吸收区→喷淋层→除雾器→浆池→循环泵的全套几何参数。
    主尺寸 m，高度/管口 mm。供 drawings/t9_spray_tower.py 取参绘图。
    """
    _t = env_data.AIR_POLLUTION_CONTROL["湿法脱硫塔"]
    eff = _t["脱硫效率"][1] if eff is None else eff
    v_tower = 3.3 if v_tower is None else v_tower
    lg = 15.0 if lg is None else lg

    Q_s = air_flow / 3600.0                              # m³/s
    # ── 塔径（空塔气速）─────────────────────────────
    D = math.sqrt(4.0 * Q_s / (math.pi * v_tower))
    D = math.ceil(D * 2.0) / 2.0                         # 上取整 0.5m
    A = math.pi * D * D / 4.0
    v_real = Q_s / A

    # ── 竖向分区（mm，自下而上）─────────────────────
    Q_L = air_flow * lg / 1000.0                         # m³/h 循环浆液量
    t_ret = 6.0                                          # min 浆池停留
    V_pool = Q_L * t_ret / 60.0                          # m³ 浆池容积
    H_pool = 4500.0                                      # mm 浆池高（工程合理值）
    # 浆池容积反推浆池直径（可大于塔身，即扩径浆池段）
    D_pool = math.sqrt(4.0 * V_pool / (math.pi * (H_pool / 1000.0)))
    D_pool = max(D, math.ceil(D_pool * 2.0) / 2.0)
    inlet_H = 3000.0                                     # mm 浆池顶→首层喷淋（进口烟道区）
    layer_gap = 1800.0                                   # mm 喷淋层间距
    H_absorb = inlet_H + n_spray * layer_gap             # mm 吸收区高
    H_demister = 2500.0                                  # mm 除雾器区（2级屋脊）
    H_total = H_pool + H_absorb + H_demister             # mm 塔总高

    # ── 进出口烟道（方形，烟速13 m/s）────────────────
    v_duct = 13.0
    inlet_dn = math.sqrt(Q_s / v_duct) * 1000.0          # mm 当量边长
    outlet_dn = inlet_dn

    # ── 循环泵（每喷淋层一台）───────────────────────
    n_pump = n_spray
    pump_q = Q_L / n_spray                               # m³/h·台

    # ── 达标判定 ───────────────────────────────────
    so2_out = so2_in * (1 - eff)
    limit = env_data.AIR_GB16297.get("SO2", dict(conc=550))["conc"]

    return dict(
        air_flow=air_flow, so2_in=so2_in, eff=round(eff, 3), lg=lg,
        D=D, A=round(A, 1), v_tower=round(v_real, 2),
        n_spray=n_spray, layer_gap=layer_gap,
        H_pool=round(H_pool, 0), D_pool=D_pool, inlet_H=inlet_H, H_absorb=round(H_absorb, 0),
        H_demister=H_demister, H_total=round(H_total, 0),
        Q_L=round(Q_L, 1), V_pool=round(V_pool, 1),
        n_pump=n_pump, pump_q=round(pump_q, 1),
        inlet_dn=round(inlet_dn, 0), outlet_dn=round(outlet_dn, 0),
        so2_out=round(so2_out, 1), limit=limit, ok=(so2_out <= limit),
        note=(f"湿法脱硫塔：烟气{air_flow}m³/h，SO2 {so2_in}→{so2_out:.0f}mg/m³；"
              f"塔径Φ{D:.1f}m，空塔气速{v_real:.2f}m/s；喷淋{n_spray}层，"
              f"液气比{lg}L/m³；浆池{V_pool:.1f}m³，总高{H_total/1000:.1f}m；"
              f"{'达标' if so2_out<=limit else '超标'}"),
    )


def design_activated_carbon_full(air_flow: float = 10000.0,
                                 voc_in: float = 200.0,
                                 eff: float = None,
                                 v_bed: float = None,
                                 t_contact: float = 1.0,
                                 n_bed: int = None) -> dict:
    """活性炭吸附装置（固定床 VOC 治理）全参数设计。

    输入提示词可给的条件：
        air_flow   废气量 (m³/h)，默认 10000
        voc_in     入口 VOC 浓度 (mg/m³)，默认 200
        eff        去除率，缺省取知识层 0.95
        v_bed      空塔气速 (m/s)，缺省 0.5
        t_contact  接触时间 (s)，默认 1.0
        n_bed      床层数，缺省按床高自动分

    返回：罐径→床层→装填量→脱附→进出口的全套几何参数。
    主尺寸 m，高度/管口 mm。供 drawings/t10_activated_carbon.py 取参绘图。
    """
    _a = env_data.AIR_POLLUTION_CONTROL["活性炭吸附"]
    eff = _a["去除率"][1] if eff is None else eff
    v_bed = 0.5 if v_bed is None else v_bed
    rho = 500.0                                          # kg/m³ 填充密度
    cap = _a["吸附容量_mg_g"][0]                         # mg/g 动态吸附容量（取保守下限）

    Q_s = air_flow / 3600.0                              # m³/s
    # ── 罐径（空塔气速）─────────────────────────────
    D = math.sqrt(4.0 * Q_s / (math.pi * v_bed))
    D = math.ceil(D * 2.0) / 2.0
    A = math.pi * D * D / 4.0

    # ── 活性炭床层（接触时间）───────────────────────
    V_c = Q_s * t_contact                                # m³ 活性炭体积
    H_bed_total = max(V_c / A * 1000.0, 500.0)           # mm 总床高（≥500）
    if n_bed is None:
        n_bed = max(1, math.ceil(H_bed_total / 1000.0))  # 单床≤1000mm
    H_bed = H_bed_total / n_bed                          # mm 单床高

    # ── 罐体竖向（mm）───────────────────────────────
    H_inlet = 800.0                                      # 进气分布区
    H_outlet = 600.0                                     # 出气区
    bed_gap = 300.0                                      # 床层间支撑间隙
    H_total = H_inlet + H_bed_total + (n_bed - 1) * bed_gap + H_outlet

    # ── 装填量与吸附周期 ────────────────────────────
    carbon_vol = V_c
    carbon_wt = V_c * rho                                # kg
    voc_load = air_flow * voc_in / 1e6                   # kg/h
    adsorp_cap = cap / 1000.0                            # kg/kg
    cycle_h = carbon_wt * adsorp_cap / voc_load if voc_load > 0 else 0.0

    # ── 进出口（烟速12 m/s）─────────────────────────
    v_duct = 12.0
    inlet_dn = math.ceil(math.sqrt(4.0 * (Q_s / v_duct) / math.pi) * 1000.0 / 50.0) * 50.0
    outlet_dn = inlet_dn
    steam_dn = 50.0                                      # 脱附蒸汽管

    voc_out = voc_in * (1 - eff)
    limit = env_data.AIR_GB16297.get("非甲烷总烃", dict(conc=120))["conc"]

    return dict(
        air_flow=air_flow, voc_in=voc_in, eff=round(eff, 3), v_bed=v_bed,
        D=D, A=round(A, 1),
        n_bed=n_bed, H_bed=round(H_bed, 0), H_bed_total=round(H_bed_total, 0),
        bed_gap=bed_gap, H_inlet=H_inlet, H_outlet=H_outlet,
        H_total=round(H_total, 0),
        carbon_vol=round(carbon_vol, 2), carbon_wt=round(carbon_wt, 0),
        cycle_h=round(cycle_h, 1),
        inlet_dn=inlet_dn, outlet_dn=outlet_dn, steam_dn=steam_dn,
        voc_out=round(voc_out, 1), limit=limit, ok=(voc_out <= limit),
        note=(f"活性炭吸附：废气{air_flow}m³/h，VOC {voc_in}→{voc_out:.0f}mg/m³；"
              f"罐径Φ{D:.1f}m，空塔气速{v_bed}m/s；活性炭{V_c:.2f}m³"
              f"（{carbon_wt:.0f}kg），{n_bed}床层；吸附周期{cycle_h:.0f}h；"
              f"{'达标' if voc_out<=limit else '超标'}"),
    )


def design_chimney_full(air_flow: float = 50000.0, H: float = 30.0,
                        v_out: float = None) -> dict:
    """钢烟囱（排气筒）全参数设计。

    输入：air_flow 烟气量(m³/h)、H 烟囱高度(m)、v_out 出口烟速(m/s,默认15)。
    返回：出口/底部直径、壁厚、平台、爬梯、采样孔、避雷。主尺寸 m，管口 mm。
    """
    _c = env_data.AIR_POLLUTION_CONTROL["烟囱"]
    v_out = 15.0 if v_out is None else v_out
    Q_s = air_flow / 3600.0
    D_out = math.sqrt(4.0 * Q_s / (math.pi * v_out))
    D_out = math.ceil(D_out * 20.0) / 20.0             # 取整 0.05m
    taper = _c["锥度"][0]
    D_base = D_out + 2.0 * H * taper                   # 底部加粗（锥形）
    wall_t = _c["壁厚_mm"][1]
    plat_gap = _c["平台间距_m"][0]
    n_platform = max(1, int(H / plat_gap))
    sample_dn = _c["采样孔_dn_mm"][0]
    sample_y = H - 2.0 * D_out                         # 采样孔距出口 2D
    return dict(
        air_flow=air_flow, H=H, v_out=v_out,
        D_out=round(D_out, 2), D_base=round(D_base, 2), taper=taper,
        wall_t=wall_t, n_platform=n_platform, plat_gap=plat_gap,
        sample_dn=sample_dn, sample_y=round(sample_y, 2),
        note=(f"钢烟囱：烟气{air_flow}m³/h，出口Φ{D_out:.2f}m"
              f"（烟速{v_out}m/s），底部Φ{D_base:.2f}m，高{H}m；"
              f"壁厚{wall_t}mm，平台{n_platform}层，采样孔Φ{sample_dn}mm"),
    )


def design_duct_full(air_flow: float = 50000.0, v_duct: float = None,
                     n_elbow: int = 3, n_tee: int = 2) -> dict:
    """风管系统全参数设计（主管+管件）。

    输入：air_flow 风量(m³/h)、v_duct 风速(m/s,默认12)、n_elbow/n_tee 管件数。
    返回：主管直径、弯头/三通/变径规格、板厚、支吊架。管径 mm。
    """
    _d = env_data.AIR_POLLUTION_CONTROL["风管"]
    v_duct = 12.0 if v_duct is None else v_duct
    Q_s = air_flow / 3600.0
    dn = math.sqrt(4.0 * Q_s / (math.pi * v_duct)) * 1000.0
    dn = math.ceil(dn / 50.0) * 50.0                   # 取整 50mm
    elbow_r = dn * _d["弯头曲率_倍径"][0]              # 曲率半径
    plate_t = 0.5 if dn < 450 else (1.0 if dn < 1000 else 2.0)
    hanger_gap = _d["支吊架间距_m"][0] * 1000.0
    flange_gap = _d["法兰间距_m"][0] * 1000.0
    reducer_len = dn * 0.5                             # 变径长度（按管径）
    return dict(
        air_flow=air_flow, v_duct=v_duct, dn=dn,
        elbow_r=elbow_r, plate_t=plate_t,
        hanger_gap=hanger_gap, flange_gap=flange_gap,
        reducer_len=reducer_len, n_elbow=n_elbow, n_tee=n_tee,
        note=(f"风管：风量{air_flow}m³/h，风速{v_duct}m/s，主管Φ{dn:.0f}mm；"
              f"板厚{plate_t}mm，弯头R={elbow_r:.0f}mm，支吊架间距{hanger_gap/1000:.0f}m"),
    )


def design_fan_full(air_flow: float = 50000.0, pressure: float = 2500.0,
                    eff: float = None) -> dict:
    """离心风机选型与外形设计。

    输入：air_flow 风量(m³/h)、pressure 全压(Pa,默认2500)、eff 全压效率。
    返回：轴功率、电机功率、进出口直径、外形尺寸。管径 mm，尺寸 mm。
    """
    _f = env_data.AIR_POLLUTION_CONTROL["风机"]
    eff = _f["全压效率"][1] if eff is None else eff
    Q_s = air_flow / 3600.0
    N_shaft = Q_s * pressure / 1000.0 / eff            # kW 轴功率
    N_need = N_shaft * _f["电机安全系数"][0]
    _std = [5.5, 7.5, 11, 15, 18.5, 22, 30, 37, 45, 55, 75, 90, 110, 132, 160, 200]
    N_rated = next((x for x in _std if x >= N_need), _std[-1])
    v_in = _f["进口流速_m_s"][0]
    inlet_dn = math.ceil(math.sqrt(4.0 * Q_s / (math.pi * v_in)) * 1000.0 / 50.0) * 50.0
    outlet_dn = inlet_dn
    # 外形（按风量粗估离心风机机号尺寸）
    L = 1500.0 + air_flow / 1000.0 * 25.0
    W = L * 0.68
    H = L * 0.82
    return dict(
        air_flow=air_flow, pressure=pressure, eff=eff,
        N_shaft=round(N_shaft, 1), N_rated=N_rated,
        inlet_dn=inlet_dn, outlet_dn=outlet_dn,
        L=round(L, 0), W=round(W, 0), H=round(H, 0),
        note=(f"离心风机：风量{air_flow}m³/h，全压{pressure}Pa；"
              f"轴功率{N_shaft:.1f}kW，配电机{N_rated}kW；"
              f"进出口Φ{inlet_dn:.0f}mm，外形{L:.0f}×{W:.0f}×{H:.0f}mm"),
    )


def design_rto_full(air_flow: float = 20000.0,
                    voc_in: float = 1000.0,
                    eff: float = None,
                    n_chamber: int = 3,
                    bed_thk: float = 1.2,
                    v_face: float = 1.2,
                    temp: float = 800.0) -> dict:
    """RTO 蓄热式焚烧炉全参数设计（VOC 治理）。

    输入提示词可给的条件：
        air_flow   废气量 (m³/h)，默认 20000
        voc_in     入口 VOC 浓度 (mg/m³)，默认 1000
        eff        净化效率，缺省 0.98
        n_chamber  蓄热室数量（2/3室），默认 3
        bed_thk    蓄热床厚度 (m)，默认 1.2
        v_face     床面气速 (m/s)，默认 1.2
        temp       焚烧温度 (℃)，默认 800（≥760 才能分解 VOC）

    返回：单室截面积→炉径→蓄热体体积→焚烧室→进出口→换热→达标判定。
    主尺寸 m，管口 mm。
    """
    eff = 0.98 if eff is None else eff
    Q_s = air_flow / 3600.0                          # m³/s
    # 单室面积（n_chamber 室中只有 n_chamber-1 室处于进气/出气，*0.5 折算）
    A_chamber = Q_s / v_face / max(1, (n_chamber - 1) * 0.5)
    D = math.sqrt(4.0 * A_chamber / math.pi)
    D = math.ceil(D * 2.0) / 2.0                     # 上取整 0.5m
    A_real = math.pi * D * D / 4.0
    v_real = Q_s / (A_real * max(1, (n_chamber - 1) * 0.5))
    V_bed = A_real * bed_thk * n_chamber             # m³ 总蓄热体

    # 焚烧室（停留时间 ~1s，按焚烧温度校核）
    H_combust = max(2.0, temp / 400.0)               # m 粗略随温度增高
    # 进出口烟道（烟速 12 m/s）
    v_duct = 12.0
    inlet_dn = math.ceil(math.sqrt(Q_s / v_duct) * 1000.0 / 50.0) * 50.0
    outlet_dn = inlet_dn

    voc_out = voc_in * (1 - eff)
    limit = env_data.AIR_GB16297.get("非甲烷总烃", dict(conc=120))["conc"]
    temp_ok = temp >= 760.0                          # 分解温度阈值
    return dict(
        air_flow=air_flow, voc_in=voc_in, eff=eff,
        n_chamber=n_chamber, bed_thk=bed_thk, v_face=v_face,
        D=D, A_chamber=round(A_real, 1), v_face_real=round(v_real, 2),
        V_bed=round(V_bed, 1), H_combust=round(H_combust, 1),
        temp=temp, temp_ok=temp_ok,
        inlet_dn=inlet_dn, outlet_dn=outlet_dn,
        voc_out=round(voc_out, 1), limit=limit, ok=(voc_out <= limit and temp_ok),
        note=(f"RTO：废气{air_flow}m³/h，VOC {voc_in}→{voc_out:.0f}mg/m³；"
              f"{n_chamber}室，炉径Φ{D:.1f}m，蓄热床{V_bed:.1f}m³，"
              f"焚烧温度{temp}℃（{'≥760℃达标' if temp_ok else '不足，需提高'}）；"
              f"{'排放达标' if voc_out<=limit else '超标'}"),
    )


def design_scr_full(air_flow: float = 200000.0,
                    nox_in: float = 400.0,
                    eff: float = None,
                    v_face: float = 0.5,
                    area_vel: float = None,
                    n_layer: int = 2) -> dict:
    """SCR 选择性催化还原脱硝反应器全参数设计。

    输入提示词可给的条件：
        air_flow   烟气量 (m³/h)，默认 200000（电站/锅炉量级）
        nox_in     入口 NOx 浓度 (mg/m³)，默认 400
        eff        脱硝效率，缺省 0.80（催化剂层设计值）
        v_face     催化剂表面气速 (m/s)，默认 0.5
        n_layer    催化剂层数，默认 2
        area_vel   空塔气速(m/s)，缺省按 v_face

    返回：反应器截面积→边长→催化剂体积→层高→压降→喷氨→达标判定。
    主尺寸 m，管口 mm。
    """
    eff = 0.80 if eff is None else eff
    Q_s = air_flow / 3600.0
    A_reactor = Q_s / v_face                        # m² 总截面积
    side = math.sqrt(A_reactor)                     # m 方形边长
    side = math.ceil(side * 2.0) / 2.0
    A_real = side * side
    v_real = Q_s / A_real
    # 催化剂层（单层层高 ~1.0m，含支撑）
    H_layer = 1.0
    H_cat = n_layer * H_layer
    H_free = 2.0                                    # 进出口均流段
    H_total = H_cat + H_free
    V_cat = A_real * H_cat                          # m³ 催化剂体积
    dp = 200.0 * n_layer                            # 每层约 200Pa 阻力

    nox_out = nox_in * (1 - eff)
    limit = env_data.AIR_GB16297.get("NOx", dict(conc=240))["conc"]
    # 喷氨（NH3/NOx 摩尔比 ~0.95）
    nh3_ratio = 0.95
    nh3_q = air_flow * nox_in / 1e6 * nh3_ratio * 17.0 / 30.0 * 1000.0 / 1000.0  # kg/h 粗估
    return dict(
        air_flow=air_flow, nox_in=nox_in, eff=eff,
        v_face=v_face, n_layer=n_layer,
        side=side, A_reactor=round(A_real, 1), v_real=round(v_real, 2),
        H_cat=round(H_cat, 1), H_total=round(H_total, 1),
        V_cat=round(V_cat, 1), dp=round(dp, 0),
        nh3_q=round(nh3_q, 1),
        nox_out=round(nox_out, 1), limit=limit, ok=(nox_out <= limit),
        note=(f"SCR：烟气{air_flow}m³/h，NOx {nox_in}→{nox_out:.0f}mg/m³；"
              f"反应器{side:.1f}×{side:.1f}m，{n_layer}层催化剂（{V_cat:.1f}m³），"
              f"阻力{dp:.0f}Pa，脱硝效率{eff*100:.0f}%；"
              f"{'达标' if nox_out<=limit else '超标'}"),
    )


def design_incinerator_full(Q: float = 300.0,
                            lhv: float = 6500.0,
                            eff: float = None,
                            temp_min: float = 850.0,
                            t_res: float = 2.0) -> dict:
    """生活垃圾焚烧炉全参数设计（回转窑/机械炉排）。

    输入提示词可给的条件：
        Q       处理量 (t/d)，默认 300
        lhv     低位热值 (kJ/kg)，默认 6500（中国生活垃圾典型值）
        eff     燃烧效率，缺省 0.99
        temp_min 炉膛温度下限(℃)，默认 850（GB 18485 要求≥850）
        t_res   烟气停留时间(s)，默认 2.0（GB 18485 要求≥2s）

    返回：炉排面积/回转窑规格→一燃室→二燃室→余热锅→达标判定（GB 18485）。
    主尺寸 m。
    """
    eff = 0.99 if eff is None else eff
    # 炉排面积（机械炉排，负荷 ~700 kg/m²·h）
    load_rate = 700.0                               # kg/m²·h
    A_grate = Q * 1000.0 / 24.0 / load_rate         # m²
    # 回转窑（按处理量估算窑径，经验 D≈0.12·Q^0.4）
    D_kiln = 0.12 * (Q ** 0.4)
    D_kiln = round(math.ceil(D_kiln * 2.0) / 2.0, 1)
    L_kiln = D_kiln * 10.0                          # 窑长径比 ~10
    # 二燃室（停留≥2s，850℃，容积热强度校核）
    Q_s = (Q * 1000.0 / 24.0 / 3600.0) * lhv / 1000.0  # MW 热输入
    # 余热锅炉蒸发量（~0.6 t蒸汽/t垃圾）
    steam_rate = 0.6
    steam = Q * steam_rate

    # 排放限值（GB 18485）
    _g = env_data.INCINERATION_GB18485
    temp_ok = temp_min >= 850.0
    tres_ok = t_res >= 2.0
    return dict(
        Q=Q, lhv=lhv, eff=eff,
        A_grate=round(A_grate, 1), D_kiln=D_kiln, L_kiln=round(L_kiln, 1),
        Q_thermal=round(Q_s, 2), steam=round(steam, 0),
        temp_min=temp_min, t_res=t_res,
        temp_ok=temp_ok, tres_ok=tres_ok,
        dioxin_limit=_g["二噁英"]["day"],
        note=(f"焚烧炉：处理量{Q}t/d，热值{lhv}kJ/kg；炉排面积{A_grate:.1f}m²，"
              f"回转窑Φ{D_kiln:.1f}×{L_kiln:.1f}m；余热{Q_s:.1f}MW，"
              f"产汽{steam:.0f}t/d；炉膛{temp_min}℃/停留{t_res}s"
              f"（{'满足' if temp_ok and tres_ok else '不满足'}GB 18485 ≥850℃·≥2s）"),
    )
