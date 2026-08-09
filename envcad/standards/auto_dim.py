"""自动尺寸链引擎——给定一组点，自动生成链式/基线/坐标标注。

施工图深度第1项：让尺寸标注不再手写。
"""
from __future__ import annotations
import math
from typing import List, Tuple, Optional
from ..utils import _r


def auto_chain_dim(msp, points: List[Tuple[float, float]],
                   offset: float = 15.0, scale: float = 100.0,
                   dim_layer="尺寸标注", txt_layer="文字",
                   tracker=None) -> List:
    """自动链式标注。points 按顺序排列的测量点。"""
    from .dim import draw_dimension
    s = scale; off = offset * s
    # 计算主方向（最长拟合线）
    n = len(points)
    if n < 2:
        return []
    # 取首尾方向为标注方向
    dx = points[-1][0] - points[0][0]
    dy = points[-1][1] - points[0][1]
    length = math.hypot(dx, dy)
    if length < 1e-6:
        return []
    ux, uy = dx / length, dy / length  # 方向单位向量
    px, py = -uy, ux  # 垂直方向（标注偏移方向）

    entities = []
    # 链式标注：相邻点间标注
    for i in range(n - 1):
        p1 = points[i]; p2 = points[i + 1]
        # 距起点
        d1 = (p1[0] - points[0][0]) * ux + (p1[1] - points[0][1]) * uy
        d2 = (p2[0] - points[0][0]) * ux + (p2[1] - points[0][1]) * uy
        dist = abs(d2 - d1)
        # 标注偏移
        ox1, _ = _r(p1[0] + px * off, p1[1] + py * off)
        ox2, _ = _r(p2[0] + px * off, p2[1] + py * off)
        draw_dimension(msp, (p1[0] + px * off, p1[1] + py * off),
                       (p2[0] + px * off, p2[1] + py * off), offset=off, scale=s,
                       text=f"{dist:.0f}", dimstyle="Standard",
                       layer=dim_layer, tracker=tracker)
    return entities


def auto_baseline_dim(msp, base: Tuple[float, float],
                      points: List[Tuple[float, float]],
                      offset: float = 20.0, scale: float = 100.0,
                      dim_layer="尺寸标注", tracker=None) -> List:
    """自动基线标注。base 为基准点，points 为测量点列表。"""
    from .dim import draw_dimension
    s = scale; off = offset * s
    entities = []
    # 计算方向
    if len(points) < 1:
        return []
    # 分垂直/水平
    cbx, cby = base if isinstance(base, tuple) else (base, base)
    for p in points:
        px, py = _r(*p)
        dist = math.hypot(px - cbx, py - cby)
        draw_dimension(msp, (cbx, cby), (px, py),
                       offset=off, scale=s,
                       text=f"{dist:.0f}",
                       dimstyle="Standard",
                       layer=dim_layer, tracker=tracker)
    return entities


def auto_ordinate_dim(msp, points: List[Tuple[float, float]],
                      origin: Optional[Tuple[float, float]] = None,
                      offset: float = 15.0, scale: float = 100.0,
                      dim_layer="尺寸标注", tracker=None) -> List:
    """自动坐标标注。origin 默认为 points[0]。"""
    from .dimensions import draw_ordinate
    if not points:
        return []
    if origin is None:
        origin = points[0]
    s = scale; off = offset * s
    entities = []
    for p in points:
        draw_ordinate(msp, p, origin, offset=off, scale=s,
                      layer=dim_layer)
    return entities


def auto_smart_dim(msp, outline: List[Tuple[float, float]],
                   scale: float = 100.0, dim_layer="尺寸标注",
                   tracker=None) -> dict:
    """智能标注：自动识别轮廓的最小包围盒，标注总长/总宽+关键分段。

    outline: 多边形顶点列表（任意形状）
    返回: {"width", "height", "entities"} 标注信息字典
    """
    s = scale
    xs = [p[0] for p in outline]
    ys = [p[1] for p in outline]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    w = max_x - min_x
    h = max_y - min_y

    from .dim import draw_dimension
    entities = []
    # 底部：总长标注
    off = 12 * s
    draw_dimension(msp, (min_x, min_y - off), (max_x, min_y - off),
                   offset=off * 0., scale=s, text=f"{w:.0f}",
                   dimstyle="Standard", layer=dim_layer)
    # 侧面：总高标注
    draw_dimension(msp, (max_x + off, max_y), (max_x + off, min_y),
                   offset=off * 0., scale=s, text=f"{h:.0f}",
                   dimstyle="Standard", layer=dim_layer)
    # 如果 outline 是矩形，加中间分段
    if len(outline) == 4 or (len(outline) >= 4 and
                             abs((max_x - min_x) * (max_y - min_y) -
                                 _polygon_area(outline, min_x, min_y)) < 0.1 * w * h):
        mid_x = (min_x + max_x) / 2
        mid_y = (min_y + max_y) / 2
        draw_dimension(msp, (min_x, min_y - off * 2), (mid_x, min_y - off * 2),
                       offset=off * 0., scale=s, text=f"{w/2:.0f}",
                       dimstyle="Standard", layer=dim_layer)
        draw_dimension(msp, (mid_x, min_y - off * 2), (max_x, min_y - off * 2),
                       offset=off * 0., scale=s, text=f"{w/2:.0f}",
                       dimstyle="Standard", layer=dim_layer)

    return {"width": w, "height": h, "entities": entities}


def _polygon_area(outline, min_x, min_y):
    """简单矩形面积检测——假设是近轴矩形。"""
    xs = [p[0] for p in outline]
    ys = [p[1] for p in outline]
    return (max(xs) - min(xs)) * (max(ys) - min(ys))
