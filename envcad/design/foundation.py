# -*- coding: utf-8 -*-
"""地基与基础设计验算（知识驱动，土木）。

覆盖三类常用验算，均从 knowledge.civil 取土层参数与修正系数：
  1) 地基承载力深宽修正
  2) 柱下独立基础底面积确定与地基验算
  3) 重力式挡土墙抗滑/抗倾覆稳定（朗肯主动土压力）

对标探索者「基础设计」：输入荷载与土层 → 输出尺寸与稳定结论。
"""
from __future__ import annotations

import math

from ..knowledge import civil


def design_spread_footing(Fk: float, soil: str = "粉质粘土",
                          d: float = 1.5, b_try: float = 3.0,
                          gamma_m: float = 18.0,
                          correction: str = "e<0.85粘性土",
                          gamma_G: float = 20.0,
                          square: bool = True) -> dict:
    """柱下独立基础底面积设计。

    参数：
        Fk        上部传至基础顶面的竖向力标准值 (kN)
        soil      持力层土类（取 knowledge.civil.SOIL）
        d         基础埋深 (m)
        b_try     试算基础宽度 (m)，用于深宽修正取值
        gamma_m   基底以上土的加权平均重度 (kN/m³)
        correction 深宽修正系数组名（knowledge.civil.BEARING_CORRECTION）
        gamma_G   基础及回填土平均重度 (kN/m³)
        square    True 方形基础，False 取给定宽度算长边

    返回：含修正后承载力 fa、所需底面积 A、基础边长、基底反力与验算结论。
    """
    sp = civil.soil_props(soil)
    cor = civil.BEARING_CORRECTION.get(correction, dict(eta_b=0.3, eta_d=1.6))
    fak = sp["fak"]
    corr = civil.correct_bearing(fak, b_try, d, sp["gamma"],
                                 gamma_m, cor["eta_b"], cor["eta_d"])
    fa = corr["fa"]                      # kPa
    # 所需底面积：A ≥ Fk / (fa - γG·d)
    denom = fa - gamma_G * d
    A_req = Fk / denom if denom > 0 else float("inf")
    if square:
        side = math.sqrt(A_req)
        side = math.ceil(side / 0.1) * 0.1   # 上取整到 100mm 模数
        A = side * side
        dims = (round(side, 2), round(side, 2))
    else:
        L = A_req / b_try
        L = math.ceil(L / 0.1) * 0.1
        A = b_try * L
        dims = (round(b_try, 2), round(L, 2))
    # 基底平均反力（含基础自重）：pk = Fk/A + γG·d
    pk = Fk / A + gamma_G * d
    return dict(
        soil=soil, fak=fak, fa=fa, correction=corr,
        Fk=Fk, d=d, gamma_G=gamma_G,
        A_req=round(A_req, 3), A=round(A, 3), dims=dims,
        pk=round(pk, 1),
        ok=(pk <= fa),
        margin=round(fa - pk, 1),
        note=(f"持力层{soil}：fak={fak}→fa={fa}kPa；所需{A_req:.2f}m²，"
              f"取底板{dims[0]}×{dims[1]}m；基底反力pk={pk:.1f}kPa "
              f"{'≤' if pk <= fa else '>'} fa"),
    )


