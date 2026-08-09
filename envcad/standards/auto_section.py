"""剖面自动生成——给定平面轮廓，生成剖切线+剖面视图。

施工图深度第4项：outline → section cut line → section view。
"""
from __future__ import annotations
from typing import List, Tuple, Optional
from ..utils import _r


def generate_section_from_outline(msp, outline: List[Tuple[float, float]],
                                  cut_line: Tuple[Tuple[float, float], ...],
                                  section_label: str = "A-A",
                                  scale: float = 100.0,
                                  section_depth: float = 3.0,
                                  floor_height: float = 3.6,
                                  n_floors: int = 1,
                                  view_offset: float = 30.0,
                                  layer="剖面", tracker=None):
    """从平面轮廓生成剖面视图。

    Args:
        msp: 模型空间
        outline: 平面轮廓顶点列表
        cut_line: 剖切线 (起点, 终点) — 剖切位置
        section_label: 剖切线编号
        scale: 比例
        section_depth: 可见深度 (m)
        floor_height: 层高 (m)
        n_floors: 层数
        view_offset: 剖面视图与平面的间距 (mm)

    Returns:
        (剖面视图左下角, 剖面视窗宽度, 剖面视窗高度)
    """
    from .views import draw_section_line

    s = scale; fh = floor_height * s; sd = section_depth * s
    ox0, off = view_offset * s, view_offset * s

    # 计算剖切线穿过的建筑范围
    if len(cut_line) >= 2:
        cl_start, cl_end = cut_line[0], cut_line[1]
        draw_section_line(msp, cl_start, cl_end, label=section_label, scale=s)

    # 找出剖切线穿过的轮廓线段
    import math
    xs = [p[0] for p in outline]; ys = [p[1] for p in outline]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    w = max_x - min_x; h = max_y - min_y

    # 剖面视图放在下部
    sec_x = min_x + off
    sec_y = min_y - 3 * off - n_floors * fh

    # 画剖面楼层
    for fi in range(n_floors):
        fy = sec_y + fi * fh
        # 楼层线
        msp.add_line((sec_x, fy), (sec_x + w, fy),
                     dxfattribs={"layer": layer, "lineweight": 30})
        # 墙体（简化为双线）
        wall_w = 0.24 * s
        for wx in [sec_x, sec_x + w * 0.3, sec_x + w * 0.7, sec_x + w]:
            msp.add_lwpolyline([(wx - wall_w / 2, fy),
                               (wx - wall_w / 2, fy + fh),
                               (wx + wall_w / 2, fy + fh),
                               (wx + wall_w / 2, fy)],
                              close=True, dxfattribs={"layer": "粗实线"})
        # 楼板
        slab = 0.12 * s
        msp.add_lwpolyline([(sec_x, fy), (sec_x + w, fy),
                           (sec_x + w, fy + slab), (sec_x, fy + slab)],
                          close=True, dxfattribs={"layer": layer})

    # 剖面标签
    from ezdxf.enums import TextEntityAlignment
    t = msp.add_text(f"剖面 {section_label}", dxfattribs={
        "layer": "文字-标题", "height": 3.5 * s, "style": "HZ",
    })
    t.set_placement((sec_x + w / 2, sec_y - 2 * off),
                    align=TextEntityAlignment.MIDDLE_CENTER)

    return ((sec_x, sec_y), w, n_floors * fh + 2 * off)


def quick_section(msp, outline: List[Tuple[float, float]],
                  cut_ratio: float = 0.5, scale: float = 100.0,
                  label: str = "A-A", n_floors: int = 3,
                  floor_height: float = 3.6, tracker=None):
    """一键从平面轮廓生成纵剖面。

    cut_ratio: 剖切线位置（轮廓纵向的百分比位置）
    """
    xs = [p[0] for p in outline]; ys = [p[1] for p in outline]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    cy = min_y + (max_y - min_y) * cut_ratio
    cut_line = ((min_x - 5, cy), (max_x + 5, cy))
    return generate_section_from_outline(
        msp, outline, cut_line, section_label=label,
        scale=scale, floor_height=floor_height, n_floors=n_floors)
