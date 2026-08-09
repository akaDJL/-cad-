# -*- coding: utf-8 -*-
"""活性炭吸附装置成套施工图 v1.0 — 提示词驱动 · A/B/C 分级出图。

用法：
    gen_activated_carbon(out_dir, level="B", air_flow=10000, voc_in=200)  # B级 6张
    gen_activated_carbon(out_dir, level="C", air_flow=20000, voc_in=300)  # C级 8张

级别：A外形(2) / B详图(6) / C成套(8)。尺寸由 design_activated_carbon_full 算出。
"""
from __future__ import annotations

import os

from ezdxf.enums import TextEntityAlignment

from ..engine.dxf_base import new_drawing, save_dxf
from ..standards.frame import FrameInfo, draw_frame
from ..standards.annotate import _t, draw_flow_arrow
from ..standards.legend import draw_legend
from ..standards.activated_carbon import (
    draw_ac_elevation, draw_ac_plan, draw_ac_section,
    draw_ac_carbon_bed, draw_ac_desorption, draw_ac_piping,
)
from ..design.env_process import design_activated_carbon_full
from . import draw_tech_notes, draw_spec_table, draw_material_table

MC = TextEntityAlignment.MIDDLE_CENTER
TECH_W = 95.0


def _frame(doc, scale, title, no, project, tracker):
    info = FrameInfo(title=title, drawing_no=no, scale_str=f"1:{int(scale)}",
                     project=project, unit="环保工程",
                     designer="envcad", date="2026.08")
    return draw_frame(doc, scale, info, tracker=tracker)


def gen_activated_carbon(out_dir: str, level: str = "B", air_flow: float = 10000.0,
                         voc_in: float = 200.0, scale: float = 100.0,
                         project: str = "活性炭吸附装置", **design_kw) -> list:
    os.makedirs(out_dir, exist_ok=True)
    p = design_activated_carbon_full(air_flow=air_flow, voc_in=voc_in, **design_kw)
    lvl = level.upper()
    paths = [_s1_outline(out_dir, scale, p, project), _s2_spec(out_dir, scale, p, project)]
    if lvl in ("B", "C"):
        paths += [_s3_section(out_dir, scale, p, project),
                  _s4_carbon_bed(out_dir, scale, p, project),
                  _s5_desorption(out_dir, scale, p, project),
                  _s6_piping(out_dir, scale, p, project)]
    if lvl == "C":
        paths += [_s7_flow(out_dir, scale, p, project),
                  _s8_material(out_dir, scale, p, project)]
    return paths


def _s1_outline(out_dir, scale, p, project):
    doc, _, tracker = new_drawing(scale, return_tracker=True)
    msp = doc.modelspace()
    x0, y0, x1, y1 = _frame(doc, scale, "活性炭吸附装置外形总图", "AC-01", project, tracker)
    s = scale
    draw_ac_elevation(msp, (x0 + 14000, y0 + 10000), p, scale,
                      label="正立面图", tracker=tracker)
    draw_ac_plan(msp, (x0 + 32000, y0 + 14000), p, scale,
                   label="平面图", tracker=tracker)
    draw_legend(msp, (x1 - 150 * s, y1 - 62 * s), scale,
                [("equip", "设备轮廓", "按图"), ("center", "中心线", "—"),
                 ("arrow_flow", "气流方向", "顺工艺"), ("elevation", "标高", "m")],
                tracker=tracker)
    draw_tech_notes(msp, (x0 + 3 * s, y1 - 30 * s), scale, "外形总图技术要求",
                    [f"废气量 {p['air_flow']:.0f} m³/h，VOC {p['voc_in']:.0f}→{p['voc_out']}mg/m³。",
                     f"罐径 Φ{p['D']}m，活性炭 {p['carbon_vol']}m³（{p['carbon_wt']:.0f}kg）。",
                     f"去除率 {p['eff']*100:.1f}%，空塔气速 {p['v_bed']} m/s。",
                     "罐体碳钢/不锈钢，内表面防腐。",
                     "设计执行 HJ 2026—2013，验收 GB 16297。"],
                    width=TECH_W, tracker=tracker)
    return save_dxf(doc, os.path.join(out_dir, "AC-01_外形总图.dxf"))


