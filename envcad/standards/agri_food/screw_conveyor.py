"""模块 21 —— 螺旋输送机（U 形槽 + 螺旋体）纵剖面 + 横断面。

复用 envcad：
  * ``standards.hydraulic.draw_motor``      → 驱动装置（马达/减速机）符号；
  * ``standards.hydraulic.draw_cylinder``   → 进料闸门液压缸（缸体画法沿用）；
  * ``standards.mechanical.draw_rolling_bearing`` → 两端轴承座（GB/T 276 简化画法）；
  * GB/T 17450 图层、仿宋 GB2312 文字样式、``standards.dim`` 标注。

上述符号函数在 envcad 中按"图纸 mm × scale"出图，本模块用
``_common.sym_scale_for`` 换算成实物 mm 目标尺寸，使符号与主体几何等比协调。

标准依据：
  * GB/T 14689—2008 图纸幅面 / GB/T 4457.4—2002 图线 / GB/T 17453 剖面符号
  * JB/T 7679—2015 螺旋输送机  # TODO: verify against JB/T 7679
    （螺旋公称直径系列 100/160/200/250/315/400/500/630mm、
     标准螺距 S=D、槽体宽度与螺旋径向间隙）
  * GB/T 276—2013 滚动轴承 深沟球轴承（轴承座简化画法）

全部尺寸为实物 mm。
"""
from __future__ import annotations

import math
from typing import Dict, List

from envcad.standards.hydraulic import draw_cylinder, draw_motor
from envcad.standards.mechanical import draw_rolling_bearing

from ._common import (
    L_CENTER, L_HIDDEN, L_MED, L_THICK, L_THIN,
    centerline, cross_center, dim_h, dim_v, hatch_solid, label, leader,
    poly, rect, sym_scale_for, view_title,
)

#: JB/T 7679 螺旋公称直径系列（mm）  # TODO: verify against JB/T 7679
SCREW_D_SERIES: List[float] = [100, 160, 200, 250, 315, 400, 500, 630]

#: 默认参数（实物 mm）
DEFAULTS: Dict[str, float] = {
    "screw_d": 315.0,          # 螺旋公称直径 D
    "pitch": 315.0,            # 螺距 S（标准型 S=D）
    "length": 6000.0,          # 机长（进料口中心 → 出料口中心）
    "shaft_d": 89.0,           # 螺旋轴外径
    "trough_gap": 20.0,        # 螺旋外缘与槽体单侧间隙
    "trough_wall": 6.0,        # 槽体壁厚
    "trough_h": 340.0,         # U 形槽直段高度
    "cover_h": 60.0,           # 盖板高
    "leg_h": 900.0,            # 支腿高（槽底 → 地面）
    "inlet_w": 500.0,          # 进料口宽
    "outlet_w": 400.0,         # 出料口宽
    "motor_d": 520.0,          # 驱动装置符号直径
    "bearing_d": 190.0,        # 轴承座外径
    "gate_cyl_len": 520.0,     # 进料闸门气/液压缸长度
    "n_legs": 3.0,             # 支腿数量
}


def nearest_screw_d(d: float) -> float:
    """把任意直径归到 JB/T 7679 螺旋公称直径系列的最近档位。"""
    return min(SCREW_D_SERIES, key=lambda v: abs(v - d))


