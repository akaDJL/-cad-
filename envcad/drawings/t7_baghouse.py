# -*- coding: utf-8 -*-
"""袋式除尘器成套施工图 v1.0 — 提示词驱动 · A/B/C 分级出图。

用法（提示词 → 参数 → 出图）：
    gen_baghouse(out_dir, level="B", air_flow=20000)         # B级 6张
    gen_baghouse(out_dir, level="A", air_flow=10000)         # A级 2张
    gen_baghouse(out_dir, level="C", air_flow=50000, bag_len_mm=4000)  # C级 8张

级别定义：
    A级（2张）：外形总图(正立面+平面) / 技术特性表
    B级（6张）：A级 + 纵剖面 / 花板布置 / 喷吹系统 / 灰斗及卸料
    C级（8张）：B级 + 系统工艺流程 / 设备材料表

所有尺寸由 design_baghouse_full(air_flow, ...) 从输入条件算出，
提示词给什么条件出什么图，缺省条件取工程默认值（可覆盖）。
"""
from __future__ import annotations

import os

from ezdxf.enums import TextEntityAlignment

from ..engine.dxf_base import new_drawing, save_dxf
from ..standards.frame import FrameInfo, draw_frame
from ..standards.annotate import _t, draw_flow_arrow
from ..standards.legend import draw_legend
from ..standards.baghouse import (
    draw_baghouse_elevation, draw_baghouse_plan, draw_baghouse_section,
    draw_baghouse_tube_sheet, draw_baghouse_pulse, draw_baghouse_hopper,
)
from ..design.env_process import design_baghouse_full
from . import draw_tech_notes, draw_spec_table, draw_material_table

MC = TextEntityAlignment.MIDDLE_CENTER
TECH_W = 95.0     # 技术要求框宽(图纸mm)


def _frame(doc, scale, title, no, project, tracker):
    info = FrameInfo(title=title, drawing_no=no, scale_str=f"1:{int(scale)}",
                     project=project, unit="环保工程",
                     designer="envcad", date="2026.08")
    return draw_frame(doc, scale, info, tracker=tracker)


def gen_baghouse(out_dir: str, level: str = "B", air_flow: float = 20000.0,
                 scale: float = 100.0, project: str = "袋式除尘器",
                 **design_kw) -> list:
    """成套出图主入口。level=A/B/C；air_flow 等输入条件由提示词给定。"""
    os.makedirs(out_dir, exist_ok=True)
    p = design_baghouse_full(air_flow=air_flow, **design_kw)
    lvl = level.upper()
    paths = []
    paths.append(_s1_outline(out_dir, scale, p, project))     # A-01
    paths.append(_s2_spec(out_dir, scale, p, project))        # A-02
    if lvl in ("B", "C"):
        paths.append(_s3_section(out_dir, scale, p, project))   # B-03
        paths.append(_s4_tube_sheet(out_dir, scale, p, project))  # B-04
        paths.append(_s5_pulse(out_dir, scale, p, project))       # B-05
        paths.append(_s6_hopper(out_dir, scale, p, project))      # B-06
    if lvl == "C":
        paths.append(_s7_flow(out_dir, scale, p, project))      # C-07
        paths.append(_s8_material(out_dir, scale, p, project))  # C-08
    return paths


