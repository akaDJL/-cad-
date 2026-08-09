"""高级标注工具 v1.0 — 坐标标注、角度标注、链式/基线标注、半径/直径引出。

【注意：dimensions ≠ dim】本模块做"标注"（Annotation），不管"公差"（Tolerance）。
如需尺寸公差（±偏差/配合公差 H7/g6），请用 `standards.dim`。

纯 ezdxf，零新依赖。
"""
from __future__ import annotations

import math
from typing import List, Optional, Tuple

from ezdxf.enums import TextEntityAlignment
from ..utils import _r, _tri


# ══════════════════════════════════════════════════════════
#  坐标标注（Ordinate Dimension）
# ══════════════════════════════════════════════════════════

def draw_ordinate(msp, point, origin: Tuple[float, float],
                   axis: str = "x",
                   scale: float = 100.0,
                   label: str = "",
                   layer: str = "尺寸标注",
                   tracker=None):
    """坐标标注（从参考零点起的绝对坐标）。

    参数:
        point: 标注点 (x, y)
        origin: 坐标零点 (ox, oy)
        axis: "x" 或 "y"
        label: 覆盖标注文字（空 = 自动计算）
    """
    s = scale
    px, py = _r(*point)
    ox, oy = _r(*origin)

    if axis == "x":
        dist = abs(px - ox)
        val = label or f"{dist / s:.0f}"
        # 竖线 + 横线（┬ 形）
        msp.add_line((px, py), (px, py - 6 * s),
                     dxfattribs={"layer": layer})
        msp.add_line((px, py - 6 * s), (ox, py - 6 * s),
                     dxfattribs={"layer": layer, "linetype": "DASHED"})
        # 文字在横线上
        tx = (px + ox) / 2
        ty = py - 9 * s
    else:
        dist = abs(py - oy)
        val = label or f"{dist / s:.0f}"
        msp.add_line((px, py), (px - 6 * s, py),
                     dxfattribs={"layer": layer})
        msp.add_line((px - 6 * s, py), (px - 6 * s, oy),
                     dxfattribs={"layer": layer, "linetype": "DASHED"})
        tx = px - 9 * s
        ty = (py + oy) / 2

    txt_h = 2.8 * s
    t = msp.add_text(val, dxfattribs={
        "layer": "文字", "height": txt_h, "style": "ENG",
    })
    t.set_placement((tx, ty), align=TextEntityAlignment.MIDDLE_CENTER)

    if tracker:
        tracker.register(min(px, ox) - 5 * s, min(py, oy) - 10 * s,
                         max(px, ox) + 5 * s, max(py, oy) + 5 * s, margin=20)

    return (tx, ty)


def draw_ordinate_grid(msp, points: List[Tuple[float, float]],
                        origin: Tuple[float, float],
                        axis: str = "x",
                        scale: float = 100.0,
                        layer: str = "尺寸标注",
                        tracker=None):
    """批量坐标标注（沿一条轴线标注多个点）。"""
    results = []
    for pt in points:
        r = draw_ordinate(msp, pt, origin, axis=axis, scale=scale,
                           layer=layer, tracker=tracker)
        results.append(r)
    return results


# ══════════════════════════════════════════════════════════
#  角度标注
# ══════════════════════════════════════════════════════════

def draw_angular(msp, vertex, arm1, arm2,
                  radius: float = 15.0,
                  scale: float = 100.0,
                  label: str = "",
                  layer: str = "尺寸标注",
                  tracker=None):
    """角度标注。

    参数:
        vertex: 角顶点 (x, y)
        arm1: 第一条边上的一点 (x, y)
        arm2: 第二条边上的一点 (x, y)
        radius: 标注弧半径（图纸 mm）
        label: 覆盖文字（空 = 自动计算角度）
    """
    s = scale
    vx, vy = _r(*vertex)
    a1x, a1y = _r(*arm1)
    a2x, a2y = _r(*arm2)

    r = radius * s

    # 计算两条边的角度
    ang1 = math.atan2(a1y - vy, a1x - vx)
    ang2 = math.atan2(a2y - vy, a2x - vx)

    # 确保逆时针
    if ang2 < ang1:
        ang2 += 2 * math.pi

    # 标注弧
    start_deg = math.degrees(ang1)
    end_deg = math.degrees(ang2)

    msp.add_arc((vx, vy), radius=r, start_angle=start_deg,
                 end_angle=end_deg, dxfattribs={"layer": layer})

    # 角度数值
    angle_deg = end_deg - start_deg
    if label:
        val = label
    else:
        val = f"{angle_deg:.1f}°"

    # 文字放在弧中点外侧
    mid_ang = math.radians((start_deg + end_deg) / 2)
    txt_r = r + 4 * s
    tx = vx + txt_r * math.cos(mid_ang)
    ty = vy + txt_r * math.sin(mid_ang)

    txt_h = 2.8 * s
    t = msp.add_text(val, dxfattribs={
        "layer": "文字", "height": txt_h, "style": "ENG",
    })
    t.set_placement((tx, ty), align=TextEntityAlignment.MIDDLE_CENTER)

    if tracker:
        tracker.register(vx - r - 5 * s, vy - r - 5 * s,
                         vx + r + 5 * s, vy + r + 5 * s, margin=20)

    return (tx, ty)


