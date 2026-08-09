"""非标工件与非标设备通用绘制 v1.0。

当标准模块无法覆盖时，使用本模块从几何基元自由构建任意形状。
所有几何数据（轮廓点、尺寸、连接关系）由用户或 Agent 搜索后显式传入。

纯 ezdxf，零新依赖。

适用场景：
  * 非标机械零件（异形法兰、定制支架、特殊腔体）
  * 非标环保设备（定制反应器、特殊填料塔、异形沉淀池）
  * 任意形状外壳、流道、加强筋
  * 标准模块组合超出预设的情况
"""
from __future__ import annotations

import math
from typing import List, Optional, Tuple, Union

from ezdxf.enums import TextEntityAlignment
from ..utils import _r, _tri


# ══════════════════════════════════════════════════════════
#  自由轮廓 — 任意多边形
# ══════════════════════════════════════════════════════════

def draw_outline(msp, points: List[Tuple[float, float]],
                  closed: bool = True,
                  scale: float = 100.0,
                  layer: str = "粗实线",
                  label: str = "",
                  tracker=None):
    """自由轮廓线 — 任意多边形。

    参数:
        points: 顶点列表 [(x1, y1), (x2, y2), ...]，单位 mm
        closed: 是否闭合
        layer: 图层名（可传 "粗实线"/"虚线"/"点画线" 等）
    """
    s = scale
    pts = [_r(p[0] * s, p[1] * s) for p in points]

    if len(pts) < 2:
        return pts[0] if pts else (0, 0)

    msp.add_lwpolyline(pts, close=closed, dxfattribs={"layer": layer})

    if label:
        cx = sum(p[0] for p in pts) / len(pts)
        cy = sum(p[1] for p in pts) / len(pts)
        txt_h = 3.0 * s
        t = msp.add_text(label, dxfattribs={
            "layer": "文字", "height": txt_h, "style": "HZ",
        })
        t.set_placement((cx, cy), align=TextEntityAlignment.MIDDLE_CENTER)

    if tracker:
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        tracker.register(min(xs) - 2 * s, min(ys) - 2 * s,
                         max(xs) + 2 * s, max(ys) + 2 * s, margin=10)

    return pts[-1]


def draw_spline_outline(msp, points: List[Tuple[float, float]],
                         scale: float = 100.0,
                         layer: str = "粗实线",
                         label: str = "",
                         tracker=None):
    """样条曲线轮廓（拟合控制点）。

    参数:
        points: 控制点序列
    """
    s = scale
    pts = [_r(p[0] * s, p[1] * s) for p in points]

    if len(pts) < 3:
        # 少于 3 点降级为折线
        return draw_outline(msp, points, closed=False, scale=scale,
                             layer=layer, label=label, tracker=tracker)

    msp.add_spline(points=pts, dxfattribs={"layer": layer})

    if label:
        cx = sum(p[0] for p in pts) / len(pts)
        cy = sum(p[1] for p in pts) / len(pts)
        t = msp.add_text(label, dxfattribs={
            "layer": "文字", "height": 3.0 * s, "style": "HZ",
        })
        t.set_placement((cx, cy), align=TextEntityAlignment.MIDDLE_CENTER)

    return pts[-1]


# ══════════════════════════════════════════════════════════
#  自定义组件 — 组合形状 + 接口
# ══════════════════════════════════════════════════════════

