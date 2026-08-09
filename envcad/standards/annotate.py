"""工程标注 v1.5 — 智能避让 + 精度增强。

改进:
  * 所有标注支持可选的 BBoxTracker 碰撞检测
  * 高程标注分级间距（自动错开避免重叠）
  * 引出线自适应方向
  * 流向箭头标签智能偏置
  * 坐标圆整函数从 utils.py 统一导入

符号按 GB/T 50001—2017。
"""
from __future__ import annotations

import math
from typing import Optional, Tuple, List

from ezdxf.enums import TextEntityAlignment

from ..utils import round_xy as _round_xy  # v1.5: 统一导入坐标圆整

# ─── 内部辅助 ───────────────────────────────────────────


def _estimate_text_width(text: str, height: float) -> float:
    """精确估算文字宽度（mm）。修复版：含安全系数防止估算偏小。"""
    w = 0.0
    for ch in str(text):
        if '\u4e00' <= ch <= '\u9fff' or '\u3000' <= ch <= '\u303f':
            w += height * 0.85  # 中文（更精确的比例）
        elif ord(ch) > 127:
            w += height * 0.85  # 全角符号
        else:
            w += height * 0.50  # ASCII
    return w * 1.15  # 安全系数，防止估算偏小导致碰撞


def _compute_bbox(px, py, text_w, txt_h, align) -> tuple:
    """根据对齐方式计算文字包围盒 (x0, y0, x1, y1)。"""
    if align in (TextEntityAlignment.MIDDLE_CENTER,):
        return (px - text_w / 2, py - txt_h / 2, px + text_w / 2, py + txt_h / 2)
    elif align in (TextEntityAlignment.MIDDLE_LEFT, TextEntityAlignment.LEFT):
        return (px, py - txt_h / 2, px + text_w, py + txt_h / 2)
    elif align in (TextEntityAlignment.MIDDLE_RIGHT, TextEntityAlignment.RIGHT):
        return (px - text_w, py - txt_h / 2, px, py + txt_h / 2)
    else:
        return (px - text_w / 2, py - txt_h / 2, px + text_w / 2, py + txt_h / 2)


