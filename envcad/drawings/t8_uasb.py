# -*- coding: utf-8 -*-
"""UASB 厌氧反应器成套施工图 v1.0 — 提示词驱动 · A/B/C 分级出图。

用法（提示词 → 参数 → 出图）：
    gen_uasb(out_dir, level="B", Q=500, cod_in=3000)          # B级 6张
    gen_uasb(out_dir, level="A", Q=200)                        # A级 2张
    gen_uasb(out_dir, level="C", Q=1000, cod_in=8000, Nv=10)   # C级 8张

级别定义：
    A级（2张）：外形总图(正立面+平面) / 技术特性表
    B级（6张）：A级 + 纵剖面 / 三相分离器 / 布水系统 / 出水堰及排泥
    C级（8张）：B级 + 工艺流程 / 设备材料表

所有尺寸由 design_uasb_full(Q, cod_in, ...) 从输入条件算出，
提示词给什么条件出什么图，缺省取工程默认值（可覆盖）。
"""
from __future__ import annotations

import os

from ezdxf.enums import TextEntityAlignment

from ..engine.dxf_base import new_drawing, save_dxf
from ..standards.frame import FrameInfo, draw_frame, save_dxf_autofit
from ..standards.annotate import _t, draw_flow_arrow
from ..standards.legend import draw_legend
from ..standards.uasb import (
    draw_uasb_elevation, draw_uasb_plan, draw_uasb_section,
    draw_uasb_three_phase, draw_uasb_distributor, draw_uasb_outlet_weir,
)
from ..design.env_process import design_uasb_full
from . import draw_tech_notes, draw_spec_table, draw_material_table

MC = TextEntityAlignment.MIDDLE_CENTER
TECH_W = 95.0


def _frame(doc, scale, title, no, project, tracker):
    info = FrameInfo(title=title, drawing_no=no, scale_str=f"1:{int(scale)}",
                     project=project, unit="环保工程",
                     designer="envcad", date="2026.08")
    x0, y0, x1, y1 = draw_frame(doc, scale, info, tracker=tracker)
    return x0, y0, x1, y1, info


def gen_uasb(out_dir: str, level: str = "B", Q: float = 500.0,
             cod_in: float = 3000.0, scale: float = 100.0,
             project: str = "UASB厌氧反应器", **design_kw) -> list:
    """成套出图主入口。level=A/B/C；Q/cod_in 等输入条件由提示词给定。"""
    os.makedirs(out_dir, exist_ok=True)
    p = design_uasb_full(Q=Q, cod_in=cod_in, **design_kw)
    lvl = level.upper()
    paths = []
    paths.append(_s1_outline(out_dir, scale, p, project))     # A-01
    paths.append(_s2_spec(out_dir, scale, p, project))        # A-02
    if lvl in ("B", "C"):
        paths.append(_s3_section(out_dir, scale, p, project))     # B-03
        paths.append(_s4_three_phase(out_dir, scale, p, project))  # B-04
        paths.append(_s5_distributor(out_dir, scale, p, project))  # B-05
        paths.append(_s6_outlet_weir(out_dir, scale, p, project))  # B-06
    if lvl == "C":
        paths.append(_s7_flow(out_dir, scale, p, project))      # C-07
        paths.append(_s8_material(out_dir, scale, p, project))  # C-08
    return paths


