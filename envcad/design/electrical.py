# -*- coding: utf-8 -*-
"""电气设计验算（知识驱动）。

从 knowledge.elec_data 取载流量/需要系数/照度标准，覆盖四类常用计算：
  1) 负荷计算（需要系数法）：设备容量 → 计算有功/无功/视在/电流
  2) 电缆选型：按计算电流选截面，载流量 + 电压降双校验
  3) 照度计算（利用系数法/流明法）：面积 → 灯具数量 + 功率密度
  4) 短路电流估算：变压器 LV 母线三相短路电流（简化，忽略系统阻抗）
"""
from __future__ import annotations

import math

from ..knowledge import elec_data


def design_power_load(Pe: float, kind: str = "办公照明") -> dict:
    """需要系数法负荷计算。

    参数：
        Pe    设备安装容量 (kW)
        kind  用电性质（决定需要系数 Kx 与功率因数 cosφ）

    公式：
        Pjs = Kx · Pe          计算有功 (kW)
        cosφ → tanφ
        Qjs = Pjs · tanφ       计算无功 (kvar)
        Sjs = Pjs / cosφ       视在功率 (kVA)
        Ijs = Sjs·1000/(√3·Un) 计算电流 (A)，Un=380V
    """
    d = elec_data.demand_factor(kind)
    Kx, cos = d["Kx"], d["cos"]
    tan = math.tan(math.acos(cos))
    Pjs = Kx * Pe
    Qjs = Pjs * tan
    Sjs = Pjs / cos
    Un = elec_data.UN_LV * 1000.0            # V
    Ijs = Sjs * 1000.0 / (math.sqrt(3) * Un)
    return dict(
        Pe=Pe, kind=kind, Kx=Kx, cos=cos,
        Pjs=round(Pjs, 2), Qjs=round(Qjs, 2), Sjs=round(Sjs, 2),
        Ijs=round(Ijs, 1),
        note=(f"{kind}：装机 {Pe}kW，Kx={Kx}、cosφ={cos}；"
              f"计算有功 {Pjs:.1f}kW，视在 {Sjs:.1f}kVA，计算电流 {Ijs:.1f}A"),
    )


def select_cable(I_calc: float, cos: float = 0.85, length: float = 50.0,
                 material: str = "铜", k_group: float = 0.8,
                 usage: str = "动力") -> dict:
    """按计算电流选电缆截面：载流量校验 + 电压降校验。

    参数：
        I_calc  计算电流 (A)
        cos     功率因数
        length  线路长度 (m)
        material 导体材质（铜/铝）
        k_group 敷设/环境综合校正系数（缺省 0.8）
        usage   用途（决定电压降限值）

    校验：
        载流量 Iz·k ≥ I_calc
        Δu% = √3·I·R·cosφ/Un ×100 ≤ 限值
    """
    rho = elec_data.RESISTIVITY[material]
    limit = elec_data.VOLTAGE_DROP_LIMIT.get(usage, 5.0)
    Un = elec_data.UN_LV * 1000.0
    chosen = None
    for S in elec_data.WIRE_SECTIONS:
        Iz = elec_data.cable_ampacity(S, material)
        if Iz * k_group < I_calc:
            continue
        R = rho * length / S                      # Ω
        dU = math.sqrt(3) * I_calc * R * cos      # V
        du_pct = dU / Un * 100.0
        if du_pct <= limit:
            chosen = dict(section=S, Iz=Iz, Iz_corr=round(Iz * k_group, 1),
                          R=round(R, 4), dU=round(dU, 2),
                          du_pct=round(du_pct, 2))
            break
    if chosen is None:
        # 载流量满足但压降超限 → 取满足压降的最小截面
        for S in elec_data.WIRE_SECTIONS:
            R = rho * length / S
            dU = math.sqrt(3) * I_calc * R * cos
            du_pct = dU / Un * 100.0
            if du_pct <= limit:
                Iz = elec_data.cable_ampacity(S, material)
                chosen = dict(section=S, Iz=Iz, Iz_corr=round(Iz * k_group, 1),
                              R=round(R, 4), dU=round(dU, 2),
                              du_pct=round(du_pct, 2))
                break
    ok = chosen is not None
    if not ok:
        chosen = dict(section=elec_data.WIRE_SECTIONS[-1], Iz=0,
                      Iz_corr=0, R=0, dU=0, du_pct=999)
    return dict(
        I_calc=I_calc, material=material, length=length, usage=usage,
        limit=limit, ok=ok, **chosen,
        note=(f"计算电流 {I_calc:.1f}A → 选 {material}芯 {chosen['section']}mm²"
              f"（载流量 {chosen['Iz']}A×{k_group}={chosen['Iz_corr']}A ≥ {I_calc:.1f}A），"
              f"电压降 {chosen['du_pct']}% {'≤' if chosen['du_pct'] <= limit else '>'} {limit}%"),
    )


