"""24. control_point —— 测量控制点符号与注记。

制图依据：
  GB/T 20257.1—2017《国家基本比例尺地图图式 第1部分》4.1 定位基础
    · 4.1.1 三角点 / 精密导线点（等边三角形，中心为定位点）
    · 4.1.3 导线点（圆内实心点，一、二、三级导线点同符号）
    · 4.1.4 埋石图根点 / 4.1.5 不埋石图根点
    · 水准点、卫星定位（GNSS）等级点
    · 注记规定：符号右方以分数式注出，分子为点名（或点号），
      分母为高程；有比高时，比高注在符号左方。
  GB/T 12898—2009《国家三、四等水准测量规范》——水准点高程等级与
    注记精度（水准点及经水准联测的三角点高程注至 0.001 m；
    三角高程测定的高程注至 0.01 m，见 GB/T 20257.1 4.1 总说明）。

尺寸：图式给出图上毫米尺寸，本模块以“图上 mm × scale”换算为实物坐标，
全部参数化。
# TODO: verify 水准点 / GNSS 点符号图形与尺寸 against GB/T 20257.1—2017 4.1
"""
from __future__ import annotations

import math
from typing import Dict, List, Sequence, Tuple

from ._common import (TextEntityAlignment, circle, ensure_doc_ready,
                      fraction_label, line, polyline, solid_fill, text)

# ── 图上尺寸默认值 (mm) ───────────────────────────────────
D_TRI_SIDE = 3.0        # 三角点等边三角形边长
D_TRAVERSE = 2.0        # 导线点圆直径
D_BENCHMARK = 2.0       # 水准点圆直径
D_GRID_PT = 2.0         # 图根点符号尺寸
D_DOT = 0.5             # 中心实心点直径
H_LABEL = 2.5           # 注记字高（图式规定不小于 1.75mm）
GAP_LABEL = 1.0         # 符号与注记间距

# 点类型 → (中文名, 高程注记小数位)
POINT_TYPES: Dict[str, Tuple[str, int]] = {
    "triangulation": ("三角点", 3),      # 经水准联测，注至 0.001m
    "small_tri": ("小三角点", 2),
    "traverse": ("导线点", 2),
    "benchmark": ("水准点", 3),          # GB/T 12898 三、四等水准
    "gnss": ("卫星定位等级点", 3),
    "grid_stone": ("埋石图根点", 2),
    "grid_free": ("不埋石图根点", 2),
}


def _tri_pts(x: float, y: float, side: float) -> List[Tuple[float, float]]:
    """以 (x,y) 为几何中心的等边三角形顶点（尖端朝上）。"""
    h = side * math.sqrt(3) / 2
    cy = y - h / 3
    return [(x, cy + h), (x - side / 2, cy), (x + side / 2, cy)]


