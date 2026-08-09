"""剖面视图与局部放大标注 v1.0（GB/T 4458.1—2002, GB/T 4458.6—2002）。

支持:
  * 剖切符号线（截面线 + 方向箭头 + 剖视名称）
  * 局部放大视图（圆形放大标记 + 比例标注）
  * 旋转剖、阶梯剖的剖切路径标注

纯 ezdxf，零新依赖。
"""
from __future__ import annotations

import math
from typing import List, Optional, Tuple

from ezdxf.enums import TextEntityAlignment
from ..utils import _r, _tri


# ─── 内部辅助 ───────────────────────────────────────────

def _thick_arrow(msp, tip, direction: Tuple[float, float], scale: float,
                 layer="粗实线"):
    """粗箭头（剖面方向指示）。"""
    tx, ty = tip
    dx, dy = direction
    n = math.hypot(dx, dy)
    if n == 0:
        return
    dx, dy = dx / n, dy / n

    h = 4.0 * scale
    w = 2.5 * scale

    # 粗箭头两条线
    perp_x, perp_y = -dy, dx
    p1 = (tx + h * dx + w * perp_x, ty + h * dy + w * perp_y)
    p2 = (tx + h * dx - w * perp_x, ty + h * dy - w * perp_y)

    msp.add_line((tx, ty), p1, dxfattribs={"layer": layer, "lineweight": 50})
    msp.add_line((tx, ty), p2, dxfattribs={"layer": layer, "lineweight": 50})

    # 填充箭头
    try:
        msp.add_solid([(tx, ty), p1, p2, p2], dxfattribs={"layer": layer})
    except Exception as _e:
        print(f'[警告] 操作失败：{_e}')


# ─── 剖切符号线 ──────────────────────────────────────────

def draw_section_line(msp, start, end, label: str = "A",
                       direction: str = "right",
                       offset: float = 6.0,
                       scale: float = 100.0,
                       layer: str = "粗实线",
                       tracker=None):
    """绘制剖切符号线（简单的直剖）。

    参数:
        start/end: 剖切线的起点和终点
        label: 剖视标记字母（如 "A", "B"）
        direction: 剖面看的方向 "right" / "left" / "up" / "down"
        offset: 符号线超出剖切迹的长度（图纸 mm）
    """
    s = scale
    sx, sy = _r(*start)
    ex, ey = _r(*end)

    dx, dy = ex - sx, ey - sy
    seg_len = math.hypot(dx, dy)
    if seg_len == 0:
        return

    ux, uy = dx / seg_len, dy / seg_len

    # 粗点画线（中心线+粗实线混合效果）
    msp.add_line((sx, sy), (ex, ey),
                 dxfattribs={"layer": layer, "lineweight": 50})

    # 两端短粗线（超出剖切点）
    off = offset * s
    sx1, sy1 = _r(sx - ux * off, sy - uy * off)
    sx2, sy2 = _r(sx + ux * off * 0.3, sy + uy * off * 0.3)
    ex1, ey1 = _r(ex - ux * off * 0.3, ey - uy * off * 0.3)
    ex2, ey2 = _r(ex + ux * off, ey + uy * off)

    msp.add_line((sx1, sy1), (sx2, sy2),
                 dxfattribs={"layer": layer, "lineweight": 50})
    msp.add_line((ex1, ey1), (ex2, ey2),
                 dxfattribs={"layer": layer, "lineweight": 50})

    # 方向箭头（两端外延方向）
    perp_x, perp_y = -uy, ux  # 法向量（顺时针90度）

    # 根据 direction 决定箭头朝向
    if direction == "left":
        perp_x, perp_y = uy, -ux
    elif direction == "up":
        perp_x, perp_y = -dy / seg_len, dx / seg_len
    elif direction == "down":
        perp_x, perp_y = dy / seg_len, -dx / seg_len

    arrow_offset = 5 * s
    _thick_arrow(msp, _r(sx1, sy1),
                 (perp_x, perp_y), s, layer=layer)
    _thick_arrow(msp, _r(ex2, ey2),
                 (perp_x, perp_y), s, layer=layer)

    # 剖视名称（两端各放一个 label）
    txt_h = 4.0 * s
    for base_pt, dir_factor in [((sx1, sy1), -1), ((ex2, ey2), -1)]:
        bx, by = base_pt
        lx = bx + perp_x * 4 * s * dir_factor
        ly = by + perp_y * 4 * s * dir_factor
        t = msp.add_text(f"{label}", dxfattribs={
            "layer": "文字-标题", "height": txt_h, "style": "ENG",
        })
        t.set_placement((lx, ly), align=TextEntityAlignment.MIDDLE_CENTER)

        # 剖面方向箭头提示
        arr_lx = lx + perp_x * 8 * s
        arr_ly = ly + perp_y * 8 * s
        _thick_arrow(msp, (arr_lx, arr_ly),
                     (perp_x, perp_y), s * 0.6, layer=layer)

    if tracker is not None:
        bbox_x = sorted([sx1, sx2, ex1, ex2])
        bbox_y = sorted([sy1, sy2, ey1, ey2])
        tracker.register(bbox_x[0], bbox_y[0], bbox_x[-1], bbox_y[-1], margin=40)

    return _r(ex2, ey2)


