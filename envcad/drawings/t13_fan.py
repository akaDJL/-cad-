# -*- coding: utf-8 -*-
"""离心风机成套施工图 v1.0 — 提示词驱动 · A/B/C 分级出图。

用法：
    gen_fan(out_dir, level="B", air_flow=50000, pressure=2500)   # B级 6张
    gen_fan(out_dir, level="C", air_flow=80000, pressure=3000)   # C级 8张

级别：A外形(2) / B详图(6) / C成套(8)。尺寸由 design_fan_full 算出。
"""
from __future__ import annotations

import os

from ezdxf.enums import TextEntityAlignment

from ..engine.dxf_base import new_drawing, save_dxf
from ..standards.frame import FrameInfo, draw_frame
from ..standards.annotate import _t, draw_flow_arrow
from ..standards.legend import draw_legend
from ..standards.fan import (
    draw_fan_elevation, draw_fan_plan, draw_fan_section,
    draw_fan_flange, draw_fan_base, draw_fan_installation,
)
from ..design.env_process import design_fan_full
from . import draw_tech_notes, draw_spec_table, draw_material_table

MC = TextEntityAlignment.MIDDLE_CENTER
TECH_W = 95.0


def _frame(doc, scale, title, no, project, tracker):
    info = FrameInfo(title=title, drawing_no=no, scale_str=f"1:{int(scale)}",
                     project=project, unit="环保工程",
                     designer="envcad", date="2026.08")
    return draw_frame(doc, scale, info, tracker=tracker)


def gen_fan(out_dir: str, level: str = "B", air_flow: float = 50000.0,
            pressure: float = 2500.0, scale: float = 100.0,
            project: str = "离心风机", **design_kw) -> list:
    os.makedirs(out_dir, exist_ok=True)
    p = design_fan_full(air_flow=air_flow, pressure=pressure, **design_kw)
    lvl = level.upper()
    paths = [_s1_outline(out_dir, scale, p, project), _s2_spec(out_dir, scale, p, project)]
    if lvl in ("B", "C"):
        paths += [_s3_section(out_dir, scale, p, project),
                  _s4_flange(out_dir, scale, p, project),
                  _s5_base(out_dir, scale, p, project),
                  _s6_installation(out_dir, scale, p, project)]
    if lvl == "C":
        paths += [_s7_flow(out_dir, scale, p, project),
                  _s8_material(out_dir, scale, p, project)]
    return paths


def _s1_outline(out_dir, scale, p, project):
    doc, _, tracker = new_drawing(scale, return_tracker=True)
    msp = doc.modelspace()
    x0, y0, x1, y1 = _frame(doc, scale, "离心风机外形总图", "FAN-01", project, tracker)
    s = scale
    draw_fan_elevation(msp, (x0 + 6000, y0 + 6000), p, scale,
                       label="正立面图", tracker=tracker)
    draw_fan_plan(msp, (x0 + 24000, y0 + 6000), p, scale,
                    label="平面图", tracker=tracker)
    draw_legend(msp, (x1 - 150 * s, y1 - 62 * s), scale,
                [("equip", "设备轮廓", "按图"), ("center", "中心线", "—"),
                 ("arrow_flow", "气流方向", "顺工艺"), ("elevation", "标高", "m")],
                tracker=tracker)
    draw_tech_notes(msp, (x0 + 3 * s, y1 - 30 * s), scale, "外形总图技术要求",
                    [f"风量 {p['air_flow']:.0f} m³/h，全压 {p['pressure']:.0f} Pa。",
                     f"轴功率 {p['N_shaft']}kW，配电机 {p['N_rated']}kW。",
                     f"进出口 Φ{p['inlet_dn']:.0f}mm，外形 {p['L']:.0f}×{p['W']:.0f}mm。",
                     "风机配进出口软接、减振器、防护罩。",
                     "安装执行 GB 50275—2010。"],
                    width=TECH_W, tracker=tracker)
    return save_dxf(doc, os.path.join(out_dir, "FAN-01_外形总图.dxf"))