# ═══ A-01 外形总图 ═══
def _s1_outline(out_dir, scale, p, project):
    doc, _, tracker = new_drawing(scale, return_tracker=True)
    msp = doc.modelspace()
    x0, y0, x1, y1 = _frame(doc, scale, "袋式除尘器外形总图", "BH-01", project, tracker)
    s = scale

    # 正立面（左半区，设备左下角为原点）
    ex0 = x0 + 12000
    ey0 = y0 + 9000
    draw_baghouse_elevation(msp, (ex0, ey0), p, scale,
                            label="正立面图", tracker=tracker)

    # 平面（右半区）
    px0 = x0 + 33000
    py0 = y0 + 9000
    draw_baghouse_plan(msp, (px0, py0), p, scale, label="平面图", tracker=tracker)

    draw_legend(msp, (x1 - 150 * s, y1 - 62 * s), scale,
                [("equip", "设备轮廓", "按图"), ("center", "中心线", "—"),
                 ("arrow_flow", "气流方向", "顺工艺"), ("elevation", "标高", "m")],
                tracker=tracker)
    draw_tech_notes(msp, (x0 + 3 * s, y1 - 30 * s), scale, "外形总图技术要求",
                    [f"处理风量 {p['air_flow']:.0f} m³/h，过滤风速 {p['filter_v']} m/min。",
                     f"总过滤面积 {p['filter_area']} m²，滤袋 {p['n_bags']} 条。",
                     f"设备阻力 {p['dp']} Pa，除尘效率 ≥{p['eff']*100:.1f}%。",
                     "壳体 Q235B 钢板，厚度≥5mm，外表面除锈刷漆。",
                     "安装执行 HJ 2020—2012，验收执行 GB 16297。"],
                    width=TECH_W, tracker=tracker)
    return save_dxf(doc, os.path.join(out_dir, "BH-01_外形总图.dxf"))


# ═══ A-02 技术特性表 ═══
def _s2_spec(out_dir, scale, p, project):
    doc, _, tracker = new_drawing(scale, return_tracker=True)
    msp = doc.modelspace()
    x0, y0, x1, y1 = _frame(doc, scale, "技术特性表", "BH-02", project, tracker)
    s = scale

    rows = [
        ("处理风量", f"{p['air_flow']:.0f}", "m³/h"),
        ("过滤风速", f"{p['filter_v']}", "m/min"),
        ("总过滤面积", f"{p['filter_area']}", "m²"),
        ("滤袋规格", f"Φ{p['bag_dia_mm']:.0f}×{p['bag_len_mm']:.0f}", "mm"),
        ("滤袋数量", f"{p['n_bags']}", "条"),
        ("滤袋排列", f"{p['rows']}行×{p['cols']}列", "—"),
        ("箱体尺寸", f"{p['box_L']:.0f}×{p['box_W']:.0f}", "mm"),
        ("设备总高", f"{p['total_H']:.0f}", "mm"),
        ("进风口", f"Φ{p['inlet_dn']:.0f}", "mm"),
        ("出风口", f"Φ{p['outlet_dn']:.0f}", "mm"),
        ("脉冲阀数量", f"{p['n_pulse_valve']}", "个"),
        ("设备阻力", f"{p['dp']}", "Pa"),
        ("除尘效率", f"{p['eff']*100:.2f}", "%"),
        ("入口浓度", f"{p['conc_in']:.0f}", "mg/m³"),
        ("出口浓度", f"{p['conc_out']}", "mg/m³"),
        ("排放限值", f"{p['limit']}", "mg/m³"),
    ]
    draw_spec_table(msp, (x0 + 30000, y1 - 8000), scale,
                    "袋式除尘器技术特性表", rows, tracker)
    draw_tech_notes(msp, (x0 + 3 * s, y1 - 30 * s), scale, "说明",
                    [f"出口浓度 {p['conc_out']} mg/m³ "
                     f"{'≤' if p['ok'] else '>'} 限值 {p['limit']} mg/m³，"
                     f"{'达标' if p['ok'] else '需提高效率'}。",
                     "滤袋材质按烟气性质选用（涤纶/PPS/PTFE）。",
                     "喷吹气源为压缩空气，压力 0.4~0.6 MPa。"],
                    width=TECH_W, tracker=tracker)
    return save_dxf(doc, os.path.join(out_dir, "BH-02_技术特性表.dxf"))


# ═══ B-03 纵剖面图 ═══
def _s3_section(out_dir, scale, p, project):
    doc, _, tracker = new_drawing(scale, return_tracker=True)
    msp = doc.modelspace()
    x0, y0, x1, y1 = _frame(doc, scale, "袋式除尘器纵剖面图", "BH-03", project, tracker)
    s = scale
    draw_baghouse_section(msp, (x0 + 16000, y0 + 9000), p, scale,
                          label="1-1 剖面图", tracker=tracker)
    draw_tech_notes(msp, (x0 + 3 * s, y1 - 30 * s), scale, "剖面技术要求",
                    [f"滤袋 Φ{p['bag_dia_mm']:.0f}×{p['bag_len_mm']:.0f}，"
                     f"配镀锌袋笼，垂直度≤1‰。",
                     f"花板孔 Φ{p['bag_dia_mm']+5:.0f}，孔口光滑无毛刺。",
                     "滤袋与花板孔采用弹性涨圈密封，不漏气。",
                     "净气室与袋室密封隔离，漏风率≤3%。"],
                    width=TECH_W, tracker=tracker)
    return save_dxf(doc, os.path.join(out_dir, "BH-03_纵剖面图.dxf"))


