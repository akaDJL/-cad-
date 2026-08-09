# -*- coding: utf-8 -*-
"""钢烟囱成套施工图 v1.0 — 提示词驱动 · A/B/C 分级出图。

用法：
    gen_chimney(out_dir, level="B", air_flow=50000, H=30)   # B级 6张
    gen_chimney(out_dir, level="C", air_flow=80000, H=45)   # C级 8张

级别：A外形(2) / B详图(6) / C成套(8)。尺寸由 design_chimney_full 算出。
高耸结构采用折断画法（底段+顶段，中段省略）。
"""
from __future__ import annotations

import os

from ezdxf.enums import TextEntityAlignment

from ..engine.dxf_base import new_drawing, save_dxf
from ..standards.frame import FrameInfo, draw_frame
from ..standards.annotate import _t, draw_flow_arrow
from ..standards.legend import draw_legend
from ..standards.chimney import (
    draw_chimney_elevation, draw_chimney_plan, draw_chimney_section,
    draw_chimney_sample_port, draw_chimney_platform, draw_chimney_foundation,
)
from ..design.env_process import design_chimney_full
from . import draw_tech_notes, draw_spec_table, draw_material_table

MC = TextEntityAlignment.MIDDLE_CENTER
TECH_W = 95.0


def _frame(doc, scale, title, no, project, tracker):
    info = FrameInfo(title=title, drawing_no=no, scale_str=f"1:{int(scale)}",
                     project=project, unit="环保工程",
                     designer="envcad", date="2026.08")
    return draw_frame(doc, scale, info, tracker=tracker)


def gen_chimney(out_dir: str, level: str = "B", air_flow: float = 50000.0,
                H: float = 30.0, scale: float = 100.0,
                project: str = "钢烟囱", **design_kw) -> list:
    os.makedirs(out_dir, exist_ok=True)
    p = design_chimney_full(air_flow=air_flow, H=H, **design_kw)
    lvl = level.upper()
    paths = [_s1_outline(out_dir, scale, p, project), _s2_spec(out_dir, scale, p, project)]
    if lvl in ("B", "C"):
        paths += [_s3_section(out_dir, scale, p, project),
                  _s4_sample(out_dir, scale, p, project),
                  _s5_platform(out_dir, scale, p, project),
                  _s6_foundation(out_dir, scale, p, project)]
    if lvl == "C":
        paths += [_s7_flow(out_dir, scale, p, project),
                  _s8_material(out_dir, scale, p, project)]
    return paths


def _s1_outline(out_dir, scale, p, project):
    doc, _, tracker = new_drawing(scale, return_tracker=True)
    msp = doc.modelspace()
    x0, y0, x1, y1 = _frame(doc, scale, "钢烟囱外形总图", "CH-01", project, tracker)
    s = scale
    draw_chimney_elevation(msp, (x0 + 8000, y0 + 4000), p, scale,
                           label="正立面图（折断画法）", tracker=tracker)
    draw_chimney_plan(msp, (x0 + 30000, y0 + 12000), p, scale,
                      label="平面图", tracker=tracker)
    draw_legend(msp, (x1 - 150 * s, y1 - 62 * s), scale,
                [("equip", "设备轮廓", "按图"), ("center", "中心线", "—"),
                 ("arrow_flow", "气流方向", "顺工艺"), ("elevation", "标高", "m")],
                tracker=tracker)
    draw_tech_notes(msp, (x0 + 3 * s, y1 - 30 * s), scale, "外形总图技术要求",
                    [f"烟气量 {p['air_flow']:.0f} m³/h，烟囱高 {p['H']}m。",
                     f"出口 Φ{p['D_out']}m，底部 Φ{p['D_base']}m，烟速 {p['v_out']}m/s。",
                     f"筒体 Q235B 钢板，壁厚 {p['wall_t']}mm，内衬防腐。",
                     f"平台 {p['n_platform']} 层，爬梯带护笼，顶部避雷针。",
                     "设计执行 GB 50051—2021，验收 GB 16297。"],
                    width=TECH_W, tracker=tracker)
    return save_dxf(doc, os.path.join(out_dir, "CH-01_外形总图.dxf"))