def _s2_spec(out_dir, scale, p, project):
    doc, _, tracker = new_drawing(scale, return_tracker=True)
    msp = doc.modelspace()
    x0, y0, x1, y1 = _frame(doc, scale, "技术特性表", "FAN-02", project, tracker)
    s = scale
    rows = [
        ("风量", f"{p['air_flow']:.0f}", "m³/h"),
        ("全压", f"{p['pressure']:.0f}", "Pa"),
        ("全压效率", f"{p['eff']*100:.0f}", "%"),
        ("轴功率", f"{p['N_shaft']}", "kW"),
        ("电机功率", f"{p['N_rated']}", "kW"),
        ("进口直径", f"Φ{p['inlet_dn']:.0f}", "mm"),
        ("出口直径", f"Φ{p['outlet_dn']:.0f}", "mm"),
        ("外形长度", f"{p['L']:.0f}", "mm"),
        ("外形宽度", f"{p['W']:.0f}", "mm"),
        ("外形高度", f"{p['H']:.0f}", "mm"),
    ]
    draw_spec_table(msp, (x0 + 30000, y1 - 8000), scale,
                    "离心风机技术特性表", rows, tracker)
    draw_tech_notes(msp, (x0 + 3 * s, y1 - 30 * s), scale, "说明",
                    [f"电机功率按轴功率×安全系数选定（{p['N_rated']}kW）。",
                     "风机叶轮经动平衡校正（G6.3级）。",
                     "含尘废气选用耐磨叶轮。"],
                    width=TECH_W, tracker=tracker)
    return save_dxf(doc, os.path.join(out_dir, "FAN-02_技术特性表.dxf"))


def _s3_section(out_dir, scale, p, project):
    doc, _, tracker = new_drawing(scale, return_tracker=True)
    msp = doc.modelspace()
    x0, y0, x1, y1 = _frame(doc, scale, "离心风机纵剖面图", "FAN-03", project, tracker)
    s = scale
    draw_fan_section(msp, (x0 + 6000, y0 + 8000), p, scale,
                     label="1-1 剖面图", tracker=tracker)
    draw_tech_notes(msp, (x0 + 3 * s, y1 - 30 * s), scale, "剖面技术要求",
                    ["蜗壳钢板焊接，内壁耐磨处理。",
                     "叶轮后倾式，效率高噪声低。",
                     "轴承座配润滑与测温，联轴器传动。"],
                    width=TECH_W, tracker=tracker)
    return save_dxf(doc, os.path.join(out_dir, "FAN-03_纵剖面图.dxf"))


def _s4_flange(out_dir, scale, p, project):
    doc, _, tracker = new_drawing(scale, return_tracker=True)
    msp = doc.modelspace()
    x0, y0, x1, y1 = _frame(doc, scale, "进出口法兰详图", "FAN-04", project, tracker)
    s = scale
    draw_fan_flange(msp, (x0 + 6000, y0 + 12000), p, scale,
                    label="进出口法兰详图", tracker=tracker)
    draw_tech_notes(msp, (x0 + 3 * s, y1 - 30 * s), scale, "法兰技术要求",
                    [f"进口法兰 Φ{p['inlet_dn']:.0f}，螺栓孔均布。",
                     f"出口法兰 {p['outlet_dn']:.0f}×{p['outlet_dn']:.0f}。",
                     "法兰角钢焊接平整，垫料密封。"],
                    width=TECH_W, tracker=tracker)
    return save_dxf(doc, os.path.join(out_dir, "FAN-04_进出口法兰详图.dxf"))