# ═══ A-01 外形总图 ═══
def _s1_outline(out_dir, scale, p, project):
    doc, _, tracker = new_drawing(scale, return_tracker=True)
    msp = doc.modelspace()
    x0, y0, x1, y1, info = _frame(doc, scale, "UASB反应器外形总图", "UASB-01", project, tracker)
    s = scale
    draw_uasb_elevation(msp, (x0 + 14000, y0 + 8000), p, scale,
                        label="正立面图", tracker=tracker)
    draw_uasb_plan(msp, (x0 + 32000, y0 + 15000), p, scale,
                   label="平面图", tracker=tracker)
    draw_legend(msp, (x1 - 150 * s, y1 - 62 * s), scale,
                [("equip", "设备轮廓", "按图"), ("center", "中心线", "—"),
                 ("arrow_flow", "水流方向", "顺工艺"), ("elevation", "标高", "m")],
                tracker=tracker)
    draw_tech_notes(msp, (x0 + 3 * s, y1 - 30 * s), scale, "外形总图技术要求",
                    [f"处理水量 {p['Q']:.0f} m³/d，进水 COD {p['cod_in']:.0f} mg/L。",
                     f"有效容积 {p['V_eff']} m³，HRT {p['HRT']} h。",
                     f"反应器 Φ{p['D']}m，总高 {p['H_total']} m。",
                     "罐体碳钢防腐（环氧煤沥青三油两布），或钢筋混凝土。",
                     "设计执行 HJ 2013—2012，施工验收 GB 50141。"],
                    width=TECH_W, tracker=tracker)
    return save_dxf_autofit(doc, os.path.join(out_dir, "UASB-01_外形总图.dxf"), scale, info, tracker)


# ═══ A-02 技术特性表 ═══
def _s2_spec(out_dir, scale, p, project):
    doc, _, tracker = new_drawing(scale, return_tracker=True)
    msp = doc.modelspace()
    x0, y0, x1, y1, info = _frame(doc, scale, "技术特性表", "UASB-02", project, tracker)
    s = scale
    rows = [
        ("处理水量", f"{p['Q']:.0f}", "m³/d"),
        ("进水COD", f"{p['cod_in']:.0f}", "mg/L"),
        ("COD负荷", f"{p['cod_load']}", "kg/d"),
        ("容积负荷", f"{p['Nv']}", "kgCOD/m³·d"),
        ("有效容积", f"{p['V_eff']}", "m³"),
        ("停留时间", f"{p['HRT']}", "h"),
        ("反应器直径", f"Φ{p['D']}", "m"),
        ("上升流速", f"{p['upflow_v']}", "m/h"),
        ("反应区高", f"{p['H_reactor']}", "m"),
        ("设备总高", f"{p['H_total']}", "m"),
        ("布水点", f"{p['n_dist_points']}", "个"),
        ("堰负荷", f"{p['weir_load']}", "L/s·m"),
        ("沼气产量", f"{p['biogas_yield']}", "m³/d"),
        ("沼气管", f"DN{p['biogas_dn']:.0f}", "mm"),
    ]
    draw_spec_table(msp, (x0 + 30000, y1 - 8000), scale,
                    "UASB反应器技术特性表", rows, tracker)
    draw_tech_notes(msp, (x0 + 3 * s, y1 - 30 * s), scale, "说明",
                    [f"上升流速 {p['upflow_v']} m/h（宜 0.5~1.5），"
                     f"{'合格' if p['v_ok'] else '需调整'}。",
                     f"停留时间 {p['HRT']} h（宜 20~40），"
                     f"{'合格' if p['hrt_ok'] else '按容积负荷设计'}。",
                     "厌氧污泥接种量≥反应器容积的 10%。",
                     "运行温度：中温 30~38℃，pH 6.8~7.5。"],
                    width=TECH_W, tracker=tracker)
    return save_dxf_autofit(doc, os.path.join(out_dir, "UASB-02_技术特性表.dxf"), scale, info, tracker)


# ═══ B-03 纵剖面图 ═══
def _s3_section(out_dir, scale, p, project):
    doc, _, tracker = new_drawing(scale, return_tracker=True)
    msp = doc.modelspace()
    x0, y0, x1, y1, info = _frame(doc, scale, "UASB反应器纵剖面图", "UASB-03", project, tracker)
    s = scale
    draw_uasb_section(msp, (x0 + 18000, y0 + 8000), p, scale,
                      label="1-1 剖面图", tracker=tracker)
    draw_tech_notes(msp, (x0 + 3 * s, y1 - 30 * s), scale, "剖面技术要求",
                    [f"污泥床高 {p['H_sludge']}m，悬浮层高 {p['H_suspend']}m。",
                     f"三相分离器高 {p['H_three_phase']}m，沉淀区高 {p['H_settle']}m。",
                     "污泥床污泥浓度 40~80 gSS/L，颗粒污泥为主。",
                     "罐体设取样口（沿高每 1.5m 一个）及检修人孔。"],
                    width=TECH_W, tracker=tracker)
    return save_dxf_autofit(doc, os.path.join(out_dir, "UASB-03_纵剖面图.dxf"), scale, info, tracker)


