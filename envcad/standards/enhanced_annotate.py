# -*- coding: utf-8 -*-
"""增强标注模块 v1.5.1 — 虚实线/材质/公差/箭头 四维补强。

目标：缩小与专业工程制图的标注差距，统一面向所有行业模块。

基于 GB/T 17450（线型）、GB/T 4458.4（尺寸注法）、GB/T 50001（建筑制图）、
GB/T 4459 系列（机械制图特殊表示法）。

功能一览：
  draw_material_callout     材质标注引线（HDPE/混凝土/钢材等）
  draw_pipe_material_mark   管道材质标记（沿线标注）
  draw_dimension_tolerance  尺寸+公差一体化标注
  draw_engineering_arrow    标准工程箭头（实心/空心）
  draw_construction_line    构造辅助线（虚/点画/双点画）
  draw_section_hatch        剖面填充（按材质自动选择填充图案）
  draw_centerline_cross     十字中心线（点画线）
  draw_break_line           折断线
  apply_line_weight         通过颜色映射线宽（打印时生效）
"""

from __future__ import annotations
import math
from ezdxf.enums import TextEntityAlignment


# ══════════════════════════════════════════════════════════
#  线型-线宽映射表（打印线宽 mm, GB/T 17450）
# ══════════════════════════════════════════════════════════
LINE_WEIGHT = {
    "粗实线":   0.50,   # 可见轮廓线
    "中实线":   0.35,   # 次要轮廓
    "细实线":   0.18,   # 尺寸线/剖面线/指引线
    "虚线":     0.35,   # 不可见轮廓
    "点画线":   0.18,   # 轴线/中心线/对称线
    "双点画线": 0.18,   # 假想轮廓/相邻辅助件
    "粗虚线":   0.50,   # 重要不可见轮廓
    "粗点画线": 0.50,   # 重要轴线
}

# ══════════════════════════════════════════════════════════
#  管道材质颜色映射（印刷灰度/屏幕色）
# ══════════════════════════════════════════════════════════
PIPE_MATERIAL_COLOR = {
    "HDPE双壁波纹管":   7,    # 黑色
    "UPVC管":           1,    # 红色
    "PE给水管":         5,    # 蓝色
    "PPR管":            2,    # 黄色
    "镀锌钢管":         4,    # 青色
    "不锈钢管":         8,    # 灰色
    "球墨铸铁管":       3,    # 绿色
    "混凝土管":         8,    # 灰色
    "玻璃钢管":         6,    # 品红
}

# ══════════════════════════════════════════════════════════
#  剖面填充图案库（简化线填充，材质→线间距/角度）
# ══════════════════════════════════════════════════════════
HATCH_PATTERN = {
    "混凝土":    dict(angle=45,  spacing=2.0, desc="45°斜线"),
    "钢筋混凝土": dict(angle=(45, -45), spacing=2.0, desc="双向45°斜线"),
    "砖砌体":    dict(angle=45,  spacing=1.5, desc="45°密斜线"),
    "金属":      dict(angle=45,  spacing=3.0, desc="45°疏斜线"),
    "土/砂":     dict(angle=0,   spacing=1.5, desc="水平短线+随机点"),
    "塑料":      dict(angle=-45, spacing=2.5, desc="-45°斜线"),
    "木材":      dict(angle=0,   spacing=2.0, desc="水平斜线+竖线"),
}


# ══════════════════════════════════════════════════════════
#  基础工具函数
# ══════════════════════════════════════════════════════════
def _round_xy(x, y):
    return round(x, 1), round(y, 1)


def _text(msp, txt, pos, h, align=TextEntityAlignment.LEFT, layer="文字", style="仿宋_GB2312"):
    """统一文字创建（兼容新旧 ezdxf）"""
    x, y = _round_xy(*pos)
    t = msp.add_text(txt, dxfattribs={"layer": layer, "height": h, "style": style})
    t.dxf.insert = (x, y)
    if align is not None:
        t.dxf.halign = align.value
    return t