def draw_custom_component(msp, origin, shapes: List[dict],
                           ports: List[dict] = None,
                           scale: float = 100.0,
                           label: str = "",
                           params: dict = None,
                           layer: str = "粗实线",
                           tracker=None):
    """自定义组件：从基元拼装非标设备。

    参数:
        origin: 组件参考点 (x, y) mm
        shapes: 形状列表，每项 dict:
            {"type":"rect", "x":0,"y":0,"w":100,"h":80} 矩形
            {"type":"circle","x":50,"y":40,"r":30}        圆
            {"type":"arc","x":0,"y":0,"r":50,"start":0,"end":180}
            {"type":"line","x1":0,"y1":0,"x2":100,"y2":50}
            {"type":"polygon","points":[(0,0),(10,20),(5,30)]}
            {"type":"hole","x":20,"y":30,"r":5}           孔（虚线圆）
            {"type":"slot","x":10,"y":0,"w":20,"h":6}     腰形槽
            {"type":"rib","x1":0,"y1":0,"x2":0,"y2":50,"t":5} 加强筋
        ports: 接口/管嘴 [{"x":50,"y":80,"dia":50,"label":"进料口","type":"inlet"}, ...]
        params: {"material":"316L","weight":"120kg","pressure":"1.6MPa",...}
    """
    s = scale
    ox, oy = _r(*origin)
    bbox_x, bbox_y = [ox], [oy]

    for shape in shapes:
        stype = shape.get("type", "rect")

        if stype == "rect":
            sx = ox + shape.get("x", 0) * s
            sy = oy + shape.get("y", 0) * s
            sw = shape.get("w", 100) * s
            sh = shape.get("h", 80) * s
            msp.add_lwpolyline(
                [(sx, sy), (sx + sw, sy), (sx + sw, sy + sh), (sx, sy + sh)],
                close=True, dxfattribs={"layer": layer})
            bbox_x.extend([sx, sx + sw])
            bbox_y.extend([sy, sy + sh])

        elif stype == "circle":
            sx = ox + shape.get("x", 0) * s
            sy = oy + shape.get("y", 0) * s
            sr = shape.get("r", 30) * s
            msp.add_circle((sx, sy), sr, dxfattribs={"layer": layer})
            bbox_x.extend([sx - sr, sx + sr])
            bbox_y.extend([sy - sr, sy + sr])

        elif stype == "arc":
            sx = ox + shape.get("x", 0) * s
            sy = oy + shape.get("y", 0) * s
            sr = shape.get("r", 50) * s
            sa = shape.get("start", 0)
            ea = shape.get("end", 180)
            msp.add_arc((sx, sy), radius=sr,
                         start_angle=sa, end_angle=ea,
                         dxfattribs={"layer": layer})
            bbox_x.extend([sx - sr, sx + sr])
            bbox_y.extend([sy - sr, sy + sr])

        elif stype == "line":
            sx1 = ox + shape.get("x1", 0) * s
            sy1 = oy + shape.get("y1", 0) * s
            sx2 = ox + shape.get("x2", 100) * s
            sy2 = oy + shape.get("y2", 50) * s
            msp.add_line((sx1, sy1), (sx2, sy2),
                         dxfattribs={"layer": layer})
            bbox_x.extend([sx1, sx2])
            bbox_y.extend([sy1, sy2])

        elif stype == "polygon":
            pts = [(ox + p[0] * s, oy + p[1] * s)
                   for p in shape.get("points", [])]
            if len(pts) >= 2:
                msp.add_lwpolyline(pts, close=True,
                                   dxfattribs={"layer": layer})
                bbox_x.extend([p[0] for p in pts])
                bbox_y.extend([p[1] for p in pts])

        elif stype == "hole":
            hx = ox + shape.get("x", 0) * s
            hy = oy + shape.get("y", 0) * s
            hr = shape.get("r", 5) * s
            msp.add_circle((hx, hy), hr,
                           dxfattribs={"layer": "细实线"})
            # 孔中心十字
            msp.add_line((hx - hr, hy), (hx + hr, hy),
                         dxfattribs={"layer": "中心线"})
            msp.add_line((hx, hy - hr), (hx, hy + hr),
                         dxfattribs={"layer": "中心线"})

        elif stype == "slot":
            sx = ox + shape.get("x", 0) * s
            sy = oy + shape.get("y", 0) * s
            sw = shape.get("w", 20) * s
            sh = shape.get("h", 6) * s
            r = sh / 2
            # 腰形槽 = 矩形 + 两端半圆
            msp.add_lwpolyline(
                [(sx, sy - r), (sx + sw, sy - r),
                 (sx + sw, sy + r), (sx, sy + r)],
                close=True, dxfattribs={"layer": layer})
            msp.add_arc((sx, sy), radius=r, start_angle=90, end_angle=270,
                         dxfattribs={"layer": layer})
            msp.add_arc((sx + sw, sy), radius=r, start_angle=270,
                         end_angle=90, dxfattribs={"layer": layer})

        elif stype == "rib":
            rx1 = ox + shape.get("x1", 0) * s
            ry1 = oy + shape.get("y1", 0) * s
            rx2 = ox + shape.get("x2", 0) * s
            ry2 = oy + shape.get("y2", 50) * s
            rt = shape.get("t", 5) * s
            # 加强筋：双线
            dx, dy = rx2 - rx1, ry2 - ry1
            lg = math.hypot(dx, dy)
            if lg > 0:
                px, py = -dy / lg * rt / 2, dx / lg * rt / 2
                msp.add_line((rx1 + px, ry1 + py),
                             (rx2 + px, ry2 + py),
                             dxfattribs={"layer": layer})
                msp.add_line((rx1 - px, ry1 - py),
                             (rx2 - px, ry2 - py),
                             dxfattribs={"layer": layer})
                bbox_x.extend([rx1 - rt, rx2 + rt])
                bbox_y.extend([ry1 - rt, ry2 + rt])

    # ── 接口/管嘴 ──
    if ports:
        for port in ports:
            px = ox + port.get("x", 0) * s
            py = oy + port.get("y", 0) * s
            pd = port.get("dia", 50) * s
            r = pd / 2
            pt = port.get("type", "")
            pl = port.get("label", "")

            if pt == "inlet":
                # 进料口：半实心三角
                msp.add_circle((px, py), r, dxfattribs={"layer": layer})
                _tri_arrow(msp, (px, py - r), (0, -1), s, layer)
            elif pt == "outlet":
                msp.add_circle((px, py), r, dxfattribs={"layer": layer})
                _tri_arrow(msp, (px, py + r), (0, 1), s, layer)
            else:
                msp.add_circle((px, py), r, dxfattribs={"layer": layer})

            if pl:
                t = msp.add_text(pl, dxfattribs={
                    "layer": "文字", "height": 2.2 * s, "style": "HZ",
                })
                t.set_placement((px, py + r + 3 * s if pt != "inlet" else py - r - 4 * s),
                                align=TextEntityAlignment.MIDDLE_CENTER)

    # ── 标注 ──
    if label:
        mid_x = (min(bbox_x) + max(bbox_x)) / 2
        top_y = max(bbox_y) + 4 * s
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": 3.5 * s, "style": "HZ",
        })
        t.set_placement((mid_x, top_y),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    if params:
        py = max(bbox_y) + 4 * s + 3.5 * s
        for key, val in params.items():
            t = msp.add_text(f"{key}:{val}", dxfattribs={
                "layer": "文字", "height": 2.0 * s, "style": "ENG",
            })
            t.set_placement((mid_x := (min(bbox_x) + max(bbox_x)) / 2, py),
                            align=TextEntityAlignment.MIDDLE_CENTER)
            py -= 2.5 * s

    if tracker:
        tracker.register(min(bbox_x) - 5 * s, min(bbox_y) - 5 * s,
                         max(bbox_x) + 5 * s, max(bbox_y) + 10 * s, margin=30)

    return (max(bbox_x), max(bbox_y))


# ══════════════════════════════════════════════════════════
#  自定义装配
# ══════════════════════════════════════════════════════════

def draw_custom_assembly(msp, components: List[dict],
                          connections: List[dict] = None,
                          scale: float = 100.0,
                          label: str = "",
                          layer: str = "粗实线",
                          tracker=None):
    """非标装配图：多个组件 + 连接关系。

    参数:
        components: 组件列表 [{"origin":(x,y), "draw_fn":..., "label":...}, ...]
        connections: 连接线 [{"from":(x1,y1),"to":(x2,y2),"type":"pipe","label":"DN50"}, ...]
    """
    s = scale
    bbox = {"x": [], "y": []}

    for comp in components:
        origin = comp.get("origin", (0, 0))
        shapes = comp.get("shapes", [])
        ports = comp.get("ports", [])
        clabel = comp.get("label", "")
        cparams = comp.get("params", {})

        end = draw_custom_component(
            msp, origin, shapes=shapes, ports=ports,
            scale=scale, label=clabel, params=cparams,
            layer=layer, tracker=tracker)

        bbox["x"].append(origin[0] * s)
        bbox["x"].append(end[0])
        bbox["y"].append(origin[1] * s)
        bbox["y"].append(end[1])

    # 连接线
    if connections:
        for conn in connections:
            fx, fy = conn.get("from", (0, 0))
            tx, ty = conn.get("to", (0, 0))
            ctype = conn.get("type", "pipe")
            clabel = conn.get("label", "")

            if ctype == "pipe":
                msp.add_line((fx * s, fy * s), (tx * s, ty * s),
                             dxfattribs={"layer": "工艺管道"})
            elif ctype == "signal":
                msp.add_line((fx * s, fy * s), (tx * s, ty * s),
                             dxfattribs={"layer": "仪表回路",
                                        "linetype": "DASHED"})
            elif ctype == "structural":
                msp.add_line((fx * s, fy * s), (tx * s, ty * s),
                             dxfattribs={"layer": "结构"})

            if clabel:
                mx = (fx + tx) / 2 * s
                my = (fy + ty) / 2 * s
                t = msp.add_text(clabel, dxfattribs={
                    "layer": "文字", "height": 2.2 * s, "style": "ENG",
                })
                t.set_placement((mx, my + 2 * s),
                                align=TextEntityAlignment.MIDDLE_CENTER)

    if label:
        tx, ty = sum(bbox["x"]) / len(bbox["x"]) if bbox["x"] else 0, max(bbox["y"]) + 5 * s if bbox["y"] else 0
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": 4.0 * s, "style": "HZ",
        })
        t.set_placement((tx, ty), align=TextEntityAlignment.MIDDLE_CENTER)

    return (max(bbox["x"]) if bbox["x"] else 0,
            max(bbox["y"]) if bbox["y"] else 0)