def _t(msp, content, point, height,
       align=TextEntityAlignment.LEFT, layer="文字", rotation=0,
       tracker=None, text_w=0.0, frame_bbox=None):
    """修复版文字放置 v1.5：带边界检查的碰撞避让 + 精确宽度估算。

    tracker: 可选 BBoxTracker，传入后自动避让 + 注册。
    text_w:  手动指定文字宽度（mm）。0 则自动估算。
    frame_bbox: 可选图框边界 (x0, y0, x1, y1)，传入后确保文字在框内。
    """
    if not content:
        return None

    px, py = _round_xy(*point)

    # ── 估算文字尺寸 ──
    if text_w <= 0:
        text_w = _estimate_text_width(str(content), height)
    txt_h = height * 1.6  # 增大行高，减少重叠

    # 计算起始包围盒
    bx0, by0, bx1, by1 = _compute_bbox(px, py, text_w, txt_h, align)

    # ── 边界检查：如果有 frame_bbox，确保文字在框内 ──
    if frame_bbox is not None:
        fx0, fy0, fx1, fy1 = frame_bbox
        margin = height * 2  # 安全边距
        
        # 如果超出左边界
        if bx0 < fx0 + margin:
            px += (fx0 + margin) - bx0
            bx0, bx1 = fx0 + margin, fx0 + margin + text_w
        # 如果超出右边界
        if bx1 > fx1 - margin:
            px -= bx1 - (fx1 - margin)
            bx0, bx1 = fx1 - margin - text_w, fx1 - margin
        # 如果超出下边界
        if by0 < fy0 + margin:
            py += (fy0 + margin) - by0
            by0, by1 = fy0 + margin, fy0 + margin + txt_h
        # 如果超出上边界
        if by1 > fy1 - margin:
            py -= by1 - (fy1 - margin)
            by0, by1 = fy1 - margin - txt_h, fy1 - margin

    # ── 碰撞检测 ──
    if tracker is not None:
        if tracker.is_occupied(bx0, by0, bx1, by1):
            # ── 智能避让策略 ──
            found = False
            candidates = []
            
            # 生成多个候选位置
            step = height * 1.2
            directions = [(0, 1), (0, -1), (1, 0), (-1, 0),
                         (1, 1), (-1, 1), (1, -1), (-1, -1)]
            
            for mult in [1, 2, 3, 4, 5]:
                for dx, dy in directions:
                    candidates.append((px + dx * step * mult, py + dy * step * mult))
            
            # 尝试每个候选位置
            for nx, ny in candidates:
                nbx0, nby0, nbx1, nby1 = _compute_bbox(nx, ny, text_w, txt_h, align)
                
                # 检查是否在图框内
                if frame_bbox is not None:
                    fx0, fy0, fx1, fy1 = frame_bbox
                    margin = height * 1.5
                    if not (fx0 + margin <= nbx0 and nbx1 <= fx1 - margin and
                            fy0 + margin <= nby0 and nby1 <= fy1 - margin):
                        continue
                
                # 检查是否与已有内容碰撞
                if not tracker.is_occupied(nbx0, nby0, nbx1, nby1):
                    px, py = nx, ny
                    bx0, by0, bx1, by1 = nbx0, nby0, nbx1, nby1
                    found = True
                    break
            
            # 如果找不到合适位置，使用最小偏移
            if not found:
                # 尝试最小步长微调
                for dy in [txt_h, -txt_h, txt_h * 0.8, -txt_h * 0.8, txt_h * 0.5, -txt_h * 0.5]:
                    nx, ny = px, py + dy
                    nbx0, nby0, nbx1, nby1 = _compute_bbox(nx, ny, text_w, txt_h, align)
                    if not tracker.is_occupied(nbx0, nby0, nbx1, nby1):
                        px, py = nx, ny
                        bx0, by0, bx1, by1 = nbx0, nby0, nbx1, nby1
                        found = True
                        break
                
                # 最终兜底：较大偏移
                if not found:
                    px, py = px, py + height * 4
                    bx0, by0, bx1, by1 = _compute_bbox(px, py, text_w, txt_h, align)

        # ── 用最终位置注册 ──
        tracker.register(bx0, by0, bx1, by1, margin=height * 0.8)

    t = msp.add_text(str(content), dxfattribs={
        "layer": layer, "height": height, "style": "HZ"})
    t.set_placement((px, py), align=align)
    if rotation:
        t.dxf.rotation = rotation
    return t


# ─── 文字包围盒估算 ──────────────────────────────────────

def _text_bbox(text: str, height: float, pos: Tuple[float, float],
               align=TextEntityAlignment.LEFT
               ) -> Tuple[float, float, float, float]:
    """估算文字包围盒 (x0, y0, x1, y1)，使用中英文精确宽度。"""
    w = _estimate_text_width(str(text), height)
    h = height * 1.4
    px, py = pos
    return _compute_bbox(px, py, w, h, align)


# —————————————— 标高 v1.4（分级间距）——————————————

def draw_elevation(msp, point, value: str, scale: float,
                   side: str = "right", leader_len: float = 10.0,
                   level: int = 0,
                   tracker=None):
    """标高标注 v1.4。

    level: 层级编号 (0=地面/基准, 1=中间, 2=底部)，用于自动偏移防重叠。
    """
    s = scale
    px, py = _round_xy(*point)

    # 多级偏移：同侧多个标高时自动上下错开
    level_offset = level * 7.0 * s  # 每级错开 7×scale（避免同侧标高标签重叠）

    tri_h = 1.5 * s
    tri_half = 1.5 * s
    top_y = py + tri_h + level_offset

    # 三角形
    apex = (px, py)
    bl = (px - tri_half, top_y)
    br = (px + tri_half, top_y)
    msp.add_lwpolyline([apex, bl, br, apex], close=True,
                       dxfattribs={"layer": "标高"})

    # 引出横线
    if side == "right":
        lx0, lx1 = px, px + leader_len * s
    else:
        lx0, lx1 = px - leader_len * s, px

    msp.add_line((lx0, top_y), (lx1, top_y), dxfattribs={"layer": "标高"})

    # 数值 — 使用避让放置
    tx = (lx0 + lx1) / 2
    ty = top_y + 0.6 * s
    _t(msp, value, (tx, ty), 2.8 * s,
       align=TextEntityAlignment.MIDDLE_CENTER, layer="标高",
       tracker=tracker, text_w=len(str(value)) * 2.8 * s * 0.7)

    if tracker is not None:
        # 注册标高符号区域
        tri_bbox = (px - tri_half, py, px + tri_half, ty + 2.8 * s)
        tracker.register(*tri_bbox, margin=20)

    return top_y


