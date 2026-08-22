"""工程图纸模板 v1.0 — A0~A4 标准图幅 + 行业标题栏。

支持快速创建标准尺寸图纸，预填项目信息，自动绘制图框和标题栏。
无需替代现有 frame.py 的 A3 图框，而是提供更灵活的模板系统。

纯 ezdxf，零新依赖。
"""
from __future__ import annotations

from typing import List, Optional, Tuple

from ezdxf.enums import TextEntityAlignment
from ..utils import _r, _tri


# ══════════════════════════════════════════════════════════
#  标准图幅定义（GB/T 14689）
# ══════════════════════════════════════════════════════════

# (宽度, 高度) 单位 mm，含装订边
PAPER_SIZES = {
    "A0": (841, 1189),
    "A1": (594, 841),
    "A2": (420, 594),
    "A3": (297, 420),
    "A4": (210, 297),
    "A0_L": (1189, 841),   # 加长（可选）
    "A1_L": (841, 594),
}

# 图框边距（带装订边）
FRAME_MARGIN = 25.0   # 装订边
OTHER_MARGIN = 10.0    # 其他三边


def draw_sheet_frame(msp, paper_size: str = "A2",
                      scale: float = 100.0,
                      layer: str = "粗实线"):
    """绘制标准图幅图框。

    返回: (图幅宽, 图幅高, 内框左下X, 内框左下Y, 内框宽, 内框高)
    """
    if paper_size not in PAPER_SIZES:
        paper_size = "A2"

    pw, ph = PAPER_SIZES[paper_size]
    w = pw * scale
    h = ph * scale
    fm = FRAME_MARGIN * scale
    om = OTHER_MARGIN * scale

    # 外框（图纸边界）
    msp.add_lwpolyline(
        [(0, 0), (w, 0), (w, h), (0, h)],
        close=True, dxfattribs={"layer": "细实线"}
    )

    # 内框（图框线）
    ix, iy = fm, om
    iw = w - fm - om
    ih = h - 2 * om

    msp.add_lwpolyline(
        [(ix, iy), (ix + iw, iy), (ix + iw, iy + ih), (ix, iy + ih)],
        close=True, dxfattribs={"layer": layer}
    )

    return (w, h, ix, iy, iw, ih)


# ══════════════════════════════════════════════════════════
#  标题栏（多行业模板）
# ══════════════════════════════════════════════════════════

def draw_title_block(msp, origin, width: float, height: float = 0,
                      project: dict = None,
                      industry: str = "mechanical",
                      scale: float = 100.0,
                      layer_grid: str = "粗实线",
                      layer_text: str = "文字",
                      tracker=None) -> Tuple[float, float]:
    """绘制带项目信息的标题栏。

    参数:
        origin: 标题栏右下角 (x, y) 或左下角
        width: 标题栏宽度（图纸 mm）
        height: 标题栏高度（图纸 mm，默认 A3/A4=40, A0/A1=56）
        project: 项目信息字典 {"name":"项目名称","no":"图号","scale":"1:100",
                  "design":"设计","review":"审核","date":"2026-07",...}
        industry: "mechanical"/"civil"/"electrical"/"plumbing"/"general"
    """
    s = scale
    ox, oy = _r(*origin)
    w = width * s
    h = height * s
    if h <= 0:
        h = 40.0 * s

    # ── 外框 ──
    msp.add_lwpolyline(
        [(ox, oy), (ox, oy + h), (ox - w, oy + h), (ox - w, oy)],
        close=True, dxfattribs={"layer": layer_grid}
    )

    # 标题栏分格（按行业不同布局）
    _draw_titlebar_grid(msp, ox, oy, w, h, industry, s, layer_grid)

    # ── 填充文字 ──
    if not project:
        project = {}

    fields = {
        "mechanical": [
            (0.08, 0.85, 0.18, "name", "HZ", 3.5, "center"),
            (0.08, 0.60, 0.18, "no", "ENG", 3.0, "center"),
            (0.08, 0.35, 0.18, "scale", "ENG", 3.0, "center"),
            (0.04, 0.15, 0.12, "weight", "ENG", 2.5, "center"),
            (0.50, 0.85, 0.20, "design", "HZ", 2.8, "left"),
            (0.50, 0.55, 0.20, "review", "HZ", 2.8, "left"),
            (0.75, 0.85, 0.25, "company", "HZ", 3.5, "center"),
            (0.75, 0.35, 0.25, "date", "ENG", 3.0, "center"),
        ],
        "civil": [
            (0.08, 0.85, 0.20, "name", "HZ", 3.5, "center"),
            (0.08, 0.55, 0.20, "no", "ENG", 3.0, "center"),
            (0.08, 0.25, 0.20, "scale", "ENG", 3.0, "center"),
            (0.40, 0.85, 0.15, "design", "HZ", 2.8, "left"),
            (0.40, 0.55, 0.15, "review", "HZ", 2.8, "left"),
            (0.40, 0.25, 0.15, "date", "ENG", 2.8, "left"),
            (0.65, 0.70, 0.35, "company", "HZ", 4.0, "center"),
            (0.65, 0.25, 0.35, "approval", "HZ", 3.5, "center"),
        ],
        "electrical": [
            (0.06, 0.85, 0.22, "name", "HZ", 3.5, "center"),
            (0.06, 0.55, 0.22, "no", "ENG", 3.0, "center"),
            (0.06, 0.25, 0.22, "scale", "ENG", 3.0, "center"),
            (0.40, 0.85, 0.18, "system", "HZ", 2.8, "left"),
            (0.40, 0.55, 0.18, "voltage", "ENG", 2.8, "left"),
            (0.40, 0.25, 0.18, "date", "ENG", 2.8, "left"),
            (0.65, 0.70, 0.35, "company", "HZ", 4.0, "center"),
            (0.65, 0.25, 0.35, "design", "HZ", 3.0, "center"),
        ],
        "plumbing": [
            (0.08, 0.85, 0.20, "name", "HZ", 3.5, "center"),
            (0.08, 0.55, 0.20, "no", "ENG", 3.0, "center"),
            (0.08, 0.25, 0.20, "scale", "ENG", 3.0, "center"),
            (0.40, 0.85, 0.18, "design", "HZ", 2.8, "left"),
            (0.40, 0.55, 0.18, "review", "HZ", 2.8, "left"),
            (0.40, 0.25, 0.18, "date", "ENG", 2.8, "left"),
            (0.70, 0.70, 0.30, "company", "HZ", 4.0, "center"),
            (0.70, 0.25, 0.30, "pipe_material", "HZ", 3.0, "center"),
        ],
        "general": [
            (0.10, 0.80, 0.20, "name", "HZ", 3.5, "center"),
            (0.10, 0.45, 0.20, "no", "ENG", 3.0, "center"),
            (0.10, 0.15, 0.20, "scale", "ENG", 3.0, "center"),
            (0.45, 0.80, 0.20, "design", "HZ", 2.8, "left"),
            (0.45, 0.45, 0.20, "review", "HZ", 2.8, "left"),
            (0.45, 0.15, 0.20, "date", "ENG", 2.8, "left"),
            (0.75, 0.60, 0.25, "company", "HZ", 3.5, "center"),
        ],
    }

    field_defs = fields.get(industry, fields["general"])

    for fx, fy, fw, key, style, fh, align in field_defs:
        val = project.get(key, "")
        if not val:
            continue

        txt_h = fh * s
        cx = ox - w * fx - w * fw / 2
        cy = oy + h * fy

        if align == "left":
            cx = ox - w * fx - w * fw + 1.5 * s
            a = TextEntityAlignment.MIDDLE_LEFT
        elif align == "right":
            cx = ox - w * fx - 1.5 * s
            a = TextEntityAlignment.MIDDLE_RIGHT
        else:
            a = TextEntityAlignment.MIDDLE_CENTER

        t = msp.add_text(val, dxfattribs={
            "layer": layer_text, "height": txt_h, "style": style,
        })
        t.set_placement((cx, cy), align=a)

    if tracker:
        tracker.register(ox - w, oy, ox, oy + h, margin=10)

    return (ox - w, oy + h)


