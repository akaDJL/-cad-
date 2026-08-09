"""27. boundary —— 红线 / 用地图（用地界址范围）。

制图依据：
  GB/T 50001—2017《房屋建筑制图统一标准》——图框、标题栏、线宽与字高
  GB/T 50103—2010《总图制图标准》——用地红线（粗实线）、道路红线、
    建筑控制线（用地范围线的线型与表示方法）
  GB/T 20257.1—2017 4.6 境界（界址点、界线的符号与注记）
  # TODO: verify 界址点符号直径 against GB/T 20257.1—2017 4.6 / 地籍图图式

复用 envcad 既有实现：
  · envcad.standards.frame.draw_frame —— A3 国标图框（经平移复用）
  · envcad.standards.layers / styles —— 国标图层与仿宋 GB2312 文字样式
  · envcad.standards.annotate.draw_leader —— 面积/用地性质引出标注

约定：坐标为实物毫米（modelspace 1:1），面积按 m² 输出。
"""
from __future__ import annotations

import math
from typing import List, Sequence, Tuple

from ._common import (FrameInfo, TextEntityAlignment, circle, draw_frame_at,
                      draw_leader, ensure_doc_ready, line, polyline,
                      solid_fill, text)

# ── 图上尺寸默认值 (mm) ───────────────────────────────────
D_CORNER = 1.4       # 界址点符号直径
H_CORNER_TAG = 2.5   # 界址点编号字高
H_EDGE = 2.5         # 边长注记字高
H_AREA = 3.5         # 面积注记字高
H_TABLE = 2.5        # 坐标表字高
TABLE_ROW_H = 6.0
TABLE_COL_W = (14.0, 26.0, 26.0)   # 点号 / X / Y
OFFSET_EDGE = 2.0    # 边长注记离边线距离
SETBACK_DEFAULT = 6000.0   # 建筑控制线退让（实物 mm）


def polygon_area(pts: Sequence[Tuple[float, float]]) -> float:
    """多边形面积（鞋带公式），输入 mm，返回 m²。"""
    n = len(pts)
    if n < 3:
        return 0.0
    a = 0.0
    for i in range(n):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % n]
        a += x1 * y2 - x2 * y1
    return abs(a) / 2.0 / 1e6


def offset_polygon(pts: Sequence[Tuple[float, float]], d: float
                   ) -> List[Tuple[float, float]]:
    """简易向内等距偏移（按顶点向形心方向收缩），用于建筑控制线示意。"""
    n = len(pts)
    cx = sum(p[0] for p in pts) / n
    cy = sum(p[1] for p in pts) / n
    out = []
    for px, py in pts:
        vx, vy = cx - px, cy - py
        lg = math.hypot(vx, vy) or 1.0
        out.append((px + vx / lg * d, py + vy / lg * d))
    return out


def draw_boundary_polygon(msp, pts: Sequence[Tuple[float, float]],
                          scale: float = 50.0,
                          layer: str = "用地红线",
                          closed: bool = True):
    """用地红线多边形（GB/T 50103—2010：用地红线用粗实线表示）。"""
    ensure_doc_ready(msp)
    return polyline(msp, pts, layer, close=closed)


def draw_corner_points(msp, pts: Sequence[Tuple[float, float]],
                       scale: float = 50.0,
                       prefix: str = "J",
                       start_no: int = 1,
                       dia: float = D_CORNER,
                       tag_h: float = H_CORNER_TAG,
                       layer: str = "界址点",
                       tag_layer: str = "控制点注记"):
    """界址点符号 + 点号注记（GB/T 20257.1 4.6 境界）。"""
    ensure_doc_ready(msp)
    s = scale
    r = dia * s / 2
    n = len(pts)
    cx = sum(p[0] for p in pts) / n
    cy = sum(p[1] for p in pts) / n
    names = []
    for i, (px, py) in enumerate(pts):
        circle(msp, (px, py), r, layer)
        solid_fill(msp, [(px + r * 0.45 * math.cos(a),
                          py + r * 0.45 * math.sin(a))
                         for a in [k * math.pi / 5 for k in range(10)]], layer)
        # 点号注在背离形心一侧，避免压盖界线
        vx, vy = px - cx, py - cy
        lg = math.hypot(vx, vy) or 1.0
        tx = px + vx / lg * r * 3.0
        ty = py + vy / lg * r * 3.0
        name = f"{prefix}{start_no + i}"
        names.append(name)
        text(msp, name, (tx, ty), tag_h * s,
             align=TextEntityAlignment.MIDDLE_CENTER, layer=tag_layer)
    return names


def draw_edge_dims(msp, pts: Sequence[Tuple[float, float]],
                   scale: float = 50.0,
                   text_h: float = H_EDGE,
                   offset: float = OFFSET_EDGE,
                   decimals: int = 2,
                   layer: str = "文字",
                   closed: bool = True):
    """界址边长注记（m，沿边线方向书写，注于界线外侧）。"""
    ensure_doc_ready(msp)
    s = scale
    n = len(pts)
    cx = sum(p[0] for p in pts) / n
    cy = sum(p[1] for p in pts) / n
    rng = n if closed else n - 1
    lens = []
    for i in range(rng):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % n]
        dx, dy = x2 - x1, y2 - y1
        L = math.hypot(dx, dy)
        lens.append(L / 1000.0)
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        nx, ny = -dy / (L or 1), dx / (L or 1)
        if (mx + nx - cx) ** 2 + (my + ny - cy) ** 2 < (mx - cx) ** 2 + (my - cy) ** 2:
            nx, ny = -nx, -ny   # 保证注记在外侧
        ang = math.degrees(math.atan2(dy, dx))
        if ang > 90 or ang <= -90:
            ang += 180
        text(msp, f"{L / 1000.0:.{decimals}f}",
             (mx + nx * offset * s, my + ny * offset * s), text_h * s,
             align=TextEntityAlignment.MIDDLE_CENTER, layer=layer,
             rotation=ang)
    return lens


