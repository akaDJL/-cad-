"""碰撞检测增强补丁 v1.5 —— 文字/符号/线条碰撞全面修复。

相比 v1.0 的关键改进（解决"仍然碰撞"问题）：
  1. 障碍几何类型全覆盖：LINE / LWPOLYLINE / POLYLINE / ARC / CIRCLE /
     SPLINE 全部采样为线段或圆参与检测。
     —— v1.0 只查 LINE，导致多段线/圆/弧上的文字碰撞被完全漏检。
  2. 文字-文字碰撞：TEXT/MTEXT 互相作为障碍，自动错开。
  3. 文字-符号碰撞：INSERT 块（工程符号）作为障碍物参与避让。
  4. 包围盒-线段精确相交：用 segment-rectangle 相交代替"仅中心点距离"，
     解决宽文字跨线但中心不在线段上的漏检。
  5. 螺旋重排同时避让所有障碍（线段+文字+符号），避免移位后又落到别处。
  6. 空间网格加速：邻域查询，避免 O(T×L) 全量两两比较。

公共 API 保持兼容：TrackedMSpace, post_process_overlaps。
"""
from __future__ import annotations

import math
from typing import List, Tuple, Optional, Dict, Any

from ezdxf.enums import TextEntityAlignment

# ─── 常量 ───────────────────────────────────────────────
_GRID = 200.0           # 空间网格单元尺寸 (mm)
_TOL = 0.5              # 文字包围盒基础膨胀 (mm)
_CLEAR = 1.5            # 候选检测/入库净距 (mm)，保证移位后留有间隙而非贴边
_LINE_HIT_TOL = 1.5     # 文字边到线段的命中容差 (mm)
_CIRCLE_INTERIOR_MIN_R = 3.0   # 仅对半径大于此值的圆做"内部包含"检测，避免小圆点误判
_SEG_SAMPLES = 24       # 圆弧/圆采样段数


# ─── 文字宽度 / 纯文本 / 高度 / 位置 ──────────────────────
def _estimate_text_width(text: str, height: float) -> float:
    """与 standards/annotate._estimate_text_width 一致的宽度估算。"""
    w = 0.0
    for ch in str(text):
        if '\u4e00' <= ch <= '\u9fff' or '\u3000' <= ch <= '\u303f':
            w += height * 0.85
        elif ord(ch) > 127:
            w += height * 0.85
        else:
            w += height * 0.50
    return w * 1.15


def _text_plain(e) -> str:
    try:
        if e.dxftype() == "MTEXT":
            return e.plain_text()
    except Exception:
        pass
    try:
        return str(e.dxf.text)
    except Exception:
        return ""


def _text_height(e) -> float:
    try:
        return float(e.dxf.height)
    except Exception:
        try:
            return float(e.dxf.char_height)
        except Exception:
            return 3.0


def _entity_insert(e) -> Optional[Tuple[float, float]]:
    """兼容获取实体定位点（对齐点优先，回退到插入点）。"""
    try:
        ap = e.dxf.align_point
        return (ap.x, ap.y)
    except Exception:
        try:
            ip = e.dxf.insert
            return (ip.x, ip.y)
        except Exception:
            return None


def _text_halign(e) -> int:
    """返回 TEXT/MTEXT 的水平对齐：1=左 2=中 3=右（近似）。"""
    try:
        return int(e.dxf.halign)
    except Exception:
        return 1


# ─── 几何采样 ───────────────────────────────────────────
def _arc_to_segments(cx: float, cy: float, r: float,
                     a0: float, a1: float, n: int = _SEG_SAMPLES
                     ) -> List[Tuple[float, float, float, float]]:
    """圆弧采样为线段列表（角度单位：度）。"""
    segs: List[Tuple[float, float, float, float]] = []
    if a1 < a0:
        a1 += 360.0
    total = math.radians(a1 - a0)
    for i in range(n):
        t0 = math.radians(a0) + total * i / n
        t1 = math.radians(a0) + total * (i + 1) / n
        segs.append((cx + r * math.cos(t0), cy + r * math.sin(t0),
                     cx + r * math.cos(t1), cy + r * math.sin(t1)))
    return segs


def _polyline_points(e) -> List[Tuple[float, float]]:
    try:
        pts = [(p[0], p[1]) for p in e.get_points()]
    except Exception:
        pts = []
    return pts


