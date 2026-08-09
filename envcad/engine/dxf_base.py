"""DXF 引擎内核 v1.5 —— 精度增强 + 区域追踪。

改进:
  * 设置 LUPREC/AUPREC 头变量（显示精度 0.01mm）
  * 坐标对齐工具从 utils.py 统一导入
  * BBoxTracker 区域占用追踪器，支持文字-线条碰撞检测
"""

from __future__ import annotations

import math
import os
from typing import Optional, Tuple, List

import ezdxf
from ezdxf.units import MM

from ..standards.layers import setup_layers
from ..standards.styles import setup_text_styles, setup_dimstyles
from ..utils import snap_grid, round_xy as round_pt, snap_pt  # v1.5: 统一导入

# ─── 精度常量（保留供内部使用） ──────────────────────────
DEFAULT_GRID = 1.0          # 默认格网间距 (mm)
DEFAULT_PRECISION = 0.01    # 坐标圆整精度 (mm)
# ezdxf 头变量
HEADER_LUPREC = 2           # 线性单位小数位 (0.01)
HEADER_AUPREC = 2           # 角度单位小数位


# ─── BBox 区域追踪器 ─────────────────────────────────────

class BBoxTracker:
    """追踪已占用的矩形区域，用于碰撞检测。

    所有坐标均为 modelspace 实物坐标（mm）。
    v1.4: 增大默认 padding 到 200mm，多方向搜索回退。
    """

    def __init__(self, padding: float = 200.0):
        self._regions: List[Tuple[float, float, float, float]] = []  # (x0, y0, x1, y1)
        self.padding = padding  # 默认安全间距

    def register(self, x0: float, y0: float, x1: float, y1: float,
                 margin: float = 0.0):
        """注册区域（含扩展边距）。"""
        m = margin if margin > 0 else self.padding
        self._regions.append((x0 - m, y0 - m, x1 + m, y1 + m))

    def is_occupied(self, x0: float, y0: float, x1: float, y1: float) -> bool:
        """检查区域是否与已注册区域重叠。"""
        for rx0, ry0, rx1, ry1 in self._regions:
            if not (x1 < rx0 or x0 > rx1 or y1 < ry0 or y0 > ry1):
                return True
        return False

    def find_clear_spot(self, cx: float, cy: float, w: float, h: float,
                        direction: str = "right",
                        step: float = 200.0, max_steps: int = 25
                        ) -> Tuple[float, float]:
        """沿指定方向搜索空白位置。

        返回 (new_cx, new_cy)。找不到时回退到原位置 + 大偏移。
        """
        dirs = {
            "right": (1, 0), "left": (-1, 0), "up": (0, 1), "down": (0, -1),
        }
        dx, dy = dirs.get(direction, (1, 0))

        for i in range(1, max_steps + 1):
            nx, ny = cx + dx * i * step, cy + dy * i * step
            x0, y0 = nx - w / 2, ny - h / 2
            x1, y1 = nx + w / 2, ny + h / 2
            if not self.is_occupied(x0, y0, x1, y1):
                return nx, ny
        # fallback: 大幅偏移
        return cx + dx * max_steps * step, cy + dy * max_steps * step


    def register_line(self, start, end, margin: float = 0.0):
        """注册线段包围盒。"""
        x0, y0 = start[0], start[1]
        x1, y1 = end[0], end[1]
        self.register(
            min(x0, x1), min(y0, y1),
            max(x0, x1), max(y0, y1),
            margin=margin
        )

    def register_circle(self, center, radius, margin: float = 0.0):
        """注册圆形包围盒。"""
        cx, cy = center[0], center[1]
        self.register(
            cx - radius, cy - radius,
            cx + radius, cy + radius,
            margin=margin
        )

    def register_arc(self, center, radius, start_angle, end_angle,
                     margin: float = 0.0):
        """注册圆弧包围盒（保守估计用整圆包围盒）。"""
        self.register_circle(center, radius, margin)

    def register_lwpolyline(self, points, margin: float = 0.0,
                             closed: bool = False, outline_only: bool = False):
        """注册多段线包围盒。

        outline_only=True 时只注册各边线段的窄条区域（不标记内部），
        适用于闭合矩形/多边形，避免内部文字被误判为碰撞。
        """
        if not points:
            return

        if outline_only and len(points) >= 2:
            # 只注册边线段的窄条（margin 控制宽度）
            pts = list(points)
            if closed:
                pts.append(pts[0])
            for i in range(len(pts) - 1):
                self.register_line(pts[i], pts[i+1], margin=margin)
        else:
            # 默认行为：注册整体包围盒
            xs = [p[0] for p in points]
            ys = [p[1] for p in points]
            self.register(
                min(xs), min(ys),
                max(xs), max(ys),
                margin=margin
            )

    def register_entity(self, entity, margin: float = 0.0):
        """通用注册：根据实体类型自动选择注册方法。"""
        dxftype = entity.dxftype()
        if dxftype == "LINE":
            self.register_line(
                (entity.dxf.start.x, entity.dxf.start.y),
                (entity.dxf.end.x, entity.dxf.end.y),
                margin=margin
            )
        elif dxftype == "CIRCLE":
            self.register_circle(
                (entity.dxf.center.x, entity.dxf.center.y),
                entity.dxf.radius,
                margin=margin
            )
        elif dxftype == "ARC":
            self.register_arc(
                (entity.dxf.center.x, entity.dxf.center.y),
                entity.dxf.radius,
                entity.dxf.start_angle,
                entity.dxf.end_angle,
                margin=margin
            )
        elif dxftype in ("LWPOLYLINE", "POLYLINE"):
            try:
                pts = [(p[0], p[1]) for p in entity.get_points()]
                self.register_lwpolyline(pts, margin=margin)
            except Exception as _e:
                print(f'[WARNING] dxf_base.py: {_e}')
        elif dxftype == "SPLINE":
            try:
                pts = [(p[0], p[1]) for p in entity.control_points]
                self.register_lwpolyline(pts, margin=margin)
            except Exception as _e:
                print(f'[WARNING] dxf_base.py: {_e}')

    def spiral_find_clear_spot(self, cx, cy, w, h,
                                max_radius=500.0, step=10.0
                                ) -> Tuple[float, float]:
        """螺旋搜索空白位置（比线性搜索更全面）。

        从原点向外螺旋扩展，覆盖所有方向。
        """
        # 先检查原位
        if not self.is_occupied(cx - w/2, cy - h/2, cx + w/2, cy + h/2):
            return cx, cy

        angle = 0.0
        r = step
        directions = 16  # 每圈采样点数

        while r <= max_radius:
            for i in range(directions):
                a = angle + i * 2 * math.pi / directions
                nx = cx + r * math.cos(a)
                ny = cy + r * math.sin(a)
                x0, y0 = nx - w/2, ny - h/2
                x1, y1 = nx + w/2, ny + h/2
                if not self.is_occupied(x0, y0, x1, y1):
                    return nx, ny
            r += step
            angle += math.pi / directions  # 旋转半步

        # 最终 fallback
        return cx, cy + h * 3

    def clear(self):
        """清空所有记录。"""
        self._regions.clear()


