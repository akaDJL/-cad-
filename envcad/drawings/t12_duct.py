# -*- coding: utf-8 -*-
"""风管系统成套施工图 v1.0 — 提示词驱动 · A/B/C 分级出图。

用法：
    gen_duct(out_dir, level="B", air_flow=50000)   # B级 6张
    gen_duct(out_dir, level="C", air_flow=30000)   # C级 8张

级别：A平面+特性表(2) / B详图(6) / C成套(8)。尺寸由 design_duct_full 算出。
"""
from __future__ import annotations

import os

from ezdxf.enums import TextEntityAlignment

from ..engine.dxf_base import new_drawing, save_dxf
from ..standards.frame import FrameInfo, draw_frame
from ..standards.annotate import _t, draw_flow_arrow
from ..standards.legend import draw_legend
from ..standards.duct import (
    draw_duct_plan, draw_duct_elevation, draw_duct_elbow,
    draw_duct_tee, draw_duct_reducer, draw_duct_hanger,
)
from ..design.env_process import design_duct_full
from . import draw_tech_notes, draw_spec_table, draw_material_table

MC = TextEntityAlignment.MIDDLE_CENTER
TECH_W = 95.0


def _frame(doc, scale, title, no, project, tracker):
    info = FrameInfo(title=title, drawing_no=no, scale_str=f"1:{int(scale)}",
                     project=project, unit="环保工程",
                     designer="envcad", date="2026.08")
    return draw_frame(doc, scale, info, tracker=tracker)


def gen_duct(out_dir: str, level: str = "B", air_flow: float = 50000.0,
             scale: float = 100.0, project: str = "废气风管系统", **design_kw) -> list:
    os.makedirs(out_dir, exist_ok=True)
    p = design_duct_full(air_flow=air_flow, **design_kw)
    lvl = level.upper()
    paths = [_s1_plan(out_dir, scale, p, project), _s2_spec(out_dir, scale, p, project)]
    if lvl in ("B", "C"):
        paths += [_s3_elevation(out_dir, scale, p, project),
                  _s4_elbow(out_dir, scale, p, project),
                  _s5_tee_reducer(out_dir, scale, p, project),
                  _s6_hanger(out_dir, scale, p, project)]
    if lvl == "C":
        paths += [_s7_flow(out_dir, scale, p, project),
                  _s8_material(out_dir, scale, p, project)]
    return paths


def _s1_plan(out_dir, scale, p, project):
    doc, _, tracker = new_drawing(scale, return_tracker=True)
    msp = doc.modelspace()
    x0, y0, x1, y1 = _frame(doc, scale, "风管平面布置图", "DU-01", project, tracker)
    s = scale
    draw_duct_plan(msp, (x0 + 4000, y0 + 4000), p, scale,
                   label="风管平面布置图", tracker=tracker)
    draw_legend(msp, (x1 - 150 * s, y1 - 62 * s), scale,
                [("pipe_solid", "风管", "按图"), ("valve", "风阀", "按图"),
                 ("arrow_flow", "气流方向", "顺工艺"), ("elevation", "标高", "m")],
                tracker=tracker)
    draw_tech_notes(msp, (x0 + 3 * s, y1 - 30 * s), scale, "平面布置技术要求",
                    [f"风量 {p['air_flow']:.0f} m³/h，风速 {p['v_duct']} m/s。",
                     f"主管 Φ{p['dn']:.0f}mm，镀锌钢板厚 {p['plate_t']}mm。",
                     "风管走向顺工艺，减少弯头降低阻力。",
                     "设计执行 GB 50243—2016。"],
                    width=TECH_W, tracker=tracker)
    return save_dxf(doc, os.path.join(out_dir, "DU-01_平面布置图.dxf"))