# ─── 障碍结构收集 ───────────────────────────────────────
def _collect_obstacles(msp) -> List[Dict[str, Any]]:
    """扫描 modelspace，构建障碍列表。

    每个障碍: {'kind': 'seg'|'circle'|'poly'|'rect', 'bbox': (x0,y0,x1,y1), ...}
      seg:    x1,y1,x2,y2
      circle: cx,cy,r
      poly:   pts (闭合多边形顶点)
      rect:   x0,y0,x1,y1（文字/符号包围盒）
    """
    obstacles: List[Dict[str, Any]] = []
    for e in msp:
        try:
            t = e.dxftype()
            if t == "LINE":
                s = e.dxf.start
                en = e.dxf.end
                x1, y1, x2, y2 = s.x, s.y, en.x, en.y
                obstacles.append({
                    'kind': 'seg',
                    'bbox': (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)),
                    'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2,
                })
            elif t in ("LWPOLYLINE", "POLYLINE"):
                pts = _polyline_points(e)
                if len(pts) < 2:
                    continue
                closed = bool(getattr(e, 'closed', False))
                bbox = (min(p[0] for p in pts), min(p[1] for p in pts),
                        max(p[0] for p in pts), max(p[1] for p in pts))
                obstacles.append({
                    'kind': 'poly',
                    'bbox': bbox,
                    'pts': (pts + [pts[0]]) if closed else pts,
                })
            elif t == "ARC":
                c = e.dxf.center
                r = float(e.dxf.radius)
                for seg in _arc_to_segments(c.x, c.y, r,
                                            float(e.dxf.start_angle),
                                            float(e.dxf.end_angle)):
                    x1, y1, x2, y2 = seg
                    obstacles.append({
                        'kind': 'seg',
                        'bbox': (min(x1, x2), min(y1, y2),
                                 max(x1, x2), max(y1, y2)),
                        'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2,
                    })
            elif t == "CIRCLE":
                c = e.dxf.center
                r = float(e.dxf.radius)
                bbox = (c.x - r, c.y - r, c.x + r, c.y + r)
                obstacles.append({
                    'kind': 'circle', 'bbox': bbox,
                    'cx': c.x, 'cy': c.y, 'r': r,
                })
            elif t == "SPLINE":
                try:
                    raw = list(e.flattening(0.1))
                    pts = [(p[0], p[1]) for p in raw]
                except Exception:
                    try:
                        pts = [(p[0], p[1]) for p in e.control_points]
                    except Exception:
                        pts = []
                if len(pts) < 2:
                    continue
                for i in range(len(pts) - 1):
                    x1, y1 = pts[i]
                    x2, y2 = pts[i + 1]
                    obstacles.append({
                        'kind': 'seg',
                        'bbox': (min(x1, x2), min(y1, y2),
                                 max(x1, x2), max(y1, y2)),
                        'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2,
                    })
            elif t in ("TEXT", "MTEXT"):
                res = _text_bbox_of(e)
                if res is None:
                    continue
                bbox, _ = res
                obstacles.append({
                    'kind': 'rect', 'bbox': bbox,
                    'x0': bbox[0], 'y0': bbox[1], 'x1': bbox[2], 'y1': bbox[3],
                    '_src': e,  # 记录源实体，检测时跳过自身
                })
            elif t == "INSERT":
                try:
                    bb = e.bbox()
                    if bb is None:
                        continue
                    mn, mx = bb.extmin, bb.extmax
                    obstacles.append({
                        'kind': 'rect', 'bbox': (mn.x, mn.y, mx.x, mx.y),
                        'x0': mn.x, 'y0': mn.y, 'x1': mx.x, 'y1': mx.y,
                        'sym': True,
                    })
                except Exception:
                    continue
        except Exception:
            continue
    return obstacles