def _s2_spec(out_dir, scale, p, project):
    doc, _, tracker = new_drawing(scale, return_tracker=True)
    msp = doc.modelspace()
    x0, y0, x1, y1 = _frame(doc, scale, "技术特性表", "CH-02", project, tracker)
    s = scale
    rows = [
        ("烟气量", f"{p['air_flow']:.0f}", "m³/h"),
        ("烟囱高度", f"{p['H']}", "m"),
        ("出口内径", f"Φ{p['D_out']}", "m"),
        ("底部内径", f"Φ{p['D_base']}", "m"),
        ("出口烟速", f"{p['v_out']}", "m/s"),
        ("筒体壁厚", f"{p['wall_t']:.0f}", "mm"),
        ("锥度", f"{p['taper']}", "—"),
        ("平台层数", f"{p['n_platform']}", "层"),
        ("平台间距", f"{p['plat_gap']}", "m"),
        ("采样孔", f"Φ{p['sample_dn']:.0f}", "mm"),
    ]
    draw_spec_table(msp, (x0 + 30000, y1 - 8000), scale,
                    "钢烟囱技术特性表", rows, tracker)
    draw_tech_notes(msp, (x0 + 3 * s, y1 - 30 * s), scale, "说明",
                    ["筒体分段制作现场焊接，焊缝一级探伤。",
                     "外表面爬梯、平台热镀锌防腐。",
                     "航空障碍灯按民航规定设置（H≥45m 时）。"],
                    width=TECH_W, tracker=tracker)
    return save_dxf(doc, os.path.join(out_dir, "CH-02_技术特性表.dxf"))


def _s3_section(out_dir, scale, p, project):
    doc, _, tracker = new_drawing(scale, return_tracker=True)
    msp = doc.modelspace()
    x0, y0, x1, y1 = _frame(doc, scale, "钢烟囱纵剖面图", "CH-03", project, tracker)
    s = scale
    draw_chimney_section(msp, (x0 + 10000, y0 + 4000), p, scale,
                         label="1-1 剖面图（折断画法）", tracker=tracker)
    draw_tech_notes(msp, (x0 + 3 * s, y1 - 30 * s), scale, "剖面技术要求",
                    [f"筒体壁厚 {p['wall_t']}mm，内衬玻璃鳞片防腐。",
                     "锥形筒体，底部加强，环向加劲肋。",
                     "内衬耐酸耐热，适应湿烟气腐蚀。"],
                    width=TECH_W, tracker=tracker)
    return save_dxf(doc, os.path.join(out_dir, "CH-03_纵剖面图.dxf"))


def _s4_sample(out_dir, scale, p, project):
    doc, _, tracker = new_drawing(scale, return_tracker=True)
    msp = doc.modelspace()
    x0, y0, x1, y1 = _frame(doc, scale, "采样孔详图", "CH-04", project, tracker)
    s = scale
    draw_chimney_sample_port(msp, (x0 + 12000, y0 + 10000), p, scale,
                             label="采样孔详图", tracker=tracker)
    draw_tech_notes(msp, (x0 + 3 * s, y1 - 30 * s), scale, "采样孔技术要求",
                    ["采样孔设于直管段，上游≥4D、下游≥2D。",
                     "配采样平台与爬梯，便于 CEMS 监测。",
                     "采样管带截止阀，不用时密封。"],
                    width=TECH_W, tracker=tracker)
    return save_dxf(doc, os.path.join(out_dir, "CH-04_采样孔详图.dxf"))


