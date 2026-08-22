"""测试5：调节池参数修改迭代测试。

第一步：长8m、宽5m、深4m 矩形调节池平面图，壁厚 250mm，C30 混凝土，
        配标题栏与土建施工技术要求，比例 1:100。
第二步：宽度改为 6m，进水口标高从 -0.500m 调整为 -0.800m，
        技术要求新增“内壁做环氧树脂玻璃钢两布三油防腐”。

两步均用 RectPoolParams 参数化生成，便于对比迭代。
"""
from __future__ import annotations

import os

from ..engine.dxf_base import new_drawing, save_dxf
from ..standards.frame import FrameInfo, draw_frame, save_dxf_autofit
from ..standards.annotate import _t
from ..components.pool import RectPoolParams, draw_rect_pool_plan, draw_rect_pool_section
from . import draw_tech_notes
from ezdxf.enums import TextEntityAlignment


def _base_notes(p: RectPoolParams) -> list:
    return [
        f"池体采用 {p.material}，抗渗等级 P6，壁厚 {int(p.wall_thick)}mm，底板厚 300mm。",
        "钢筋 HRB400，保护层：池壁内侧 35mm、外侧 30mm。",
        "混凝土浇筑分层振捣密实，施工缝设止水钢板。",
        "池体完工后做闭水试验，24h 渗水量≤2L/m²。",
        f"进水管内底标高 {p.inlet_il:.3f}m。",
        "施工及验收执行 GB 50141—2008。",
    ]


def _draw(doc, scale, p: RectPoolParams, title, no, tracker=None):
    msp = doc.modelspace()
    info = FrameInfo(title=title, drawing_no=no, scale_str=f"1:{int(scale)}",
                     project="边界容错测试", unit="环保工程",
                     designer="envcad", date="2026.07")
    x0, y0, x1, y1 = draw_frame(doc, scale, info, tracker=tracker)
    # 平面图
    draw_rect_pool_plan(msp, (x0 + 4000, y0 + 5000), p, scale, tracker=tracker)
    _t(msp, "平面图", (x0 + 8000, y0 + 3000), 3.5 * scale, layer="文字-标题",
       tracker=tracker)
    # 剖面图
    draw_rect_pool_section(msp, x0 + 4000, y0 + 21000, p, scale, tracker=tracker)
    _t(msp, "1-1 剖面图", (x0 + 8000, y0 + 22000 + 5 * scale), 3.5 * scale, layer="文字-标题",
       tracker=tracker)
    # 技术要求（基础 + extra_req）
    notes = _base_notes(p) + p.extra_req
    draw_tech_notes(msp, (x1 - 95 * scale, y1 - (8 + len(notes)) * scale - 5 * scale), scale,
                    "土建施工技术要求", notes, tracker=tracker)
    return doc


def gen_t5a(out_dir: str, scale: float = 100.0) -> str:
    """第一步：8×5×4m 调节池。"""
    p = RectPoolParams(length=8000, width=5000, depth=4000, wall_thick=250,
                       material="C30钢筋混凝土", top_elev=0.000, bottom_elev=-4.000,
                       inlet_il=-0.500, outlet_il=-1.200, water_level=-0.300, name="调节池")
    doc, _, tracker = new_drawing(scale, return_tracker=True)
    _draw(doc, scale, p, "调节池平剖面图（第一步 8×5×4m）", "T5-01", tracker=tracker)
    return save_dxf_autofit(doc, os.path.join(out_dir, "T5a_调节池_第一步_8x5x4.dxf"), scale, info, tracker)


def gen_t5b(out_dir: str, scale: float = 100.0) -> str:
    """第二步：宽改 6m，进水口标高 -0.800，新增防腐要求。"""
    p = RectPoolParams(length=8000, width=6000, depth=4000, wall_thick=250,
                       material="C30钢筋混凝土", top_elev=0.000, bottom_elev=-4.000,
                       inlet_il=-0.800, outlet_il=-1.200, water_level=-0.300, name="调节池")
    p.extra_req = ["内壁做环氧树脂玻璃钢两布三油防腐。"]
    doc, _, tracker = new_drawing(scale, return_tracker=True)
    _draw(doc, scale, p, "调节池平剖面图（第二步 8×6×4m 进水-0.800）", "T5-02", tracker=tracker)
    return save_dxf_autofit(doc, os.path.join(out_dir, "T5b_调节池_第二步_8x6x4_防腐.dxf"), scale, info, tracker)


def gen_t5(out_dir: str, scale: float = 100.0) -> list:
    return [gen_t5a(out_dir, scale), gen_t5b(out_dir, scale)]
