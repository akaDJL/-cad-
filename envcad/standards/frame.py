"""A3 图框与标题栏（GB/T 14689—2008 幅面 + GB/T 50001—2017 标题栏）。

约定：modelspace 按 1:1 实际尺寸（mm）绘制实物；图框按出图比例放大
（A3 = 420×297，乘以 scale）。出图 1:1 即得正确比例图纸。
"""
from __future__ import annotations

from dataclasses import dataclass

from ezdxf.enums import TextEntityAlignment

# A3 横式幅面（mm）
A3_W, A3_H = 420.0, 297.0
MARGIN_L = 25.0   # 装订边
MARGIN_O = 10.0   # 其余边
TITLE_W, TITLE_H = 180.0, 56.0  # 标题栏尺寸


@dataclass
class FrameInfo:
    title: str = "未命名图纸"
    drawing_no: str = "ENV-00"
    scale_str: str = "1:100"
    designer: str = ""
    checker: str = ""
    auditor: str = ""
    project: str = "环保工程"
    unit: str = "设计单位"
    date: str = "2026.07"


def draw_frame(doc, scale: float, info: FrameInfo, tracker=None):
    """绘制 A3 图框 + 标题栏，返回内框范围 (x0,y0,x1,y1)（实物坐标系）。
    v1.4: 支持 tracker 注册图框文字区域。
    """
    msp = doc.modelspace()
    W, H = A3_W * scale, A3_H * scale
    ml, mo = MARGIN_L * scale, MARGIN_O * scale
    # 外框（图幅边界，细实线）
    msp.add_lwpolyline([(0, 0), (W, 0), (W, H), (0, H)], close=True,
                       dxfattribs={"layer": "图框"})
    # 内框（图框线，粗实线）
    x0, y0 = ml, mo
    x1, y1 = W - mo, H - mo
    msp.add_lwpolyline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], close=True,
                       dxfattribs={"layer": "图框"})
    # 对中标志（四边中点小三角，可选，便于折叠定位）
    _center_marks(msp, x0, y0, x1, y1, scale)
    # 标题栏（右下角，向左上展开）
    _draw_title_block(msp, x1, y0, scale, info, tracker)
    # 注册图框边距区域（仅四周留白，不占绘图区，避免假碰撞）
    if tracker is not None:
        # 左装订边、右/上/下留白边
        tracker.register(0, 0, ml, H, margin=50)            # 左边距
        tracker.register(W - mo, 0, W, H, margin=50)        # 右边距
        tracker.register(ml, H - mo, W - mo, H, margin=50)  # 上边距
        tracker.register(ml, 0, W - mo, mo, margin=50)      # 下边距
    return (x0, y0, x1, y1)


def _center_marks(msp, x0, y0, x1, y1, s):
    mid_w = (x0 + x1) / 2
    mid_h = (y0 + y1) / 2
    L = 5 * s
    for (cx, cy, dx, dy) in [
        (mid_w, y1, L, L),   # 上
        (mid_w, y0, L, -L),  # 下
        (x0, mid_h, -L, L),  # 左
        (x1, mid_h, L, L),   # 右
    ]:
        msp.add_line((cx - dx / 2, cy), (cx + dx / 2, cy), dxfattribs={"layer": "图框"})
        msp.add_line((cx, cy - dy / 2), (cx, cy + dy / 2), dxfattribs={"layer": "图框"})