# ─── DXF 创建与保存 ─────────────────────────────────────

def new_drawing(scale: float = 100.0, setup_std: bool = True,
                tracker: Optional[BBoxTracker] = None,
                return_tracker: bool = False,
                use_fixes: bool = True):
    """创建一张新图。

    scale: 出图比例倒数（1:100 → 100）。
    tracker: 可选 BBoxTracker 实例，用于后续碰撞检测。
    return_tracker: 设为 True 时返回 3 元组 (doc, dim, tracker)。
    use_fixes: 设为 True 时应用 fix_patch 修复（线型/碰撞/出框）。

    默认返回 (doc, dimstyle_name)，兼容旧调用。
    """
    doc = ezdxf.new("R2018", setup=True)
    doc.units = MM

    # 设置单位头变量
    doc.header["$INSUNITS"] = 13          # 13 = mm
    doc.header["$LUNITS"] = 2             # 十进制
    doc.header["$LUPREC"] = HEADER_LUPREC  # 线性精度
    doc.header["$AUNITS"] = 0             # 十进制度
    doc.header["$AUPREC"] = HEADER_AUPREC  # 角度精度

    # 设置 DIM 精度变量
    try:
        doc.header["$DIMDEC"] = 2
        doc.header["$DIMRND"] = 0.0
        doc.header["$DIMTDEC"] = 2
    except Exception as _e:
        print(f'[警告] 操作失败：{_e}')  # 旧版 ezdxf 可能不支持

    if setup_std:
        setup_text_styles(doc)
        if use_fixes:
            from ..fix_patch import setup_layers_fixed
            setup_layers_fixed(doc)
        else:
            setup_layers(doc)

    dim_name = setup_dimstyles(doc, scale) if setup_std else "Standard"

    # 返回追踪器
    if tracker is None:
        tracker = BBoxTracker()
    tracker.clear()

    if return_tracker:
        return doc, dim_name, tracker
    return doc, dim_name


def save_dxf(doc, path: str) -> str:
    """保存 DXF，自动创建父目录，返回绝对路径。"""
    path = os.path.abspath(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    doc.saveas(path)
    return path


# ─── text-to-cad 适配器 ─────────────────────────────────

def from_gen_dxf(gen_dxf_func, scale: float = 100.0, setup_std: bool = True):
    """适配 text-to-cad 的 gen_dxf() 约定。"""
    doc, dim_name = new_drawing(scale=scale, setup_std=setup_std)
    result = gen_dxf_func(doc)
    return result if result is not None else doc, dim_name