def design_retaining_wall(H: float, soil: str = "中砂",
                          b_bottom: float = None, b_top: float = 0.5,
                          gamma_wall: float = 24.0,
                          mu: float = 0.5, q: float = 10.0) -> dict:
    """重力式挡土墙抗滑与抗倾覆稳定验算（朗肯主动土压力）。

    参数：
        H         墙高 (m)
        soil      墙背填土土类，缺省中砂（重力式挡墙宜用无粘性/透水回填料）
        b_bottom  墙底宽 (m)，缺省取 0.75H（重力式挡墙常用 0.5~0.8H）
        b_top     墙顶宽 (m)
        gamma_wall 墙身材料重度 (kN/m³，浆砌石/混凝土 22~24)
        mu        基底摩擦系数（砂土/砂砾 0.4~0.5，岩石 0.6~0.7）
        q         墙顶均布超载 (kPa)

    返回：土压力、稳定安全系数与结论（Ks≥1.3 抗滑、K0≥1.6 抗倾覆）。
    """
    sp = civil.soil_props(soil)
    gamma, phi, c = sp["gamma"], sp["phi"], sp["c"]
    if b_bottom is None:
        b_bottom = round(0.75 * H, 2)
    Ka = civil.active_earth_coef(phi)

    # 主动土压力（含超载，忽略粘聚力有利影响以偏安全）
    Ea_soil = 0.5 * gamma * H * H * Ka          # kN/m 三角形分布
    Ea_q = q * H * Ka                           # kN/m 矩形分布(超载)
    Ea = Ea_soil + Ea_q
    # 合力作用点高度（对墙趾取矩）
    y_soil = H / 3.0
    y_q = H / 2.0
    M_over = Ea_soil * y_soil + Ea_q * y_q      # 倾覆力矩 kN·m/m

    # 墙体自重（梯形断面）与重心到墙趾距离
    A_wall = 0.5 * (b_top + b_bottom) * H       # m²
    W = A_wall * gamma_wall                      # kN/m
    # 梯形形心距墙趾（墙趾在底宽外侧，取墙背竖直、墙面倾斜的常规布置近似）
    x_w = (b_bottom * b_bottom + b_bottom * b_top + b_top * b_top) \
        / (3.0 * (b_bottom + b_top))
    M_resist = W * x_w                           # 抗倾覆力矩 kN·m/m

    # 抗滑：Ks = (μ·W) / Ea
    Ks = (mu * W) / Ea if Ea > 0 else float("inf")
    # 抗倾覆：K0 = M_resist / M_over
    K0 = M_resist / M_over if M_over > 0 else float("inf")

    return dict(
        soil=soil, H=H, Ka=round(Ka, 3),
        b_bottom=b_bottom, b_top=b_top,
        Ea=round(Ea, 1), Ea_soil=round(Ea_soil, 1), Ea_q=round(Ea_q, 1),
        W=round(W, 1), x_w=round(x_w, 3),
        M_over=round(M_over, 1), M_resist=round(M_resist, 1),
        Ks=round(Ks, 2), K0=round(K0, 2),
        Ks_ok=Ks >= 1.3, K0_ok=K0 >= 1.6,
        all_ok=(Ks >= 1.3 and K0 >= 1.6),
        note=(f"H={H}m，填土{soil}(φ={phi}°)，Ka={Ka:.3f}；"
              f"Ea={Ea:.1f}kN/m，W={W:.1f}kN/m；"
              f"抗滑Ks={Ks:.2f}(≥1.3)，抗倾覆K0={K0:.2f}(≥1.6)"),
    )


def format_footing_result(r: dict) -> str:
    lines = ["【柱下独立基础设计】"]
    lines.append(f"持力层：{r['soil']}，fak={r['fak']} kPa → 修正后 fa={r['fa']} kPa")
    lines.append(f"竖向力 Fk={r['Fk']} kN，埋深 d={r['d']} m")
    lines.append(f"所需底面积 {r['A_req']} m² → 取底板 {r['dims'][0]}×{r['dims'][1]} m（A={r['A']} m²）")
    lines.append(f"基底反力 pk={r['pk']} kPa，{'满足' if r['ok'] else '超限'}（余量 {r['margin']} kPa）")
    return "\n".join(lines)


def format_retaining_result(r: dict) -> str:
    lines = ["【重力式挡土墙稳定验算】"]
    lines.append(f"墙高 H={r['H']} m，填土 {r['soil']}，Ka={r['Ka']}")
    lines.append(f"底宽 {r['b_bottom']} m / 顶宽 {r['b_top']} m")
    lines.append(f"主动土压力 Ea={r['Ea']} kN/m，墙重 W={r['W']} kN/m")
    lines.append(f"抗滑 Ks={r['Ks']}（≥1.3）{'√' if r['Ks_ok'] else '×'}；"
                 f"抗倾覆 K0={r['K0']}（≥1.6）{'√' if r['K0_ok'] else '×'}")
    lines.append("结论：" + ("稳定满足" if r["all_ok"] else "稳定不足，需加大断面"))
    return "\n".join(lines)