# ═══ B-04 花板布置图 ═══
def _s4_tube_sheet(out_dir, scale, p, project):
    doc, _, tracker = new_drawing(scale, return_tracker=True)
    msp = doc.modelspace()
    x0, y0, x1, y1 = _frame(doc, scale, "花板布置图", "BH-04", project, tracker)
    s = scale
    draw_baghouse_tube_sheet(msp, (x0 + 12000, y0 + 10000), p, scale,
                             label="花板布置图", tracker=tracker)
    draw_tech_notes(msp, (x0 + 3 * s, y1 - 30 * s), scale, "花板技术要求",
                    [f"花板尺寸 {p['plate_L']:.0f}×{p['plate_W']:.0f} mm，"
                     f"厚度≥6mm。",
                     f"孔径 Φ{p['bag_dia_mm']+5:.0f}，共 {p['n_bags']} 孔。",
                     f"孔中心距 {p['spacing']:.0f} mm，偏差≤±1mm。",
                     "花板平面度≤2‰，焊后整体热处理。"],
                    width=TECH_W, tracker=tracker)
    return save_dxf(doc, os.path.join(out_dir, "BH-04_花板布置图.dxf"))


# ═══ B-05 喷吹系统图 ═══
def _s5_pulse(out_dir, scale, p, project):
    doc, _, tracker = new_drawing(scale, return_tracker=True)
    msp = doc.modelspace()
    x0, y0, x1, y1 = _frame(doc, scale, "喷吹系统图", "BH-05", project, tracker)
    s = scale
    draw_baghouse_pulse(msp, (x0 + 12000, y0 + 12000), p, scale,
                        label="喷吹系统图", tracker=tracker)
    draw_tech_notes(msp, (x0 + 3 * s, y1 - 30 * s), scale, "喷吹技术要求",
                    [f"脉冲阀 {p['n_pulse_valve']} 个（每列1个），"
                     f"直角式 1″。",
                     f"喷吹管 {p['cols']} 根，每管 {p['rows']} 喷嘴对准袋口。",
                     "喷吹压力 0.4~0.6 MPa，脉冲宽度 0.1~0.2 s。",
                     "气包配安全阀、排污阀，容量满足连续喷吹。"],
                    width=TECH_W, tracker=tracker)
    return save_dxf(doc, os.path.join(out_dir, "BH-05_喷吹系统图.dxf"))


# ═══ B-06 灰斗及卸料装置详图 ═══
def _s6_hopper(out_dir, scale, p, project):
    doc, _, tracker = new_drawing(scale, return_tracker=True)
    msp = doc.modelspace()
    x0, y0, x1, y1 = _frame(doc, scale, "灰斗及卸料装置详图", "BH-06", project, tracker)
    s = scale
    draw_baghouse_hopper(msp, (x0 + 14000, y1 - 12000), p, scale,
                         label="灰斗及卸料装置详图", tracker=tracker)
    draw_tech_notes(msp, (x0 + 3 * s, y1 - 30 * s), scale, "灰斗技术要求",
                    ["灰斗斗壁倾角≥60°，内壁光滑防积灰。",
                     "灰斗设料位计，高料位报警联锁卸料。",
                     "卸料采用插板阀+星型卸料器，锁风防漏。",
                     "灰斗外壁设蒸汽/电伴热（高湿烟气时）。"],
                    width=TECH_W, tracker=tracker)
    return save_dxf(doc, os.path.join(out_dir, "BH-06_灰斗及卸料装置详图.dxf"))