def _s2_spec(out_dir, scale, p, project):
    doc, _, tracker = new_drawing(scale, return_tracker=True)
    msp = doc.modelspace()
    x0, y0, x1, y1 = _frame(doc, scale, "技术特性表", "DU-02", project, tracker)
    s = scale
    rows = [
        ("风量", f"{p['air_flow']:.0f}", "m³/h"),
        ("风速", f"{p['v_duct']}", "m/s"),
        ("主管直径", f"Φ{p['dn']:.0f}", "mm"),
        ("钢板厚度", f"{p['plate_t']}", "mm"),
        ("弯头曲率", f"R={p['elbow_r']:.0f}", "mm"),
        ("支吊架间距", f"{p['hanger_gap']/1000:.0f}", "m"),
        ("法兰间距", f"{p['flange_gap']/1000:.0f}", "m"),
        ("变径长度", f"{p['reducer_len']:.0f}", "mm"),
        ("弯头数", f"{p['n_elbow']}", "个"),
        ("三通数", f"{p['n_tee']}", "个"),
    ]
    draw_spec_table(msp, (x0 + 30000, y1 - 8000), scale,
                    "风管系统技术特性表", rows, tracker)
    draw_tech_notes(msp, (x0 + 3 * s, y1 - 30 * s), scale, "说明",
                    ["风管采用镀锌钢板咬口/焊接制作。",
                     "法兰连接，垫料密封防漏风。",
                     "含尘废气风管内壁做耐磨处理。"],
                    width=TECH_W, tracker=tracker)
    return save_dxf(doc, os.path.join(out_dir, "DU-02_技术特性表.dxf"))


def _s3_elevation(out_dir, scale, p, project):
    doc, _, tracker = new_drawing(scale, return_tracker=True)
    msp = doc.modelspace()
    x0, y0, x1, y1 = _frame(doc, scale, "风管立面图", "DU-03", project, tracker)
    s = scale
    draw_duct_elevation(msp, (x0 + 8000, y0 + 14000), p, scale,
                        label="风管立面图", tracker=tracker)
    draw_tech_notes(msp, (x0 + 3 * s, y1 - 30 * s), scale, "立面技术要求",
                    [f"风管标高按工艺要求敷设，坡度顺气流。",
                     f"支吊架间距 {p['hanger_gap']/1000:.0f}m，转弯处加密。",
                     "穿墙/楼板处设套管，密封防火。"],
                    width=TECH_W, tracker=tracker)
    return save_dxf(doc, os.path.join(out_dir, "DU-03_立面图.dxf"))


def _s4_elbow(out_dir, scale, p, project):
    doc, _, tracker = new_drawing(scale, return_tracker=True)
    msp = doc.modelspace()
    x0, y0, x1, y1 = _frame(doc, scale, "弯头详图", "DU-04", project, tracker)
    s = scale
    draw_duct_elbow(msp, (x0 + 8000, y0 + 8000), p, scale,
                    label="90°弯头详图", tracker=tracker)
    draw_tech_notes(msp, (x0 + 3 * s, y1 - 30 * s), scale, "弯头技术要求",
                    [f"曲率半径 R={p['elbow_r']:.0f}mm（≥1.0D）。",
                     "内外弧咬口/焊接，导流叶片（大曲率时）。",
                     "弯头两端法兰连接。"],
                    width=TECH_W, tracker=tracker)
    return save_dxf(doc, os.path.join(out_dir, "DU-04_弯头详图.dxf"))


def _s5_tee_reducer(out_dir, scale, p, project):
    doc, _, tracker = new_drawing(scale, return_tracker=True)
    msp = doc.modelspace()
    x0, y0, x1, y1 = _frame(doc, scale, "三通及变径详图", "DU-05", project, tracker)
    s = scale
    draw_duct_tee(msp, (x0 + 6000, y0 + 16000), p, scale,
                  label="三通详图", tracker=tracker)
    draw_duct_reducer(msp, (x0 + 24000, y0 + 16000), p, scale,
                      label="变径详图", tracker=tracker)
    draw_tech_notes(msp, (x0 + 3 * s, y1 - 30 * s), scale, "管件技术要求",
                    ["三通主管×支管，夹角顺气流方向。",
                     "变径采用同心渐缩，长度按管径确定。",
                     "管件与主管等壁厚，法兰连接。"],
                    width=TECH_W, tracker=tracker)
    return save_dxf(doc, os.path.join(out_dir, "DU-05_三通及变径详图.dxf"))