def _draw_titlebar_grid(msp, ox, oy, w, h, industry, s, layer):
    """根据行业画标题栏分隔线。"""
    if industry == "mechanical":
        # 横向线
        for ratio in [0.25, 0.45, 0.65]:
            y = oy + h * ratio
            msp.add_line((ox - w, y), (ox, y), dxfattribs={"layer": layer})
        # 竖线
        for ratio in [0.25, 0.40, 0.28]:
            x = ox - w * ratio
            msp.add_line((x, oy), (x, oy + h), dxfattribs={"layer": layer})
    elif industry == "civil":
        for ratio in [0.30, 0.55]:
            y = oy + h * ratio
            msp.add_line((ox - w, y), (ox, y), dxfattribs={"layer": layer})
        for ratio in [0.35, 0.55]:
            x = ox - w * ratio
            msp.add_line((x, oy), (x, oy + h), dxfattribs={"layer": layer})
    elif industry == "electrical":
        for ratio in [0.30, 0.55]:
            y = oy + h * ratio
            msp.add_line((ox - w, y), (ox, y), dxfattribs={"layer": layer})
        for ratio in [0.33, 0.55]:
            x = ox - w * ratio
            msp.add_line((x, oy), (x, oy + h), dxfattribs={"layer": layer})
    elif industry == "plumbing":
        for ratio in [0.30, 0.55]:
            y = oy + h * ratio
            msp.add_line((ox - w, y), (ox, y), dxfattribs={"layer": layer})
        for ratio in [0.35, 0.55]:
            x = ox - w * ratio
            msp.add_line((x, oy), (x, oy + h), dxfattribs={"layer": layer})
    else:
        for ratio in [0.30, 0.55]:
            y = oy + h * ratio
            msp.add_line((ox - w, y), (ox, y), dxfattribs={"layer": layer})
        for ratio in [0.33, 0.60]:
            x = ox - w * ratio
            msp.add_line((x, oy), (x, oy + h), dxfattribs={"layer": layer})


# ══════════════════════════════════════════════════════════
#  一键创建模板图纸
# ══════════════════════════════════════════════════════════

def create_sheet(msp, paper: str = "A2",
                  industry: str = "mechanical",
                  project: dict = None,
                  scale: float = 100.0,
                  layer: str = "粗实线"):
    """一键创建带图框和标题栏的模板图纸。

    返回: (w, h, ix, iy, iw, ih) — 可用于定位后续内容。
    """
    # 图框
    pw, ph, ix, iy, iw, ih = draw_sheet_frame(
        msp, paper_size=paper, scale=scale, layer=layer)

    # 标题栏（放在右下角内框）
    tb_w = 180.0 if paper in ("A0", "A1", "A0_L", "A1_L") else 130.0
    tb_h = 56.0 if paper in ("A0", "A1", "A0_L", "A1_L") else 40.0

    draw_title_block(
        msp, (ix + iw, iy), width=tb_w, height=tb_h,
        project=project, industry=industry, scale=scale, layer_grid=layer)

    return (pw, ph, ix, iy, iw, ih)

