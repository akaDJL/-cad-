"""模块 17 —— 轮式拖拉机侧视图（外形轮廓图）。

复用 envcad：图层（GB/T 17450 粗/中/细实线）、仿宋 GB2312 文字样式、
``standards.dim.draw_dimension`` 线性标注、``standards.annotate.draw_leader``
指引线、``standards.frame`` A3 图框。

标准依据：
  * GB/T 14689—2008 技术制图 图纸幅面和格式（图框）
  * GB/T 4457.4—2002 机械制图 图样画法 图线（粗/细实线、点画线）
  * GB/T 6960.1—2025 拖拉机术语 第1部分：整机  # TODO: verify against GB/T 6960.1（2025版替代2007版，2026-05-01实施）
    （轴距、最小离地间隙、外廓尺寸等术语定义；envcad 内置知识库
     standards_kb.json 目前未覆盖农机行业，数值均由参数显式传入）

全部尺寸为实物 mm，modelspace 按 1:1 绘制。
"""
from __future__ import annotations

import math
from typing import Dict

from ._common import (
    L_CENTER, L_MED, L_THICK, L_THIN,
    centerline, dim_h, dim_v, ground_line, leader, poly, rect, wheel,
)

#: 典型 60kW 级四轮驱动轮式拖拉机默认外廓（实物 mm）
DEFAULTS: Dict[str, float] = {
    "wheelbase": 2050.0,        # 轴距
    "front_overhang": 780.0,    # 前悬（车头端面 → 前轴）
    "rear_overhang": 900.0,     # 后悬（后轴 → 车尾端面）
    "front_wheel_d": 900.0,     # 前转向轮外径
    "rear_wheel_d": 1500.0,     # 后驱动轮外径
    "clearance": 380.0,         # 最小离地间隙
    "chassis_h": 820.0,         # 车架上平面高
    "hood_h": 1420.0,           # 发动机罩顶高
    "cab_h": 2650.0,            # 驾驶室顶高（整机高度）
    "cab_front_ratio": 0.46,    # 驾驶室前壁位置（占轴距比）
    "fender_gap": 110.0,        # 后挡泥板与胎面间隙
}


def _draw_hood(msp, x_nose, y0, x_end, chassis_h, hood_h):
    """发动机罩：前端带斜鼻锥的封闭轮廓（粗实线）。"""
    nose = (x_end - x_nose) * 0.12
    poly(msp, [
        (x_nose, y0 + chassis_h * 0.55),
        (x_nose, y0 + hood_h * 0.72),
        (x_nose + nose, y0 + hood_h),
        (x_end, y0 + hood_h),
        (x_end, y0 + chassis_h * 0.55),
    ], layer=L_THICK, closed=True)
    # 散热格栅（细实线）
    for i in range(1, 5):
        gy = y0 + chassis_h * 0.6 + i * (hood_h - chassis_h) * 0.13
        msp.add_line((x_nose + 30, gy), (x_nose + nose * 0.9, gy),
                     dxfattribs={"layer": L_THIN})


def _draw_cab(msp, x0, x1, y_floor, y_top, scale):
    """驾驶室：前风挡外倾的封闭轮廓 + 车窗 + 后视镜支架。"""
    slope = (x1 - x0) * 0.22
    poly(msp, [
        (x0, y_floor),
        (x0 + slope * 0.25, y_floor),
        (x0 + slope, y_top),
        (x1, y_top),
        (x1, y_floor),
    ], layer=L_THICK, closed=True)
    # 侧窗（细实线内框）
    inset = (x1 - x0) * 0.10
    wy0 = y_floor + (y_top - y_floor) * 0.30
    wy1 = y_top - (y_top - y_floor) * 0.12
    poly(msp, [(x0 + slope + inset, wy0), (x1 - inset, wy0),
               (x1 - inset, wy1), (x0 + slope + inset * 1.4, wy1)],
         layer=L_THIN, closed=True)
    # 车门竖分缝
    xm = (x0 + slope + x1) / 2
    msp.add_line((xm, y_floor), (xm, y_top - (y_top - y_floor) * 0.05),
                 dxfattribs={"layer": L_THIN})


def _draw_fender(msp, cx, cy, r, gap):
    """后轮挡泥板：与后轮同心的 160° 圆弧 + 前后立边。"""
    rf = r + gap
    msp.add_arc((cx, cy), rf, start_angle=15, end_angle=175,
                dxfattribs={"layer": L_MED})
    for a in (15, 175):
        ax = math.radians(a)
        msp.add_line((cx + r * math.cos(ax), cy + r * math.sin(ax)),
                     (cx + rf * math.cos(ax), cy + rf * math.sin(ax)),
                     dxfattribs={"layer": L_MED})


def _draw_hitch(msp, x_tail, y0, chassis_h, scale):
    """后三点悬挂 + 牵引杆示意（中实线）。"""
    # 上拉杆
    poly(msp, [(x_tail - 180, y0 + chassis_h * 0.95),
               (x_tail + 320, y0 + chassis_h * 0.80)], layer=L_MED)
    # 下拉杆
    poly(msp, [(x_tail - 220, y0 + chassis_h * 0.42),
               (x_tail + 420, y0 + chassis_h * 0.22)], layer=L_MED)
    # 提升油缸连杆
    poly(msp, [(x_tail - 120, y0 + chassis_h * 1.05),
               (x_tail + 180, y0 + chassis_h * 0.52)], layer=L_THIN)
    # 牵引钩
    rect(msp, x_tail + 60, y0 + chassis_h * 0.05,
         x_tail + 200, y0 + chassis_h * 0.22, layer=L_MED)