# ─── 空间网格 ───────────────────────────────────────────
class _Grid:
    """均匀网格：障碍按包围盒插入所有覆盖单元，查询时取并集。"""

    def __init__(self, cell: float = _GRID):
        self.cell = cell
        self.buckets: Dict[Tuple[int, int], List[Any]] = {}

    def insert(self, bbox, item) -> None:
        x0, y0, x1, y1 = bbox
        c = self.cell
        ix0, iy0 = int(math.floor(x0 / c)), int(math.floor(y0 / c))
        ix1, iy1 = int(math.floor(x1 / c)), int(math.floor(y1 / c))
        for ix in range(ix0, ix1 + 1):
            for iy in range(iy0, iy1 + 1):
                self.buckets.setdefault((ix, iy), []).append(item)

    def query(self, bbox) -> List[Any]:
        x0, y0, x1, y1 = bbox
        c = self.cell
        ix0, iy0 = int(math.floor(x0 / c)), int(math.floor(y0 / c))
        ix1, iy1 = int(math.floor(x1 / c)), int(math.floor(y1 / c))
        seen = set()
        out: List[Any] = []
        for ix in range(ix0, ix1 + 1):
            for iy in range(iy0, iy1 + 1):
                for it in self.buckets.get((ix, iy), ()):
                    oid = id(it)
                    if oid not in seen:
                        seen.add(oid)
                        out.append(it)
        return out


# ─── 几何相交 ───────────────────────────────────────────
def _point_in_rect(px: float, py: float, x0: float, y0: float,
                   x1: float, y1: float, tol: float = 0.0) -> bool:
    return (x0 - tol) <= px <= (x1 + tol) and (y0 - tol) <= py <= (y1 + tol)


def _ccw(ax, ay, bx, by, cx, cy):
    return (cy - ay) * (bx - ax) - (by - ay) * (cx - ax)


def _seg_seg(p1, p2, p3, p4) -> bool:
    """线段 p1p2 与 p3p4 是否相交（不含共线退化情况）。"""
    a1 = _ccw(p1[0], p1[1], p2[0], p2[1], p3[0], p3[1])
    a2 = _ccw(p1[0], p1[1], p2[0], p2[1], p4[0], p4[1])
    a3 = _ccw(p3[0], p3[1], p4[0], p4[1], p1[0], p1[1])
    a4 = _ccw(p3[0], p3[1], p4[0], p4[1], p2[0], p2[1])
    return ((a1 > 0) != (a2 > 0)) and ((a3 > 0) != (a4 > 0))


def _seg_rect(x1, y1, x2, y2, rx0, ry0, rx1, ry1,
              tol: float = _LINE_HIT_TOL) -> bool:
    """线段是否与矩形相交（含端点落入矩形）。"""
    # 包围盒快速拒绝
    if (max(x1, x2) < rx0 - tol or min(x1, x2) > rx1 + tol or
            max(y1, y2) < ry0 - tol or min(y1, y2) > ry1 + tol):
        return False
    # 端点落入矩形
    if (_point_in_rect(x1, y1, rx0, ry0, rx1, ry1, tol) or
            _point_in_rect(x2, y2, rx0, ry0, rx1, ry1, tol)):
        return True
    # 与矩形四条边相交
    edges = [
        (rx0, ry0, rx1, ry0), (rx1, ry0, rx1, ry1),
        (rx1, ry1, rx0, ry1), (rx0, ry1, rx0, ry0),
    ]
    for e in edges:
        if _seg_seg((x1, y1), (x2, y2), (e[0], e[1]), (e[2], e[3])):
            return True
    return False