# ═══ B-04 三相分离器详图 ═══
def _s4_three_phase(out_dir, scale, p, project):
    doc, _, tracker = new_drawing(scale, return_tracker=True)
    msp = doc.modelspace()
    x0, y0, x1, y1, info = _frame(doc, scale, "三相分离器详图", "UASB-04", project, tracker)
    s = scale
    draw_uasb_three_phase(msp, (x0 + 12000, y0 + 14000), p, scale,
                          label="三相分离器详图", tracker=tracker)
    draw_tech_notes(msp, (x0 + 3 * s, y1 - 30 * s), scale, "三相分离器技术要求",
                    [f"集气罩倾角 {p['ts_angle']:.0f}°（宜 45~60°）。",
                     "集气罩缝隙流速≤2 m/h，防污泥随气带出。",
                     "气、液、固三相有效分离，污泥顺利回流。",
                     "材质 PP 或玻璃钢，耐腐蚀，连接牢固。"],
                    width=TECH_W, tracker=tracker)
    return save_dxf_autofit(doc, os.path.join(out_dir, "UASB-04_三相分离器详图.dxf"), scale, info, tracker)


# ═══ B-05 布水系统图 ═══
def _s5_distributor(out_dir, scale, p, project):
    doc, _, tracker = new_drawing(scale, return_tracker=True)
    msp = doc.modelspace()
    x0, y0, x1, y1, info = _frame(doc, scale, "布水系统图", "UASB-05", project, tracker)
    s = scale
    draw_uasb_distributor(msp, (x0 + 25000, y0 + 16000), p, scale,
                          label="布水系统平面图", tracker=tracker)
    draw_tech_notes(msp, (x0 + 3 * s, y1 - 30 * s), scale, "布水技术要求",
                    [f"布水点 {p['n_dist_points']} 个，每点服务 {p['serve_area']} m²。",
                     "进水分配均匀，避免短流与死区。",
                     "布水管 UPVC，穿孔管或一管多点配水。",
                     "大阻力配水，孔口流速≥2 m/s 防堵。"],
                    width=TECH_W, tracker=tracker)
    return save_dxf_autofit(doc, os.path.join(out_dir, "UASB-05_布水系统图.dxf"), scale, info, tracker)


# ═══ B-06 出水堰及排泥详图 ═══
def _s6_outlet_weir(out_dir, scale, p, project):
    doc, _, tracker = new_drawing(scale, return_tracker=True)
    msp = doc.modelspace()
    x0, y0, x1, y1, info = _frame(doc, scale, "出水堰及排泥详图", "UASB-06", project, tracker)
    s = scale
    draw_uasb_outlet_weir(msp, (x0 + 10000, y0 + 18000), p, scale,
                          label="出水堰及排泥详图", tracker=tracker)
    draw_tech_notes(msp, (x0 + 3 * s, y1 - 30 * s), scale, "出水堰技术要求",
                    [f"三角堰板 90°齿形，堰负荷 {p['weir_load']} L/s·m。",
                     "堰口水平，高差≤2mm，出水均匀。",
                     "堰板 304 不锈钢，可调高低。",
                     "排泥管定期排泥，防污泥过度累积。"],
                    width=TECH_W, tracker=tracker)
    return save_dxf_autofit(doc, os.path.join(out_dir, "UASB-06_出水堰及排泥详图.dxf"), scale, info, tracker)