# ═══ C-07 除尘系统工艺流程图 ═══
def _s7_flow(out_dir, scale, p, project):
    doc, _, tracker = new_drawing(scale, return_tracker=True)
    msp = doc.modelspace()
    x0, y0, x1, y1 = _frame(doc, scale, "除尘系统工艺流程图", "BH-07", project, tracker)
    s = scale

    stages = ["集气罩", "风管", "袋式除尘器", "离心风机", "烟囱排放"]
    n = len(stages)
    avail = (x1 - x0) - 12000            # 可用宽度（左右留边）
    gap = avail * 0.05 / max(1, n - 1)
    bw = (avail - gap * (n - 1)) / n     # 框宽自适应图框
    bh_ = 6000
    bx = x0 + 6000
    by = y0 + 16000
    for i, st in enumerate(stages):
        cx0 = bx + i * (bw + gap)
        msp.add_lwpolyline([(cx0, by), (cx0 + bw, by), (cx0 + bw, by + bh_),
                            (cx0, by + bh_)], close=True, dxfattribs={"layer": "工艺"})
        _t(msp, st, (cx0 + bw / 2, by + bh_ / 2), 3 * s, align=MC,
           layer="文字", tracker=tracker)
        if i < len(stages) - 1:
            ax0 = cx0 + bw
            draw_flow_arrow(msp, (ax0, by + bh_ / 2), (gap, 0), scale,
                            length=8.0, label="", tracker=tracker)
    _t(msp, f"系统处理风量 {p['air_flow']:.0f} m³/h",
       (x0 + (x1 - x0) / 2, y0 + 10000), 3 * s, align=MC, layer="文字-标题", tracker=tracker)
    draw_tech_notes(msp, (x0 + 3 * s, y1 - 30 * s), scale, "工艺流程说明",
                    ["含尘气体经集气罩收集，由风管送入袋式除尘器。",
                     f"净化后气体经离心风机由烟囱排放，出口≤{p['limit']}mg/m³。",
                     "除尘器收集的粉尘经卸料装置定期外运。",
                     "系统负压运行，风机置于除尘器后（清洁侧）。"],
                    width=TECH_W, tracker=tracker)
    return save_dxf(doc, os.path.join(out_dir, "BH-07_工艺流程图.dxf"))


# ═══ C-08 设备材料表 ═══
def _s8_material(out_dir, scale, p, project):
    doc, _, tracker = new_drawing(scale, return_tracker=True)
    msp = doc.modelspace()
    x0, y0, x1, y1 = _frame(doc, scale, "设备材料表", "BH-08", project, tracker)
    rows = [
        ("1", "袋式除尘器本体", f"{p['filter_area']}m² Q235B", "台", "1"),
        ("2", "滤袋", f"Φ{p['bag_dia_mm']:.0f}×{p['bag_len_mm']:.0f} 涤纶针刺毡", "条", f"{p['n_bags']}"),
        ("3", "袋笼", f"Φ{p['bag_dia_mm']-10:.0f}×{p['bag_len_mm']:.0f} 镀锌", "个", f"{p['n_bags']}"),
        ("4", "脉冲阀", "直角式 1″ 24V", "个", f"{p['n_pulse_valve']}"),
        ("5", "气包", f"Φ250 L={p['air_tank_L']:.0f}", "个", "1"),
        ("6", "喷吹管", f"Φ25 带喷嘴", "根", f"{p['cols']}"),
        ("7", "星型卸料器", "300×300 N=1.1kW", "台", "1"),
        ("8", "插板阀", "300×300 手动", "个", "1"),
        ("9", "离心风机", f"Q={p['air_flow']:.0f}m³/h P={p['dp']+500}Pa", "台", "1"),
        ("10", "料位计", "阻旋式 220V", "个", "1"),
        ("11", "控制柜", "PLC 定时/定压喷吹", "台", "1"),
        ("12", "花板", f"{p['plate_L']:.0f}×{p['plate_W']:.0f} δ=6", "块", "1"),
    ]
    draw_material_table(msp, (x0 + 8000, y1 - 8000), scale, rows, tracker)
    _t(msp, "设备材料表", (x0 + (x1 - x0) / 2, y0 + 5000), 5 * scale,
       align=MC, layer="文字-标题", tracker=tracker)
    return save_dxf(doc, os.path.join(out_dir, "BH-08_设备材料表.dxf"))