def _s5_base(out_dir, scale, p, project):
    doc, _, tracker = new_drawing(scale, return_tracker=True)
    msp = doc.modelspace()
    x0, y0, x1, y1 = _frame(doc, scale, "减振基础详图", "FAN-05", project, tracker)
    s = scale
    draw_fan_base(msp, (x0 + 8000, y0 + 12000), p, scale,
                  label="减振基础详图", tracker=tracker)
    draw_tech_notes(msp, (x0 + 3 * s, y1 - 30 * s), scale, "减振基础技术要求",
                    ["弹簧减振器×4，额定荷载按风机重量选。",
                     "钢筋混凝土惰性块，质量≥3倍风机。",
                     "减振效率≥90%，隔振良好。"],
                    width=TECH_W, tracker=tracker)
    return save_dxf(doc, os.path.join(out_dir, "FAN-05_减振基础详图.dxf"))


def _s6_installation(out_dir, scale, p, project):
    doc, _, tracker = new_drawing(scale, return_tracker=True)
    msp = doc.modelspace()
    x0, y0, x1, y1 = _frame(doc, scale, "风机安装系统图", "FAN-06", project, tracker)
    s = scale
    draw_fan_installation(msp, (x0 + 4000, y0 + 8000), p, scale,
                          label="风机安装系统图", tracker=tracker)
    draw_tech_notes(msp, (x0 + 3 * s, y1 - 30 * s), scale, "安装技术要求",
                    ["进出口配帆布软接，隔振降噪。",
                     "联轴器配防护罩，安全运行。",
                     "减振器+惰性块，整体安装。"],
                    width=TECH_W, tracker=tracker)
    return save_dxf(doc, os.path.join(out_dir, "FAN-06_安装系统图.dxf"))


def _s7_flow(out_dir, scale, p, project):
    doc, _, tracker = new_drawing(scale, return_tracker=True)
    msp = doc.modelspace()
    x0, y0, x1, y1 = _frame(doc, scale, "废气系统流程图", "FAN-07", project, tracker)
    s = scale
    stages = ["集气罩", "风管", "治理设备", "离心风机", "烟囱"]
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
    draw_tech_notes(msp, (x0 + 3 * s, y1 - 30 * s), scale, "系统流程说明",
                    [f"离心风机提供系统动力，风量 {p['air_flow']:.0f}m³/h。",
                     "风机置于治理设备后（清洁侧），负压运行。",
                     f"全压 {p['pressure']:.0f}Pa，克服系统阻力。"],
                    width=TECH_W, tracker=tracker)
    return save_dxf(doc, os.path.join(out_dir, "FAN-07_工艺流程图.dxf"))


def _s8_material(out_dir, scale, p, project):
    doc, _, tracker = new_drawing(scale, return_tracker=True)
    msp = doc.modelspace()
    x0, y0, x1, y1 = _frame(doc, scale, "设备材料表", "FAN-08", project, tracker)
    rows = [
        ("1", "离心风机", f"Q={p['air_flow']:.0f}m³/h P={p['pressure']:.0f}Pa", "台", "1"),
        ("2", "电机", f"{p['N_rated']}kW 380V 防爆(可选)", "台", "1"),
        ("3", "进口软接", f"Φ{p['inlet_dn']:.0f} 帆布", "个", "1"),
        ("4", "出口软接", f"Φ{p['outlet_dn']:.0f} 帆布", "个", "1"),
        ("5", "弹簧减振器", "额定荷载按风机", "个", "4"),
        ("6", "联轴器防护罩", "钢板网罩", "个", "1"),
        ("7", "钢底座", f"{p['L']:.0f}×{p['W']:.0f} 槽钢", "个", "1"),
        ("8", "混凝土基础", "惰性块 C30", "m³", "2"),
        ("9", "轴承座", "配油杯+测温", "个", "2"),
        ("10", "地脚螺栓", "M20", "套", "8"),
    ]
    draw_material_table(msp, (x0 + 8000, y1 - 8000), scale, rows, tracker)
    _t(msp, "设备材料表", (x0 + (x1 - x0) / 2, y0 + 5000), 5 * scale,
       align=MC, layer="文字-标题", tracker=tracker)
    return save_dxf(doc, os.path.join(out_dir, "FAN-08_设备材料表.dxf"))
