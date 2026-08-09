# -*- coding: utf-8 -*-
"""《地基与基础设计说明》DOCX 自动生成（土木，数据来自知识层）。

用法：
  from envcad.docgen.geotech_doc import generate_geotech_spec
  generate_geotech_spec("基础说明.docx", project="阳泉某厂房",
                        footing=footing_result, retaining=retaining_result)
"""
from __future__ import annotations

from ..knowledge import civil
from . import new_cn_doc, add_heading_cn, add_para_cn, add_table_cn


def generate_geotech_spec(out_path: str, project: str = "XX 工程",
                          footing: dict = None, retaining: dict = None,
                          bearing_layer: str = "粉质粘土") -> str:
    """生成地基与基础设计说明。footing/retaining 为 design.foundation 结果。"""
    doc = new_cn_doc(f"{project} 地基与基础设计说明")

    # 1 工程概况
    add_heading_cn(doc, "一、工程概况", 1)
    add_para_cn(doc, f"工程名称：{project}")
    add_para_cn(doc, f"基础持力层：{bearing_layer}。基础形式按上部结构与地质条件确定，"
                     "本说明含天然地基独立基础与重力式挡土墙设计要点。")

    # 2 设计依据
    add_heading_cn(doc, "二、设计依据", 1)
    add_para_cn(doc, "本工程岩土与基础设计遵照下列现行标准、规范：")
    rows = [[no, name] for no, name in civil.civil_code_list()]
    add_table_cn(doc, ["规范编号", "名称"], rows)

    # 3 岩土参数
    add_heading_cn(doc, "三、主要岩土参数", 1)
    add_para_cn(doc, "各土层物理力学指标（常用代表值，以勘察报告为准）：")
    rows = []
    for name, p in civil.SOIL.items():
        rows.append([name, p["gamma"], p["phi"], p["c"], p["fak"],
                     p["Es"] if p["Es"] is not None else "—"])
    add_table_cn(doc, ["土层", "重度γ(kN/m³)", "内摩擦角φ(°)",
                       "粘聚力c(kPa)", "承载力fak(kPa)", "压缩模量Es(MPa)"], rows)

    # 4 地基承载力修正
    add_heading_cn(doc, "四、地基承载力修正", 1)
    add_para_cn(doc, "承载力特征值按 GB 50007 式 5.2.4 作深宽修正："
                     "fa = fak + ηb·γ·(b-3) + ηd·γm·(d-0.5)。")
    rows = [[k, v["eta_b"], v["eta_d"]] for k, v in civil.BEARING_CORRECTION.items()]
    add_table_cn(doc, ["土类", "宽度修正系数ηb", "深度修正系数ηd"], rows)

    # 5 独立基础设计
    if footing:
        add_heading_cn(doc, "五、柱下独立基础设计", 1)
        add_para_cn(doc, f"持力层 {footing['soil']}，fak={footing['fak']} kPa，"
                         f"深宽修正后 fa={footing['fa']} kPa。")
        add_para_cn(doc, f"上部竖向力标准值 Fk={footing['Fk']} kN，基础埋深 d={footing['d']} m。")
        add_para_cn(doc, f"所需底面积 {footing['A_req']} m²，取底板 "
                         f"{footing['dims'][0]}×{footing['dims'][1]} m。")
        add_para_cn(doc, f"基底平均反力 pk={footing['pk']} kPa "
                         f"{'≤' if footing['ok'] else '>'} fa={footing['fa']} kPa，"
                         f"{'满足要求' if footing['ok'] else '不满足，需加大底板'}。")

    # 6 挡土墙设计
    if retaining:
        add_heading_cn(doc, "六、重力式挡土墙稳定验算", 1)
        add_para_cn(doc, f"墙高 H={retaining['H']} m，墙背填土 {retaining['soil']}，"
                         f"主动土压力系数 Ka={retaining['Ka']}。")
        add_para_cn(doc, f"底宽 {retaining['b_bottom']} m，顶宽 {retaining['b_top']} m；"
                         f"主动土压力合力 Ea={retaining['Ea']} kN/m，墙重 W={retaining['W']} kN/m。")
        rows = [
            ["抗滑稳定 Ks", retaining["Ks"], "≥1.3", "满足" if retaining["Ks_ok"] else "不足"],
            ["抗倾覆 K0", retaining["K0"], "≥1.6", "满足" if retaining["K0_ok"] else "不足"],
        ]
        add_table_cn(doc, ["验算项", "计算值", "规范限值", "结论"], rows)

    # 7 施工与构造要求
    add_heading_cn(doc, "七、施工与构造要求", 1)
    add_para_cn(doc, "1）基坑开挖至设计标高后应会同勘察、监理验槽，严禁扰动持力层；"
                     "2）基础混凝土强度等级不低于 C30，垫层 C15 厚 100 mm；"
                     "3）挡土墙应设置泄水孔与反滤层，墙后回填分层夯实；"
                     "4）软弱下卧层应按规范验算，必要时进行地基处理。")

    doc.save(out_path)
    return out_path