def draw_tractor(msp, x: float, y: float, scale: float = 50.0,
                 with_dims: bool = True, with_labels: bool = True,
                 tracker=None, **params) -> Dict[str, object]:
    """绘制轮式拖拉机侧视外形图。

    Args:
        msp: ezdxf modelspace
        x, y: 插入基点 —— 机器最前端与**地平线**的交点（实物 mm）
        scale: 出图比例倒数（1:50 → 50），仅影响文字/标注大小
        with_dims: 是否绘制轮廓尺寸（总长、轴距、总高、轮径、离地间隙）
        with_labels: 是否绘制零部件指引线
        **params: 覆盖 :data:`DEFAULTS` 中任意尺寸（实物 mm）

    Returns:
        dict：``bbox``、``front_axle``、``rear_axle``、``length``、``height``
    """
    p = dict(DEFAULTS)
    p.update({k: float(v) for k, v in params.items() if k in DEFAULTS})

    fr = p["front_wheel_d"] / 2.0
    rr = p["rear_wheel_d"] / 2.0
    x_nose = x
    x_fa = x + p["front_overhang"]                 # 前轴 X
    x_ra = x_fa + p["wheelbase"]                   # 后轴 X
    x_tail = x_ra + p["rear_overhang"]             # 车尾 X
    length = x_tail - x_nose

    # ── 地平线 ──
    ground_line(msp, x - 600, x_tail + 900, y, scale, n_ticks=26)

    # ── 车架 / 底盘梁 ──
    rect(msp, x_nose + 60, y + p["clearance"],
         x_tail, y + p["chassis_h"], layer=L_THICK)
    # 前配重块
    rect(msp, x_nose, y + p["clearance"] + 60,
         x_nose + 60, y + p["chassis_h"] * 0.9, layer=L_MED)

    # ── 发动机罩 ──
    x_hood_end = x_fa + p["wheelbase"] * p["cab_front_ratio"]
    _draw_hood(msp, x_nose, y, x_hood_end, p["chassis_h"], p["hood_h"])

    # ── 驾驶室 ──
    _draw_cab(msp, x_hood_end, x_ra + 420, y + p["chassis_h"] * 0.98,
              y + p["cab_h"], scale)
    # 排气管（罩后立管）
    rect(msp, x_hood_end - 150, y + p["hood_h"],
         x_hood_end - 80, y + p["hood_h"] + 620, layer=L_MED)

    # ── 车轮 ──
    wheel(msp, x_fa, y + fr, p["front_wheel_d"], scale, n_lugs=12)
    wheel(msp, x_ra, y + rr, p["rear_wheel_d"], scale, n_lugs=16)
    _draw_fender(msp, x_ra, y + rr, rr, p["fender_gap"])
    # 前后轴中心线
    centerline(msp, (x_fa, y + fr), (x_ra, y + rr), scale, ext=1.0,
               layer=L_CENTER)

    # ── 后悬挂 ──
    _draw_hitch(msp, x_tail, y, p["chassis_h"], scale)

    # ── 尺寸（每一个都是参数） ──
    if with_dims:
        dim_h(msp, (x_nose, y), (x_tail, y), scale, offset=26,
              text=f"{length:.0f}", tracker=tracker)
        dim_h(msp, (x_fa, y), (x_ra, y), scale, offset=16,
              text=f"{p['wheelbase']:.0f}", tracker=tracker)
        dim_v(msp, (x_nose, y), (x_nose, y + p["cab_h"]), scale, offset=14,
              text=f"{p['cab_h']:.0f}", tracker=tracker)
        dim_v(msp, (x_nose + 60, y), (x_nose + 60, y + p["clearance"]),
              scale, offset=6, text=f"{p['clearance']:.0f}", tracker=tracker)
        dim_v(msp, (x_ra + rr, y + rr - rr), (x_ra + rr, y + rr + rr),
              scale, offset=-8, text=f"φ{p['rear_wheel_d']:.0f}",
              tracker=tracker)

    # ── 零件标注 ──
    if with_labels:
        leader(msp, (x_hood_end * 0.55 + x_nose * 0.45, y + p["hood_h"]),
               "发动机罩", scale, bend=(-6, 9), text_dir="left",
               tracker=tracker)
        leader(msp, ((x_hood_end + x_ra) / 2, y + p["cab_h"]),
               "驾驶室（ROPS）", scale, bend=(6, 8), tracker=tracker)
        leader(msp, (x_ra, y + rr + rr * 0.72), "后驱动轮", scale,
               bend=(8, 6), tracker=tracker)
        leader(msp, (x_fa, y + fr * 1.6), "前转向轮", scale,
               bend=(-7, 7), text_dir="left", tracker=tracker)
        leader(msp, (x_tail + 300, y + p["chassis_h"] * 0.3),
               "后三点悬挂", scale, bend=(7, -5), tracker=tracker)

    return {
        "bbox": (x_nose, y, x_tail + 500, y + p["cab_h"]),
        "front_axle": (x_fa, y + fr),
        "rear_axle": (x_ra, y + rr),
        "length": length,
        "height": p["cab_h"],
        "params": p,
    }