# —————————————— 管径标注 v1.4 ——————————————

def draw_pipe_diameter(msp, target, dn: str, scale: float,
                       leader_dir=(1, 1), label: str = "DN",
                       tracker=None):
    """管径引出标注（碰撞检测增强）。"""
    s = scale
    tx, ty = _round_xy(*target)
    dx, dy = leader_dir
    L = 12 * s
    bend = _round_xy(tx + dx * L * 0.6, ty + dy * L * 0.8)
    end = _round_xy(bend[0] + (dx if dx else 1) * L * 0.6, bend[1])

    msp.add_line((tx, ty), bend, dxfattribs={"layer": "细实线-尺寸"})
    msp.add_line(bend, end, dxfattribs={"layer": "细实线-尺寸"})
    msp.add_circle((tx, ty), 0.6 * s, dxfattribs={"layer": "细实线-尺寸"})

    txt = f"{label}{dn}" if not str(dn).startswith(("DN", "dn", "D")) else str(dn)
    txt_x = end[0] + (1.5 * s if dx >= 0 else -1.5 * s)
    txt_y = end[1] + 0.6 * s

    _t(msp, txt, (txt_x, txt_y), 3.0 * s,
       align=TextEntityAlignment.LEFT if dx >= 0 else TextEntityAlignment.RIGHT,
       layer="文字", tracker=tracker)

    if tracker is not None:
        tracker.register(tx - s, ty - s, txt_x + 8 * s, txt_y + 4 * s, margin=30)

    return end


# —————————————— 坡度 v1.4 ——————————————

def draw_slope(msp, start, end, slope_str: str, scale: float,
               offset: float = 8.0, label: str = "i=",
               tracker=None):
    """在管线斜上方写坡度标注（碰撞检测增强）。"""
    s = scale
    sx, sy = _round_xy(*start)
    ex, ey = _round_xy(*end)
    mx, my = (sx + ex) / 2, (sy + ey) / 2

    length = math.hypot(ex - sx, ey - sy) or 1.0
    nx, ny = -(ey - sy) / length, (ex - sx) / length
    if ny < 0:
        nx, ny = -nx, -ny

    tx = mx + nx * offset * s
    ty = my + ny * offset * s
    _t(msp, f"{label}{slope_str}", (tx, ty), 3.0 * s,
       align=TextEntityAlignment.MIDDLE_CENTER, layer="文字",
       tracker=tracker)

    # 坡向箭头
    arrow_len = 3 * s
    ax = mx + (ex - sx) / length * arrow_len
    ay = my + (ey - sy) / length * arrow_len
    _arrow(msp, (mx, my), (ax, ay), s, layer="流向")

    return (tx, ty)


# —————————————— 流向箭头 v1.4 ——————————————

def draw_flow_arrow(msp, start, direction, scale: float,
                    length: float = 12.0, label: str = None,
                    angle_deg: float = None,
                    label_side: str = "above",
                    tracker=None):
    """水流方向箭头 v1.4：标签智能偏置。"""
    s = scale
    sx, sy = _round_xy(*start)

    if angle_deg is not None:
        a = math.radians(angle_deg)
        dx, dy = math.cos(a), math.sin(a)
    else:
        dx, dy = direction
        n = math.hypot(dx, dy) or 1.0
        dx, dy = dx / n, dy / n

    end = _round_xy(sx + dx * length * s, sy + dy * length * s)
    _arrow(msp, start, end, s, layer="流向")

    if label:
        # 标签放在箭头侧上方
        perp_x, perp_y = -dy, dx  # 垂直向量
        lx = end[0] + perp_x * 4 * s
        ly = end[1] + perp_y * 4 * s
        if label_side == "above":
            lx = end[0] + dx * 2 * s + perp_x * 4 * s
            ly = end[1] + dy * 2 * s + perp_y * 4 * s
        _t(msp, label, (lx, ly), 2.8 * s,
           align=TextEntityAlignment.MIDDLE_CENTER, layer="文字",
           tracker=tracker)

    return end


