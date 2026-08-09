"""26. as_built_frame —— 竣工测绘图框（A3 + 竣工测绘专用标题栏）。

制图依据：
  GB/T 50001—2017《房屋建筑制图统一标准》
    · 3.1 图纸幅面（A3 横式 420×297，装订边 25，其余边 10）
    · 3.2 会签栏（100×20，栏内填写专业、实名、签名、日期）
    · 3.3 标题栏（图名、图号、比例、设计/校核/审核、设计单位）
  GB/T 14689—2008 图纸幅面和格式
  GB/T 20257.1—2017 附录C 图廓整饰样式（测绘成果图廓附注要求）

复用 envcad 既有实现：
  · envcad.standards.frame.draw_frame —— A3 图框 + 国标标题栏（经平移复用）
  · envcad.standards.templates.draw_title_block —— 附加信息栏（civil 版式）
  · envcad.standards.layers / styles —— 国标图层与仿宋 GB2312 文字样式
"""
from __future__ import annotations

from typing import List, Sequence, Tuple

from envcad.standards.templates import draw_title_block

from ._common import (FrameInfo, TextEntityAlignment, draw_frame_at,
                      ensure_doc_ready, line, polyline, text)

# ── 图上尺寸默认值 (mm) ───────────────────────────────────
SIGNOFF_W, SIGNOFF_H = 100.0, 20.0   # GB/T 50001 3.2 会签栏
SIGNOFF_COLS = 4
PANEL_W, PANEL_H = 180.0, 32.0       # 竣工测绘附加栏（与标题栏同宽）
PANEL_LABEL_W = 26.0
H_PANEL = 2.5
H_SIGNOFF = 2.5

# 竣工测绘成果必备信息项（测绘成果图廓附注常规内容）
DEFAULT_AS_BUILT_ROWS = [
    ("坐标系统", "2000国家大地坐标系"),
    ("高程系统", "1985国家高程基准"),
    ("施测单位", ""),
    ("施测日期", ""),
    ("竣工日期", ""),
    ("成图比例", "1:500"),
]


def draw_as_built_panel(msp, x: float, y: float, scale: float = 50.0,
                        rows: Sequence[Tuple[str, str]] = (),
                        width: float = PANEL_W, height: float = PANEL_H,
                        label_w: float = PANEL_LABEL_W,
                        cols: int = 2,
                        text_h: float = H_PANEL,
                        layer_grid: str = "图框",
                        layer_text: str = "文字",
                        **params):
    """竣工测绘信息附加栏（左下角定位于 (x, y)，向右上展开）。

    rows: [(标签, 值), ...]，按 cols 列自动排布。
    """
    ensure_doc_ready(msp)
    s = scale
    w, h = width * s, height * s
    rows = list(rows) or DEFAULT_AS_BUILT_ROWS
    n_row = (len(rows) + cols - 1) // cols
    rh = h / max(1, n_row)
    cw = w / cols
    lw = label_w * s

    polyline(msp, [(x, y), (x + w, y), (x + w, y + h), (x, y + h)],
             layer_grid, close=True)
    for i in range(1, n_row):
        line(msp, (x, y + i * rh), (x + w, y + i * rh), layer_grid)
    for c in range(cols):
        cx = x + c * cw
        if c:
            line(msp, (cx, y), (cx, y + h), layer_grid)
        line(msp, (cx + lw, y), (cx + lw, y + h), layer_grid)

    for i, (k, v) in enumerate(rows):
        c, r = i // n_row, i % n_row
        cx = x + c * cw
        cy = y + h - (r + 0.5) * rh
        text(msp, k, (cx + 1.5 * s, cy), text_h * s,
             align=TextEntityAlignment.MIDDLE_LEFT, layer=layer_text)
        text(msp, v, (cx + lw + 1.5 * s, cy), text_h * s,
             align=TextEntityAlignment.MIDDLE_LEFT, layer=layer_text)
    return (x, y, x + w, y + h)