def draw_control_point(msp, x: float, y: float, scale: float = 50.0,
                       pt_type: str = "triangulation",
                       name: str = "",
                       elevation: float | None = None,
                       rel_height: float | None = None,
                       tri_side: float = D_TRI_SIDE,
                       dia: float = D_TRAVERSE,
                       dot_d: float = D_DOT,
                       label_h: float = H_LABEL,
                       gap: float = GAP_LABEL,
                       elev_decimals: int | None = None,
                       show_label: bool = True,
                       layer: str = "测量控制点",
                       label_layer: str = "控制点注记",
                       **params):
    """绘制单个测量控制点符号 + 分数式注记（GB/T 20257.1 4.1）。

    参数:
        pt_type: POINT_TYPES 中的键。
        name: 点名或点号（分子）。
        elevation: 高程 m（分母）；None 则不注高程。
        rel_height: 比高 m，注在符号左方（图式 4.1 注记规定）。
        tri_side/dia/dot_d/label_h/gap: 图上 mm 尺寸，全部可调。
    返回符号定位点 (x, y)。
    """
    ensure_doc_ready(msp)
    s = scale
    side = tri_side * s
    d = dia * s
    r = d / 2

    if pt_type in ("triangulation", "small_tri", "gnss"):
        pts = _tri_pts(x, y, side)
        polyline(msp, pts, layer, close=True)
        if pt_type == "small_tri":
            # 小三角点：三角形内加小圆（区别于国家等级三角点）
            circle(msp, (x, y), side * 0.18, layer)
        elif pt_type == "gnss":
            # 卫星定位等级点：三角形内加内接小三角
            polyline(msp, _tri_pts(x, y, side * 0.45), layer, close=True)
        solid_fill(msp, _circle_pts(x, y, dot_d * s / 2), layer)
        half_w = side / 2
    elif pt_type == "traverse":
        circle(msp, (x, y), r, layer)
        solid_fill(msp, _circle_pts(x, y, dot_d * s / 2), layer)
        half_w = r
    elif pt_type == "benchmark":
        # 水准点：圆 + 十字分象限，对角象限涂黑
        circle(msp, (x, y), r, layer)
        line(msp, (x - r, y), (x + r, y), layer)
        line(msp, (x, y - r), (x, y + r), layer)
        solid_fill(msp, _quadrant(x, y, r, 90, 180), layer)
        solid_fill(msp, _quadrant(x, y, r, 270, 360), layer)
        half_w = r
    elif pt_type == "grid_stone":
        # 埋石图根点：正方形 + 中心点
        a = D_GRID_PT * s / 2
        polyline(msp, [(x - a, y - a), (x + a, y - a),
                       (x + a, y + a), (x - a, y + a)], layer, close=True)
        solid_fill(msp, _circle_pts(x, y, dot_d * s / 2), layer)
        half_w = a
    else:  # grid_free 不埋石图根点：单圆 + 中心点（细）
        circle(msp, (x, y), r * 0.8, layer)
        solid_fill(msp, _circle_pts(x, y, dot_d * s / 2), layer)
        half_w = r * 0.8

    if show_label and (name or elevation is not None):
        dec = elev_decimals
        if dec is None:
            dec = POINT_TYPES.get(pt_type, ("", 2))[1]
        num = str(name) if name else ""
        den = f"{elevation:.{dec}f}" if elevation is not None else ""
        if num and den:
            fraction_label(msp, (x + half_w + gap * s, y), num, den,
                           label_h * s, layer=label_layer)
        elif num or den:
            text(msp, num or den, (x + half_w + gap * s, y), label_h * s,
                 align=TextEntityAlignment.MIDDLE_LEFT, layer=label_layer)

    if rel_height is not None:
        # 比高注在符号左方
        text(msp, f"{rel_height:.1f}", (x - half_w - gap * s, y), label_h * s,
             align=TextEntityAlignment.MIDDLE_RIGHT, layer=label_layer)

    return (x, y)


def _circle_pts(cx, cy, r, n: int = 12):
    return [(cx + r * math.cos(2 * math.pi * i / n),
             cy + r * math.sin(2 * math.pi * i / n)) for i in range(n)]


def _quadrant(cx, cy, r, a0, a1, n: int = 6):
    pts = [(cx, cy)]
    for i in range(n + 1):
        a = math.radians(a0 + (a1 - a0) * i / n)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def draw_control_network(msp, x: float, y: float, scale: float = 50.0,
                         points: Sequence[dict] | None = None,
                         connect: bool = True,
                         net_layer: str = "细实线-辅助",
                         **params):
    """绘制控制网：多个控制点 + 观测边连线（图根导线/三角网示意）。

    points: [{"dx","dy","type","name","elev"}...]，dx/dy 为相对 (x,y) 的
            实物坐标偏移 mm。
    """
    ensure_doc_ready(msp)
    pts = list(points or [])
    coords = []
    for p in pts:
        px, py = x + p.get("dx", 0.0), y + p.get("dy", 0.0)
        coords.append((px, py))
        draw_control_point(msp, px, py, scale,
                           pt_type=p.get("type", "traverse"),
                           name=p.get("name", ""),
                           elevation=p.get("elev"),
                           **{k: v for k, v in p.items()
                              if k in ("tri_side", "dia", "label_h")})
    if connect and len(coords) > 1:
        polyline(msp, coords, net_layer, close=bool(params.get("closed", True)))
    return coords
