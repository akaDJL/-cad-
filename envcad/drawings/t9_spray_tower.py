# -*- coding: utf-8 -*-
"""湿法脱硫塔成套施工图 v1.0 — 提示词驱动 · A/B/C 分级出图。

用法：
    gen_spray_tower(out_dir, level="B", air_flow=50000, so2_in=2000)   # B级 6张
    gen_spray_tower(out_dir, level="C", air_flow=100000, so2_in=3000)  # C级 8张

级别：A外形(2) / B详图(6) / C成套(8)。尺寸由 design_spray_tower_full 算出。
"""
from __future__ import annotations

import os

from ezdxf.enums import TextEntityAlignment

from ..engine.dxf_base import new_drawing, save_dxf
from ..standards.frame import FrameInfo, draw_frame
from ..standards.annotate import _t, draw_flow_arrow
from ..standards.legend import draw_legend
from ..standards.spray_tower import (
    draw_spray_tower_elevation, draw_spray_tower_plan, draw_spray_tower_section,
    draw_spray_tower_spray_layer, draw_spray_tower_demister,
    draw_spray_tower_slurry_system,
)
from ..design.env_process import design_spray_tower_full
from . import draw_tech_notes, draw_spec_table, draw_material_table

MC = TextEntityAlignment.MIDDLE_CENTER
TECH_W = 95.0


def _frame(doc, scale, title, no, project, tracker):
    info = FrameInfo(title=title, drawing_no=no, scale_str=f"1:{int(scale)}",
                     project=project, unit="环保工程",
                     designer="envcad", date="2026.08")
    return draw_frame(doc, scale, info, tracker=tracker)


def gen_spray_tower(out_dir: str, level: str = "B", air_flow: float = 50000.0,
                    so2_in: float = 2000.0, scale: float = 100.0,
                    project: str = "湿法脱硫塔", **design_kw) -> list:
    os.makedirs(out_dir, exist_ok=True)
    p = design_spray_tower_full(air_flow=air_flow, so2_in=so2_in, **design_kw)
    lvl = level.upper()
    paths = [_s1_outline(out_dir, scale, p, project), _s2_spec(out_dir, scale, p, project)]
    if lvl in ("B", "C"):
        paths += [_s3_section(out_dir, scale, p, project),
                  _s4_spray_layer(out_dir, scale, p, project),
                  _s5_demister(out_dir, scale, p, project),
                  _s6_slurry(out_dir, scale, p, project)]
    if lvl == "C":
        paths += [_s7_flow(out_dir, scale, p, project),
                  _s8_material(out_dir, scale, p, project)]
    return paths


def _s1_outline(out_dir, scale, p, project):
    doc, _, tracker = new_drawing(scale, return_tracker=True)
    msp = doc.modelspace()
    x0, y0, x1, y1 = _frame(doc, scale, "脱硫塔外形总图", "ST-01", project, tracker)
    s = scale
    draw_spray_tower_elevation(msp, (x0 + 12000, y0 + 4000), p, scale,
                               label="正立面图", tracker=tracker)
    draw_spray_tower_plan(msp, (x0 + 32000, y0 + 12000), p, scale,
                          label="平面图", tracker=tracker)
    draw_legend(msp, (x1 - 150 * s, y1 - 62 * s), scale,
                [("equip", "设备轮廓", "按图"), ("center", "中心线", "—"),
                 ("arrow_flow", "气流方向", "顺工艺"), ("elevation", "标高", "m")],
                tracker=tracker)
    draw_tech_notes(msp, (x0 + 3 * s, y1 - 30 * s), scale, "外形总图技术要求",
                    [f"烟气量 {p['air_flow']:.0f} m³/h，SO2 {p['so2_in']:.0f}→{p['so2_out']}mg/m³。",
                     f"塔径 Φ{p['D']}m，浆池 Φ{p['D_pool']}m，总高 {p['H_total']/1000:.1f}m。",
                     f"脱硫效率 {p['eff']*100:.1f}%，液气比 {p['lg']} L/m³。",
                     "塔体碳钢内衬玻璃鳞片防腐，喷淋层 FRP。",
                     "设计执行 HJ 2001—2018，验收 GB 16297。"],
                    width=TECH_W, tracker=tracker)
    return save_dxf(doc, os.path.join(out_dir, "ST-01_外形总图.dxf"))


