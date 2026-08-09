"""修订标记与图纸审查 v1.0。

修订云线、变更三角、审查意见框、版本标注。
图纸审查和变更管理中高频使用。

纯 ezdxf，零新依赖。
"""
from __future__ import annotations

import math
import random
from typing import List, Optional, Tuple

from ezdxf.enums import TextEntityAlignment
from ..utils import _r, _tri


# ─── 内部辅助 ───────────────────────────────────────────

# ══════════════════════════════════════════════════════════
#  修订云线
# ══════════════════════════════════════════════════════════

def draw_revision_cloud(msp, points: List[Tuple[float, float]],
                          arc_radius: float = 5.0,
                          scale: float = 100.0,
                          layer: str = "细实线",
                          tracker=None):
    """绘制修订云线（沿线段的连续弧线）。

    参数:
        points: 云线路径点（多边形顶点），按顺序连接
        arc_radius: 弧半径（图纸 mm）
    """
    s = scale
    r = arc_radius * s

    if len(points) < 2:
        return

    # 闭合路径
    pts = [_r(*p) for p in points]
    # 自动闭合
    if math.hypot(pts[0][0] - pts[-1][0], pts[0][1] - pts[-1][1]) > r:
        pts.append(pts[0])

    for i in range(len(pts) - 1):
        x1, y1 = pts[i]
        x2, y2 = pts[i + 1]

        dx, dy = x2 - x1, y2 - y1
        seg_len = math.hypot(dx, dy)
        if seg_len == 0:
            continue

        ux, uy = dx / seg_len, dy / seg_len
        perp_x, perp_y = -uy, ux

        # 沿线段均匀放置弧段
        step = r * 1.2  # 弧段间距略大于半径
        n_arcs = max(1, int(seg_len / step))
        actual_step = seg_len / n_arcs

        for j in range(n_arcs):
            # 弧段中心
            cx = x1 + ux * (j * actual_step + actual_step / 2)
            cy = y1 + uy * (j * actual_step + actual_step / 2)

            # 弧段方向交替（正反弧交替制造云朵效果）
            sign = 1 if j % 2 == 0 else -1
            arc_cx = cx + perp_x * r * sign * 0.3
            arc_cy = cy + perp_y * r * sign * 0.3

            # 绘制圆弧（180°）
            start_ang = math.degrees(math.atan2(-perp_y * sign, -perp_x * sign))
            end_ang = start_ang + 180

            try:
                msp.add_arc((arc_cx, arc_cy), radius=r * 0.9,
                             start_angle=start_ang, end_angle=end_ang,
                             dxfattribs={"layer": layer})
            except Exception as _e:
                print(f'[WARNING] markup.py: {_e}')

    if tracker:
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        tracker.register(min(xs) - r, min(ys) - r,
                         max(xs) + r, max(ys) + r, margin=10)


def draw_revision_cloud_rect(msp, origin, width: float, height: float,
                              arc_radius: float = 5.0,
                              scale: float = 100.0,
                              layer: str = "细实线",
                              tracker=None):
    """矩形区域修订云线（简化接口）。

    参数:
        origin: 矩形左下角 (x, y)
        width/height: 矩形尺寸（图纸 mm）
    """
    s = scale
    ox, oy = _r(*origin)
    w = width * s
    h = height * s

    rect_pts = [(ox, oy), (ox + w, oy), (ox + w, oy + h), (ox, oy + h)]

    draw_revision_cloud(msp, rect_pts, arc_radius=arc_radius,
                         scale=scale, layer=layer, tracker=tracker)

    return (ox + w, oy + h)


# ══════════════════════════════════════════════════════════
#  变更三角标记
# ══════════════════════════════════════════════════════════

def draw_revision_triangle(msp, point, rev_no: int = 1,
                            scale: float = 100.0,
                            description: str = "",
                            layer: str = "细实线",
                            tracker=None):
    """绘制变更三角（图纸修订标记，△1 △2）。

    参数:
        point: 三角顶点位置 (x, y)
        rev_no: 修订编号
        description: 变更描述文字
    """
    s = scale
    tx, ty = _r(*point)
    tri_w = 6.0 * s
    tri_h = 6.0 * s

    # 等边三角（顶点朝上）
    pts = [(tx, ty), (tx - tri_w / 2, ty - tri_h), (tx + tri_w / 2, ty - tri_h)]
    msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": layer})

    # 编号
    txt_h = 2.8 * s
    t = msp.add_text(str(rev_no), dxfattribs={
        "layer": "文字", "height": txt_h, "style": "ENG",
    })
    t.set_placement((tx, ty - tri_h * 0.4),
                    align=TextEntityAlignment.MIDDLE_CENTER)

    # 描述
    if description:
        t2 = msp.add_text(description, dxfattribs={
            "layer": "文字", "height": 2.0 * s, "style": "HZ",
        })
        t2.set_placement((tx + tri_w / 2 + 2 * s, ty - tri_h * 0.6),
                         align=TextEntityAlignment.MIDDLE_LEFT)

    if tracker:
        tracker.register(tx - tri_w - 10 * s, ty - tri_h - 5 * s,
                         tx + tri_w + 15 * s, ty + 2 * s, margin=10)

    return (tx + tri_w / 2, ty - tri_h)


# ══════════════════════════════════════════════════════════
#  审查意见框
# ══════════════════════════════════════════════════════════

