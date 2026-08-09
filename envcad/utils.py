"""公共工具函数 v1.5 — 坐标圆整、文字宽度估算等。

集中管理跨模块复用的工具函数，消除 _r/_round_xy/_tri 在 20+ 模块中的重复定义。
所有其他模块应从此处导入，而非自行定义。
"""
from __future__ import annotations

import math
from typing import Tuple

# 精度常量
DEFAULT_PRECISION = 0.01  # mm
DEFAULT_GRID = 1.0        # mm


# ══════════════════════════════════════════════════════════
#  坐标处理（统一替代各模块的 _r/_round_xy/_ir）
# ══════════════════════════════════════════════════════════

def round_coord(val: float, prec: float = DEFAULT_PRECISION) -> float:
    """圆整单个坐标值到指定精度。"""
    return round(val / prec) * prec


def round_xy(x: float, y: float, prec: float = DEFAULT_PRECISION) -> Tuple[float, float]:
    """圆整坐标对到指定精度。"""
    return (round(x / prec) * prec, round(y / prec) * prec)


# 兼容别名：各模块中 _r 函数的统一实现
_r = round_xy
_r.__doc__ = "兼容别名：圆整坐标对（与 round_xy 相同）"


def snap_grid(val: float, grid: float = DEFAULT_GRID) -> float:
    """对齐到格网。"""
    return round(val / grid) * grid


def snap_pt(x: float, y: float, grid: float = DEFAULT_GRID) -> Tuple[float, float]:
    """对齐到格网（先圆整再格网）。"""
    return (snap_grid(round(x, 4), grid), snap_grid(round(y, 4), grid))


# ══════════════════════════════════════════════════════════
#  文字处理
# ══════════════════════════════════════════════════════════

def estimate_text_width(text: str, height: float) -> float:
    """精确估算文字宽度（mm）。修复版：含安全系数。"""
    w = 0.0
    for ch in str(text):
        if '\u4e00' <= ch <= '\u9fff' or '\u3000' <= ch <= '\u303f':
            w += height * 0.85  # 中文（更精确）
        elif ord(ch) > 127:
            w += height * 0.85  # 全角符号
        else:
            w += height * 0.50  # ASCII
    return w * 1.15  # 安全系数


# ══════════════════════════════════════════════════════════
#  图元绘制辅助
# ══════════════════════════════════════════════════════════

def _tri_standard(msp, tip: Tuple[float, float], direction: str = "up", 
                  size: float = 1.0, layer: str = "三角标高") -> None:
    """绘制标准三角标高符号（方向字符串接口）。

    Args:
        msp: ezdxf modelspace
        tip: 三角顶点坐标 (x, y)
        direction: 方向 ("up", "down", "left", "right")
        size: 三角边长（mm）
        layer: 图层名
    """
    x, y = tip
    h = size * 0.866  # 等边三角形高
    
    if direction == "up":
        pts = [(x, y), (x - size/2, y - h), (x + size/2, y - h)]
    elif direction == "down":
        pts = [(x, y), (x - size/2, y + h), (x + size/2, y + h)]
    elif direction == "left":
        pts = [(x, y), (x + h, y - size/2), (x + h, y + size/2)]
    elif direction == "right":
        pts = [(x, y), (x - h, y - size/2), (x - h, y + size/2)]
    else:
        pts = [(x, y), (x - size/2, y - h), (x + size/2, y - h)]
    
    # 绘制填充三角
    try:
        hatch = msp.add_hatch(color=7, dxfattribs={"layer": layer})
        hatch.paths.add_polyline_path(pts, is_closed=True)
        hatch.set_pattern_fill("SOLID", scale=1)
    except Exception as _e:
        # 兼容性回退：用多段线代替填充
        msp.add_lwpolyline(pts + [pts[0]], dxfattribs={"layer": layer})


def _tri_vector(msp, tip: Tuple[float, float], direction: Tuple[float, float],
                size: float, layer: str = "三角标高") -> None:
    """绘制三角标高符号（方向向量接口，兼容旧版）。

    Args:
        msp: ezdxf modelspace
        tip: 三角顶点坐标 (x, y)
        direction: 方向向量 (dx, dy)，自动归一化
        size: 三角边长（mm）
        layer: 图层名
    """
    tx, ty = tip
    dx, dy = direction
    # 归一化方向向量
    length = math.sqrt(dx * dx + dy * dy)
    if length < 1e-6:
        dx, dy = 0, -1  # 默认向上
    else:
        dx, dy = dx / length, dy / length
    
    h = 3 * size  # 三角高度
    w = 1.5 * size  # 三角宽度
    px, py = -dy * w, dx * w  # 垂直方向偏移
    
    pts = [
        (tx, ty),
        (tx - h * dx + px, ty - h * dy + py),
        (tx - h * dx - px, ty - h * dy - py)
    ]
    
    try:
        msp.add_solid(pts + [pts[0]], dxfattribs={"layer": layer})
    except Exception as _e:
        msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": layer})


# 默认使用向量版本以保持向后兼容
_tri = _tri_vector


def draw_elevation_triangle(msp, tip: Tuple[float, float], direction: str = "up",
                            size: float = 1.0, layer: str = "三角标高") -> None:
    """公开接口：绘制三角标高符号（标准方向接口）。"""
    _tri_standard(msp, tip, direction, size, layer)
