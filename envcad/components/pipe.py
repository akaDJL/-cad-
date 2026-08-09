"""管道组件：单线/双线管段、带坡度管段、穿墙套管段。

单位：modelspace mm，DN 也按 mm 计（DN300=300）。
"""
from __future__ import annotations

import math

from ezdxf.enums import TextEntityAlignment

from ..standards.annotate import _t


def draw_pipe(msp, start, end, dn: float = 300, scale: float = 100,
              style: str = "single", layer: str = "管道-污水"):
    """绘制管段。

    style='single' 平面单线；'double' 剖面双线（管壁双线，间距=dn）。
    """
    sx, sy = start
    ex, ey = end
    if style == "single":
        msp.add_line((sx, sy), (ex, ey), dxfattribs={"layer": layer})
        return
    # 双线
    L = math.hypot(ex - sx, ey - sy) or 1.0
    nx, ny = -(ey - sy) / L, (ex - sx) / L
    off = dn / 2
    p1 = (sx + nx * off, sy + ny * off)
    p2 = (ex + nx * off, ey + ny * off)
    p3 = (ex - nx * off, ey - ny * off)
    p4 = (sx - nx * off, sy - ny * off)
    msp.add_line(p1, p2, dxfattribs={"layer": layer})
    msp.add_line(p4, p3, dxfattribs={"layer": layer})
    msp.add_line(p1, p4, dxfattribs={"layer": layer})  # 端口
    msp.add_line(p2, p3, dxfattribs={"layer": layer})


def draw_pipe_with_fall(msp, start, end, start_il: float, end_il: float,
                        dn: float = 300, scale: float = 100,
                        layer: str = "管道-污水", style: str = "single"):
    """带管内底标高的管段（剖面图用）。

    start_il/end_il: 管内底绝对标高（m，如 -1.200）。
    坐标系：x=管段水平投影（mm），y=标高绝对值（m→mm，统一 mm）。
    约定：传入的 start/end 为 (x_mm, z_mm)，z 已换算为 mm（标高×1000 取绝对值或带号）。
    """
    # 直接按给定坐标绘制，坡度由两点高差决定
    draw_pipe(msp, start, end, dn, scale, style, layer)
    return start, end


def pipe_slope(start, end) -> float:
    """计算坡度（%，正=顺流方向下降）。start/end 为 (x_mm, z_mm)。"""
    sx, sy = start
    ex, ey = end
    dx = abs(ex - sx)
    if dx == 0:
        return 0.0
    return (sy - ey) / dx * 100  # sy 高于 ey 为正坡（顺流下降）


def draw_pipe_wall_sleeve(msp, point, scale: float, wall_thick: float = 250,
                          dn: float = 300, layer: str = "设备"):
    """穿墙刚性防水套管（平面图符号）：管两侧画套管短线。"""
    s = scale
    px, py = point
    wt = wall_thick
    half = wt / 2
    # 套管两侧短粗线（垂直于管轴，假设管轴水平）
    msp.add_line((px - half, py - dn / 2 - 60), (px - half, py + dn / 2 + 60),
                 dxfattribs={"layer": layer})
    msp.add_line((px + half, py - dn / 2 - 60), (px + half, py + dn / 2 + 60),
                 dxfattribs={"layer": layer})
    # 套管上下边
    msp.add_line((px - half, py + dn / 2 + 60), (px + half, py + dn / 2 + 60),
                 dxfattribs={"layer": layer})
    msp.add_line((px - half, py - dn / 2 - 60), (px + half, py - dn / 2 - 60),
                 dxfattribs={"layer": layer})