def _solid_fill_arrow(msp, tip, tail, width, scale, layer="标注"):
    """绘制实心工程箭头（三角填充）。

    tip:  箭头尖端 (x, y)
    tail: 箭头根部 (x, y)
    width: 箭头根部宽度(mm, 图纸尺寸)
    """
    scale = scale or 100
    tx, ty = tip
    bx, by = tail
    dx, dy = tx - bx, ty - by
    length = math.hypot(dx, dy)
    if length < 0.01:
        return
    ux, uy = dx / length, dy / length          # 指向尖端单位向量
    nx, ny = -uy, ux                            # 法向量
    hw = (width / 2) * scale * 0.01            # 半宽(图纸mm→模型)

    # 三角箭头：尖端 + 根部左右两点
    p1 = (bx + nx * hw, by + ny * hw)          # 根部左
    p2 = (bx - nx * hw, by - ny * hw)          # 根部右
    msp.add_lwpolyline([tip, p1, p2, tip], close=True,
                       dxfattribs={"layer": layer, "color": 7})


# ══════════════════════════════════════════════════════════
#  1. 材质标注引线
# ══════════════════════════════════════════════════════════
def draw_material_callout(msp, target, material: str, spec: str = "",
                          standard: str = "", scale: float = 100,
                          direction: str = "right", bend: tuple = None,
                          layer: str = "文字", tracker=None):
    """材质标注引线 — 对目标点引出标注线，显示材质/规格/标准。

    参数:
        target:     (x, y) 标注目标点
        material:   材质名称 (HDPE/C30混凝土/Q235B...)
        spec:       规格 (SN8/DN200/φ20...)
        standard:   标准号 (GB/T 13663/GB 50010/...)
        direction:  "right"左上右下自动选择 "up"/"down"/"left"/"right"
        bend:       (dx, dy) 引线折点偏移，None 则自动
    """
    s = scale
    px, py = _round_xy(*target)

    if direction == "right":
        bend = bend or (8 * s, 0)
        text_dir = "right"
        align = TextEntityAlignment.MIDDLE_LEFT
    elif direction == "left":
        bend = bend or (-8 * s, 0)
        text_dir = "left"
        align = TextEntityAlignment.MIDDLE_RIGHT
    elif direction == "up":
        bend = bend or (0, 8 * s)
        text_dir = "up"
        align = TextEntityAlignment.TOP_CENTER
    else:  # down
        bend = bend or (0, -8 * s)
        text_dir = "down"
        align = TextEntityAlignment.BOTTOM_CENTER

    bx, by = bend
    kink = (px + bx, py + by)
    end_pt = (px + bx * 1.5, py + by * 1.5)

    # 引线：目标点→折点→水平尾线
    msp.add_line((px, py), kink, dxfattribs={"layer": layer, "color": 3})
    msp.add_line(kink, end_pt, dxfattribs={"layer": layer, "color": 3})

    # 材质文字（粗体位置）
    lines = [f"材质: {material}"]
    if spec:
        lines.append(f"规格: {spec}")
    if standard:
        lines.append(standard)
    th = 2.5 * s / 100

    for i, line in enumerate(lines):
        offset_y = -i * th * 1.6 if direction != "up" else i * th * 1.6
        tx = end_pt[0] + (3 * s if direction == "right" else -3 * s if direction == "left" else 0)
        ty = end_pt[1] + offset_y + (0 if direction in ("right", "left") else
                                       (3 * s if direction == "down" else -3 * s))
        bold = (i == 0)
        _text(msp, line, (tx, ty), th * (1.2 if bold else 1.0),
              align=align, layer=layer)

    return end_pt


