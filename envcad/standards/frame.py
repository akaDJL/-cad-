"""国标图框与标题栏（GB/T 14689—2008 幅面 + GB/T 50001—2017 标题栏）。

支持 A0~A4 任意图幅与横式/纵式，默认 A2 横式，向后兼容。

约定：modelspace 按 1:1 实际尺寸（mm）绘制实物；图框按出图比例放大
（A3 横式 = 420×297，乘以 scale）。出图 1:1 即得正确比例图纸。

图幅选择（二选一）：
  * 显式：``FrameInfo(size="A1", orientation="landscape")``；
  * 进程级默认：调用前用 ``set_default_paper_size("A2")`` /
    ``set_default_orientation("portrait")`` 设置，所有未显式指定尺寸的
    绘图自动采用。未设置时回退到 A2 横式。
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass

from ezdxf.enums import TextEntityAlignment

from ..engine.dxf_base import save_dxf

# ── 标准图幅（GB/T 14689）：(长边, 短边) mm，含装订边 ──
PAPER_BASE = {
    "A0": (1189.0, 841.0),
    "A1": (841.0, 594.0),
    "A2": (594.0, 420.0),
    "A3": (420.0, 297.0),
    "A4": (297.0, 210.0),
}
# 历史别名，保留以兼容旧调用（survey_gis 等直接引用 A3_W/A3_H）
A3_W, A3_H = PAPER_BASE["A3"]

# ── 标准留边（GB/T 14689-2008 留装订边）：(a装订边, c其他三边) mm ──
#   a 全幅面 = 25；c: A0/A1/A2 = 10，A3/A4 = 5
#   优先从本地标准知识库 standards_kb.json 读取（见 _load_margins_from_kb），
#   知识库缺字段或不可用时回退到下方内置常量。
MARGIN = {
    "A0": (25.0, 10.0),
    "A1": (25.0, 10.0),
    "A2": (25.0, 10.0),
    "A3": (25.0, 5.0),
    "A4": (25.0, 5.0),
}
# 历史别名（兼容旧调用）
MARGIN_L = 25.0   # 装订边 a
MARGIN_O = 10.0   # 其余边 c（A2 基准值）
TITLE_W, TITLE_H = 180.0, 56.0  # 标题栏基准尺寸（× tb 缩放）

# ── 优先从本地标准知识库补齐留边（GB/T 14689）──
_KB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                        "standards_kb.json")


def _load_margins_from_kb():
    """从本地标准知识库 standards_kb.json 读取 GB/T 14689 留边，补齐
    a(装订边)/c(其他三边) 的逐幅面数值；缺失或解析失败时静默回退内置常量。
    """
    try:
        with open(_KB_PATH, "r", encoding="utf-8") as fh:
            kb = json.load(fh)
    except Exception:
        return
    for r in kb.get("rules", {}).get("Sheet", []):
        if str(r.get("std", "")).startswith("GB/T 14689"):
            p = r.get("param", {})
            a = float(p.get("border_a_mm", 25.0))
            c_map = p.get("border_c_mm", {})
            for size in PAPER_BASE:
                if isinstance(c_map, dict):
                    c = float(c_map.get(size, 10.0))
                else:
                    c = float(c_map)
                MARGIN[size] = (a, c)
            return


_load_margins_from_kb()

# 标题栏随图幅放大系数（大图标题栏放大更清晰，小图不喧宾夺主）
TITLE_SCALE = {"A0": 1.8, "A1": 1.5, "A2": 1.25, "A3": 1.0, "A4": 1.0}

# 进程级默认图幅/方向（CLI 通过 set_default_* 设置；未设置则用 A2 横式）
_DEFAULT_PAPER_SIZE = "A2"
_DEFAULT_ORIENTATION = "landscape"


def set_default_paper_size(size: str) -> None:
    """设置进程级默认图幅（"A0"~"A4"）。非法值忽略。"""
    global _DEFAULT_PAPER_SIZE
    if str(size).upper() in PAPER_BASE:
        _DEFAULT_PAPER_SIZE = str(size).upper()


def get_default_paper_size() -> str:
    return _DEFAULT_PAPER_SIZE


def set_default_orientation(orientation: str) -> None:
    """设置进程级默认方向：'landscape'（横式，默认）或 'portrait'（纵式）。"""
    global _DEFAULT_ORIENTATION
    o = str(orientation).lower()
    if o in ("landscape", "portrait"):
        _DEFAULT_ORIENTATION = o


def get_default_orientation() -> str:
    return _DEFAULT_ORIENTATION


def _resolve_sheet(size, orientation):
    """返回 (W, H, tb_scale, size)，W/H 为图幅长/短边按方向展开后的 mm，
    size 为实际采用的幅面代号。

    size/orientation 为空时回退到进程级默认（再回退 _DEFAULT_PAPER_SIZE 横式）。
    """
    s = (size or "").upper() or _DEFAULT_PAPER_SIZE
    if s not in PAPER_BASE:
        s = _DEFAULT_PAPER_SIZE
    o = (orientation or "").lower() or _DEFAULT_ORIENTATION
    long, short = PAPER_BASE[s]
    W, H = (long, short) if o == "landscape" else (short, long)
    return W, H, TITLE_SCALE.get(s, 1.0), s


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
    size: str = None        # 图幅：A0~A4；None=进程级默认（默认 A2）
    orientation: str = None  # 方向：landscape 横式 / portrait 纵式；None=默认


def draw_frame(doc, scale: float, info: FrameInfo, tracker=None):
    """绘制国标图框 + 标题栏，返回内框范围 (x0,y0,x1,y1)（实物坐标系）。

    v1.5: 图幅由 ``info.size`` / ``info.orientation`` 或进程级默认
    （``set_default_paper_size`` / ``set_default_orientation``）决定，
    默认 A2 横式，向后兼容。
    """
    msp = doc.modelspace()
    W, H, tb, s = _resolve_sheet(info.size, info.orientation)
    W, H = W * scale, H * scale
    a, c = MARGIN.get(s, (MARGIN_L, MARGIN_O))
    ml, mo = a * scale, c * scale
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
    # 标题栏（右下角，向左上展开）；随图幅缩放系数 tb 等比放大
    _draw_title_block(msp, x1, y0, scale, info, tracker, tb)
    # 注册图框边距区域（仅四周留白，不占绘图区，避免假碰撞）
    if tracker is not None:
        # 左装订边、右/上/下留白边
        tracker.register(0, 0, ml, H, margin=50)            # 左边距
        tracker.register(W - mo, 0, W, H, margin=50)        # 右边距
        tracker.register(ml, H - mo, W - mo, H, margin=50)  # 上边距
        tracker.register(ml, 0, W - mo, mo, margin=50)      # 下边距
    return (x0, y0, x1, y1)


def draw_frame_at(doc, scale, info, bbox, tracker=None):
    """在已有内容的外包络 bbox=(xmin,ymin,xmax,ymax) 之外绘制国标图框 + 标题栏。

    用于标注/一键出图等“内容坐标已固定、无法整体平移”的场景：图框直接包住
    内容，标题栏固定在内容外包络的右下角。bbox 为内容实物坐标（未乘 scale）。
    返回图框外边范围 (fx0,fy0,fx1,fy1)。
    """
    msp = doc.modelspace()
    s = scale
    xmin, ymin, xmax, ymax = bbox
    # 留白：装订边 a=25（左），其余边 c=10（按 A2 基准统一留白）
    a = 25.0 * s
    c = 10.0 * s
    fx0, fy0 = xmin - a, ymin - c
    fx1, fy1 = xmax + c, ymax + c
    # 外框
    msp.add_lwpolyline([(fx0, fy0), (fx1, fy0), (fx1, fy1), (fx0, fy1)],
                       close=True, dxfattribs={"layer": "图框"})
    # 内框（粗实线）
    ix0, iy0 = fx0 + a, fy0 + c
    ix1, iy1 = fx1 - c, fy1 - c
    msp.add_lwpolyline([(ix0, iy0), (ix1, iy0), (ix1, iy1), (ix0, iy1)],
                       close=True, dxfattribs={"layer": "图框"})
    _center_marks(msp, ix0, iy0, ix1, iy1, s)
    # 标题栏：固定在内容外包络右下角（fx1, fy0 处）
    _draw_title_block(msp, fx1, fy0, s, info, tracker, 1.0)
    if tracker is not None:
        tracker.register(fx0, fy0, fx0 + a, fy1, margin=50)
        tracker.register(fx1 - c, fy0, fx1, fy1, margin=50)
        tracker.register(ix0, fy1 - c, ix1, fy1, margin=50)
        tracker.register(ix0, fy0, ix1, fy0 + c, margin=50)
    # 选幅面（仅用于信息标注，不改绘制）
    return (fx0, fy0, fx1, fy1)


def _content_bbox(msp, scale):
    """扫描模型空间所有实体，返回内容外包络 (xmin,ymin,xmax,ymax)。

    忽略已存在的图框图层实体（避免"旧框"被当成内容）。MTEXT/INSERT 等
    bbox 不稳定时退而取插入点；圆/弧取外接矩形。
    """
    xmin = ymin = 1e18
    xmax = ymax = -1e18
    for e in list(msp):
        if e.dxf.layer == "图框":
            continue
        t = e.dxftype()
        try:
            if t == "LWPOLYLINE":
                for x, y in e.get_points("xy"):
                    xmin, ymin, xmax, ymax = min(xmin, x), min(ymin, y), max(xmax, x), max(ymax, y)
            elif t == "LINE":
                for x, y in [(e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)]:
                    xmin, ymin, xmax, ymax = min(xmin, x), min(ymin, y), max(xmax, x), max(ymax, y)
            elif t in ("ARC", "CIRCLE"):
                c, r = e.dxf.center, e.dxf.radius
                xmin, ymin = min(xmin, c.x - r), min(ymin, c.y - r)
                xmax, ymax = max(xmax, c.x + r), max(ymax, c.y + r)
            elif t in ("TEXT", "MTEXT", "INSERT", "ATTDEF"):
                ip = e.dxf.insert
                xmin, ymin = min(xmin, ip.x), min(ymin, ip.y)
                xmax, ymax = max(xmax, ip.x), max(ymax, ip.y)
            else:
                b = e.bbox()
                if b:
                    xmin, ymin = min(xmin, b.extmin.x), min(ymin, b.extmin.y)
                    xmax, ymax = max(xmax, b.extmax.x), max(ymax, b.extmax.y)
        except Exception:
            continue
    if xmax < xmin or ymax < ymin:
        return (0.0, 0.0, 1.0, 1.0)
    return (xmin, ymin, xmax, ymax)


def choose_paper_for_content(bbox, scale, orientation="landscape"):
    """按内容外包络选能装下的最小标准幅面。

    先试给定方向，放不下再试另一方向，再不行就 A0（超大内容仍包住）。
    返回 (size, orientation)。
    """
    xmin, ymin, xmax, ymax = bbox
    cw = (xmax - xmin) + 35.0 * scale   # 左右留白 a+c
    ch = (ymax - ymin) + 20.0 * scale   # 上下留白 c+c
    for o in ([orientation] if orientation else ["landscape", "portrait"]):
        for sz in ("A4", "A3", "A2", "A1", "A0"):
            long, short = PAPER_BASE[sz]
            W, H = (long, short) if o == "landscape" else (short, long)
            if cw <= W * scale and ch <= H * scale:
                return sz, o
    return "A0", orientation or "landscape"


def refit_frame(doc, scale, info, tracker=None, orientation=None):
    """在保存前调用：量实际内容，若原图框（或默认幅面）装不下则重选幅面并覆画图框。

    不改变任何内容坐标——图框直接包住内容（与 draw_frame_at 一致）。
    返回最终采用的 (size, orientation)。
    """
    msp = doc.modelspace()
    bbox = _content_bbox(msp, scale)
    size, o = choose_paper_for_content(bbox, scale, orientation or info.orientation or _DEFAULT_ORIENTATION)
    # 移除旧图框（若存在）
    old = [e for e in list(msp) if e.dxf.layer == "图框"]
    for e in old:
        try:
            msp.delete_entity(e)
        except Exception:
            pass
    info.size = size
    info.orientation = o
    draw_frame_at(doc, scale, info, bbox, tracker)
    return size, o


def save_dxf_autofit(doc, path, scale, info, tracker=None, orientation=None):
    """save_dxf 的自适应封装：保存前先 refit_frame，保证图幅与内容匹配。"""
    refit_frame(doc, scale, info, tracker, orientation)
    return save_dxf(doc, path)


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


def _draw_title_block(msp, rx, by, s, info: FrameInfo, tracker=None, tb: float = 1.0):
    """标题栏右下角位于 (rx, by)，向左上展开 180×56（×scale×tb）。

    v1.5: tb 为图幅缩放系数（大图标题栏放大，小图不变），所有内部几何
    与字高均按 ts = s * tb 等比缩放，保持图框比例正确。
    """
    ts = s * tb
    tw, th = TITLE_W * ts, TITLE_H * ts
    lx, ty = rx - tw, by + th  # 左上角
    # 外框（粗实线）
    msp.add_lwpolyline([(lx, by), (rx, by), (rx, ty), (lx, ty)], close=True,
                       dxfattribs={"layer": "图框"})
    # 注册标题栏区域
    if tracker is not None:
        tracker.register(lx, by, rx, ty, margin=50)
    # —— 分格 ——
    # 主分界：图名区(左96) | 签字区(36) | 单位区(28) | 比例图号区(20)
    c1 = lx + 96 * ts      # 图名 | 签字
    c2 = lx + 132 * ts     # 签字 | 单位
    c3 = lx + 160 * ts     # 单位 | 比例图号
    hmid = by + 28 * ts    # 上下分界
    for x in (c1, c2, c3):
        msp.add_line((x, by), (x, ty), dxfattribs={"layer": "图框"})
    msp.add_line((lx, hmid), (c1, hmid), dxfattribs={"layer": "图框"})
    # 比例/图号 上下分界
    msp.add_line((c3, by + 14 * ts), (rx, by + 14 * ts), dxfattribs={"layer": "图框"})
    # 签字区三行（上半格 28~56 内均分，与签字文字行对应）
    for i in (1, 2):
        y = by + (28 + 28 / 3 * i) * ts
        msp.add_line((c1, y), (c2, y), dxfattribs={"layer": "图框"})

    # —— 文字 ——
    H = ts  # 字高基数（随图幅缩放）
    # 图名（大字，居中，上半格 28~56）
    _text(msp, info.title, ((lx + c1) / 2, by + 42 * ts), 5 * H,
          align=TextEntityAlignment.MIDDLE_CENTER, layer="文字-标题",
          tracker=tracker)
    # 项目名（下半格 0~28 居中）
    _text(msp, info.project, ((lx + c1) / 2, by + 14 * ts), 3 * H,
          align=TextEntityAlignment.MIDDLE_CENTER, layer="文字",
          tracker=tracker)
    # 签字三行
    rows = [("设计", info.designer), ("校核", info.checker), ("审核", info.auditor)]
    rh = 28 / 3 * ts
    for i, (lbl, name) in enumerate(rows):
        cy = by + th - rh * (i + 0.5)
        _text(msp, lbl, (c1 + 4 * ts, cy), 2.5 * H, layer="文字", tracker=tracker)
        _text(msp, name, (c1 + 14 * ts, cy), 2.5 * H, layer="文字", tracker=tracker)
    # 单位
    _text(msp, info.unit, ((c2 + c3) / 2, (by + ty) / 2), 2.8 * H,
          align=TextEntityAlignment.MIDDLE_CENTER, layer="文字", tracker=tracker)
    # 比例
    _text(msp, "比例", (c3 + 2 * ts, by + 21 * ts), 2.2 * H, layer="文字", tracker=tracker)
    _text(msp, info.scale_str, ((c3 + rx) / 2, by + 18 * ts), 3 * H,
          align=TextEntityAlignment.MIDDLE_CENTER, layer="文字", tracker=tracker)
    # 图号
    _text(msp, "图号", (c3 + 2 * ts, by + 7 * ts), 2.2 * H, layer="文字", tracker=tracker)
    _text(msp, info.drawing_no, ((c3 + rx) / 2, by + 4 * ts), 3 * H,
          align=TextEntityAlignment.MIDDLE_CENTER, layer="文字", tracker=tracker)
    # 日期（下半格 0~28 居中，签字区下方）
    _text(msp, info.date, ((c1 + c2) / 2, by + 14 * ts), 2.5 * H,
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
