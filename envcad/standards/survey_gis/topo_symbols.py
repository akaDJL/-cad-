"""23. topo_symbols —— 地形图符号库。

制图依据：
  GB/T 20257.1—2017《国家基本比例尺地图图式 第1部分：1:500 1:1000 1:2000
  地形图图式》——符号形状、尺寸、定位与注记规定。
  GB/T 50001—2017 线宽组与字高系列（图层线宽复用 envcad.standards.layers）。

约定（与 envcad 一致）：modelspace 按实物尺寸绘制；符号尺寸按“图上 mm ×
成图比例分母 scale”换算，故 1:500 图上 2.0mm 的圆 → 实物 2.0*500。

符号尺寸取值说明：GB/T 20257.1 对每个符号给出图上毫米尺寸，envcad 内部
知识库（standards_kb.json）目前未收录测绘图式条目，故下列默认值按图式
常用取值给出，并全部参数化，可由调用方覆盖。
# TODO: verify symbol dimensions against GB/T 20257.1—2017 第4章 符号图表
"""
from __future__ import annotations

import math
from typing import List, Sequence, Tuple

from ._common import (TextEntityAlignment, circle, ensure_doc_ready, line,
                      polyline, solid_fill, text)

# ── 图上尺寸默认值 (mm)，乘 scale 得实物尺寸 ─────────────────
D_TREE_CROWN = 2.0      # 独立树树冠直径
D_TREE_STEM = 1.2       # 独立树树干高
D_CONIFER_W = 2.0       # 针叶树底宽
D_CONIFER_H = 3.0       # 针叶树高
D_SHRUB = 1.6           # 灌木直径
H_TEXT_NOTE = 2.0       # 说明注记字高（图式规定注记不小于 1.75mm）
H_TEXT_NAME = 2.5       # 名称注记字高
D_CONTOUR_GAP = 6.0     # 等高线高程注记断开长度
D_ROAD_CENTER_DASH = 4.0


# ══════════════════════════════════════════════════════════
#  4.8 植被：独立树 / 灌木
# ══════════════════════════════════════════════════════════

def sym_tree(msp, x: float, y: float, scale: float = 500.0,
             kind: str = "broadleaf",
             crown_d: float = D_TREE_CROWN,
             stem_h: float = D_TREE_STEM,
             conifer_w: float = D_CONIFER_W,
             conifer_h: float = D_CONIFER_H,
             shrub_d: float = D_SHRUB,
             label: str = "",
             layer: str = "地形-植被"):
    """独立树/灌木符号（GB/T 20257.1 4.8 植被与土质）。

    kind: "broadleaf" 阔叶独立树 / "conifer" 针叶独立树 /
          "fruit" 果树 / "shrub" 独立灌木
    定位点为符号底部中心（图式 3.3 符号定位规定：几何中心或底部中心）。
    """
    ensure_doc_ready(msp)
    s = scale
    if kind == "conifer":
        w, h = conifer_w * s, conifer_h * s
        polyline(msp, [(x - w / 2, y), (x, y + h), (x + w / 2, y)], layer)
        line(msp, (x, y), (x, y - stem_h * s), layer)
    elif kind == "shrub":
        r = shrub_d * s / 2
        circle(msp, (x, y + r), r, layer)
        for a in (90, 210, 330):
            ar = math.radians(a)
            line(msp, (x + r * math.cos(ar) * 1.0, y + r + r * math.sin(ar)),
                 (x + r * math.cos(ar) * 1.6, y + r + r * math.sin(ar) * 1.6),
                 layer)
    else:  # broadleaf / fruit
        r = crown_d * s / 2
        cy = y + stem_h * s + r
        circle(msp, (x, cy), r, layer)
        line(msp, (x, y), (x, y + stem_h * s), layer)
        if kind == "fruit":
            solid_fill(msp, _dot(x, cy, r * 0.28), layer)
    if label:
        text(msp, label, (x + crown_d * s, y), H_TEXT_NOTE * s,
             align=TextEntityAlignment.MIDDLE_LEFT, layer="地形-注记")
    return (x, y)


def _dot(cx, cy, r, n: int = 8):
    return [(cx + r * math.cos(2 * math.pi * i / n),
             cy + r * math.sin(2 * math.pi * i / n)) for i in range(n)]


# ══════════════════════════════════════════════════════════
#  4.3 居民地及设施：房屋
# ══════════════════════════════════════════════════════════