def _s2_spec(out_dir, scale, p, project):
    doc, _, tracker = new_drawing(scale, return_tracker=True)
    msp = doc.modelspace()
    x0, y0, x1, y1 = _frame(doc, scale, "技术特性表", "AC-02", project, tracker)
    s = scale
    rows = [
        ("废气量", f"{p['air_flow']:.0f}", "m³/h"),
        ("入口VOC", f"{p['voc_in']:.0f}", "mg/m³"),
        ("出口VOC", f"{p['voc_out']}", "mg/m³"),
        ("去除率", f"{p['eff']*100:.1f}", "%"),
        ("罐径", f"Φ{p['D']}", "m"),
        ("空塔气速", f"{p['v_bed']}", "m/s"),
        ("活性炭", f"{p['carbon_vol']}", "m³"),
        ("装填量", f"{p['carbon_wt']:.0f}", "kg"),
        ("床层数", f"{p['n_bed']}", "层"),
        ("单床高", f"{p['H_bed']:.0f}", "mm"),
        ("吸附周期", f"{p['cycle_h']:.0f}", "h"),
        ("进气管", f"Φ{p['inlet_dn']:.0f}", "mm"),
        ("出气管", f"Φ{p['outlet_dn']:.0f}", "mm"),
    ]
    draw_spec_table(msp, (x0 + 30000, y1 - 8000), scale,
                    "活性炭吸附装置技术特性表", rows, tracker)
    draw_tech_notes(msp, (x0 + 3 * s, y1 - 30 * s), scale, "说明",
                    [f"出口 VOC {p['voc_out']} mg/m³ {'≤' if p['ok'] else '>'} "
                     f"限值 {p['limit']}，{'达标' if p['ok'] else '需提效'}。",
                     "活性炭选用煤质/椰壳颗粒炭，碘值≥800mg/g。",
                     f"吸附周期约 {p['cycle_h']:.0f}h，饱和后蒸汽再生。"],
                    width=TECH_W, tracker=tracker)
    return save_dxf(doc, os.path.join(out_dir, "AC-02_技术特性表.dxf"))


def _s3_section(out_dir, scale, p, project):
    doc, _, tracker = new_drawing(scale, return_tracker=True)
    msp = doc.modelspace()
    x0, y0, x1, y1 = _frame(doc, scale, "活性炭吸附罐纵剖面图", "AC-03", project, tracker)
    s = scale
    draw_ac_section(msp, (x0 + 16000, y0 + 10000), p, scale,
                    label="1-1 剖面图", tracker=tracker)
    draw_tech_notes(msp, (x0 + 3 * s, y1 - 30 * s), scale, "剖面技术要求",
                    [f"活性炭 {p['carbon_vol']}m³，{p['n_bed']} 床层。",
                     "底部进气分布器，气流均匀通过炭层。",
                     "炭层下设支撑格栅+滤网，防炭粒流失。",
                     "顶部设脱附蒸汽分布管。"],
                    width=TECH_W, tracker=tracker)
    return save_dxf(doc, os.path.join(out_dir, "AC-03_纵剖面图.dxf"))


def _s4_carbon_bed(out_dir, scale, p, project):
    doc, _, tracker = new_drawing(scale, return_tracker=True)
    msp = doc.modelspace()
    x0, y0, x1, y1 = _frame(doc, scale, "活性炭层详图", "AC-04", project, tracker)
    s = scale
    draw_ac_carbon_bed(msp, (x0 + 8000, y0 + 14000), p, scale,
                       label="活性炭层详图", tracker=tracker)
    draw_tech_notes(msp, (x0 + 3 * s, y1 - 30 * s), scale, "炭层技术要求",
                    [f"颗粒活性炭，粒径 4~8 目，床高 {p['H_bed']:.0f}mm。",
                     "支撑格栅+不锈钢滤网，承托炭层。",
                     "顶部压紧格栅，防气流扰动流化。",
                     "装填密实均匀，密度约 500kg/m³。"],
                    width=TECH_W, tracker=tracker)
    return save_dxf(doc, os.path.join(out_dir, "AC-04_炭层详图.dxf"))


def _s5_desorption(out_dir, scale, p, project):
    doc, _, tracker = new_drawing(scale, return_tracker=True)
    msp = doc.modelspace()
    x0, y0, x1, y1 = _frame(doc, scale, "脱附系统图", "AC-05", project, tracker)
    s = scale
    draw_ac_desorption(msp, (x0 + 6000, y0 + 16000), p, scale,
                       label="脱附系统图", avail_w=(x1 - x0) - 12000, tracker=tracker)
    draw_tech_notes(msp, (x0 + 3 * s, y1 - 30 * s), scale, "脱附技术要求",
                    ["饱和活性炭通入蒸汽/热氮气脱附再生。",
                     "脱附气经冷凝器冷凝，溶剂回收利用。",
                     f"脱附周期约 {p['cycle_h']:.0f}h，可在线切换。",
                     "高沸点溶剂宜用热氮气再生。"],
                    width=TECH_W, tracker=tracker)
    return save_dxf(doc, os.path.join(out_dir, "AC-05_脱附系统图.dxf"))


