"""图片辅助绘图 v1.0 — 从图片/照片估算尺寸后生成 DXF。

本模块不包含 CV/OCR 能力（需外部 AI 视觉），但提供标准化接口：
Agent 观察图片后，将估算的几何数据填入 dict/dict 列表，即可生成图纸。

配合 WorkBuddy 的图片读取能力，形成"看图→估尺寸→出图"半自动管线。
"""
from __future__ import annotations
import math
from typing import List, Optional, Tuple
from ezdxf.enums import TextEntityAlignment

# 碰撞检测增强：复用 annotate 的文字避让逻辑
from .annotate import _t, _estimate_text_width, _round_xy


def draw_from_image_estimate(msp, origin, items: List[dict],
                              scale: float = 100.0,
                              reference_dim: dict = None,
                              label: str = "图片估算图",
                              layer: str = "粗实线",
                              tracker=None):
    """从图片估算数据直接生成 DXF。

    参数:
        origin: 图纸原点 (x, y) mm
        items: Agent 观察图片后列出的几何要素:
            [
              {"type":"circle","x":50,"y":40,"r":100,"layer":"粗实线"},
              {"type":"rect","x":0,"y":0,"w":200,"h":80},
              {"type":"hole","x":40,"y":20,"r":6},
              {"type":"slot","x":100,"y":0,"w":30,"h":8},
              {"type":"arc","x":0,"y":0,"r":150,"start":0,"end":90},
              {"type":"text","x":50,"y":120,"text":"ø200","height":3.5},
              {"type":"line","x1":0,"y1":0,"x2":100,"y2":0},
              {"type":"polygon","points":[(0,0),(20,10),(10,30),(-10,20)]},
              {"type":"spline","points":[(0,0),(10,5),(20,3),(30,8)]},
            ]
            所有坐标和尺寸单位 mm。
        reference_dim: 参考尺寸 {"known":100,"pixels_in_image":500}
                       用于推算未知尺寸。例如图中有已知 100mm 参考物，
                       在图中占 500px → 比例尺 = 0.2mm/px。
    """
    s = scale
    ox, oy = _ir(*origin)
    ratio = 1.0
    if reference_dim:
        known = reference_dim.get("known", 100)
        pix = reference_dim.get("pixels_in_image", 500)
        ratio = known / pix if pix > 0 else 1.0

    bbox_x, bbox_y = [ox], [oy]

    for item in items:
        itype = item.get("type", "rect")
        ilayer = item.get("layer", layer)

        if itype == "circle":
            cx = ox + item.get("x", 0) * ratio * s
            cy = oy + item.get("y", 0) * ratio * s
            r = item.get("r", 10) * ratio * s
            msp.add_circle((cx, cy), r, dxfattribs={"layer": ilayer})
            if tracker is not None:
                tracker.register_circle((cx, cy), r, margin=2.0)
            bbox_x.extend([cx - r, cx + r]); bbox_y.extend([cy - r, cy + r])

        elif itype == "rect":
            rx = ox + item.get("x", 0) * ratio * s
            ry = oy + item.get("y", 0) * ratio * s
            rw = item.get("w", 100) * ratio * s
            rh = item.get("h", 80) * ratio * s
            msp.add_lwpolyline(
                [(rx, ry), (rx + rw, ry), (rx + rw, ry + rh), (rx, ry + rh)],
                close=True, dxfattribs={"layer": ilayer})
            if tracker is not None:
                tracker.register_lwpolyline(
                    [(rx, ry), (rx + rw, ry), (rx + rw, ry + rh), (rx, ry + rh)],
                    margin=2.0, closed=True, outline_only=True)
            bbox_x.extend([rx, rx + rw]); bbox_y.extend([ry, ry + rh])

        elif itype == "hole":
            hx = ox + item.get("x", 0) * ratio * s
            hy = oy + item.get("y", 0) * ratio * s
            hr = item.get("r", 5) * ratio * s
            msp.add_circle((hx, hy), hr, dxfattribs={"layer": "细实线"})
            msp.add_line((hx - hr, hy), (hx + hr, hy), dxfattribs={"layer": "中心线"})
            msp.add_line((hx, hy - hr), (hx, hy + hr), dxfattribs={"layer": "中心线"})
            if tracker is not None:
                tracker.register_circle((hx, hy), hr, margin=2.0)

        elif itype == "slot":
            sx = ox + item.get("x", 0) * ratio * s
            sy = oy + item.get("y", 0) * ratio * s
            sw = item.get("w", 20) * ratio * s
            sh = item.get("h", 6) * ratio * s
            r = sh / 2
            msp.add_lwpolyline(
                [(sx, sy - r), (sx + sw, sy - r), (sx + sw, sy + r), (sx, sy + r)],
                close=True, dxfattribs={"layer": ilayer})
            msp.add_arc((sx, sy), radius=r, start_angle=90, end_angle=270,
                         dxfattribs={"layer": ilayer})
            msp.add_arc((sx + sw, sy), radius=r, start_angle=270, end_angle=90,
                         dxfattribs={"layer": ilayer})

        elif itype == "arc":
            ax = ox + item.get("x", 0) * ratio * s
            ay = oy + item.get("y", 0) * ratio * s
            ar = item.get("r", 50) * ratio * s
            sa = item.get("start", 0)
            ea = item.get("end", 180)
            msp.add_arc((ax, ay), radius=ar, start_angle=sa, end_angle=ea,
                         dxfattribs={"layer": ilayer})

        elif itype == "line":
            lx1 = ox + item.get("x1", 0) * ratio * s
            ly1 = oy + item.get("y1", 0) * ratio * s
            lx2 = ox + item.get("x2", 0) * ratio * s
            ly2 = oy + item.get("y2", 0) * ratio * s
            msp.add_line((lx1, ly1), (lx2, ly2), dxfattribs={"layer": ilayer})
            if tracker is not None:
                tracker.register_line((lx1, ly1), (lx2, ly2), margin=2.0)

        elif itype == "polygon":
            pts = [(ox + p[0] * ratio * s, oy + p[1] * ratio * s)
                   for p in item.get("points", [])]
            if len(pts) >= 2:
                msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": ilayer})
                if tracker is not None:
                    tracker.register_lwpolyline(pts, margin=2.0)
                bbox_x.extend([p[0] for p in pts])
                bbox_y.extend([p[1] for p in pts])

        elif itype == "spline":
            pts = [(ox + p[0] * ratio * s, oy + p[1] * ratio * s)
                   for p in item.get("points", [])]
            if len(pts) >= 3:
                msp.add_spline(points=pts, dxfattribs={"layer": ilayer})

        elif itype == "text":
            tx = ox + item.get("x", 0) * ratio * s
            ty = oy + item.get("y", 0) * ratio * s
            txt = item.get("text", "")
            th = item.get("height", 3.0) * s
            if txt:
                # 碰撞检测增强：走 _t() 自动避让
                _t(msp, txt, (tx, ty), th,
                   align=TextEntityAlignment.MIDDLE_CENTER,
                   layer="文字", tracker=tracker)

    if label:
        mid_x = (min(bbox_x) + max(bbox_x)) / 2
        top_y = max(bbox_y) + 5 * s
        _t(msp, label, (mid_x, top_y), 3.5 * s,
           align=TextEntityAlignment.MIDDLE_CENTER,
           layer="文字-标题", tracker=tracker)

    if reference_dim:
        ref_y = min(bbox_y) - 8 * s
        _t(msp,
           f"比例尺: {reference_dim.get('known',100)}mm = "
           f"{reference_dim.get('pixels_in_image',500)}px",
           ((min(bbox_x) + max(bbox_x)) / 2, ref_y), 2.0 * s,
           align=TextEntityAlignment.MIDDLE_CENTER,
           layer="文字", tracker=tracker)

    return (max(bbox_x), min(bbox_y))


def _ir(x: float, y: float) -> Tuple[float, float]:
    return (round(x / 0.01) * 0.01, round(y / 0.01) * 0.01)