def sym_building(msp, x: float, y: float, scale: float = 500.0,
                 width: float = 20000.0, depth: float = 12000.0,
                 structure: str = "混", floors: int = 3,
                 under: int = 0,
                 permanent: bool = True,
                 text_h: float = H_TEXT_NOTE,
                 layer: str = "地形-居民地"):
    """依比例尺房屋符号（GB/T 20257.1 4.3 居民地及设施）。

    width/depth 为房屋实物平面尺寸（mm，实物坐标，不乘 scale）。
    结构注记格式：结构代号 + 层数，如 "混3"；有地下室时注 "混3-1"。
    permanent=False 表示简单房屋，图式以细实线（虚线轮廓）表示。
    """
    ensure_doc_ready(msp)
    pts = [(x, y), (x + width, y), (x + width, y + depth), (x, y + depth)]
    polyline(msp, pts, layer if permanent else "细实线", close=True,
             linetype=None if permanent else "DASHED")
    note = f"{structure}{floors}" + (f"-{under}" if under else "")
    text(msp, note, (x + width / 2, y + depth / 2), text_h * scale,
         align=TextEntityAlignment.MIDDLE_CENTER, layer="地形-注记")
    return pts


# ══════════════════════════════════════════════════════════
#  4.4 交通：道路
# ══════════════════════════════════════════════════════════

def sym_road(msp, x: float, y: float, scale: float = 500.0,
             length: float = 40000.0, width: float = 7000.0,
             angle: float = 0.0,
             road_class: str = "等级公路",
             code: str = "",
             show_center: bool = True,
             layer: str = "地形-交通"):
    """道路符号（GB/T 20257.1 4.4 交通）。

    依比例尺道路以双线（路边线）表示，中心线用点画线；
    road_class: "等级公路"/"等外公路"/"机耕路"/"乡村路"。
    length/width 为实物尺寸 mm；angle 为走向（度）。
    """
    ensure_doc_ready(msp)
    a = math.radians(angle)
    ux, uy = math.cos(a), math.sin(a)
    nx, ny = -uy, ux
    half = width / 2
    p0 = (x + nx * half, y + ny * half)
    p1 = (x + ux * length + nx * half, y + uy * length + ny * half)
    q0 = (x - nx * half, y - ny * half)
    q1 = (x + ux * length - nx * half, y + uy * length - ny * half)
    lt = None if road_class in ("等级公路", "等外公路") else "DASHED"
    line(msp, p0, p1, layer, linetype=lt)
    line(msp, q0, q1, layer, linetype=lt)
    if show_center:
        line(msp, (x, y), (x + ux * length, y + uy * length),
             "点画线")
    if code:
        text(msp, code, (x + ux * length / 2, y + uy * length / 2),
             H_TEXT_NAME * scale, align=TextEntityAlignment.MIDDLE_CENTER,
             layer="地形-注记", rotation=angle)
    return [(p0, p1), (q0, q1)]


# ══════════════════════════════════════════════════════════
#  4.7 地貌：等高线与高程注记
# ══════════════════════════════════════════════════════════

def sym_contour(msp, pts: Sequence[Tuple[float, float]],
                scale: float = 500.0,
                elevation: float = 0.0,
                index: bool = False,
                interval: float = 1.0,
                label_pos: float = 0.5,
                text_h: float = H_TEXT_NOTE,
                gap: float = D_CONTOUR_GAP):
    """等高线（GB/T 20257.1 4.7 地貌）。

    index=True 为计曲线（每 5 条首曲线加粗并注记高程，注记字头朝高处，
    图式规定注记处等高线应断开）；否则为首曲线。
    interval 为等高距（m），仅作说明参数。
    """
    ensure_doc_ready(msp)
    layer = "地形-计曲线" if index else "地形-等高线"
    pts = list(pts)
    if not index or len(pts) < 2:
        polyline(msp, pts, layer)
        return layer
    # 计曲线：在 label_pos 处断开并注记高程
    i = max(1, min(len(pts) - 1, int(len(pts) * label_pos)))
    px, py = pts[i]
    dx, dy = pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]
    lg = math.hypot(dx, dy) or 1.0
    ux, uy = dx / lg, dy / lg
    g = gap * scale / 2
    polyline(msp, pts[:i] + [(px - ux * g, py - uy * g)], layer)
    polyline(msp, [(px + ux * g, py + uy * g)] + pts[i:], layer)
    text(msp, f"{elevation:.0f}", (px, py), text_h * scale,
         align=TextEntityAlignment.MIDDLE_CENTER, layer="地形-注记",
         rotation=math.degrees(math.atan2(uy, ux)))
    return layer


# ══════════════════════════════════════════════════════════
#  4.2 水系
# ══════════════════════════════════════════════════════════