def _point_in_polygon(px: float, py: float,
                      pts: List[Tuple[float, float]]) -> bool:
    inside = False
    n = len(pts)
    j = n - 1
    for i in range(n):
        xi, yi = pts[i]
        xj, yj = pts[j]
        if ((yi > py) != (yj > py)) and \
                (px < (xj - xi) * (py - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside


def _circle_rect(cx, cy, r, rx0, ry0, rx1, ry1) -> bool:
    """圆是否与矩形相交（含矩形落入圆内 / 圆内包含矩形角点）。"""
    if _point_in_rect(cx, cy, rx0, ry0, rx1, ry1):
        return True
    for (x, y) in [(rx0, ry0), (rx1, ry0), (rx1, ry1), (rx0, ry1)]:
        if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
            return True
    for seg in _arc_to_segments(cx, cy, r, 0, 360, 16):
        if _seg_rect(seg[0], seg[1], seg[2], seg[3], rx0, ry0, rx1, ry1,
                     tol=0.0):
            return True
    return False


def _obstacle_hits_text(o: Dict[str, Any],
                        rx0, ry0, rx1, ry1) -> bool:
    """判断障碍 o 是否与文字包围盒 (rx0..ry1) 相交。"""
    k = o['kind']
    if k == 'seg':
        return _seg_rect(o['x1'], o['y1'], o['x2'], o['y2'],
                         rx0, ry0, rx1, ry1)
    if k == 'circle':
        if o['r'] >= _CIRCLE_INTERIOR_MIN_R and \
                _point_in_rect(o['cx'], o['cy'], rx0, ry0, rx1, ry1):
            return True
        return _circle_rect(o['cx'], o['cy'], o['r'], rx0, ry0, rx1, ry1)
    if k == 'poly':
        pts = o['pts']
        for i in range(len(pts) - 1):
            if _seg_rect(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1],
                         rx0, ry0, rx1, ry1):
                return True
        return False  # 多边形内包含：对大边框类图形不做内部检测，避免误判
    if k == 'rect':
        return not (rx1 < o['x0'] or rx0 > o['x1'] or
                    ry1 < o['y0'] or ry0 > o['y1'])
    return False


# ─── 文字包围盒 ─────────────────────────────────────────
def _rect_from_center(cx: float, cy: float, tw: float,
                      th_box: float, inflate: float = _TOL):
    return (cx - tw / 2 - inflate, cy - th_box / 2 - inflate,
            cx + tw / 2 + inflate, cy + th_box / 2 + inflate)


def _text_bbox_of(e) -> Optional[Tuple[Tuple[float, float, float, float],
                                       Tuple[float, float, float, float]]]:
    """返回 (bbox, (x,y,tw,th_box))；无法定位返回 None。"""
    pos = _entity_insert(e)
    if pos is None:
        return None
    x, y = pos
    th = _text_height(e)
    tw = _estimate_text_width(_text_plain(e), th)
    th_box = th * 1.4
    ha = _text_halign(e)
    if ha == 1:
        bx0, bx1 = x - tw / 2, x + tw / 2          # 居中
    elif ha == 2:
        bx0, bx1 = x - tw, x                       # 右对齐
    else:  # 0/3/4/5：左对齐或对齐/适配（按左锚点近似）
        bx0, bx1 = x, x + tw
    by0, by1 = y - th_box / 2, y + th_box / 2
    bbox = (bx0 - _TOL, by0 - _TOL, bx1 + _TOL, by1 + _TOL)
    return bbox, (x, y, tw, th_box)


# ─── 螺旋重排 ───────────────────────────────────────────
def _relocate(bbox, x, y, tw, th_box, grid: _Grid,
              max_offset: float, step: float,
              directions: int = 16) -> Optional[Tuple[float, float]]:
    """螺旋搜索不与任何障碍相交的新中心位置。"""
    angle = 0.0
    r = step
    while r <= max_offset:
        for i in range(directions):
            a = angle + i * 2 * math.pi / directions
            nx = x + r * math.cos(a)
            ny = y + r * math.sin(a)
            cand = _rect_from_center(nx, ny, tw, th_box, inflate=_CLEAR)
            near = grid.query(cand)
            hit = False
            for o in near:
                if _obstacle_hits_text(o, *cand):
                    hit = True
                    break
            if not hit:
                return nx, ny
        r += step
        angle += math.pi / directions
    return None


# ─── 主入口 ─────────────────────────────────────────────
def post_process_overlaps(doc, tracker=None,
                          max_offset: float = 50.0, step: float = 5.0,
                          protected_layers: Tuple[str, ...] =
                          ("图框", "标题栏", "文字-标题", "图框-标题"),
                          return_report: bool = False):
    """后处理扫描：检测并修复 TEXT 与（线条/文字/符号）的碰撞。

    在所有绘图完成后调用，作为最后一道防线。

    参数:
        doc:               ezdxf 文档
        tracker:           兼容保留（当前基于文档直接扫描，更可靠）
        max_offset:        最大移位距离 (mm)
        step:              螺旋搜索步长 (mm)
        protected_layers:  这些层上的文字不被移动（但仍作为障碍）
        return_report:     True 时返回统计字典，否则返回移动数量(int)

    返回: int（移动数量）或 dict（详细统计）
    """
    msp = doc.modelspace()

    obstacles = _collect_obstacles(msp)
    grid = _Grid(_GRID)
    for o in obstacles:
        grid.insert(o['bbox'], o)

    # 可移动文字：TEXT 且不在受保护层
    movable = [e for e in msp.query('TEXT')
               if e.dxf.layer not in protected_layers]
    if not movable:
        return {} if return_report else 0

    moved = hits_line = hits_text = hits_symbol = 0

    for e in movable:
        res = _text_bbox_of(e)
        if res is None:
            continue
        bbox, (x, y, tw, th_box) = res

        near = grid.query(bbox)
        overlap = False
        kind = None
        for o in near:
            if o.get('_src') is e:   # 跳过自身包围盒
                continue
            if _obstacle_hits_text(o, *bbox):
                overlap = True
                if o.get('sym'):
                    kind = 'symbol'
                elif o['kind'] == 'rect':
                    kind = 'text'
                else:
                    kind = 'line'
                break
        if not overlap:
            continue

        nx, ny = _relocate(bbox, x, y, tw, th_box, grid, max_offset, step)
        if nx is None:
            # 兜底：向上推一个字高，避免无限循环
            nx, ny = x, y + th_box * 1.5

        # 以居中方式重定位，并同步更新网格障碍，避免后续文字再压上来
        e.set_placement((nx, ny), align=TextEntityAlignment.MIDDLE_CENTER)
        new_bbox = _rect_from_center(nx, ny, tw, th_box, inflate=_CLEAR)
        grid.insert(new_bbox, {
            'kind': 'rect', 'bbox': new_bbox,
            'x0': new_bbox[0], 'y0': new_bbox[1],
            'x1': new_bbox[2], 'y1': new_bbox[3],
        })

        moved += 1
        if kind == 'line':
            hits_line += 1
        elif kind == 'text':
            hits_text += 1
        elif kind == 'symbol':
            hits_symbol += 1

    summary = (f"[collision_fix v2] 修复文字碰撞: 移动 {moved} 处 "
               f"(线条/轮廓 {hits_line}, 文字 {hits_text}, 符号 {hits_symbol})")
    print(summary)

    if return_report:
        return {'moved': moved, 'line': hits_line,
                'text': hits_text, 'symbol': hits_symbol}
    return moved


# ─── TrackedMSpace（保持不变，兼容旧调用）─────────────────
class TrackedMSpace:
    """ModelSpace 包装器：自动将几何实体注册到 BBoxTracker。

    用法：
      msp = TrackedMSpace(doc.modelspace(), tracker)
      msp.add_line((0,0), (100,0))   # 画线 + 自动注册 bbox
    """

    def __init__(self, msp, tracker):
        self._msp = msp
        self._tracker = tracker

    def __getattr__(self, name):
        return getattr(self._msp, name)

    def add_line(self, start, end, dxfattribs=None):
        e = self._msp.add_line(start, end, dxfattribs=dxfattribs or {})
        if self._tracker is not None:
            self._tracker.register_line(start, end, margin=2.0)
        return e

    def add_circle(self, center, radius, dxfattribs=None):
        e = self._msp.add_circle(center, radius, dxfattribs=dxfattribs or {})
        if self._tracker is not None:
            self._tracker.register_circle(center, radius, margin=2.0)
        return e

    def add_arc(self, center, radius, start_angle, end_angle,
                dxfattribs=None):
        e = self._msp.add_arc(center, radius, start_angle, end_angle,
                              dxfattribs=dxfattribs or {})
        if self._tracker is not None:
            self._tracker.register_arc(center, radius, start_angle,
                                       end_angle, margin=2.0)
        return e

    def add_lwpolyline(self, points, close=False, dxfattribs=None):
        e = self._msp.add_lwpolyline(points, close=close,
                                     dxfattribs=dxfattribs or {})
        if self._tracker is not None:
            pts = [(p[0], p[1]) if isinstance(p, (tuple, list))
                   else (p[0], p[1]) for p in points]
            self._tracker.register_lwpolyline(pts, margin=2.0)
        return e

    def add_spline(self, points=None, dxfattribs=None, **kwargs):
        e = self._msp.add_spline(points=points, dxfattribs=dxfattribs or {},
                                 **kwargs)
        if self._tracker is not None and points:
            pts = [(p[0], p[1]) if isinstance(p, (tuple, list))
                   else (p[0], p[1]) for p in points]
            self._tracker.register_lwpolyline(pts, margin=2.0)
        return e

    def add_solid(self, points, dxfattribs=None):
        e = self._msp.add_solid(points, dxfattribs=dxfattribs or {})
        if self._tracker is not None:
            pts = [(p[0], p[1]) if isinstance(p, (tuple, list))
                   else (p[0], p[1]) for p in points]
            self._tracker.register_lwpolyline(pts, margin=2.0)
        return e

    def add_text(self, text, dxfattribs=None):
        return self._msp.add_text(text, dxfattribs=dxfattribs or {})