def _s2_spec(out_dir, scale, p, project):
    doc, _, tracker = new_drawing(scale, return_tracker=True)
    msp = doc.modelspace()
    x0, y0, x1, y1 = _frame(doc, scale, "技术特性表", "ST-02", project, tracker)
    s = scale
    rows = [
        ("烟气量", f"{p['air_flow']:.0f}", "m³/h"),
        ("入口SO2", f"{p['so2_in']:.0f}", "mg/m³"),
        ("出口SO2", f"{p['so2_out']}", "mg/m³"),
        ("脱硫效率", f"{p['eff']*100:.1f}", "%"),
        ("塔径", f"Φ{p['D']}", "m"),
        ("浆池直径", f"Φ{p['D_pool']}", "m"),
        ("空塔气速", f"{p['v_tower']}", "m/s"),
        ("液气比", f"{p['lg']}", "L/m³"),
        ("喷淋层", f"{p['n_spray']}", "层"),
        ("循环液量", f"{p['Q_L']}", "m³/h"),
        ("浆池容积", f"{p['V_pool']}", "m³"),
        ("塔总高", f"{p['H_total']/1000:.1f}", "m"),
        ("循环泵", f"{p['n_pump']}", "台"),
    ]
    draw_spec_table(msp, (x0 + 30000, y1 - 8000), scale,
                    "湿法脱硫塔技术特性表", rows, tracker)
    draw_tech_notes(msp, (x0 + 3 * s, y1 - 30 * s), scale, "说明",
                    [f"出口 SO2 {p['so2_out']} mg/m³ {'≤' if p['ok'] else '>'} "
                     f"限值 {p['limit']}，{'达标' if p['ok'] else '需提效'}。",
                     "喷淋浆液为石灰石浆，钙硫比 1.02~1.08。",
                     "副产物石膏经脱水外运综合利用。"],
                    width=TECH_W, tracker=tracker)
    return save_dxf(doc, os.path.join(out_dir, "ST-02_技术特性表.dxf"))


def _s3_section(out_dir, scale, p, project):
    doc, _, tracker = new_drawing(scale, return_tracker=True)
    msp = doc.modelspace()
    x0, y0, x1, y1 = _frame(doc, scale, "脱硫塔纵剖面图", "ST-03", project, tracker)
    s = scale
    draw_spray_tower_section(msp, (x0 + 16000, y0 + 5000), p, scale,
                             label="1-1 剖面图", tracker=tracker)
    draw_tech_notes(msp, (x0 + 3 * s, y1 - 30 * s), scale, "剖面技术要求",
                    [f"浆池高 {p['H_pool']:.0f}mm，浆池容积 {p['V_pool']}m³。",
                     f"喷淋 {p['n_spray']} 层，层间距 {p['layer_gap']:.0f}mm。",
                     "浆池设氧化空气管，亚硫酸钙强制氧化。",
                     "除雾器 2 级，出口雾滴≤75mg/m³。"],
                    width=TECH_W, tracker=tracker)
    return save_dxf(doc, os.path.join(out_dir, "ST-03_纵剖面图.dxf"))


def _s4_spray_layer(out_dir, scale, p, project):
    doc, _, tracker = new_drawing(scale, return_tracker=True)
    msp = doc.modelspace()
    x0, y0, x1, y1 = _frame(doc, scale, "喷淋层布置图", "ST-04", project, tracker)
    s = scale
    draw_spray_tower_spray_layer(msp, (x0 + 22000, y0 + 15000), p, scale,
                                 label="喷淋层布置图", tracker=tracker)
    draw_tech_notes(msp, (x0 + 3 * s, y1 - 30 * s), scale, "喷淋层技术要求",
                    [f"喷淋母管+支管 FRP，喷嘴碳化硅螺旋实心锥。",
                     f"喷嘴覆盖率≥200%，雾化粒径 1500~2500μm。",
                     f"每喷淋层配一台循环泵（{p['pump_q']:.0f}m³/h）。",
                     "喷淋层可拆卸，便于检修更换喷嘴。"],
                    width=TECH_W, tracker=tracker)
    return save_dxf(doc, os.path.join(out_dir, "ST-04_喷淋层布置图.dxf"))


def _s5_demister(out_dir, scale, p, project):
    doc, _, tracker = new_drawing(scale, return_tracker=True)
    msp = doc.modelspace()
    x0, y0, x1, y1 = _frame(doc, scale, "除雾器详图", "ST-05", project, tracker)
    s = scale
    draw_spray_tower_demister(msp, (x0 + 8000, y0 + 12000), p, scale,
                              label="除雾器详图", tracker=tracker)
    draw_tech_notes(msp, (x0 + 3 * s, y1 - 30 * s), scale, "除雾器技术要求",
                    ["屋脊式折流板，PP 材质，2 级串联。",
                     "级间设在线冲洗水管，定时冲洗防结垢。",
                     "出口雾滴浓度≤75mg/m³。",
                     "折流板间距按气流分布均匀设计。"],
                    width=TECH_W, tracker=tracker)
    return save_dxf(doc, os.path.join(out_dir, "ST-05_除雾器详图.dxf"))