# ══════════════════════════════════════════════════════════
#  自定义标注（任意几何）
# ══════════════════════════════════════════════════════════

def draw_custom_dimension(msp, p1: Tuple[float, float],
                           p2: Tuple[float, float],
                           offset: float = 10.0,
                           scale: float = 100.0,
                           label: str = "",
                           layer: str = "尺寸标注",
                           tracker=None):
    """自定义两点标注（支持斜线标注）。

    参数:
        p1, p2: 标注起止点 (mm)
        offset: 尺寸线偏移距离（图纸 mm）
        label: 覆盖文字（空则自动计算距离）
    """
    s = scale
    x1, y1 = _r(p1[0] * s, p1[1] * s)
    x2, y2 = _r(p2[0] * s, p2[1] * s)
    off = offset * s

    dx, dy = x2 - x1, y2 - y1
    dist = math.hypot(dx, dy)
    if dist == 0:
        return (x1, y1)

    # 法向量
    ux, uy = dx / dist, dy / dist
    nx, ny = -uy, ux

    # 尺寸线（偏置）
    d1x, d1y = x1 + nx * off, y1 + ny * off
    d2x, d2y = x2 + nx * off, y2 + ny * off

    msp.add_line((x1, y1), (d1x, d1y),
                 dxfattribs={"layer": layer, "linetype": "DASHED"})
    msp.add_line((x2, y2), (d2x, d2y),
                 dxfattribs={"layer": layer, "linetype": "DASHED"})
    msp.add_line((d1x, d1y), (d2x, d2y),
                 dxfattribs={"layer": layer})

    # 箭头
    _tri_arrow(msp, (d1x, d1y), (ux, uy), s, layer)
    _tri_arrow(msp, (d2x, d2y), (-ux, -uy), s, layer)

    # 文字
    val = label or f"{dist / s:.1f}"
    mx = (d1x + d2x) / 2 + nx * 2 * s
    my = (d1y + d2y) / 2 + ny * 2 * s
    txt_h = 2.8 * s
    t = msp.add_text(val, dxfattribs={
        "layer": "文字", "height": txt_h, "style": "ENG",
    })
    t.set_placement((mx, my), align=TextEntityAlignment.MIDDLE_CENTER)

    if tracker:
        tracker.register(min(x1, x2) - off, min(y1, y2) - off,
                         max(x1, x2) + off, max(y1, y2) + off, margin=20)

    return (mx, my)