def _s6_hanger(out_dir, scale, p, project):
    doc, _, tracker = new_drawing(scale, return_tracker=True)
    msp = doc.modelspace()
    x0, y0, x1, y1 = _frame(doc, scale, "支吊架详图", "DU-06", project, tracker)
    s = scale
    draw_duct_hanger(msp, (x0 + 16000, y0 + 10000), p, scale,
                     label="支吊架详图", tracker=tracker)
    draw_tech_notes(msp, (x0 + 3 * s, y1 - 30 * s), scale, "支吊架技术要求",
                    [f"支吊架间距 {p['hanger_gap']/1000:.0f}m。",
                     "吊杆+槽钢横担+抱箍，热镀锌。",
                     "承载按风管自重+积灰荷载验算。"],
                    width=TECH_W, tracker=tracker)
    return save_dxf(doc, os.path.join(out_dir, "DU-06_支吊架详图.dxf"))


def _s7_flow(out_dir, scale, p, project):
    doc, _, tracker = new_drawing(scale, return_tracker=True)
    msp = doc.modelspace()
    x0, y0, x1, y1 = _frame(doc, scale, "废气收集系统流程图", "DU-07", project, tracker)
    s = scale
    stages = ["集气罩", "支风管", "主风管", "治理设备", "风机"]
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
    draw_tech_notes(msp, (x0 + 3 * s, y1 - 30 * s), scale, "收集系统说明",
                    [f"各集气罩废气经支风管汇入主管（Φ{p['dn']:.0f}）。",
                     "主管风速 10~15m/s，防粉尘沉积。",
                     "系统负压运行，风机置于治理设备后。"],
                    width=TECH_W, tracker=tracker)
    return save_dxf(doc, os.path.join(out_dir, "DU-07_工艺流程图.dxf"))


def _s8_material(out_dir, scale, p, project):
    doc, _, tracker = new_drawing(scale, return_tracker=True)
    msp = doc.modelspace()
    x0, y0, x1, y1 = _frame(doc, scale, "设备材料表", "DU-08", project, tracker)
    rows = [
        ("1", "主风管", f"Φ{p['dn']:.0f} 镀锌钢板 δ={p['plate_t']}", "m", "45"),
        ("2", "90°弯头", f"Φ{p['dn']:.0f} R={p['elbow_r']:.0f}", "个", f"{p['n_elbow']}"),
        ("3", "三通", f"Φ{p['dn']:.0f}×Φ{p['dn']*0.7:.0f}", "个", f"{p['n_tee']}"),
        ("4", "变径", f"Φ{p['dn']:.0f}→Φ{p['dn']*0.7:.0f}", "个", "1"),
        ("5", "风阀", f"Φ{p['dn']:.0f} 手动/气动", "个", "3"),
        ("6", "软接", f"Φ{p['dn']:.0f} 帆布", "个", "2"),
        ("7", "法兰", f"Φ{p['dn']:.0f} 角钢", "付", "20"),
        ("8", "支吊架", "吊杆+槽钢+抱箍", "套", "15"),
        ("9", "镀锌钢板", f"δ={p['plate_t']}mm", "m²", "60"),
        ("10", "密封垫料", "橡胶/8501", "m", "80"),
    ]
    draw_material_table(msp, (x0 + 8000, y1 - 8000), scale, rows, tracker)
    _t(msp, "设备材料表", (x0 + (x1 - x0) / 2, y0 + 5000), 5 * scale,
       align=MC, layer="文字-标题", tracker=tracker)
    return save_dxf(doc, os.path.join(out_dir, "DU-08_设备材料表.dxf"))