# ══════════════════════════════════════════════════════════
#  链式 / 基线标注
# ══════════════════════════════════════════════════════════

def draw_chain_dimension(msp, points: List[Tuple[float, float]],
                          offset: float = 12.0,
                          scale: float = 100.0,
                          layer: str = "尺寸标注",
                          tracker=None):
    """链式标注（相邻两两标注）。

    参数:
        points: 标注点序列 [(x1,y1),(x2,y2),...]
        offset: 尺寸线偏移距离（图纸 mm）
    """
    s = scale
    off = offset * s

    if len(points) < 2:
        return []

    # 判断方向
    x0, y0 = points[0]
    xn, yn = points[-1]
    horizontal = abs(xn - x0) > abs(yn - y0)

    results = []
    for i in range(len(points) - 1):
        p1x, p1y = _r(*points[i])
        p2x, p2y = _r(*points[i + 1])

        if horizontal:
            # 水平链式
            ly = min(p1y, p2y) - off - i * 2 * s
            msp.add_line((p1x, ly), (p2x, ly), dxfattribs={"layer": layer})
            # 尺寸界线
            if i == 0:
                msp.add_line((p1x, p1y), (p1x, ly), dxfattribs={"layer": layer})
            msp.add_line((p2x, p2y), (p2x, ly), dxfattribs={"layer": layer})

            dist = abs(p2x - p1x) / s
            mx = (p1x + p2x) / 2
            my = ly - 2 * s
        else:
            lx = min(p1x, p2x) - off - i * 2 * s
            msp.add_line((lx, p1y), (lx, p2y), dxfattribs={"layer": layer})
            if i == 0:
                msp.add_line((p1x, p1y), (lx, p1y), dxfattribs={"layer": layer})
            msp.add_line((p2x, p2y), (lx, p2y), dxfattribs={"layer": layer})

            dist = abs(p2y - p1y) / s
            mx = lx - 3 * s
            my = (p1y + p2y) / 2

        txt_h = 2.5 * s
        t = msp.add_text(f"{dist:.0f}", dxfattribs={
            "layer": "文字", "height": txt_h, "style": "ENG",
        })
        t.set_placement((mx, my), align=TextEntityAlignment.MIDDLE_CENTER)
        results.append((mx, my))

    return results


def draw_baseline_dimension(msp, base: Tuple[float, float],
                             points: List[Tuple[float, float]],
                             offset: float = 12.0,
                             gap: float = 6.0,
                             scale: float = 100.0,
                             layer: str = "尺寸标注",
                             tracker=None):
    """基线标注（从共同基准到各点的距离）。

    参数:
        base: 基准点 (x, y)
        points: 标注目标点序列
        gap: 各标注线之间的间距（图纸 mm）
    """
    s = scale
    off = offset * s
    g = gap * s
    bx, by = _r(*base)

    # 判断方向
    if len(points) < 1:
        return []

    px0, py0 = points[0]
    horizontal = abs(px0 - bx) > abs(py0 - by)

    results = []
    for i, pt in enumerate(points):
        px, py = _r(*pt)

        if horizontal:
            ly = min(by, py) - off - i * g
            msp.add_line((bx, ly), (px, ly), dxfattribs={"layer": layer})
            msp.add_line((bx, by), (bx, ly), dxfattribs={"layer": layer})
            msp.add_line((px, py), (px, ly), dxfattribs={"layer": layer})

            dist = abs(px - bx) / s
            mx = (bx + px) / 2
            my = ly - 2 * s
        else:
            lx = min(bx, px) - off - i * g
            msp.add_line((lx, by), (lx, py), dxfattribs={"layer": layer})
            msp.add_line((bx, by), (lx, by), dxfattribs={"layer": layer})
            msp.add_line((px, py), (lx, py), dxfattribs={"layer": layer})

            dist = abs(py - by) / s
            mx = lx - 3 * s
            my = (by + py) / 2

        txt_h = 2.5 * s
        t = msp.add_text(f"{dist:.0f}", dxfattribs={
            "layer": "文字", "height": txt_h, "style": "ENG",
        })
        t.set_placement((mx, my), align=TextEntityAlignment.MIDDLE_CENTER)
        results.append((mx, my))

    return results