# ══════════════════════════════════════════════════════════
#  2. 管道材质沿线标记
# ══════════════════════════════════════════════════════════
def draw_pipe_material_mark(msp, start, end, material: str, dn: str,
                             scale: float = 100, layer: str = "文字"):
    """管道沿线材质标记 — 在管道中点上方标注材质+管径。

    参数:
        start, end: 管道起终点
        material:   材质 (HDPE双壁波纹管)
        dn:         管径 (DN200)
    """
    s = scale
    mx = (start[0] + end[0]) / 2
    my = (start[1] + end[1]) / 2

    # 垂直管道偏移方向
    dx, dy = end[0] - start[0], end[1] - start[1]
    perp_x, perp_y = -dy, dx
    n = math.hypot(perp_x, perp_y) or 1.0
    px, py = perp_x / n, perp_y / n

    # 文字位置：管中点上方向偏移
    offset = 4.5 * s
    tx, ty = mx + px * offset, my + py * offset

    # 材质标注
    _text(msp, f"{material} {dn}", (tx, ty), 2.5 * s / 100,
          align=TextEntityAlignment.MIDDLE_CENTER, layer=layer)

    # 短引线
    mid = (mx + px * 1.5 * s, my + py * 1.5 * s)
    msp.add_line((mx, my), mid, dxfattribs={"layer": "细实线", "color": 3})
    msp.add_line(mid, (tx, ty + py * -2 * s), dxfattribs={"layer": "细实线", "color": 3})


# ══════════════════════════════════════════════════════════
#  3. 尺寸+公差一体化标注
# ══════════════════════════════════════════════════════════
def draw_dimension_tolerance(msp, p1, p2, dim_text: str,
                              upper: str = "", lower: str = "",
                              offset: float = 10.0, scale: float = 100,
                              layer: str = "细实线", sym: bool = False):
    """尺寸标注+公差 — 在尺寸线下方附加公差值。

    参数:
        p1, p2:    标注起点/终点
        dim_text:  尺寸文字 (如 "DN200"、"6000")
        upper:     上偏差 (如 "+0.5")
        lower:     下偏差 (如 "-0.3")
        offset:    尺寸线偏移(mm, 图纸)
        scale:     比例
        sym:       对称公差? (±)
    """
    s = scale
    off = offset * s / 100  # 图纸mm→模型

    # 尺寸线方向：垂直于 p1→p2
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    n = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / n, dx / n  # 法向量

    # 尺寸线
    ts1 = (p1[0] + nx * off, p1[1] + ny * off)
    ts2 = (p2[0] + nx * off, p2[1] + ny * off)
    msp.add_line(ts1, ts2, dxfattribs={"layer": layer, "color": 3})

    # 尺寸界线
    msp.add_line(p1, ts1, dxfattribs={"layer": layer, "color": 3})
    msp.add_line(p2, ts2, dxfattribs={"layer": layer, "color": 3})

    # 尺寸文字
    mid_x = (ts1[0] + ts2[0]) / 2
    mid_y = (ts1[1] + ts2[1]) / 2
    th = 3.0 * s / 100
    _text(msp, dim_text, (mid_x, mid_y + th * 0.3), th,
          align=TextEntityAlignment.MIDDLE_CENTER, layer="文字")

    # 公差文字（尺寸线下方）
    if upper or lower:
        if sym:
            tol_text = f"±{upper}" if upper else f"±{lower}"
        else:
            tol_text = f"({upper}/{lower})" if upper and lower else f"({upper or lower})"
        _text(msp, tol_text, (mid_x, mid_y - th * 1.2), th * 0.7,
              align=TextEntityAlignment.MIDDLE_CENTER, layer="文字")

    # 箭头
    arrow_w = 2.5 * s / 100
    for pt, dx_sign in [(ts1, 1), (ts2, -1)]:
        ax = pt[0] + dx_sign * dx / n * arrow_w * 0.5
        ay = pt[1] + dx_sign * dy / n * arrow_w * 0.5
        _solid_fill_arrow(msp, pt, (ax, ay), 3.0, scale, layer=layer)