def _draw_title_block(msp, rx, by, s, info: FrameInfo, tracker=None):
    """标题栏右下角位于 (rx, by)，向左上展开 180×56（×scale）。v1.4 +tracker。"""
    tw, th = TITLE_W * s, TITLE_H * s
    lx, ty = rx - tw, by + th  # 左上角
    # 外框（粗实线）
    msp.add_lwpolyline([(lx, by), (rx, by), (rx, ty), (lx, ty)], close=True,
                       dxfattribs={"layer": "图框"})
    # 注册标题栏区域
    if tracker is not None:
        tracker.register(lx, by, rx, ty, margin=50)
    # —— 分格 ——
    # 主分界：图名区(左96) | 签字区(36) | 单位区(28) | 比例图号区(20)
    c1 = lx + 96 * s      # 图名 | 签字
    c2 = lx + 132 * s     # 签字 | 单位
    c3 = lx + 160 * s     # 单位 | 比例图号
    hmid = by + 28 * s    # 上下分界
    for x in (c1, c2, c3):
        msp.add_line((x, by), (x, ty), dxfattribs={"layer": "图框"})
    msp.add_line((lx, hmid), (c1, hmid), dxfattribs={"layer": "图框"})
    # 比例/图号 上下分界
    msp.add_line((c3, by + 14 * s), (rx, by + 14 * s), dxfattribs={"layer": "图框"})
    # 签字区三行（上半格 28~56 内均分，与签字文字行对应）
    for i in (1, 2):
        y = by + (28 + 28 / 3 * i) * s
        msp.add_line((c1, y), (c2, y), dxfattribs={"layer": "图框"})

    # —— 文字 ——
    H = s  # 字高基数
    # 图名（大字，居中，上半格 28~56）
    _text(msp, info.title, ((lx + c1) / 2, by + 42 * s), 5 * H,
          align=TextEntityAlignment.MIDDLE_CENTER, layer="文字-标题",
          tracker=tracker)
    # 项目名（下半格 0~28 居中）
    _text(msp, info.project, ((lx + c1) / 2, by + 14 * s), 3 * H,
          align=TextEntityAlignment.MIDDLE_CENTER, layer="文字",
          tracker=tracker)
    # 签字三行
    rows = [("设计", info.designer), ("校核", info.checker), ("审核", info.auditor)]
    rh = 28 / 3 * s
    for i, (lbl, name) in enumerate(rows):
        cy = by + th - rh * (i + 0.5)
        _text(msp, lbl, (c1 + 4 * s, cy), 2.5 * H, layer="文字", tracker=tracker)
        _text(msp, name, (c1 + 14 * s, cy), 2.5 * H, layer="文字", tracker=tracker)
    # 单位
    _text(msp, info.unit, ((c2 + c3) / 2, (by + ty) / 2), 2.8 * H,
          align=TextEntityAlignment.MIDDLE_CENTER, layer="文字", tracker=tracker)
    # 比例
    _text(msp, "比例", (c3 + 2 * s, by + 21 * s), 2.2 * H, layer="文字", tracker=tracker)
    _text(msp, info.scale_str, ((c3 + rx) / 2, by + 18 * s), 3 * H,
          align=TextEntityAlignment.MIDDLE_CENTER, layer="文字", tracker=tracker)
    # 图号
    _text(msp, "图号", (c3 + 2 * s, by + 7 * s), 2.2 * H, layer="文字", tracker=tracker)
    _text(msp, info.drawing_no, ((c3 + rx) / 2, by + 4 * s), 3 * H,
          align=TextEntityAlignment.MIDDLE_CENTER, layer="文字", tracker=tracker)
    # 日期（下半格 0~28 居中，签字区下方）
    _text(msp, info.date, ((c1 + c2) / 2, by + 14 * s), 2.5 * H,
          align=TextEntityAlignment.MIDDLE_CENTER, layer="文字", tracker=tracker)


def _text(msp, content, point, height, align=TextEntityAlignment.LEFT, layer="文字",
          tracker=None):
    """图框文字写入 v1.5 — 使用修复版文字宽度估算。"""
    if not content:
        return
    t = msp.add_text(content, dxfattribs={"layer": layer, "height": height, "style": "HZ"})
    t.set_placement(point, align=align)
    if tracker is not None:
        # 注册文字区域（使用修复版估算逻辑）
        from .annotate import _estimate_text_width
        px, py = point
        tw = _estimate_text_width(content, height)
        th = height * 1.6  # 修复：增大行高
        if align in (TextEntityAlignment.MIDDLE_CENTER,):
            bx0, by0 = px - tw / 2, py - th / 2
            bx1, by1 = px + tw / 2, py + th / 2
        elif align in (TextEntityAlignment.MIDDLE_LEFT, TextEntityAlignment.LEFT):
            bx0, by0 = px, py - th / 2
            bx1, by1 = px + tw, py + th / 2
        else:
            bx0, by0 = px - tw / 2, py - th / 2
            bx1, by1 = px + tw / 2, py + th / 2
        tracker.register(bx0, by0, bx1, by1, margin=height * 0.5)
    return t