def draw_signoff_bar(msp, x: float, y: float, scale: float = 50.0,
                     specialties: Sequence[str] = ("测绘", "建筑", "结构", "水电"),
                     width: float = SIGNOFF_W, height: float = SIGNOFF_H,
                     text_h: float = H_SIGNOFF,
                     layer_grid: str = "图框",
                     layer_text: str = "文字",
                     **params):
    """会签栏（GB/T 50001—2017 3.2：100mm×20mm，分格填专业/姓名/日期）。

    左下角定位于 (x, y)。
    """
    ensure_doc_ready(msp)
    s = scale
    w, h = width * s, height * s
    n = max(1, len(specialties))
    rh = h / n
    c1 = x + w * 0.25   # 专业
    c2 = x + w * 0.60   # 实名
    polyline(msp, [(x, y), (x + w, y), (x + w, y + h), (x, y + h)],
             layer_grid, close=True)
    for i in range(1, n):
        line(msp, (x, y + i * rh), (x + w, y + i * rh), layer_grid)
    for cx in (c1, c2):
        line(msp, (cx, y), (cx, y + h), layer_grid)
    for i, sp in enumerate(specialties):
        cy = y + h - (i + 0.5) * rh
        text(msp, sp, (x + 1.5 * s, cy), text_h * s,
             align=TextEntityAlignment.MIDDLE_LEFT, layer=layer_text)
    return (x, y, x + w, y + h)


def draw_as_built_frame(msp, x: float = 0.0, y: float = 0.0,
                        scale: float = 50.0,
                        title: str = "竣工测绘平面图",
                        drawing_no: str = "CG-01",
                        project: str = "××项目竣工测量",
                        unit: str = "××测绘院",
                        designer: str = "", checker: str = "", auditor: str = "",
                        date: str = "2026.07",
                        scale_str: str | None = None,
                        as_built_rows: Sequence[Tuple[str, str]] = (),
                        panel_w: float = PANEL_W, panel_h: float = PANEL_H,
                        show_panel: bool = True,
                        show_signoff: bool = True,
                        signoff_specialties: Sequence[str] = ("测绘", "建筑",
                                                              "结构", "水电"),
                        **params):
    """竣工测绘 A3 图框总装（图框与标题栏复用 envcad，附加竣工信息栏）。

    返回内框范围 (x0, y0, x1, y1)，供后续测绘内容定位。
    """
    ensure_doc_ready(msp)
    s = scale
    info = FrameInfo(
        title=title, drawing_no=drawing_no,
        scale_str=scale_str or f"1:{int(scale)}",
        designer=designer, checker=checker, auditor=auditor,
        project=project, unit=unit, date=date,
    )
    x0, y0, x1, y1 = draw_frame_at(msp, x, y, s, info)

    if show_panel:
        rows = list(as_built_rows) or [
            (k, (v or unit if k == "施测单位" else v) or
                (date if k in ("施测日期", "竣工日期") else v) or
                (info.scale_str if k == "成图比例" else v))
            for k, v in DEFAULT_AS_BUILT_ROWS
        ]
        # 附加栏置于标题栏正上方（标题栏高 56mm，见 envcad frame.TITLE_H）
        draw_as_built_panel(msp, x1 - panel_w * s, y0 + 56.0 * s, s,
                            rows=rows, width=panel_w, height=panel_h)

    if show_signoff:
        # 会签栏置于图框左上角内侧（GB/T 50001 3.2 允许置于图框上方或左方）
        draw_signoff_bar(msp, x0, y1 - SIGNOFF_H * s, s,
                         specialties=signoff_specialties)

    # 附加信息栏（复用 envcad.standards.templates 的 civil 版式）作为
    # 图框左下角的成果说明小栏
    draw_title_block(
        msp, (x0 + 120.0 * s, y0), width=120.0, height=24.0,
        project={"name": "竣工测量成果", "no": drawing_no,
                 "scale": info.scale_str, "design": designer or "—",
                 "review": checker or "—", "date": date,
                 "company": unit},
        industry="civil", scale=s, layer_grid="图框", layer_text="文字")

    return (x0, y0, x1, y1)