def draw_coord_table(msp, x: float, y: float, scale: float = 50.0,
                     rows: Sequence[Tuple[str, float, float]] = (),
                     row_h: float = TABLE_ROW_H,
                     col_w: Sequence[float] = TABLE_COL_W,
                     text_h: float = H_TABLE,
                     title: str = "界址点坐标表（2000国家大地坐标系）",
                     decimals: int = 3,
                     layer_grid: str = "细实线",
                     layer_text: str = "文字"):
    """界址点坐标成果表（左上角定位于 (x, y)）。"""
    ensure_doc_ready(msp)
    s = scale
    cw = [c * s for c in col_w]
    w = sum(cw)
    rh = row_h * s
    n = len(rows) + 1  # 含表头
    text(msp, title, (x, y + rh * 0.8), text_h * s * 1.1,
         align=TextEntityAlignment.MIDDLE_LEFT, layer="文字-标题")
    top = y
    polyline(msp, [(x, top - n * rh), (x + w, top - n * rh),
                   (x + w, top), (x, top)], layer_grid, close=True)
    for i in range(1, n):
        line(msp, (x, top - i * rh), (x + w, top - i * rh), layer_grid)
    acc = 0.0
    for c in cw[:-1]:
        acc += c
        line(msp, (x + acc, top - n * rh), (x + acc, top), layer_grid)

    hdr = ("点号", "X (m)", "Y (m)")
    for j, htxt in enumerate(hdr):
        text(msp, htxt, (x + sum(cw[:j]) + cw[j] / 2, top - rh / 2),
             text_h * s, align=TextEntityAlignment.MIDDLE_CENTER,
             layer=layer_text)
    for i, (tag, X, Y) in enumerate(rows):
        cy = top - (i + 1.5) * rh
        vals = (tag, f"{X:.{decimals}f}", f"{Y:.{decimals}f}")
        for j, v in enumerate(vals):
            text(msp, v, (x + sum(cw[:j]) + cw[j] / 2, cy), text_h * s,
                 align=TextEntityAlignment.MIDDLE_CENTER, layer=layer_text)
    return (x, top - n * rh, x + w, top)


def draw_boundary(msp, x: float = 0.0, y: float = 0.0, scale: float = 50.0,
                  points: Sequence[Tuple[float, float]] | None = None,
                  land_use: str = "二类居住用地 R2",
                  parcel_no: str = "DK-2026-018",
                  show_frame: bool = False,
                  frame_title: str = "建设用地规划红线图",
                  frame_no: str = "YD-01",
                  show_corner: bool = True,
                  show_edge_dim: bool = True,
                  show_area: bool = True,
                  show_setback: bool = True,
                  setback: float = SETBACK_DEFAULT,
                  show_table: bool = True,
                  table_dx: float = 0.0, table_dy: float = 0.0,
                  base_east: float = 435000.0, base_north: float = 3395000.0,
                  area_h: float = H_AREA,
                  **params):
    """红线/用地图总装。

    points: 界址点相对 (x, y) 的实物毫米坐标，逆时针或顺时针均可。
    base_east/base_north: 用于生成界址点坐标表的测区基准坐标（m）。
    返回 (用地面积 m², 界址点名列表)。
    """
    ensure_doc_ready(msp)
    s = scale
    pts_rel = list(points or [(0, 0), (60000, 0), (60000, 40000), (0, 40000)])
    pts = [(x + dx, y + dy) for dx, dy in pts_rel]

    if show_frame:
        draw_frame_at(msp, 0.0, 0.0, s, FrameInfo(
            title=frame_title, drawing_no=frame_no,
            scale_str=f"1:{int(s)}", project=parcel_no,
            unit="××测绘院", date="2026.07"))

    draw_boundary_polygon(msp, pts, s)

    if show_setback:
        polyline(msp, offset_polygon(pts, setback), "建筑控制线", close=True)

    names = draw_corner_points(msp, pts, s) if show_corner else []
    if show_edge_dim:
        draw_edge_dims(msp, pts, s)

    area = polygon_area(pts)
    if show_area:
        cx = sum(p[0] for p in pts) / len(pts)
        cy = sum(p[1] for p in pts) / len(pts)
        text(msp, parcel_no, (cx, cy + area_h * s * 1.6), area_h * s,
             align=TextEntityAlignment.MIDDLE_CENTER, layer="文字-标题")
        text(msp, land_use, (cx, cy), area_h * s * 0.8,
             align=TextEntityAlignment.MIDDLE_CENTER, layer="文字")
        text(msp, f"用地面积 {area:.2f} m²", (cx, cy - area_h * s * 1.6),
             area_h * s * 0.8, align=TextEntityAlignment.MIDDLE_CENTER,
             layer="文字")

    if show_table:
        rows = [(names[i] if names else f"J{i + 1}",
                 base_north + p[1] / 1000.0, base_east + p[0] / 1000.0)
                for i, p in enumerate(pts_rel)]
        tx = x + (table_dx or (max(p[0] for p in pts_rel) + 12000.0))
        ty = y + (table_dy or max(p[1] for p in pts_rel))
        draw_coord_table(msp, tx, ty, s, rows=rows)

    return (area, names)