# ══════════════════════════════════════════════════════════
#  4. 标准工程箭头（独立使用）
# ══════════════════════════════════════════════════════════
def draw_engineering_arrow(msp, tip, direction, arrow_length: float = 8.0,
                           scale: float = 100, filled: bool = True,
                           layer: str = "标注"):
    """绘制独立的标准工程箭头。

    参数:
        tip:           箭头尖端 (x, y)
        direction:     方向向量 (dx, dy) — 从根部指向尖端
        arrow_length:  箭头长度(mm, 图纸尺寸)
        filled:        True=实心三角 / False=空心箭头
    """
    s = scale
    al = arrow_length * s / 100
    tx, ty = tip
    dx, dy = direction
    n = math.hypot(dx, dy) or 1.0
    ux, uy = dx / n, dy / n

    # 根部中心
    bx, by = tx - ux * al, ty - uy * al
    # 箭头宽度 = 0.4×长度
    nx, ny = -uy, ux
    hw = 0.2 * al

    p_left = (bx + nx * hw, by + ny * hw)
    p_right = (bx - nx * hw, by - ny * hw)

    if filled:
        msp.add_lwpolyline([tip, p_left, p_right, tip], close=True,
                           dxfattribs={"layer": layer, "color": 7})
    else:
        msp.add_line(tip, p_left, dxfattribs={"layer": layer, "color": 7})
        msp.add_line(tip, p_right, dxfattribs={"layer": layer, "color": 7})
        msp.add_line(p_left, p_right, dxfattribs={"layer": layer, "color": 7})


# ══════════════════════════════════════════════════════════
#  5. 构造辅助线（虚线/点画线/双点画线）
# ══════════════════════════════════════════════════════════
def draw_construction_line(msp, p1, p2, line_type: str = "虚线",
                           scale: float = 100, layer: str = None,
                           label: str = None):
    """绘制构造辅助线。

    参数:
        line_type: "虚线" | "点画线" | "双点画线" | "粗虚线"
    """
    type_map = {
        "虚线":     "DASHED",
        "点画线":   "CENTER",
        "双点画线": "PHANTOM",
        "粗虚线":   "DASHED",
    }
    lw_map = {
        "虚线":     0.35, "点画线": 0.18,
        "双点画线": 0.18, "粗虚线": 0.50,
    }
    layer = layer or {
        "虚线": "虚线", "点画线": "点画线",
        "双点画线": "双点画线", "粗虚线": "虚线",
    }.get(line_type, "细实线")

    lt = type_map.get(line_type, "DASHED")
    try:
        msp.add_line(p1, p2, dxfattribs={"layer": layer, "linetype": lt})
    except Exception:
        msp.add_line(p1, p2, dxfattribs={"layer": layer})

    if label:
        mx, my = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
        _text(msp, label, (mx, my - 3 * scale / 100), 2.0 * scale / 100,
              align=TextEntityAlignment.TOP_CENTER, layer="文字")


# ══════════════════════════════════════════════════════════
#  6. 剖面填充
# ══════════════════════════════════════════════════════════
def draw_section_hatch(msp, boundary_pts, material: str = "混凝土",
                       scale: float = 100, layer: str = "细实线"):
    """剖面填充 — 按材质自动选择填充图案。

    boundary_pts: [(x,y), ...] 闭合边界顶点列表
    material: 材质类型 (见 HATCH_PATTERN)
    """
    if material not in HATCH_PATTERN:
        material = "金属"

    pattern = HATCH_PATTERN[material]
    spacing = pattern["spacing"] * scale / 100

    # 取包围盒
    xs = [p[0] for p in boundary_pts]
    ys = [p[1] for p in boundary_pts]
    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys), max(ys)

    # 简化：在包围盒内绘制平行斜线
    if isinstance(pattern["angle"], (list, tuple)):
        angles = pattern["angle"]
    else:
        angles = [pattern["angle"]]

    for ang in angles:
        rad = math.radians(ang)
        cos_a, sin_a = math.cos(rad), math.sin(rad)
        # 斜线间距在垂直方向上
        gap = spacing / abs(sin_a) if abs(sin_a) > 0.01 else spacing / abs(cos_a)

        # 从包围盒一角开始画
        start_x = xmin - (ymax - ymin) * abs(sin_a)
        end_x = xmax + (ymax - ymin) * abs(sin_a)

        y = ymin
        while y <= ymax + gap:
            msp.add_line((start_x, y), (end_x, y + (end_x - start_x) * math.tan(rad)),
                         dxfattribs={"layer": layer, "color": 8})
            y += gap