def sym_water(msp, x: float, y: float, scale: float = 500.0,
              width: float = 26000.0, height: float = 16000.0,
              kind: str = "pond",
              name: str = "塘",
              water_level: str = "",
              layer: str = "地形-水系"):
    """水系符号（GB/T 20257.1 4.2 水系）。

    kind: "pond" 池塘（依比例尺水涯线 + 水域说明注记）/
          "river" 河流（双线 + 流向箭头）。
    """
    ensure_doc_ready(msp)
    s = scale
    if kind == "river":
        line(msp, (x, y), (x + width, y), layer)
        line(msp, (x, y + height), (x + width, y + height), layer)
        # 流向箭头（图式 4.2 水流方向符号）
        mx, my = x + width / 2, y + height / 2
        line(msp, (mx - 3 * s, my), (mx + 3 * s, my), layer)
        polyline(msp, [(mx + 3 * s, my), (mx + 1.2 * s, my + 0.7 * s),
                       (mx + 1.2 * s, my - 0.7 * s)], layer, close=True)
    else:
        polyline(msp, [(x, y), (x + width, y), (x + width, y + height),
                       (x, y + height)], layer, close=True)
        # 水域面状说明注记（图式规定水系注记用左斜宋体，此处以 HZ 代替）
        text(msp, name, (x + width / 2, y + height / 2), H_TEXT_NAME * s,
             align=TextEntityAlignment.MIDDLE_CENTER, layer="地形-水系")
    if water_level:
        text(msp, water_level, (x, y - 2.5 * s), H_TEXT_NOTE * s,
             align=TextEntityAlignment.MIDDLE_LEFT, layer="地形-注记")
    return (x, y, x + width, y + height)


# ══════════════════════════════════════════════════════════
#  符号库总装：图例式排布
# ══════════════════════════════════════════════════════════

SYMBOL_CATALOG = [
    ("broadleaf", "阔叶独立树"),
    ("conifer", "针叶独立树"),
    ("fruit", "果树"),
    ("shrub", "独立灌木"),
    ("building", "房屋（混3）"),
    ("road", "等级公路"),
    ("contour", "计曲线/首曲线"),
    ("water", "池塘"),
]


def draw_topo_symbols(msp, x: float, y: float, scale: float = 50.0,
                      items: List[str] | None = None,
                      col_w: float = 60.0, row_h: float = 26.0,
                      cols: int = 2,
                      title: str = "地形图符号库（GB/T 20257.1—2017）",
                      title_h: float = 4.0,
                      show_title: bool = True,
                      **params):
    """绘制地形图符号库图例表。

    参数（全部可覆盖）：
        items: 需绘制的符号键列表，默认全部 SYMBOL_CATALOG。
        col_w / row_h: 图例格宽高（图上 mm，乘 scale）。
        cols: 列数。
    返回图例整体包围盒 (x0, y0, x1, y1)。
    """
    ensure_doc_ready(msp)
    s = scale
    keys = items or [k for k, _ in SYMBOL_CATALOG]
    names = dict(SYMBOL_CATALOG)
    cw, rh = col_w * s, row_h * s
    rows = (len(keys) + cols - 1) // cols
    top = y
    if show_title:
        text(msp, title, (x, y + 6 * s), title_h * s,
             align=TextEntityAlignment.MIDDLE_LEFT, layer="文字-标题")
        top = y

    for i, key in enumerate(keys):
        c, r = i % cols, i // cols
        cx = x + c * cw
        cy = top - r * rh
        # 图例格
        polyline(msp, [(cx, cy - rh), (cx + cw, cy - rh),
                       (cx + cw, cy), (cx, cy)], "细实线", close=True)
        sx = cx + cw * 0.22
        sy = cy - rh * 0.72
        if key in ("broadleaf", "conifer", "fruit", "shrub"):
            sym_tree(msp, sx, sy, s, kind=key)
        elif key == "building":
            sym_building(msp, cx + cw * 0.08, cy - rh * 0.75, s,
                         width=cw * 0.30, depth=rh * 0.50)
        elif key == "road":
            sym_road(msp, cx + cw * 0.06, cy - rh * 0.5, s,
                     length=cw * 0.34, width=rh * 0.30)
        elif key == "contour":
            base = cy - rh * 0.72
            sym_contour(msp, [(cx + cw * 0.06 + k * cw * 0.07,
                               base + math.sin(k * 0.9) * rh * 0.10)
                              for k in range(5)], s, index=False)
            sym_contour(msp, [(cx + cw * 0.06 + k * cw * 0.07,
                               base + rh * 0.28 + math.sin(k * 0.9) * rh * 0.10)
                              for k in range(5)], s, elevation=105,
                        index=True, gap=3.0)
        elif key == "water":
            sym_water(msp, cx + cw * 0.06, cy - rh * 0.78, s,
                      width=cw * 0.32, height=rh * 0.56)
        text(msp, names.get(key, key), (cx + cw * 0.52, cy - rh * 0.5),
             H_TEXT_NAME * s, align=TextEntityAlignment.MIDDLE_LEFT,
             layer="文字")

    return (x, top - rows * rh, x + cols * cw, top)