# ══════════════════════════════════════════════════════════
#  半径/直径引出
# ══════════════════════════════════════════════════════════

def draw_radius_dim(msp, arc_center: Tuple[float, float],
                     point_on_arc: Tuple[float, float],
                     scale: float = 100.0,
                     label: str = "",
                     inside: bool = True,
                     layer: str = "尺寸标注",
                     tracker=None):
    """半径标注。

    参数:
        arc_center: 圆弧中心
        point_on_arc: 圆弧上一点
        inside: True = 标注线从圆心指向弧, False = 从弧外指向圆心
        label: 覆盖文字（空 = 自动 R<值>）
    """
    s = scale
    cx, cy = _r(*arc_center)
    px, py = _r(*point_on_arc)

    dx, dy = px - cx, py - cy
    r = math.hypot(dx, dy)

    if r == 0:
        return (cx, cy)

    # 标注线
    if inside:
        msp.add_line((cx, cy), (px, py), dxfattribs={"layer": layer})
    else:
        # 外标注：从弧向外延伸
        ux, uy = dx / r, dy / r
        ex = px + ux * 8 * s
        ey = py + uy * 8 * s
        msp.add_line((px, py), (ex, ey), dxfattribs={"layer": layer})

    # 箭头（弧上端点）
    ux, uy = dx / r, dy / r
    _small_arrow(msp, (px, py), (-ux, -uy) if inside else (ux, uy), s, layer)

    # 标注文字
    val = label or f"R{r / s:.0f}"
    txt_h = 2.8 * s
    tx = px + ux * 5 * s
    ty = py + uy * 5 * s

    t = msp.add_text(val, dxfattribs={
        "layer": "文字", "height": txt_h, "style": "ENG",
    })
    t.set_placement((tx, ty),
                    align=TextEntityAlignment.LEFT if ux >= 0 else TextEntityAlignment.RIGHT)

    if tracker:
        tracker.register(cx - r - 10 * s, cy - r - 10 * s,
                         cx + r + 10 * s, cy + r + 10 * s, margin=30)

    return (tx, ty)


def draw_diameter_dim(msp, circle_center: Tuple[float, float],
                       point_on_circle: Tuple[float, float],
                       scale: float = 100.0,
                       label: str = "",
                       layer: str = "尺寸标注",
                       tracker=None):
    """直径标注（"φ" 引出线）。"""
    s = scale
    cx, cy = _r(*circle_center)
    px, py = _r(*point_on_circle)

    dx, dy = px - cx, py - cy
    r = math.hypot(dx, dy)
    if r == 0:
        return (cx, cy)

    ux, uy = dx / r, dy / r

    # 引出线（从圆心穿过弧到外）
    ex = cx + ux * (r + 8 * s)
    ey = cy + uy * (r + 8 * s)
    msp.add_line((cx, cy), (ex, ey), dxfattribs={"layer": layer})

    # 箭头（弧上）
    apt = (cx + ux * r, cy + uy * r)
    _small_arrow(msp, apt, (ux, uy), s, layer)

    # 文字
    val = label or f"φ{r * 2 / s:.0f}"
    txt_h = 2.8 * s

    # Leader 水平延伸
    hx = ex + (abs(uy) * 6 * s if abs(ux) < 0.7 else 0)
    hy = ey + (abs(ux) * 6 * s if abs(uy) < 0.7 else 0)
    msp.add_line((ex, ey), (hx, hy), dxfattribs={"layer": layer})

    t = msp.add_text(val, dxfattribs={
        "layer": "文字", "height": txt_h, "style": "ENG",
    })
    t.set_placement((hx + 2 * s, hy),
                    align=TextEntityAlignment.MIDDLE_LEFT)

    return (hx, hy)


def _small_arrow(msp, tip, direction, scale, layer):
    """小三角箭头。"""
    tx, ty = tip
    dx, dy = direction
    h = 3.0 * scale
    w = 1.5 * scale
    px, py = -dy * w, dx * w
    pts = [(tx, ty),
           (tx - h * dx + px, ty - h * dy + py),
           (tx - h * dx - px, ty - h * dy - py)]
    try:
        msp.add_solid(pts + [pts[0]], dxfattribs={"layer": layer})
    except Exception as _e:
        msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": layer})