def _s6_piping(out_dir, scale, p, project):
    doc, _, tracker = new_drawing(scale, return_tracker=True)
    msp = doc.modelspace()
    x0, y0, x1, y1 = _frame(doc, scale, "管路系统图", "AC-06", project, tracker)
    s = scale
    draw_ac_piping(msp, (x0 + 4000, y0 + 6000), p, scale,
                   label="管路系统图", tracker=tracker)
    draw_tech_notes(msp, (x0 + 3 * s, y1 - 30 * s), scale, "管路技术要求",
                    [f"进气管 Φ{p['inlet_dn']:.0f}，先经预过滤除颗粒物。",
                     "净化气经风机由排气筒达标排放。",
                     "脱附蒸汽/冷凝水管路单独敷设。",
                     "系统负压运行，阀门气密防泄漏。"],
                    width=TECH_W, tracker=tracker)
    return save_dxf(doc, os.path.join(out_dir, "AC-06_管路系统图.dxf"))


def _s7_flow(out_dir, scale, p, project):
    doc, _, tracker = new_drawing(scale, return_tracker=True)
    msp = doc.modelspace()
    x0, y0, x1, y1 = _frame(doc, scale, "VOC治理工艺流程图", "AC-07", project, tracker)
    s = scale
    stages = ["VOC废气", "预过滤", "活性炭吸附", "风机", "排气筒"]
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
        _t(msp, st, (cx0 + bw / 2, by + bh_ / 2), 3 * s, align=MC, layer="文字", tracker=tracker)
        if i < n - 1:
            draw_flow_arrow(msp, (cx0 + bw, by + bh_ / 2), (gap, 0), scale,
                            length=8.0, label="", tracker=tracker)
    _t(msp, f"饱和炭 → 蒸汽脱附 → 溶剂回收",
       (bx + 2 * (bw + gap) + bw / 2, by + bh_ + 5 * s), 2.5 * s, align=MC,
       layer="文字", tracker=tracker)
    draw_tech_notes(msp, (x0 + 3 * s, y1 - 30 * s), scale, "工艺流程说明",
                    [f"VOC废气预过滤后入活性炭罐吸附，VOC {p['voc_in']:.0f}→{p['voc_out']}mg/m³。",
                     "活性炭吸附饱和后蒸汽脱附再生，循环使用。",
                     "净化气经风机由排气筒达标排放。",
                     f"去除率≥{p['eff']*100:.0f}%，适用于低浓度大风量VOC。"],
                    width=TECH_W, tracker=tracker)
    return save_dxf(doc, os.path.join(out_dir, "AC-07_工艺流程图.dxf"))


def _s8_material(out_dir, scale, p, project):
    doc, _, tracker = new_drawing(scale, return_tracker=True)
    msp = doc.modelspace()
    x0, y0, x1, y1 = _frame(doc, scale, "设备材料表", "AC-08", project, tracker)
    rows = [
        ("1", "活性炭吸附罐", f"Φ{p['D']}×{p['H_total']/1000:.1f}m 碳钢防腐", "台", "1"),
        ("2", "颗粒活性炭", f"碘值≥800 {p['carbon_wt']:.0f}kg", "kg", f"{p['carbon_wt']:.0f}"),
        ("3", "支撑格栅+滤网", "304不锈钢", "套", f"{p['n_bed']}"),
        ("4", "压紧格栅", "304不锈钢", "套", f"{p['n_bed']}"),
        ("5", "预过滤器", "滤棉/滤袋 除颗粒物", "台", "1"),
        ("6", "离心风机", f"Q={p['air_flow']:.0f}m³/h 防爆", "台", "1"),
        ("7", "蒸汽发生器", "脱附用 电/燃气", "套", "1"),
        ("8", "冷凝器", "列管式 循环水冷", "台", "1"),
        ("9", "溶剂回收槽", "不锈钢 带液位", "个", "1"),
        ("10", "进气管道", f"Φ{p['inlet_dn']:.0f} 碳钢", "m", "15"),
        ("11", "排气筒", f"Φ{p['outlet_dn']:.0f} H=15m", "座", "1"),
        ("12", "控制柜", "PLC 温度/压差/VOC监测", "台", "1"),
    ]
    draw_material_table(msp, (x0 + 8000, y1 - 8000), scale, rows, tracker)
    _t(msp, "设备材料表", (x0 + (x1 - x0) / 2, y0 + 5000), 5 * scale,
       align=MC, layer="文字-标题", tracker=tracker)
    return save_dxf(doc, os.path.join(out_dir, "AC-08_设备材料表.dxf"))