def design_illumination(area: float, place: str = "办公室",
                        lamp_power: float = 36.0, lamp_type: str = "LED",
                        U: float = 0.5, K: float = 0.8) -> dict:
    """流明法照度计算：面积 → 灯具数量 + 安装功率 + 功率密度。

    公式：
        Φ_total = E·A / (U·K)      需要总光通量 (lm)
        Φ_lamp  = P_lamp·η         单灯光通量 (lm)
        N = ceil(Φ_total / Φ_lamp) 灯具数量
    """
    std = elec_data.illuminance_std(place)
    E = std["lx"]
    eff = elec_data.LAMP_EFFICACY.get(lamp_type, 100)
    phi_total = E * area / (U * K)
    phi_lamp = lamp_power * eff
    N = max(1, math.ceil(phi_total / phi_lamp))
    P_install = N * lamp_power / 1000.0           # kW
    lpd = N * lamp_power / area                    # W/m²
    E_actual = N * phi_lamp * U * K / area
    return dict(
        area=area, place=place, E=E, lamp_type=lamp_type,
        lamp_power=lamp_power, N=N,
        P_install=round(P_install, 3), lpd=round(lpd, 1),
        E_actual=round(E_actual, 0),
        note=(f"{place}：照度标准 {E}lx，面积 {area}m²；采用 {lamp_type} {lamp_power}W×{N} 套，"
              f"实现照度约 {E_actual:.0f}lx，照明功率密度 {lpd:.1f}W/m²，安装功率 {P_install:.2f}kW"),
    )


def estimate_short_circuit(Sn: float, uk: float = 4.5,
                           Un: float = 0.4) -> dict:
    """变压器低压母线三相短路电流估算（忽略系统与线路阻抗）。

    参数：
        Sn  变压器容量 (kVA)
        uk  阻抗电压百分数 (%)
        Un  低压侧线电压 (kV)

    公式：
        In = Sn / (√3·Un)              额定电流 (kA，Un取kV则In为kA×… 换算见下)
        Ik = In · 100/uk              三相短路电流
    """
    In = Sn / (math.sqrt(3) * Un * 1000.0) * 1000.0   # A: Sn kVA/(√3·Un_V)
    Ik = In * 100.0 / uk                               # A
    ik_ka = Ik / 1000.0
    ip = 2.55 * ik_ka                                  # 冲击电流峰值 kA (χ≈1.8)
    return dict(
        Sn=Sn, uk=uk, Un=Un,
        In=round(In, 1), Ik=round(ik_ka, 2), ip=round(ip, 2),
        note=(f"{Sn}kVA 变压器（uk={uk}%）低压 {Un}kV 母线：额定电流 {In:.0f}A，"
              f"三相短路电流 Ik≈{ik_ka:.2f}kA，冲击电流峰值 ip≈{ip:.1f}kA"),
    )


def format_load_result(load: dict, cable: dict = None) -> str:
    lines = ["【电气负荷计算】", load["note"]]
    if cable:
        lines.append("电缆选型：" + cable["note"])
        lines.append("结论：" + ("满足载流量与电压降要求" if cable["ok"] else "需加大截面或缩短线路"))
    return "\n".join(lines)


def format_illumination_result(r: dict) -> str:
    return "【照度计算】\n" + r["note"]


def format_sc_result(r: dict) -> str:
    return "【短路电流估算】\n" + r["note"]