def draw_leader_note(msp, target: Tuple[float, float],
                      text: str,
                      direction: Tuple[float, float] = (1, 1),
                      length: float = 15.0,
                      scale: float = 100.0,
                      layer: str = "细实线",
                      tracker=None):
    """引出标注（自由方向）。

    参数:
        target: 标注点 (mm)
        text: 引出文字
        direction: 引出方向 (dx, dy)，自动归一化
        length: 引出线长度（图纸 mm）
    """
    s = scale
    tx, ty = _r(target[0] * s, target[1] * s)
    dx, dy = direction
    norm = math.hypot(dx, dy) or 1
    dx, dy = dx / norm, dy / norm
    L = length * s

    # 引出线
    ex, ey = tx + dx * L, ty + dy * L
    msp.add_line((tx, ty), (ex, ey), dxfattribs={"layer": layer})

    # 横线
    h_len = 6 * s
    hx = ex + (h_len if dx >= 0 else -h_len)
    msp.add_line((ex, ey), (hx, ey), dxfattribs={"layer": layer})

    # 文字
    txt_h = 2.5 * s
    t = msp.add_text(text, dxfattribs={
        "layer": "文字", "height": txt_h, "style": "HZ",
    })
    align = TextEntityAlignment.MIDDLE_LEFT if dx >= 0 else TextEntityAlignment.MIDDLE_RIGHT
    t.set_placement((hx + (1.5 * s if dx >= 0 else -1.5 * s), ey),
                    align=align)

    if tracker:
        tracker.register(min(tx, hx) - 2 * s, min(ty, ey) - 2 * s,
                         max(tx, hx) + 10 * s, max(ty, ey) + 2 * s, margin=10)

    return (hx, ey)


