"""批量出图引擎 v1.0 — 多规格紧固件自动排版 / 多图合并 / 分别输出。

两种批量模式：
  1. 合并模式（mode='merge'）：多规格排版到同一张 DXF，自动网格布局
  2. 分别模式（mode='split'）：每个规格单独输出一个 DXF

用法：
  from envcad.engine.batch_layout import batch_fasteners
  paths = batch_fasteners(out_dir, specs=["M6","M8","M10"],
                          component="bolt", mode="merge")
"""
from __future__ import annotations

import os
import math
from typing import List, Optional, Dict, Tuple

from ..engine.dxf_base import new_drawing, save_dxf, BBoxTracker
from ..engine.collision_fix import TrackedMSpace, post_process_overlaps
from ..standards.styles import setup_text_styles
from ..standards.layers import setup_layers
from ..standards.frame import draw_frame, FrameInfo, save_dxf_autofit
from ..standards.annotate import _t
from ..components.fasteners import (
    draw_hex_bolt, draw_hex_nut, draw_screw,
    draw_washer, draw_spring_washer, draw_bolt_assembly,
    list_specs,
)

# ─── 组件调度表 ──────────────────────────────────────────
_DRAW_FUNCS = {
    "bolt": draw_hex_bolt,
    "nut": draw_hex_nut,
    "screw_hex": lambda msp, c, s, spec, L, **kw: draw_screw(
        msp, c, s, spec, L, screw_type="hex_socket", **kw),
    "screw_pan": lambda msp, c, s, spec, L, **kw: draw_screw(
        msp, c, s, spec, L, screw_type="pan", **kw),
    "washer_flat": lambda msp, c, s, spec, L=30, **kw: draw_washer(
        msp, c, s, spec, washer_type="flat", **kw),
    "washer_spring": lambda msp, c, s, spec, L=30, **kw: draw_spring_washer(
        msp, c, s, spec, **kw),
    "assembly": draw_bolt_assembly,
}

_SPEC_TABLES = {
    "bolt": "bolt",
    "nut": "nut",
    "screw_hex": "screw_hex",
    "screw_pan": "screw_pan",
    "washer_flat": "washer_flat",
    "washer_spring": "washer_spring",
    "assembly": "bolt",
}


def _estimate_cell_size(spec: str, component: str, scale: float,
                        length: float = 30.0) -> Tuple[float, float]:
    """估算单个组件所需排版单元格大小 (width, height) mm。"""
    from ..components.fasteners import (
        get_bolt_params, get_nut_params, get_screw_params, get_washer_params
    )
    s = scale
    if component in ("bolt", "assembly"):
        p = get_bolt_params(spec, length)
        w = (p["k"] + length + 10) * s
        h = (p["s"] * 2 + 20) * s
    elif component == "nut":
        p = get_nut_params(spec)
        w = (p["m"] + 15) * s
        h = (p["s"] * 2 + 20) * s
    elif component in ("screw_hex", "screw_pan"):
        st = "hex_socket" if component == "screw_hex" else "pan"
        p = get_screw_params(spec, st, length)
        w = (p["k"] + length + 10) * s
        h = (p["dk"] * 2 + 20) * s
    elif component in ("washer_flat", "washer_spring"):
        wt = "flat" if component == "washer_flat" else "spring"
        p = get_washer_params(spec, wt)
        w = (p["d2"] + 15) * s
        h = (p["d2"] * 2 + 20) * s
    else:
        w, h = 80 * s, 60 * s
    return w, h


def _grid_layout(n: int, cell_w: float, cell_h: float,
                 area_w: float, area_h: float,
                 padding: float = 15.0) -> List[Tuple[float, float]]:
    """计算 n 个单元格在区域内的网格排版坐标（左上角起始）。

    返回 [(x0, y0), ...] 列表，坐标系：区域内左上角为原点。
    """
    cols = max(1, int((area_w + padding) / (cell_w + padding)))
    rows = math.ceil(n / cols)
    positions = []
    for i in range(n):
        col = i % cols
        row = i // cols
        x = col * (cell_w + padding)
        # y 从上往下（DXF y 向上，所以反转）
        y = area_h - (row + 1) * (cell_h + padding)
        positions.append((x, y))
    return positions