def _draw_screw_flight(msp, x0: float, cy: float, length: float,
                       d: float, pitch: float, layer: str = L_MED):
    """螺旋叶片纵剖面展开画法：每半个螺距一段半椭圆，上下交替。

    这是 JB/T 7679 图样中螺旋体的惯用示意画法。
    """
    r = d / 2.0
    half = pitch / 2.0
    n = max(1, int(length // half))
    for i in range(n):
        sx = x0 + i * half
        up = (i % 2 == 0)
        try:
            msp.add_ellipse((sx + half / 2, cy), major_axis=(half / 2, 0),
                            ratio=min(1.0, (2 * r) / max(half, 1e-6)) * 0.5,
                            start_param=0 if up else math.pi,
                            end_param=math.pi if up else 2 * math.pi,
                            dxfattribs={"layer": layer})
        except Exception as _e:
            # 兼容回退：用圆弧近似
            msp.add_arc((sx + half / 2, cy), half / 2,
                        start_angle=0 if up else 180,
                        end_angle=180 if up else 360,
                        dxfattribs={"layer": layer})
    return n


def draw_screw_conveyor(msp, x: float, y: float, scale: float = 25.0,
                        with_dims: bool = True, with_labels: bool = True,
                        with_drive: bool = True, tracker=None,
                        **params) -> Dict[str, object]:
    """绘制螺旋输送机**纵剖面图**（进料端在左，驱动端在右）。

    Args:
        msp: ezdxf modelspace
        x, y: 插入基点 —— 槽体左端外壁与**槽底内表面**的交点（实物 mm）
        scale: 出图比例倒数
        with_drive: 是否绘制驱动装置与轴承座（复用 envcad 符号）
        **params: 覆盖 :data:`DEFAULTS`，如 screw_d=400, length=8000

    Returns:
        dict：``bbox``、``axis_y``、``n_flights``、``params``
    """
    p = dict(DEFAULTS)
    p.update({k: float(v) for k, v in params.items() if k in DEFAULTS})
    p["screw_d"] = nearest_screw_d(p["screw_d"])

    D = p["screw_d"]
    r = D / 2.0
    trough_w_in = D + 2 * p["trough_gap"]      # 槽体内宽（横断面用）
    L = p["length"]
    cy = y + r + p["trough_gap"]               # 螺旋轴中心高
    x1 = x + L

    # ── U 形槽体（纵剖面：底板 + 两侧板 + 盖板）──
    y_bot = y
    y_top = cy + r + p["trough_gap"] + p["trough_h"] * 0.0
    msp.add_line((x, y_bot), (x1, y_bot), dxfattribs={"layer": L_THICK})
    msp.add_line((x, y_bot - p["trough_wall"]), (x1, y_bot - p["trough_wall"]),
                 dxfattribs={"layer": L_THICK})
    y_side = cy + r + p["trough_gap"]
    for xe in (x, x1):
        msp.add_line((xe, y_bot - p["trough_wall"]), (xe, y_side),
                     dxfattribs={"layer": L_THICK})
    msp.add_line((x, y_side), (x1, y_side), dxfattribs={"layer": L_THIN})
    # 盖板
    rect(msp, x, y_side, x1, y_side + p["cover_h"], layer=L_MED)

    # ── 螺旋轴 + 叶片 ──
    msp.add_line((x + 120, cy - p["shaft_d"] / 2), (x1 - 120, cy - p["shaft_d"] / 2),
                 dxfattribs={"layer": L_MED})
    msp.add_line((x + 120, cy + p["shaft_d"] / 2), (x1 - 120, cy + p["shaft_d"] / 2),
                 dxfattribs={"layer": L_MED})
    n_flights = _draw_screw_flight(msp, x + 200, cy, L - 400, D, p["pitch"])
    centerline(msp, (x, cy), (x1, cy), scale, ext=4.0, layer=L_CENTER)

    # ── 进料口（左上）+ 闸门液压缸（复用 hydraulic.draw_cylinder）──
    ix0 = x + L * 0.06
    ix1 = ix0 + p["inlet_w"]
    poly(msp, [(ix0, y_side + p["cover_h"]), (ix0 - 90, y_side + p["cover_h"] + 520),
               (ix1 + 90, y_side + p["cover_h"] + 520), (ix1, y_side + p["cover_h"])],
         layer=L_THICK, closed=True)
    if with_drive:
        draw_cylinder(msp, ((ix0 + ix1) / 2 - p["inlet_w"] * 1.5,
                            y_side + p["cover_h"] + 300),
                      c_type="double",
                      scale=sym_scale_for(p["gate_cyl_len"], 24.0),
                      label="闸门缸", layer=L_MED)

    # ── 出料口（右下）──
    ox1 = x1 - L * 0.06
    ox0 = ox1 - p["outlet_w"]
    poly(msp, [(ox0, y_bot - p["trough_wall"]),
               (ox0 - 60, y_bot - p["trough_wall"] - 460),
               (ox1 + 60, y_bot - p["trough_wall"] - 460),
               (ox1, y_bot - p["trough_wall"])],
         layer=L_THICK, closed=True)

    # ── 轴承座（复用 mechanical.draw_rolling_bearing）+ 驱动装置 ──
    if with_drive:
        b_scale = sym_scale_for(p["bearing_d"], 80.0)  # 源函数 D 默认 80×scale
        draw_rolling_bearing(msp, (x - p["bearing_d"] * 1.6, cy),
                             b_type="deep_groove", d=40.0, D=80.0, B=18.0,
                             scale=b_scale, label="", layer=L_THICK)
        draw_rolling_bearing(msp, (x1 + p["bearing_d"] * 0.2, cy),
                             b_type="deep_groove", d=40.0, D=80.0, B=18.0,
                             scale=b_scale, label="", layer=L_THICK)
        m_scale = sym_scale_for(p["motor_d"] / 2, 6.0)  # 源函数 r = 6×scale
        draw_motor(msp, (x1 + p["motor_d"] * 1.5, cy), m_type="fixed_uni",
                   scale=m_scale, label="驱动装置", layer=L_MED)
        msp.add_line((x1 + p["bearing_d"] * 0.8, cy),
                     (x1 + p["motor_d"], cy), dxfattribs={"layer": L_MED})

    # ── 支腿 ──
    n_legs = max(2, int(p["n_legs"]))
    for i in range(n_legs):
        lx = x + L * (i + 0.5) / n_legs
        rect(msp, lx - 60, y_bot - p["trough_wall"] - p["leg_h"],
             lx + 60, y_bot - p["trough_wall"], layer=L_MED)
        msp.add_line((lx - 220, y_bot - p["trough_wall"] - p["leg_h"]),
                     (lx + 220, y_bot - p["trough_wall"] - p["leg_h"]),
                     dxfattribs={"layer": L_THICK})

    # ── 尺寸 ──
    if with_dims:
        dim_h(msp, (x, y_bot - p["trough_wall"] - p["leg_h"]),
              (x1, y_bot - p["trough_wall"] - p["leg_h"]), scale, offset=20,
              text=f"L={L:.0f}", tracker=tracker)
        dim_h(msp, (x + 200, cy + r), (x + 200 + p["pitch"], cy + r), scale,
              offset=-14, text=f"S={p['pitch']:.0f}", tracker=tracker)
        dim_v(msp, (x, cy - r), (x, cy + r), scale, offset=9,
              text=f"φ{D:.0f}", tracker=tracker)
        dim_v(msp, (x1, y_bot - p["trough_wall"] - p["leg_h"]), (x1, y_bot),
              scale, offset=-9, text=f"{p['leg_h']:.0f}", tracker=tracker)

    if with_labels:
        leader(msp, ((ix0 + ix1) / 2, y_side + p["cover_h"] + 520), "进料口",
               scale, bend=(5, 6), tracker=tracker)
        leader(msp, ((ox0 + ox1) / 2, y_bot - p["trough_wall"] - 460), "出料口",
               scale, bend=(6, -6), tracker=tracker)
        leader(msp, (x + L * 0.45, cy + r * 0.8), f"螺旋体 φ{D:.0f}  S={p['pitch']:.0f}",
               scale, bend=(-6, 8), text_dir="left", tracker=tracker)
        leader(msp, (x + L * 0.75, y_side + p["cover_h"]), "槽体盖板", scale,
               bend=(6, 7), tracker=tracker)

    return {
        "bbox": (x - p["bearing_d"] * 3, y_bot - p["trough_wall"] - p["leg_h"],
                 x1 + p["motor_d"] * 2.4, y_side + p["cover_h"] + 560),
        "axis_y": cy,
        "trough_w_in": trough_w_in,
        "n_flights": n_flights,
        "params": p,
    }


def draw_screw_section(msp, x: float, y: float, scale: float = 25.0,
                       tracker=None, **params) -> Dict[str, object]:
    """绘制螺旋输送机 **A—A 横断面**（U 形槽 + 螺旋 + 物料填充率）。

    Args:
        x, y: 断面中心线与槽底内表面的交点（实物 mm）
    """
    p = dict(DEFAULTS)
    p.update({k: float(v) for k, v in params.items() if k in DEFAULTS})
    p["screw_d"] = nearest_screw_d(p["screw_d"])

    D = p["screw_d"]
    r = D / 2.0
    g, t = p["trough_gap"], p["trough_wall"]
    cy = y + r + g
    r_in = r + g            # 槽内半径
    r_out = r_in + t        # 槽外半径
    h_str = p["trough_h"]   # 直段高

    # U 形槽（内外双线：下半圆 + 两侧直段）
    for rr, lay in ((r_in, L_THICK), (r_out, L_THICK)):
        msp.add_arc((x, cy), rr, start_angle=180, end_angle=360,
                    dxfattribs={"layer": lay})
        for sgn in (-1, 1):
            msp.add_line((x + sgn * rr, cy), (x + sgn * rr, cy + h_str),
                         dxfattribs={"layer": lay})
    # 上翻边 + 盖板
    msp.add_line((x - r_out, cy + h_str), (x - r_out - 80, cy + h_str),
                 dxfattribs={"layer": L_THICK})
    msp.add_line((x + r_out, cy + h_str), (x + r_out + 80, cy + h_str),
                 dxfattribs={"layer": L_THICK})
    rect(msp, x - r_out - 80, cy + h_str, x + r_out + 80,
         cy + h_str + p["cover_h"], layer=L_MED)

    # 螺旋外缘 + 轴
    msp.add_circle((x, cy), r, dxfattribs={"layer": L_MED})
    msp.add_circle((x, cy), p["shaft_d"] / 2, dxfattribs={"layer": L_THICK})
    cross_center(msp, x, cy, r_out, scale)

    # 物料填充（GB/T 17453 剖面符号；填充系数 ψ≈0.3）
    fill_y = cy - r * 0.35
    hatch_solid(msp, [(x - r_in * 0.95, cy - r_in * 0.2),
                      (x + r_in * 0.95, cy - r_in * 0.2),
                      (x + r_in * 0.8, fill_y), (x - r_in * 0.8, fill_y)],
                layer=L_THIN, pattern="AR-SAND", pattern_scale=6.0)

    dim_h(msp, (x - r, cy), (x + r, cy), scale, offset=16, text=f"φ{D:.0f}",
          tracker=tracker)
    dim_h(msp, (x - r_out, cy + h_str), (x + r_out, cy + h_str), scale,
          offset=-10, text=f"{2 * r_out:.0f}", tracker=tracker)
    view_title(msp, "A—A 横断面", (x, cy - r_out - 22 * scale), scale,
               tracker=tracker)
    label(msp, "填充系数 ψ=0.30  # TODO: verify against JB/T 7679",
          (x, cy - r_out - 30 * scale), scale, height=2.5, tracker=tracker)

    return {"bbox": (x - r_out - 200, cy - r_out - 32 * scale,
                     x + r_out + 200, cy + h_str + p["cover_h"]),
            "params": p}