def draw_review_comment(msp, origin, comment: str,
                         reviewer: str = "",
                         date: str = "",
                         width: float = 60.0,
                         scale: float = 100.0,
                         status: str = "open",
                         layer: str = "细实线",
                         tracker=None) -> Tuple[float, float]:
    """审查意见标注框。

    参数:
        origin: 左上角 (x, y)
        comment: 审查意见内容
        reviewer: 审查人
        date: 日期
        status: "open"/"resolved"/"rejected"
    """
    s = scale
    ox, oy = _r(*origin)
    w = width * s
    txt_h = 2.5 * s
    pad = 2.0 * s

    # 状态颜色（通过线型/线宽表达）
    status_lw = {"open": 30, "resolved": 18, "rejected": 50}.get(status, 18)

    cur_y = oy

    # 标题行
    status_label = {"open": "【待处理】", "resolved": "【已处理】",
                     "rejected": "【驳回】"}.get(status, "【审查意见】")
    t = msp.add_text(status_label, dxfattribs={
        "layer": "文字-标题", "height": 3.0 * s, "style": "HZ",
    })
    t.set_placement((ox + pad, cur_y - pad),
                    align=TextEntityAlignment.MIDDLE_LEFT)
    cur_y -= 4.5 * s

    # 审查内容
    from .notes import draw_text_block as _tb
    _, block_bottom = _tb(msp, (ox + pad, cur_y), comment,
                           width=width - pad * 2 / s, scale=scale,
                           txt_height=txt_h / s, layer="文字", align="left",
                           tracker=tracker)
    cur_y = block_bottom - 3 * s

    # 审查人 + 日期
    info_line = f"{reviewer}  {date}" if reviewer or date else ""
    if info_line:
        t = msp.add_text(info_line, dxfattribs={
            "layer": "文字", "height": 2.0 * s, "style": "HZ",
        })
        t.set_placement((ox + w - pad, cur_y),
                        align=TextEntityAlignment.MIDDLE_RIGHT)
        cur_y -= 3.5 * s

    # 外框
    box_h = oy - cur_y
    msp.add_lwpolyline(
        [(ox, oy), (ox + w, oy), (ox + w, oy - box_h), (ox, oy - box_h)],
        close=True,
        dxfattribs={"layer": layer, "lineweight": status_lw}
    )

    if tracker:
        tracker.register(ox, oy - box_h, ox + w, oy, margin=15)

    return (ox + w, oy - box_h)


# ══════════════════════════════════════════════════════════
#  图纸版本修订记录
# ══════════════════════════════════════════════════════════

def draw_revision_history(msp, origin, revisions: List[dict],
                           scale: float = 100.0,
                           layer_grid: str = "细实线",
                           layer_text: str = "文字",
                           layer_header: str = "粗实线",
                           tracker=None):
    """图纸修订记录表。

    参数:
        revisions: [{"rev":"A","date":"2026-07-30","desc":"首次发布",
                      "by":"张三","approved":"李四"}, ...]
    """
    s = scale
    ox, oy = _r(*origin)

    cols = [
        ("版本", 8.0, "center"),
        ("日期", 14.0, "center"),
        ("修改说明", 36.0, "left"),
        ("修改", 10.0, "center"),
        ("批准", 10.0, "center"),
    ]

    col_w = [c[1] * s for c in cols]
    total_w = sum(col_w)
    row_h = 7.0 * s
    txt_h = 2.3 * s

    _markup_cell(msp, ox, oy - row_h, total_w, row_h,
                 "修订记录", "center", 3.0 * s, layer_grid, layer_text,
                 bold_layer=layer_header)
    cur_y = oy - row_h

    # 表头
    cx = ox
    for i, (name, _, align) in enumerate(cols):
        _markup_cell(msp, cx, cur_y - row_h, col_w[i], row_h, name,
                     "center", 2.5 * s, layer_grid, layer_text)
        cx += col_w[i]
    cur_y -= row_h

    # 数据（从旧到新）
    for rev in revisions:
        vals = [
            str(rev.get("rev", "")),
            str(rev.get("date", "")),
            str(rev.get("desc", "")),
            str(rev.get("by", "")),
            str(rev.get("approved", "")),
        ]
        cx = ox
        for i, val in enumerate(vals):
            _markup_cell(msp, cx, cur_y - row_h, col_w[i], row_h, val,
                         cols[i][2], txt_h, layer_grid, layer_text)
            cx += col_w[i]
        cur_y -= row_h

    msp.add_lwpolyline(
        [(ox, oy - row_h), (ox + total_w, oy - row_h),
         (ox + total_w, cur_y), (ox, cur_y)],
        close=True, dxfattribs={"layer": layer_header}
    )

    return (ox + total_w, cur_y)


def _markup_cell(msp, x0, y0, w, h, text, align, txt_h,
                 layer_grid, layer_text, bold_layer=None):
    """标记表格单元格。"""
    layer = bold_layer if bold_layer else layer_grid
    msp.add_lwpolyline(
        [(x0, y0), (x0 + w, y0), (x0 + w, y0 + h), (x0, y0 + h)],
        close=True, dxfattribs={"layer": layer})
    if not text:
        return
    alignment = {
        "left": TextEntityAlignment.MIDDLE_LEFT,
        "center": TextEntityAlignment.MIDDLE_CENTER,
        "right": TextEntityAlignment.MIDDLE_RIGHT,
    }.get(align, TextEntityAlignment.MIDDLE_CENTER)
    if align == "left":
        px = x0 + 1.0 * txt_h
    elif align == "right":
        px = x0 + w - 1.0 * txt_h
    else:
        px = x0 + w / 2
    py = y0 + h / 2
    t = msp.add_text(str(text), dxfattribs={
        "layer": layer_text, "height": txt_h, "style": "HZ",
    })
    t.set_placement((px, py), align=alignment)