def batch_fasteners(
    out_dir: str,
    specs: Optional[List[str]] = None,
    component: str = "bolt",
    mode: str = "merge",
    scale: float = 1.0,
    length: float = 30.0,
    orientation: str = "h",
    title: str = "紧固件批量出图",
    custom_params: Optional[Dict[str, Dict]] = None,
) -> List[str]:
    """批量生成紧固件图纸。

    参数：
      out_dir:      输出目录
      specs:        规格列表如 ["M6","M8","M10"]，None 则用全部国标规格
      component:    组件类型 bolt/nut/screw_hex/screw_pan/
                    washer_flat/washer_spring/assembly
      mode:         'merge' 合并到一张图 / 'split' 分别输出
      scale:        出图比例倒数（1:1=1）
      length:       螺栓/螺钉长度（mm）
      orientation:  'h' 水平 / 'v' 竖直
      title:        图纸标题
      custom_params: 自定义参数 {spec: {d, P, s, ...}}

    返回：生成的 DXF 文件路径列表
    """
    os.makedirs(out_dir, exist_ok=True)

    # 默认全部规格
    if specs is None:
        spec_key = _SPEC_TABLES.get(component, "bolt")
        specs = list_specs(spec_key)

    func = _DRAW_FUNCS.get(component, draw_hex_bolt)
    custom_params = custom_params or {}

    paths = []

    if mode == "split":
        # ── 分别模式：每规格一张图 ──
        for spec in specs:
            doc, dim_name, tracker = new_drawing(
                scale=scale, return_tracker=True)
            setup_text_styles(doc)
            setup_layers(doc)
            msp = TrackedMSpace(doc.modelspace(), tracker)

            frame_info = FrameInfo(
                title=f"{title} - {spec}",
                drawing_no=f"FAST-{component[:3].upper()}",
                scale_str=f"1:{int(scale)}" if scale >= 1 else f"1:{scale}",
            )
            inner = draw_frame(doc, scale=scale, info=frame_info,
                               tracker=tracker)
            # 绘制区域中心
            cx = (inner[0] + inner[2]) / 2
            cy = (inner[1] + inner[3]) / 2

            kw = {}
            if spec in custom_params:
                kw["custom"] = custom_params[spec]
            if component in ("bolt", "assembly", "screw_hex", "screw_pan"):
                func(msp, (cx - 40 * scale, cy), scale, spec, length,
                     orientation=orientation, label=spec,
                     tracker=tracker, **kw)
            else:
                func(msp, (cx, cy), scale, spec,
                     orientation=orientation, label=spec,
                     tracker=tracker, **kw)

            post_process_overlaps(doc, tracker)
            fname = f"{component}_{spec}_L{int(length)}.dxf"
            path = save_dxf_autofit(doc, os.path.join(out_dir, fname), scale, frame_info, tracker)
            paths.append(path)

    else:
        # ── 合并模式：多规格排版到一张图 ──
        doc, dim_name, tracker = new_drawing(
            scale=scale, return_tracker=True)
        setup_text_styles(doc)
        setup_layers(doc)
        msp = TrackedMSpace(doc.modelspace(), tracker)

        frame_info = FrameInfo(
            title=title,
            drawing_no=f"FAST-{component[:3].upper()}-BATCH",
            scale_str=f"1:{int(scale)}" if scale >= 1 else f"1:{scale}",
        )
        inner = draw_frame(doc, scale=scale, info=frame_info,
                           tracker=tracker)

        area_x0, area_y0, area_x1, area_y1 = inner
        area_w = area_x1 - area_x0 - 20 * scale
        area_h = area_y1 - area_y0 - 20 * scale

        n = len(specs)
        # 取最大单元格尺寸做网格
        max_w, max_h = 0, 0
        for spec in specs:
            w, h = _estimate_cell_size(spec, component, scale, length)
            max_w = max(max_w, w)
            max_h = max(max_h, h)

        positions = _grid_layout(n, max_w, max_h, area_w, area_h)

        for i, spec in enumerate(specs):
            px, py = positions[i]
            cx = area_x0 + 10 * scale + px + max_w / 2
            cy = area_y0 + 10 * scale + py + max_h / 2

            kw = {}
            if spec in custom_params:
                kw["custom"] = custom_params[spec]
            if component in ("bolt", "assembly", "screw_hex", "screw_pan"):
                func(msp, (cx - max_w / 4, cy), scale, spec, length,
                     orientation=orientation, label=spec,
                     tracker=tracker, **kw)
            else:
                func(msp, (cx, cy), scale, spec,
                     orientation=orientation, label=spec,
                     tracker=tracker, **kw)

        post_process_overlaps(doc, tracker)
        fname = f"{component}_batch_{n}specs.dxf"
        path = save_dxf_autofit(doc, os.path.join(out_dir, fname), scale, frame_info, tracker)
        paths.append(path)

    return paths