# ══════════════════════════════════════════════════════════
#  参数化非标形状生成器
# ══════════════════════════════════════════════════════════

def generate_rounded_rect(origin, w: float, h: float, r: float = 10):
    """生成圆角矩形轮廓点列表（用于 draw_outline）。"""
    ox, oy = origin
    pts = []
    # 右上角
    for a in [0, 30, 60, 90]:
        ang = math.radians(a)
        pts.append((ox + w - r + r * math.cos(ang),
                     oy + h - r + r * math.sin(ang)))
    # 左上角
    for a in [90, 120, 150, 180]:
        ang = math.radians(a)
        pts.append((ox + r + r * math.cos(ang),
                     oy + h - r + r * math.sin(ang)))
    # 左下角
    for a in [180, 210, 240, 270]:
        ang = math.radians(a)
        pts.append((ox + r + r * math.cos(ang),
                     oy + r + r * math.sin(ang)))
    # 右下角
    for a in [270, 300, 330, 360]:
        ang = math.radians(a)
        pts.append((ox + w - r + r * math.cos(ang),
                     oy + r + r * math.sin(ang)))
    return pts


def generate_flange(origin, od: float, id: float,
                     n_holes: int = 4, hole_dia: float = 12,
                     bolt_circle: float = 0):
    """生成法兰盘 shapes 列表（用于 draw_custom_component）。"""
    ox, oy = origin
    shapes = [
        {"type": "circle", "x": ox, "y": oy, "r": od / 2},
        {"type": "circle", "x": ox, "y": oy, "r": id / 2},
    ]
    if bolt_circle == 0:
        bolt_circle = (od + id) / 2

    for i in range(n_holes):
        ang = 2 * math.pi * i / n_holes
        hx = ox + bolt_circle / 2 * math.cos(ang)
        hy = oy + bolt_circle / 2 * math.sin(ang)
        shapes.append({
            "type": "hole", "x": hx, "y": hy, "r": hole_dia / 2
        })

    return shapes


def generate_tray_section(origin, width: float, height: float,
                           weir_h: float = 50, downcomer_w: float = 80):
    """生成塔板截面轮廓（用于 draw_outline）。"""
    ox, oy = origin
    pts = [
        (ox, oy),
        (ox + width, oy),
        (ox + width, oy + height),
        (ox + width - downcomer_w, oy + weir_h),
        (ox + downcomer_w, oy + weir_h),
        (ox, oy + height),
    ]
    return pts


# ─── 辅助 ──────────────────────────────────────────────

def _tri_arrow(msp, tip, direction, scale, layer):
    """三角箭头。"""
    tx, ty = tip
    dx, dy = direction
    h = 3.0 * scale
    w = 1.5 * scale
    px, py = -dy * w, dx * w
    pts = [(tx, ty), (tx - h * dx + px, ty - h * dy + py),
           (tx - h * dx - px, ty - h * dy - py)]
    try:
        msp.add_solid(pts + [pts[0]], dxfattribs={"layer": layer})
    except Exception as _e:
        print(f"[警告] custom 填充失败：{_e}")
