# -*- coding: utf-8 -*-
"""《结构计算书》DOCX 自动生成（数据来自设计层结果）。

用法：
  from envcad.design.rc_beam import design_rc_beam, format_rc_beam_result
  from envcad.docgen.calc_book import generate_calc_book
  r = design_rc_beam(250, 500, 20, "C30", "HRB400", M=120e6, V=180e3, l=6000)
  generate_calc_book("计算书.docx", r, project="XX 梁 KL1")
"""
from __future__ import annotations

from ..design.rc_beam import format_rc_beam_result
from . import new_cn_doc, add_heading_cn, add_para_cn, add_table_cn


def generate_calc_book(out_path: str, result: dict, project: str = "XX 构件") -> str:
    doc = new_cn_doc(f"{project} 结构计算书")

    # 1 设计输入
    add_heading_cn(doc, "一、设计输入", 1)
    s, m = result["section"], result["material"]
    add_table_cn(doc, ["项目", "取值"], [
        ["截面 b×h (mm)", f"{s['b']}×{s['h']}"],
        ["有效高度 h0 (mm)", f"{s['h0']:.0f}"],
        ["保护层 (mm)", f"{s['cover']}"],
        ["混凝土", m["concrete"]],
        ["钢筋", m["rebar"]],
        ["fc / ft (N/mm²)", f"{m['fc']} / {m['ft']}"],
        ["fy (N/mm²)", f"{m['fy']}"],
    ])

    # 2 正截面受弯
    add_heading_cn(doc, "二、正截面受弯承载力", 1)
    fl = result["flexure"]
    if fl["As"] is not None:
        add_table_cn(doc, ["参数", "结果"], [
            ["相对受压区高度 ξ", f"{fl['xi']:.4f}"],
            ["受压区高度 x (mm)", f"{fl['x']:.1f}"],
            ["计算配筋 As (mm²)", f"{fl['As']:.0f}"],
            ["抗弯承载力 Mu (kN·m)", f"{fl['Mu']/1e6:.1f}"],
            ["ξ≤ξb", "满足" if fl["ok"] else "不满足"],
        ])
        add_para_cn(doc, f"实配纵筋：{result['rebar']['note']}（面积 {result['rebar']['area']:.0f} mm²）")
    else:
        add_para_cn(doc, fl["note"])

    # 3 斜截面受剪
    add_heading_cn(doc, "三、斜截面受剪承载力", 1)
    sh = result["shear"]
    add_table_cn(doc, ["参数", "结果"], [
        ["混凝土抗剪 Vc (kN)", f"{sh['Vc']/1e3:.1f}"],
        ["截面限制 Vmax (kN)", f"{sh['Vmax']/1e3:.1f}"],
        ["所需 Asv/s (mm²/mm)", f"{sh['Asv_s']:.4f}"],
        ["截面抗剪", "满足" if sh["ok_section"] else "不满足"],
    ])
    add_para_cn(doc, f"箍筋配置：{result['stirrup']['note']}")

    # 4 裂缝
    add_heading_cn(doc, "四、裂缝宽度验算", 1)
    cr = result["crack"]
    add_table_cn(doc, ["参数", "结果"], [
        ["最大裂缝 wmax (mm)", f"{cr['wmax']:.3f}"],
        ["钢筋应力水平 ψ", f"{cr['psi']:.3f}"],
        ["限值", "满足" if cr["ok"] else "不满足"],
    ])

    # 5 挠度
    add_heading_cn(doc, "五、挠度验算", 1)
    if result["deflect"]:
        df = result["deflect"]
        add_table_cn(doc, ["参数", "结果"], [
            ["挠度 f (mm)", f"{df['f']:.1f}"],
            ["短期刚度 Bs (N·mm²)", f"{df['Bs']:.2e}"],
            ["限值", "满足" if df["ok"] else "不满足"],
        ])
    else:
        add_para_cn(doc, "未提供计算跨度，挠度验算略。")

    # 6 结论
    add_heading_cn(doc, "六、配筋率与结论", 1)
    add_para_cn(doc, f"配筋率 ρ = {result['rho']*100:.2f}%（最小 {result['rho_min']*100:.2f}%），"
                     f"{'满足' if result['rho_ok'] else '不满足'}最小配筋率。")
    add_para_cn(doc, "计算结论：" + ("各项满足设计要求。" if result["all_ok"]
                                     else "存在不满足项，需调整截面或材料等级后重算。"))

    doc.save(out_path)
    return out_path
