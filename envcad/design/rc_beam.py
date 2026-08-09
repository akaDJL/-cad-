# -*- coding: utf-8 -*-
"""钢筋混凝土梁设计验算（知识驱动）。

把 knowledge 的材料库与公式库串起来，给定截面与内力即自动算配筋，
像探索者那样「输入内力 → 输出配筋与验算结论」，供绘图与文档复用。
"""
from __future__ import annotations

import math

from ..knowledge import materials, formulas


def _select_rebar(As):
    """按计算面积选受拉纵筋（nΦd），取最接近且不小于计算值。"""
    if As is None or As <= 0:
        return dict(n=0, d=0, area=0.0, note="—")
    for d in (25, 22, 20, 18, 16, 14, 12, 10, 8):
        a = materials.rebar_area(d)
        for n in range(2, 9):
            if n * a >= As:
                return dict(n=n, d=d, area=n * a, note=f"{n}Φ{d}")
    d, a = 32, materials.rebar_area(32)
    n = max(2, math.ceil(As / a))
    return dict(n=n, d=d, area=n * a, note=f"{n}Φ{d}")


def _select_stirrup(Asv_s):
    """按 Asv/s 选双肢箍（Φd@s）。"""
    if Asv_s <= 0:
        return dict(d=8, s=200, Asv=2 * materials.rebar_area(8), note="Φ8@200(构造)")
    for d in (8, 10, 12):
        Asv = 2 * materials.rebar_area(d)
        s = Asv / Asv_s
        s = max(100, min(200, round(s / 50) * 50))
        if s >= 100:
            return dict(d=d, s=s, Asv=Asv, note=f"Φ{d}@{s}")
    return dict(d=12, s=100, Asv=2 * materials.rebar_area(12), note="Φ12@100(最大配箍)")


def design_rc_beam(b: float, h: float, cover: float = 20.0,
                   concrete_grade: str = "C30", rebar_grade: str = "HRB400",
                   M: float = 0.0, V: float = 0.0, Mk: float = None,
                   l: float = None, fyv: float = 360.0, alpha1: float = 1.0,
                   crack_limit: float = 0.30,
                   deflect_div: float = 200.0) -> dict:
    """钢筋混凝土矩形梁一键验算。

    参数（单位 mm / N·mm）：
        b,h          截面宽、高
        cover        保护层厚度
        concrete_grade / rebar_grade  材料等级
        M,V          弯矩、剪力设计值
        Mk           准永久组合弯矩（裂缝/挠度用，缺省取 M）
        l            计算跨度（挠度验算用）
        fyv          箍筋强度设计值
    返回：结构化结果，含配筋建议与各项验算 ok 标志。
    """
    conc = materials.concrete_props(concrete_grade)
    reb = materials.rebar_props(rebar_grade)
    h0 = h - cover
    fc, ft, ftk = conc["fc"], conc["ft"], conc["ftk"]
    Ec = conc["Ec"] * 1e4
    fy, Es = reb["fy"], reb["Es"]

    flex = formulas.rc_flexure(b, h0, M, fc, fy, alpha1)
    shear = formulas.rc_shear(b, h0, V, ft, conc["fc"], fyv)
    mk = M * 0.5 if Mk is None else Mk  # 缺省按准永久组合≈设计值×0.5(G=Q时)

    crack = formulas.rc_crack(mk, flex["As"] or 0.0, b, h, h0, ftk, cover, 25, Es, 2.1, crack_limit)
    deflect = (formulas.rc_deflect(mk, flex["As"] or 0.0, b, h0, l, Ec, Es, deflect_div)
               if l else None)

    rebar = _select_rebar(flex["As"])
    stirrup = _select_stirrup(shear["Asv_s"])

    rho = (rebar["area"] / (b * h0)) if b * h0 else 0.0
    rho_min = max(0.0020, 0.45 * ft / fy)

    return dict(
        section=dict(b=b, h=h, h0=h0, cover=cover),
        material=dict(concrete=concrete_grade, rebar=rebar_grade,
                      fc=fc, ft=ft, fy=fy),
        flexure=flex, shear=shear, crack=crack, deflect=deflect,
        rebar=rebar, stirrup=stirrup,
        rho=rho, rho_min=rho_min,
        rho_ok=rho >= rho_min,
        all_ok=(flex["ok"] and shear["ok_section"] and crack["ok"]
                and (deflect["ok"] if deflect else True) and rho >= rho_min),
    )


def format_rc_beam_result(r: dict) -> str:
    """把结果格式化为可读文本，供 CLI 与文档引用。"""
    lines = []
    s = r["section"]
    lines.append(f"截面 b×h = {s['b']}×{s['h']} mm，h0={s['h0']:.0f}，保护层 {s['cover']} mm")
    m = r["material"]
    lines.append(f"材料：混凝土 {m['concrete']}（fc={m['fc']}），钢筋 {m['rebar']}（fy={m['fy']}）")
    fl = r["flexure"]
    if fl["As"] is not None:
        lines.append(f"正截面：ξ={fl['xi']:.3f}，As计={fl['As']:.0f} mm² → 选 {r['rebar']['note']}，ok={fl['ok']}")
    else:
        lines.append(f"正截面：{fl['note']}")
    sh = r["shear"]
    lines.append(f"斜截面：Vc={sh['Vc']:.0f}，Vmax={sh['Vmax']:.0f}，Asv/s={sh['Asv_s']:.3f} → 箍筋 {r['stirrup']['note']}，截面ok={sh['ok_section']}")
    cr = r["crack"]
    lines.append(f"裂缝：wmax={cr['wmax']:.3f} mm，ok={cr['ok']}")
    if r["deflect"]:
        df = r["deflect"]
        lines.append(f"挠度：f={df['f']:.1f} mm，ok={df['ok']}")
    lines.append(f"配筋率 ρ={r['rho']*100:.2f}%（最小 {r['rho_min']*100:.2f}%），ok={r['rho_ok']}")
    lines.append("结论：" + ("全部满足" if r["all_ok"] else "存在不满足项，请调整"))
    return "\n".join(lines)
