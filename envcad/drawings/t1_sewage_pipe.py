"""测试1：DN300 铸铁污水管道专属标注生成。

6m DN300 铸铁污水管，起点管内底标高 -1.200m，终点 -1.176m；
标注管径、管内底标高、0.4% 坡度及水流方向箭头。
"""
from __future__ import annotations

import os

from ..engine.dxf_base import new_drawing, save_dxf
from ..standards.frame import FrameInfo, draw_frame, save_dxf_autofit
from ..standards.annotate import (
    draw_elevation, draw_pipe_diameter, draw_slope, draw_flow_arrow,
)
from ..components.pipe import draw_pipe
from . import draw_tech_notes


def gen_t1(out_dir: str, scale: float = 50.0,
           length: float = 6000.0, dn: float = 300.0,
           start_il: float = -1.200, end_il: float = -1.176) -> str:
    """生成测试1 DXF。返回文件路径。"""
    doc, dim, tracker = new_drawing(scale, return_tracker=True)
    msp = doc.modelspace()
    info = FrameInfo(
        title="污水管道标注图",
        drawing_no="T1-01",
        scale_str=f"1:{int(scale)}",
        project="基础单元测试",
        unit="环保工程",
        designer="envcad",
        date="2026.07",
    )
    x0, y0, x1, y1 = draw_frame(doc, scale, info, tracker=tracker)

    # 管段坐标（剖面：水平投影=管长，y 用图上基准 + 标高差）
    y_base = (y0 + y1) / 2 + 1000  # 图框中部偏上
    start_h = start_il * 1000      # mm（标高×1000）
    end_h = end_il * 1000
    px0 = x0 + 3000
    px1 = px0 + length
    P1 = (px0, y_base + start_h)   # 起点（图上 y）
    P2 = (px1, y_base + end_h)     # 终点

    # 双线管（剖面，DN300，沿管轴偏移±150）
    draw_pipe(msp, P1, P2, dn=dn, scale=scale, style="double", layer="管道-污水")

    # 管径标注（中段上方引出）
    mid = ((P1[0] + P2[0]) / 2, (P1[1] + P2[1]) / 2 + dn / 2)
    draw_pipe_diameter(msp, mid, f"DN{int(dn)}", scale, leader_dir=(0, 1), label="", tracker=tracker)

    # 管内底标高（起点、终点）
    draw_elevation(msp, (P1[0], P1[1] - dn / 2), f"{start_il:.3f}", scale, side="left", tracker=tracker)
    draw_elevation(msp, (P2[0], P2[1] - dn / 2), f"{end_il:.3f}", scale, side="right", tracker=tracker)

    # 坡度标注（含坡向小箭头）
    slope_pct = round((start_h - end_h) / length * 100, 3)  # 顺流下降为正
    # 题目数据：起点 -1.200（低），终点 -1.176（高）；坡度绝对值 0.4%
    slope_str = f"0.4%"
    draw_slope(msp, P1, P2, slope_str, scale, offset=12.0, tracker=tracker)

    # 水流方向箭头（起点→终点，带标签）
    import math
    dx, dy = P2[0] - P1[0], P2[1] - P1[1]
    n = math.hypot(dx, dy)
    midx = (P1[0] + P2[0]) / 2
    midy = (P1[1] + P2[1]) / 2 - dn / 2 - 8 * scale
    draw_flow_arrow(msp, (midx - 10 * scale, midy), (dx / n, dy / n), scale,
                    length=20.0, label="水流方向", tracker=tracker)

    # 管长标注
    from ..standards.annotate import _t
    _t(msp, f"L={int(length)}mm", (midx, midy - 6 * scale), 3 * scale, layer="文字",
       tracker=tracker)

    # 技术要求
    draw_tech_notes(msp, (x1 - 90 * scale, y1 - 25 * scale), scale,
                    "技术要求",
                    ["管道为 DN300 铸铁管，承插接口，橡胶圈密封。",
                     "管道坡度 0.4%，坡向水流方向，严禁倒坡。",
                     "管内底标高单位为 m，管道中心线标注见纵断图。",
                     "管道施工及验收执行 GB 50268—2008。"],
                    tracker=tracker)

    return save_dxf_autofit(doc, os.path.join(out_dir, "T1_污水管道标注图.dxf"), scale, info, tracker)