# ─── 局部放大视图标记 ────────────────────────────────────

def draw_detail_circle(msp, center, radius: float, label: str = "I",
                        scale_ratio: str = "2:1",
                        leader_to: Tuple[float, float] = None,
                        view_scale: float = 100.0,
                        layer: str = "细实线",
                        tracker=None):
    """绘制局部放大视图标记。

    在原始视图上画一个带细实线的圆圈+引出线+比例标注。
    参数:
        center: 圆圈中心（原始视图坐标）
        radius: 圆圈半径（原始视图坐标，mm）
        label: 放大图标记字母
        scale_ratio: 放大比例（如 "2:1"）
        leader_to: 引出线指向的目标点（如放大图位置）
        view_scale: 本图出图比例
    """
    s = view_scale
    cx, cy = _r(*center)
    r = radius  # 已经是 scaled 坐标

    # 画圆圈（细实线）
    msp.add_circle((cx, cy), r, dxfattribs={"layer": layer})

    # 引出线（从圆右边缘 → 放大图位置）
    if leader_to:
        lx, ly = _r(*leader_to)
        # 圆到引出起点的线
        msp.add_line((cx + r, cy), (cx + r + 5 * s, cy),
                     dxfattribs={"layer": layer})
        # 弯折到目标点
        msp.add_line((cx + r + 5 * s, cy), (lx, ly),
                     dxfattribs={"layer": layer})

    # 字母标注在圆圈旁
    txt_h = 3.5 * s
    t = msp.add_text(label, dxfattribs={
        "layer": "文字-标题", "height": txt_h, "style": "ENG",
    })
    t.set_placement((cx + r + 3 * s, cy + r + 3 * s),
                    align=TextEntityAlignment.MIDDLE_LEFT)

    if tracker is not None:
        tracker.register(cx - r, cy - r, cx + r, cy + r, margin=20)

    return (cx + r, cy)


def draw_detail_label(msp, origin, label: str = "I",
                       scale_ratio: str = "2:1",
                       view_scale: float = 100.0,
                       layer: str = "粗实线",
                       tracker=None):
    """在放大视图位置画标注（细实线圆 + 比例说明）。

    返回标注边界。
    """
    s = view_scale
    ox, oy = _r(*origin)

    r = 4.0 * s  # 标注圆半径
    msp.add_circle((ox, oy), r, dxfattribs={"layer": "细实线"})

    # 标注文字在圆下方
    txt_h = 3.0 * s
    t = msp.add_text(label, dxfattribs={
        "layer": "文字-标题", "height": txt_h, "style": "ENG",
    })
    t.set_placement((ox, oy - r - 2 * s),
                    align=TextEntityAlignment.MIDDLE_CENTER)

    # 比例标注
    t2 = msp.add_text(scale_ratio, dxfattribs={
        "layer": "文字", "height": 2.5 * s, "style": "ENG",
    })
    t2.set_placement((ox, oy - r - 6 * s),
                     align=TextEntityAlignment.MIDDLE_CENTER)

    if tracker is not None:
        tracker.register(ox - r - 5 * s, oy - r - 10 * s,
                         ox + r + 5 * s, oy + r + 2 * s, margin=20)

    return (ox + r, oy - r - 8 * s)