# ═══ C-07 工艺流程图 ═══
def _s7_flow(out_dir, scale, p, project):
    doc, _, tracker = new_drawing(scale, return_tracker=True)
    msp = doc.modelspace()
    x0, y0, x1, y1, info = _frame(doc, scale, "厌氧处理工艺流程图", "UASB-07", project, tracker)
    s = scale
    stages = ["调节池", "提升泵", "UASB反应器", "后续处理", "达标出水"]
    n = len(stages)
    avail = (x1 - x0) - 12000
    gap = avail * 0.05 / max(1, n - 1)
    bw = (avail - gap * (n - 1)) / n
    bh_ = 6000
    bx = x0 + 6000
    by = y0 + 16000
    for i, st in enumerate(stages):
        cx0 = bx + i * (bw + gap)
        msp.add_lwpolyline([(cx0, by), (cx0 + bw, by), (cx0 + bw, by + bh_),
                            (cx0, by + bh_)], close=True, dxfattribs={"layer": "工艺"})
        _t(msp, st, (cx0 + bw / 2, by + bh_ / 2), 3 * s, align=MC,
           layer="文字", tracker=tracker)
        if i < n - 1:
            draw_flow_arrow(msp, (cx0 + bw, by + bh_ / 2), (gap, 0), scale,
                            length=8.0, label="", tracker=tracker)
    # 沼气支线
    _t(msp, f"沼气 {p['biogas_yield']:.0f} m³/d → 收集利用",
       (bx + 2 * (bw + gap) + bw / 2, by + bh_ + 5 * s), 2.5 * s, align=MC,
       layer="文字", tracker=tracker)
    draw_tech_notes(msp, (x0 + 3 * s, y1 - 30 * s), scale, "工艺流程说明",
                    [f"高浓度有机废水（COD {p['cod_in']:.0f}mg/L）经调节后入UASB。",
                     f"厌氧降解去除率约 85%，COD负荷 {p['cod_load']} kg/d。",
                     "产生沼气收集利用（发电/锅炉），污泥定期排放。",
                     "出水进后续好氧处理，确保达标排放。"],
                    width=TECH_W, tracker=tracker)
    return save_dxf_autofit(doc, os.path.join(out_dir, "UASB-07_工艺流程图.dxf"), scale, info, tracker)


# ═══ C-08 设备材料表 ═══
def _s8_material(out_dir, scale, p, project):
    doc, _, tracker = new_drawing(scale, return_tracker=True)
    msp = doc.modelspace()
    x0, y0, x1, y1, info = _frame(doc, scale, "设备材料表", "UASB-08", project, tracker)
    rows = [
        ("1", "UASB反应器罐体", f"Φ{p['D']}×{p['H_total']}m 碳钢防腐", "座", "1"),
        ("2", "三相分离器", f"PP 倾角{p['ts_angle']:.0f}°", "套", "1"),
        ("3", "布水系统", f"UPVC {p['n_dist_points']}点", "套", "1"),
        ("4", "出水堰板", "304不锈钢三角堰", "m", f"{p['weir_len']:.0f}"),
        ("5", "沼气收集管", f"DN{p['biogas_dn']:.0f} UPVC", "m", "15"),
        ("6", "水封罐", "Φ500 碳钢防腐", "个", "1"),
        ("7", "排泥管", f"DN{p['sludge_dn']:.0f}", "m", "10"),
        ("8", "进水泵", f"Q={p['Q']/24:.0f}m³/h H=15m", "台", "2"),
        ("9", "循环泵", "Q=进水量的100%", "台", "1"),
        ("10", "沼气火炬", f"{p['biogas_yield']:.0f}m³/d 内燃式", "套", "1"),
        ("11", "爬梯平台", "Q235 镀锌", "套", "1"),
        ("12", "控制柜", "PLC pH/温度/液位监测", "台", "1"),
    ]
    draw_material_table(msp, (x0 + 8000, y1 - 8000), scale, rows, tracker)
    _t(msp, "设备材料表", (x0 + (x1 - x0) / 2, y0 + 5000), 5 * scale,
       align=MC, layer="文字-标题", tracker=tracker)
    return save_dxf_autofit(doc, os.path.join(out_dir, "UASB-08_设备材料表.dxf"), scale, info, tracker)