def _s6_slurry(out_dir, scale, p, project):
    doc, _, tracker = new_drawing(scale, return_tracker=True)
    msp = doc.modelspace()
    x0, y0, x1, y1 = _frame(doc, scale, "浆池及循环系统图", "ST-06", project, tracker)
    s = scale
    draw_spray_tower_slurry_system(msp, (x0 + 8000, y0 + 12000), p, scale,
                                   label="浆池及循环系统图", tracker=tracker)
    draw_tech_notes(msp, (x0 + 3 * s, y1 - 30 * s), scale, "浆池技术要求",
                    [f"浆池 Φ{p['D_pool']}m，容积 {p['V_pool']}m³。",
                     "侧进式搅拌器防沉降，氧化空气强制氧化。",
                     f"循环泵 {p['n_pump']} 台，单台 {p['pump_q']:.0f}m³/h。",
                     "石膏浆液排出至真空皮带脱水机。"],
                    width=TECH_W, tracker=tracker)
    return save_dxf(doc, os.path.join(out_dir, "ST-06_浆池及循环系统图.dxf"))


def _s7_flow(out_dir, scale, p, project):
    doc, _, tracker = new_drawing(scale, return_tracker=True)
    msp = doc.modelspace()
    x0, y0, x1, y1 = _frame(doc, scale, "脱硫工艺流程图", "ST-07", project, tracker)
    s = scale
    stages = ["锅炉烟气", "除尘器", "脱硫塔", "除雾器", "烟囱排放"]
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
    _t(msp, f"石灰石浆液制备 → 浆池循环  |  石膏脱水外运",
       (bx + 2 * (bw + gap) + bw / 2, by + bh_ + 5 * s), 2.5 * s, align=MC,
       layer="文字", tracker=tracker)
    draw_tech_notes(msp, (x0 + 3 * s, y1 - 30 * s), scale, "工艺流程说明",
                    [f"烟气经除尘后入脱硫塔，SO2 {p['so2_in']:.0f}→{p['so2_out']}mg/m³。",
                     "石灰石浆液喷淋吸收，生成石膏（CaSO4·2H2O）。",
                     "净化烟气经除雾器后由烟囱排放。",
                     "脱硫效率≥95%，副产石膏综合利用。"],
                    width=TECH_W, tracker=tracker)
    return save_dxf(doc, os.path.join(out_dir, "ST-07_工艺流程图.dxf"))


def _s8_material(out_dir, scale, p, project):
    doc, _, tracker = new_drawing(scale, return_tracker=True)
    msp = doc.modelspace()
    x0, y0, x1, y1 = _frame(doc, scale, "设备材料表", "ST-08", project, tracker)
    rows = [
        ("1", "脱硫塔塔体", f"Φ{p['D']}×{p['H_total']/1000:.1f}m 碳钢玻璃鳞片", "座", "1"),
        ("2", "喷淋层", f"FRP母管+碳化硅喷嘴 ×{p['n_spray']}", "层", f"{p['n_spray']}"),
        ("3", "除雾器", "屋脊式PP 2级 带冲洗", "套", "1"),
        ("4", "浆液循环泵", f"{p['pump_q']:.0f}m³/h 耐磨", "台", f"{p['n_pump']}"),
        ("5", "氧化风机", "罗茨式 强制氧化", "台", "2"),
        ("6", "侧进搅拌器", "N=5.5kW 耐磨", "台", "3"),
        ("7", "石膏排出泵", "耐磨渣浆泵", "台", "2"),
        ("8", "石灰石浆液制备", "球磨/搅拌制浆", "套", "1"),
        ("9", "真空皮带脱水机", "石膏脱水", "台", "1"),
        ("10", "进口烟道", f"{p['inlet_dn']:.0f}×{p['inlet_dn']:.0f} 碳钢防腐", "m", "12"),
        ("11", "挡板门", "电动密封", "个", "2"),
        ("12", "控制柜", "PLC pH/密度/液位联锁", "台", "1"),
    ]
    draw_material_table(msp, (x0 + 8000, y1 - 8000), scale, rows, tracker)
    _t(msp, "设备材料表", (x0 + (x1 - x0) / 2, y0 + 5000), 5 * scale,
       align=MC, layer="文字-标题", tracker=tracker)
    return save_dxf(doc, os.path.join(out_dir, "ST-08_设备材料表.dxf"))