# —————————————— 箭头绘制 ───────────────────────────────

def _arrow(msp, start, end, s, layer="流向", head: float = 2.0):
    """画带实心箭头的线段 — 工程标准三角比例(长宽比≈3:1, 张角≈20°)。"""
    sx, sy = start
    ex, ey = end
    a = math.atan2(ey - sy, ex - sx)
    h = head * s
    # 半宽 = 0.25h (张角 ≈2×atan(0.25)=28°, 工程标准)
    hw = h * 0.25

    msp.add_line(start, end, dxfattribs={"layer": layer})

    # 实心三角填充（标准工程箭头比例）
    p_tip = (ex, ey)
    p_left = (ex - h * math.cos(a) + hw * math.sin(a),
              ey - h * math.sin(a) - hw * math.cos(a))
    p_right = (ex - h * math.cos(a) - hw * math.sin(a),
               ey - h * math.sin(a) + hw * math.cos(a))
    try:
        msp.add_solid([p_tip, p_left, p_right], dxfattribs={"layer": layer})
    except Exception as _e:
        print(f"[警告] annotate 填充失败：{_e}")


# —————————————— 引出线 v1.4 ——————————————

def draw_leader(msp, target, text: str, scale: float,
                bend=(8, 8), text_dir="right",
                tracker=None):
    """引出线标注 v1.4（碰撞检测）。"""
    s = scale
    tx, ty = _round_xy(*target)
    bend_pt = _round_xy(tx + bend[0] * s, ty + bend[1] * s)

    if text_dir == "right":
        end = (bend_pt[0] + 8 * s, bend_pt[1])
    else:
        end = (bend_pt[0] - 8 * s, bend_pt[1])

    msp.add_line((tx, ty), bend_pt, dxfattribs={"layer": "细实线-尺寸"})
    msp.add_line(bend_pt, end, dxfattribs={"layer": "细实线-尺寸"})
    msp.add_circle((tx, ty), 0.5 * s, dxfattribs={"layer": "细实线-尺寸"})

    txt_x = end[0] + (1.0 * s if text_dir == "right" else -1.0 * s)
    txt_y = end[1] + 0.8 * s

    _t(msp, text, (txt_x, txt_y), 2.8 * s,
       align=TextEntityAlignment.LEFT if text_dir == "right" else TextEntityAlignment.RIGHT,
       layer="文字", tracker=tracker)

    return end


# —————————————— 剖面标注 v1.4 ——————————————

def draw_section_mark(msp, point, scale: float, label: str = "1",
                      direction: str = "right", size: float = 5.0,
                      tracker=None):
    """剖面剖切符号。"""
    s = scale
    px, py = _round_xy(*point)
    L = size * s

    if direction == "right":
        p1, p2 = (px, py), (px + L, py)
    else:
        p1, p2 = (px, py), (px - L, py)

    msp.add_line(p1, p2, dxfattribs={"layer": "粗实线"})
    cx = p2[0] + (2 * s if direction == "right" else -2 * s)
    _t(msp, label, (cx, py + 2 * s), 3.5 * s,
       align=TextEntityAlignment.MIDDLE_CENTER, layer="文字-标题",
       tracker=tracker)

    return p2


# —————————————— 文字组（防重叠批量放置）———————————————

def draw_text_block(msp, lines: List[str], start_pt, height: float,
                    scale: float, line_spacing: float = 1.5,
                    align=TextEntityAlignment.LEFT,
                    layer="文字", tracker=None, title: str = None):
    """批量放置多行文字，自动计算行距并避让。

    lines: 文字行列表。
    start_pt: 首行起点。
    height: 字高 (图纸 mm，已乘 scale)。
    line_spacing: 行距倍率。
    返回最后一行底边 Y 坐标。
    """
    s = scale
    x, y = _round_xy(*start_pt)
    dy = height * line_spacing

    if title:
        _t(msp, title, (x, y), height * 1.15,
           align=align, layer="文字-标题", tracker=tracker)
        y -= dy * 1.3

    for line in lines:
        _t(msp, line, (x, y), height,
           align=align, layer=layer, tracker=tracker)
        y -= dy

    return y