def batch_mixed(
    out_dir: str,
    items: List[Dict],
    scale: float = 1.0,
    title: str = "紧固件混合批量出图",
) -> List[str]:
    """混合批量出图：不同类型组件排版到同一张图。

    items 格式：
      [
        {"component": "bolt", "spec": "M10", "length": 40},
        {"component": "nut", "spec": "M10"},
        {"component": "washer_flat", "spec": "M10"},
        {"component": "screw_hex", "spec": "M6", "length": 20},
        {"component": "assembly", "spec": "M8", "length": 30, "grip": 20},
      ]

    返回：DXF 文件路径列表
    """
    os.makedirs(out_dir, exist_ok=True)

    doc, dim_name, tracker = new_drawing(scale=scale, return_tracker=True)
    setup_text_styles(doc)
    setup_layers(doc)
    msp = TrackedMSpace(doc.modelspace(), tracker)

    frame_info = FrameInfo(
        title=title,
        drawing_no="FAST-MIXED-BATCH",
        scale_str=f"1:{int(scale)}" if scale >= 1 else f"1:{scale}",
    )
    inner = draw_frame(doc, scale=scale, info=frame_info, tracker=tracker)

    area_x0, area_y0, area_x1, area_y1 = inner
    area_w = area_x1 - area_x0 - 20 * scale
    area_h = area_y1 - area_y0 - 20 * scale

    n = len(items)
    max_w, max_h = 0, 0
    for item in items:
        comp = item["component"]
        spec = item.get("spec", "M10")
        L = item.get("length", 30)
        w, h = _estimate_cell_size(spec, comp, scale, L)
        max_w = max(max_w, w)
        max_h = max(max_h, h)

    positions = _grid_layout(n, max_w, max_h, area_w, area_h)

    for i, item in enumerate(items):
        comp = item["component"]
        spec = item.get("spec", "M10")
        L = item.get("length", 30)
        orientation = item.get("orientation", "h")
        func = _DRAW_FUNCS.get(comp, draw_hex_bolt)

        px, py = positions[i]
        cx = area_x0 + 10 * scale + px + max_w / 2
        cy = area_y0 + 10 * scale + py + max_h / 2

        if comp in ("bolt", "assembly", "screw_hex", "screw_pan"):
            if comp == "assembly":
                grip = item.get("grip", 20)
                func(msp, (cx - max_w / 4, cy), scale, spec, L,
                     grip=grip, orientation=orientation, label=spec,
                     tracker=tracker)
            else:
                func(msp, (cx - max_w / 4, cy), scale, spec, L,
                     orientation=orientation, label=spec, tracker=tracker)
        else:
            func(msp, (cx, cy), scale, spec,
                 orientation=orientation, label=spec, tracker=tracker)

    post_process_overlaps(doc, tracker)
    fname = f"mixed_batch_{n}items.dxf"
    path = save_dxf_autofit(doc, os.path.join(out_dir, fname), scale, frame_info, tracker)
    return [path]
