# -*- coding: utf-8 -*-
"""《结构设计总说明》DOCX 自动生成（数据来自知识层）。

用法：
  from envcad.docgen.spec_doc import generate_structure_spec
  generate_structure_spec("说明.docx", project="阳泉某车间", structure_type="框架结构")
"""
from __future__ import annotations

from ..knowledge import materials, codes, theory, user_data
from . import new_cn_doc, add_heading_cn, add_para_cn, add_table_cn


def generate_structure_spec(out_path: str, project: str = "XX 工程",
                             structure_type: str = "钢筋混凝土框架结构",
                             seismic_grade: str = "三级",
                             seismic_degree: str = "7 (0.10g)",
                             note: str = "") -> str:
    doc = new_cn_doc(f"{project} 结构设计总说明")

    # 1 工程概况
    add_heading_cn(doc, "一、工程概况", 1)
    add_para_cn(doc, f"工程名称：{project}")
    add_para_cn(doc, f"结构体系：{structure_type}")
    add_para_cn(doc, f"抗震设防：{seismic_degree}，框架抗震等级 {seismic_grade}")
    if note:
        add_para_cn(doc, f"补充说明：{note}")

    # 2 设计依据
    add_heading_cn(doc, "二、设计依据", 1)
    add_para_cn(doc, "本工程遵照下列现行国家标准、规范（节选，详勘与专项按最新版执行）：")
    rows = [[no, name] for no, name in codes.code_list()]
    add_table_cn(doc, ["规范编号", "名称"], rows)

    # 3 材料
    add_heading_cn(doc, "三、主要材料", 1)
    add_heading_cn(doc, "3.1 混凝土", 2)
    rows = [[g, f"{p['fc']}", f"{p['ft']}", f"{p['Ec']}"] for g, p in materials.CONCRETE.items()]
    add_table_cn(doc, ["强度等级", "fc(N/mm²)", "ft(N/mm²)", "Ec(×10⁴N/mm²)"], rows)
    add_para_cn(doc, "注：梁板柱混凝土强度等级按结构部位另行注明，基础混凝土不低于 C30。")

    add_heading_cn(doc, "3.2 钢筋", 2)
    rows = [[g, f"{p['fy']}", f"{p['fyk']}", p["rtype"]] for g, p in materials.REBAR_GRADE.items()]
    add_table_cn(doc, ["牌号", "fy(N/mm²)", "fyk(N/mm²)", "类型"], rows)

    add_heading_cn(doc, "3.3 钢材", 2)
    rows = [[g, f"{p['f']}", f"{p['fy']}", f"{p['fu']}"] for g, p in materials.STEEL.items()]
    add_table_cn(doc, ["牌号", "f(N/mm²)", "fy(N/mm²)", "fu(N/mm²)"], rows)

    # 4 主要结构参数
    add_heading_cn(doc, "四、主要结构参数", 1)
    add_para_cn(doc, f"混凝土保护层最小厚度（一类环境）：板墙 {codes.cover_min('板墙')} mm，"
                     f"梁柱 {codes.cover_min('梁柱')} mm，基础 {codes.cover_min('基础')} mm。")
    add_para_cn(doc, "楼面活荷载标准值（kN/m²，常用）："
                     + "、".join(f"{k} {v}" for k, v in
                                codes.GB_CODES['GB 50009-2012']['params']['楼面活荷载'].items()
                                if isinstance(v, (int, float))))
    add_para_cn(doc, "荷载分项系数：永久荷载 γG=1.3，可变荷载 γQ=1.5。")

    # 5 构造要求
    add_heading_cn(doc, "五、构造要求", 1)
    add_para_cn(doc, "最小配筋率 ρmin = max(0.20%, 45ft/fy%)，防止少筋脆断。")
    add_para_cn(doc, "钢筋锚固长度 la = α·(fy/ft)·d，抗震锚固 laE = ζaE·la；"
                     "绑扎搭接长度按规范 8.4 节取值。")
    add_para_cn(doc, "裂缝控制：一般环境梁板按三级（允许开裂但限值 0.30 mm）控制；"
                     "对耐久性要求高者提高等级。")

    # 6 设计理论要点
    add_heading_cn(doc, "六、设计理论要点", 1)
    groups = {}
    for cat, name, desc in theory.all_principles():
        groups.setdefault(cat, []).append((name, desc))
    for cat, items in groups.items():
        add_heading_cn(doc, f"6.{list(groups).index(cat)+1} {cat}", 2)
        for name, desc in items:
            add_para_cn(doc, f"· {name}：{desc}")

    # 7 施工要求
    add_heading_cn(doc, "七、施工要求", 1)
    add_para_cn(doc, "1）混凝土浇筑应连续，振捣密实，按规定留置试块；"
                     "2）钢筋代换须征得设计同意，等强等面积换算；"
                     "3）模板拆除以混凝土强度为准；4）未尽事宜按现行施工验收规范执行。")

    # 8 用户订阅数据
    keys = user_data.list_user_keys()
    if keys:
        add_heading_cn(doc, "八、补充数据（用户订阅/自有）", 1)
        add_para_cn(doc, "本说明已并入以下用户数据：" + "、".join(keys))

    doc.save(out_path)
    return out_path