# ══════════════════════════════════════════════════════════
#  7. 十字中心线
# ══════════════════════════════════════════════════════════
def draw_centerline_cross(msp, center, radius: float, scale: float = 100,
                          layer: str = "点画线"):
    """圆/孔的十字中心线（点画线+超出圆外）。

    参数:
        center: 圆心 (x, y)
        radius: 圆半径 (模型坐标)
    """
    cx, cy = _round_xy(*center)
    ext = radius * 1.3  # 超出
    try:
        msp.add_line((cx - ext, cy), (cx + ext, cy),
                     dxfattribs={"layer": layer, "linetype": "CENTER"})
        msp.add_line((cx, cy - ext), (cx, cy + ext),
                     dxfattribs={"layer": layer, "linetype": "CENTER"})
    except Exception:
        msp.add_line((cx - ext, cy), (cx + ext, cy),
                     dxfattribs={"layer": layer})
        msp.add_line((cx, cy - ext), (cx, cy + ext),
                     dxfattribs={"layer": layer})


# ══════════════════════════════════════════════════════════
#  8. 折断线
# ══════════════════════════════════════════════════════════
def draw_break_line(msp, p1, p2, scale: float = 100,
                    layer: str = "细实线"):
    """长构件折断线标记。

    在 p1→p2 连线的中点绘制Z字形折断标记。
    """
    s = scale
    mx = (p1[0] + p2[0]) / 2
    my = (p1[1] + p2[1]) / 2

    # 方向向量
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    n = math.hypot(dx, dy) or 1.0
    ux, uy = dx / n, dy / n
    nx, ny = -uy, ux

    z_size = 2.5 * s / 100

    # Z字形：三段
    msp.add_line(p1, (mx - ux * z_size, my - uy * z_size),
                 dxfattribs={"layer": layer, "color": 7})
    # Z中间斜线
    mid1 = (mx - ux * z_size * 0.3 + nx * z_size * 0.5,
            my - uy * z_size * 0.3 + ny * z_size * 0.5)
    mid2 = (mx + ux * z_size * 0.3 - nx * z_size * 0.5,
            my + uy * z_size * 0.3 - ny * z_size * 0.5)
    msp.add_line(mid1, mid2, dxfattribs={"layer": layer, "color": 7})
    msp.add_line(mid2, (mx + ux * z_size, my + uy * z_size),
                 dxfattribs={"layer": layer, "color": 7})
    msp.add_line((mx + ux * z_size, my + uy * z_size), p2,
                 dxfattribs={"layer": layer, "color": 7})


# ══════════════════════════════════════════════════════════
#  9. 公差表格（批量标注配合/公差）
# ══════════════════════════════════════════════════════════
def draw_tolerance_table(msp, origin, items: list, scale: float = 100,
                         title: str = "安装公差要求", layer: str = "文字"):
    """批量公差要求表 — 列出各管段/构件的安装公差。

    items: [dict(part, dim, upper, lower), ...]
    """
    s = scale
    ox, oy = origin
    th = 3.0 * s / 100
    col_w = [12 * s, 8 * s, 6 * s, 6 * s]
    headers = ["部位", "尺寸", "上偏差", "下偏差"]

    # 表头
    _text(msp, title, (ox, oy), th * 1.2, align=TextEntityAlignment.MIDDLE_LEFT,
          layer=layer)
    x = ox
    y = oy - th * 1.5
    for i, h in enumerate(headers):
        _text(msp, h, (x, y), th * 0.8, align=TextEntityAlignment.MIDDLE_LEFT,
              layer=layer)
        x += col_w[i]

    # 分隔线
    msp.add_line((ox, y - th * 0.3), (ox + sum(col_w), y - th * 0.3),
                 dxfattribs={"layer": "细实线", "color": 3})

    # 数据行
    y -= th * 1.2
    for item in items:
        x = ox
        vals = [item.get("part", ""), item.get("dim", ""),
                item.get("upper", ""), item.get("lower", "")]
        for i, v in enumerate(vals):
            _text(msp, str(v), (x, y), th * 0.75,
                  align=TextEntityAlignment.MIDDLE_LEFT, layer=layer)
            x += col_w[i]
        y -= th * 1.1

    # 底框
    msp.add_line((ox, y + th * 0.3), (ox + sum(col_w), y + th * 0.3),
                 dxfattribs={"layer": "细实线", "color": 3})

    return ox + sum(col_w), y