def _s5_platform(out_dir, scale, p, project):
    doc, _, tracker = new_drawing(scale, return_tracker=True)
    msp = doc.modelspace()
    x0, y0, x1, y1 = _frame(doc, scale, "休息平台详图", "CH-05", project, tracker)
    s = scale
    draw_chimney_platform(msp, (x0 + 8000, y0 + 14000), p, scale,
                          label="休息平台详图", tracker=tracker)
    draw_tech_notes(msp, (x0 + 3 * s, y1 - 30 * s), scale, "平台技术要求",
                    [f"全塔平台 {p['n_platform']} 层，间距 {p['plat_gap']}m。",
                     "钢格栅平台板，防滑排水。",
                     "栏杆高 1050mm，三横杆+踢脚板。",
                     "爬梯带护笼，底部设防坠自锁器。"],
                    width=TECH_W, tracker=tracker)
    return save_dxf(doc, os.path.join(out_dir, "CH-05_休息平台详图.dxf"))


def _s6_foundation(out_dir, scale, p, project):
    doc, _, tracker = new_drawing(scale, return_tracker=True)
    msp = doc.modelspace()
    x0, y0, x1, y1 = _frame(doc, scale, "烟囱基础详图", "CH-06", project, tracker)
    s = scale
    draw_chimney_foundation(msp, (x0 + 8000, y0 + 12000), p, scale,
                            label="烟囱基础详图", tracker=tracker)
    draw_tech_notes(msp, (x0 + 3 * s, y1 - 30 * s), scale, "基础技术要求",
                    [f"环形钢筋混凝土基础 Φ{p['D_base']+2:.1f}m，C30。",
                     "配双层双向钢筋，地脚螺栓预埋。",
                     "基础按风荷载与地震作用验算抗倾覆。"],
                    width=TECH_W, tracker=tracker)
    return save_dxf(doc, os.path.join(out_dir, "CH-06_烟囱基础详图.dxf"))


def _s7_flow(out_dir, scale, p, project):
    doc, _, tracker = new_drawing(scale, return_tracker=True)
    msp = doc.modelspace()
    x0, y0, x1, y1 = _frame(doc, scale, "废气排放系统流程图", "CH-07", project, tracker)
    s = scale
    stages = ["废气", "治理设备", "风机", "钢烟囱", "达标排放"]
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
    draw_tech_notes(msp, (x0 + 3 * s, y1 - 30 * s), scale, "排放系统说明",
                    [f"净化后废气经风机由钢烟囱高空排放。",
                     f"烟囱高 {p['H']}m，出口烟速 {p['v_out']}m/s 防倒灌。",
                     "CEMS 在线监测设于烟囱直管段采样孔。"],
                    width=TECH_W, tracker=tracker)
    return save_dxf(doc, os.path.join(out_dir, "CH-07_工艺流程图.dxf"))


def _s8_material(out_dir, scale, p, project):
    doc, _, tracker = new_drawing(scale, return_tracker=True)
    msp = doc.modelspace()
    x0, y0, x1, y1 = _frame(doc, scale, "设备材料表", "CH-08", project, tracker)
    rows = [
        ("1", "烟囱筒体", f"Φ{p['D_base']}→Φ{p['D_out']}m Q235B δ={p['wall_t']}", "t", "8"),
        ("2", "内衬防腐", "玻璃鳞片 耐酸", "m²", "120"),
        ("3", "爬梯", "热镀锌 带护笼", "m", f"{p['H']:.0f}"),
        ("4", "休息平台", "钢格栅+栏杆", "层", f"{p['n_platform']}"),
        ("5", "采样孔", f"Φ{p['sample_dn']:.0f} 带截止阀", "个", "2"),
        ("6", "避雷针", "Φ20 圆钢 L=1.2m", "根", "1"),
        ("7", "环形基础", f"Φ{p['D_base']+2:.1f}m C30", "m³", "15"),
        ("8", "地脚螺栓", "M30 8.8级", "套", "16"),
        ("9", "环向加劲肋", "角钢 L75", "m", "60"),
        ("10", "航空障碍灯", "LED 中光强", "套", "1"),
    ]
    draw_material_table(msp, (x0 + 8000, y1 - 8000), scale, rows, tracker)
    _t(msp, "设备材料表", (x0 + (x1 - x0) / 2, y0 + 5000), 5 * scale,
       align=MC, layer="文字-标题", tracker=tracker)
    return save_dxf(doc, os.path.join(out_dir, "CH-08_设备材料表.dxf"))
