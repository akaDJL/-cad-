"""池体组件 v1.4 — 精度增强 + 标注避让。

改进:
  * 所有坐标自动圆整到 0.01mm
  * 平剖面标注自动错层（避免文字线条重叠）
  * 增大平面与剖面的安全间距
  * 高程标注按层级分级（0=顶，1=中，2=底）
  * 支持 BBoxTracker 碰撞检测

坐标约定:
  * 平面图：x-y 实物 mm，1:1
  * 剖面图：x 为水平实物 mm；y 为图上坐标，由 origin_y 起算向下。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from ezdxf.enums import TextEntityAlignment

from ..standards.annotate import _t, draw_elevation
from .fittings import _hatch, _line, _poly
from ..utils import _r  # v1.5: 统一工具函数


@dataclass
class RectPoolParams:
    """矩形池参数。单位 mm / m。"""
    length: float = 8000.0
    width: float = 5000.0
    depth: float = 4000.0
    wall_thick: float = 250.0
    bottom_thick: float = 300.0
    material: str = "C30钢筋混凝土"
    top_elev: float = 0.000
    bottom_elev: float = -4.000
    inlet_il: float = -0.500
    outlet_il: float = -0.600
    water_level: float = -0.300
    name: str = "调节池"
    extra_req: list = field(default_factory=list)


# ─── 平面视图间距常量 ────────────────────────────────────
PLAN_TO_SECTION_GAP = 5000.0  # 平面图底到剖面图顶的最小间距 (mm)


def draw_rect_pool_plan(msp, origin, p: RectPoolParams, scale: float,
                        show_dims: bool = True,
                        tracker=None):
    """矩形池平面图。origin=外框左下角。返回 (x0,y0,x1,y1) 外框范围。"""
    s = scale
    ox, oy = _r(*origin)
    L, W, t = p.length, p.width, p.wall_thick

    x0, y0 = ox, oy
    x1, y1 = _r(ox + L + 2 * t, oy + W + 2 * t)
    ix0, iy0 = _r(ox + t, oy + t)
    ix1, iy1 = _r(ox + L + t, oy + W + t)

    # 池壁外框
    _poly(msp, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], "池体-壁")
    # 池壁内框
    _poly(msp, [(ix0, iy0), (ix1, iy0), (ix1, iy1), (ix0, iy1)], "中实线")

    # 进出水管（中心线）
    in_y = iy0 + W * 0.5
    pipe_in_start = _r(x0 - 4 * s, in_y)
    pipe_in_end = _r(ix0, in_y)
    _line(msp, pipe_in_start, pipe_in_end, "管道-污水")
    _line(msp, _r(ix1, in_y), _r(x1 + 4 * s, in_y), "管道-污水")

    # 内部构造线
    _line(msp, _r(ix0 + 200, iy1 - 400), _r(ix1 - 200, iy1 - 400), "虚线")

    # 名称（池中心，大字）
    _t(msp, p.name, _r((ix0 + ix1) / 2, (iy0 + iy1) / 2), 5 * s,
       align=TextEntityAlignment.MIDDLE_CENTER, layer="文字-标题",
       tracker=tracker)

    if show_dims:
        # 尺寸标注（避让池体）
        _t(msp, f"L={int(L)}", _r((ix0 + ix1) / 2, y0 - 4 * s), 3 * s,
           align=TextEntityAlignment.MIDDLE_CENTER, layer="文字",
           tracker=tracker)
        _t(msp, f"W={int(W)}", _r(x1 + 4 * s, (iy0 + iy1) / 2), 3 * s,
           align=TextEntityAlignment.MIDDLE_CENTER, layer="文字", rotation=90,
           tracker=tracker)

    # 注册占用区域
    if tracker is not None:
        tracker.register(x0 - 6 * s, y0 - 6 * s, x1 + 6 * s, y1 + 6 * s, margin=50)

    return (x0, y0, x1, y1)


def draw_rect_pool_section(msp, origin_x, origin_y: float, p: RectPoolParams,
                           scale: float, show_dims: bool = True,
                           tracker=None):
    """矩形池剖面图（纵剖）v1.4 — 标注分级避让。

    origin_x: 剖面左端 x（mm）。
    origin_y: 池顶图上 y（图纸坐标系，越大越上方）。
    返回 (x0, y_top, x1, y_base) 剖面包络。
    """
    s = scale
    ox = origin_x
    t = p.wall_thick
    bt = p.bottom_thick
    L = p.length

    y_top = origin_y
    y_bot = origin_y - p.depth             # 池底
    y_base = y_bot - bt                    # 底板底
    rx0 = ox + t + L                       # 右壁右边界

    # ── 墙体 ──
    lw = [(ox, y_top), (ox + t, y_top), (ox + t, y_bot), (ox, y_bot)]
    _poly(msp, lw, "池体-壁")
    _hatch(msp, lw)

    rw = [(rx0, y_top), (rx0 + t, y_top), (rx0 + t, y_bot), (rx0, y_bot)]
    _poly(msp, rw, "池体-壁")
    _hatch(msp, rw)

    # 底板
    bot = [(ox, y_bot), (rx0 + t, y_bot), (rx0 + t, y_base), (ox, y_base)]
    _poly(msp, bot, "池体-壁")
    _hatch(msp, bot)

    # ── 水位线 ──
    wl = origin_y - (p.top_elev - p.water_level) * 1000
    _line(msp, (ox + t, wl), (rx0, wl), "池体-水")

    # ── 进出水管 ──
    in_y = origin_y - (p.top_elev - p.inlet_il) * 1000
    out_y = origin_y - (p.top_elev - p.outlet_il) * 1000
    _line(msp, (ox - 6 * s, in_y), (ox + t, in_y), "管道-污水")
    _line(msp, (rx0, out_y), (rx0 + t + 6 * s, out_y), "管道-污水")

    # ── 尺寸文字（池内标注 — 放在池体注册前以避免被挤出）──
    if show_dims:
        _t(msp, f"H={int(p.depth)}",
           _r(ox + t + L * 0.5, (y_top + y_bot) / 2), 3 * s,
           align=TextEntityAlignment.MIDDLE_CENTER, layer="文字",
           tracker=tracker)
        _t(msp, f"L={int(L)}",
           _r(ox + t + L * 0.5, y_base - 4 * s), 3 * s,
           align=TextEntityAlignment.MIDDLE_CENTER, layer="文字",
           tracker=tracker)
        _t(msp, f"t={int(t)}",
           _r(ox + t / 2, y_top + 3 * s), 2.5 * s,
           align=TextEntityAlignment.MIDDLE_CENTER, layer="文字",
           tracker=tracker)

    # 注册池体占地区域（使后续标高标注自动避让池体）
    if tracker is not None:
        margin = 10 * s
        tracker.register(ox - margin, y_base - margin,
                         rx0 + t + margin, y_top + margin, margin=100)

    # ── 标高标注（池外标注 — 会检测池体占地区自动偏离）──
    elev_positions = {
        "top":   (ox + t + L * 0.2, y_top, p.top_elev, "right", 0),
        "water": (ox + t + L * 0.5, wl, p.water_level, "right", 1),
        "bottom":(ox + t + L * 0.2, y_bot, p.bottom_elev, "right", 2),
        "inlet": (ox - 6 * s, in_y, p.inlet_il, "left", 0),
        "outlet":(rx0 + t + 6 * s, out_y, p.outlet_il, "right", 0),
    }

    for key, (ex, ey, evalue, eside, elevel) in elev_positions.items():
        draw_elevation(msp, (ex, ey), f"{evalue:.3f}", s,
                       side=eside, level=elevel, tracker=tracker)

    return (ox, y_top, rx0 + t, y_base)


def draw_circular_pool_plan(msp, center, diameter: float, wall_thick: float,
                            scale: float, name: str = "沉淀池",
                            inlet_dn: float = 300, sludge_dn: float = 150,
                            tracker=None):
    """圆形池平面图。"""
    s = scale
    cx, cy = _r(*center)
    r = diameter / 2

    msp.add_circle((cx, cy), r, dxfattribs={"layer": "池体-壁"})
    msp.add_circle((cx, cy), r - wall_thick, dxfattribs={"layer": "中实线"})
    msp.add_circle((cx, cy), inlet_dn / 2 + 100, dxfattribs={"layer": "管道-污水"})
    msp.add_circle((cx, cy), r - wall_thick - 200, dxfattribs={"layer": "虚线"})
    _line(msp, (cx, cy), (cx + r, cy), "管道-污水")

    # 名称和尺寸（分上下放置防重叠）
    _t(msp, name, (cx, cy - r - 5 * s), 4 * s,
       align=TextEntityAlignment.MIDDLE_CENTER, layer="文字-标题",
       tracker=tracker)
    _t(msp, f"D={int(diameter)}", (cx, cy - r / 2 - 2 * s), 3 * s,
       align=TextEntityAlignment.MIDDLE_CENTER, layer="文字",
       tracker=tracker)

    _t(msp, f"DN{int(inlet_dn)}进水管",
       _r(cx, cy + r / 2 + 2 * s), 2.5 * s,
       align=TextEntityAlignment.MIDDLE_CENTER, layer="文字",
       tracker=tracker)
    _t(msp, f"DN{int(sludge_dn)}排泥管",
       _r(cx + r / 2, cy + 3 * s), 2.5 * s, layer="文字", tracker=tracker)

    if tracker is not None:
        tracker.register(cx - r - 10 * s, cy - r - 10 * s,
                         cx + r + 10 * s, cy + r + 10 * s, margin=50)

    return (cx - r, cy - r, cx + r, cy + r)


def draw_circular_pool_section(msp, origin_x, origin_y: float, diameter: float,
                               total_h: float, hopper_h: float, tube_h: float,
                               wall_thick: float, scale: float,
                               top_elev: float = 0.300,
                               name: str = "竖流斜管沉淀池",
                               inlet_dn: float = 300, sludge_dn: float = 150,
                               tracker=None):
    """圆形池剖面图 v1.4 — 标注分级避让。

    返回 (x0, y_top, x1, y_bot) 剖面包络。
    """
    s = scale
    ox = origin_x
    r = diameter / 2
    y_top = origin_y
    y_bot = origin_y - total_h * 1000
    y_hopper_top = y_bot + hopper_h * 1000
    y_tube_top = y_hopper_top + tube_h * 1000

    e_top = top_elev
    e_bot = top_elev - total_h
    e_hopper = e_bot + hopper_h
    e_tube = e_hopper + tube_h

    # 左壁
    lw = [(ox, y_top), (ox + wall_thick, y_top),
          (ox + wall_thick, y_bot), (ox, y_bot)]
    _poly(msp, lw, "池体-壁")
    _hatch(msp, lw)

    # 右壁
    rx0 = ox + diameter
    rw = [(rx0, y_top), (rx0 - wall_thick, y_top),
          (rx0 - wall_thick, y_bot), (rx0, y_bot)]
    _poly(msp, rw, "池体-壁")
    _hatch(msp, rw)

    # 底板
    _line(msp, (ox, y_bot), (rx0, y_bot), "池体-壁")

    # 污泥斗
    cx = ox + r
    hop_half_top = r * 0.85
    _poly(msp, [(cx - hop_half_top, y_hopper_top),
                (cx + hop_half_top, y_hopper_top),
                (cx, y_bot)], "池体-壁", close=False)

    # 斜管区
    tube = [(ox + wall_thick, y_hopper_top), (rx0 - wall_thick, y_hopper_top),
            (rx0 - wall_thick, y_tube_top), (ox + wall_thick, y_tube_top)]
    _poly(msp, tube, "中实线")
    _hatch(msp, tube, pattern="ANSI37", scale_h=4.0)

    # 中心进水管
    _line(msp, (cx - inlet_dn / 2, y_top), (cx - inlet_dn / 2, y_hopper_top), "管道-污水")
    _line(msp, (cx + inlet_dn / 2, y_top), (cx + inlet_dn / 2, y_hopper_top), "管道-污水")

    # 出水堰
    _line(msp, (ox + wall_thick, y_top - 200),
          (rx0 - wall_thick, y_top - 200), "虚线")

    # 排泥管
    _line(msp, (cx - sludge_dn / 2, y_bot),
          (cx - sludge_dn / 2, y_bot + 600), "管道-污水")
    _line(msp, (cx + sludge_dn / 2, y_bot),
          (cx + sludge_dn / 2, y_bot + 600), "管道-污水")

    # ── 名称和尺寸（池内标注 — 放在池体注册前）──
    _t(msp, name, (cx, y_top + 5 * s), 4 * s,
       align=TextEntityAlignment.MIDDLE_CENTER, layer="文字-标题",
       tracker=tracker)
    _t(msp, f"总高 {total_h}m", (cx + r + 5 * s, (y_top + y_bot) / 2), 3 * s,
       align=TextEntityAlignment.MIDDLE_CENTER, layer="文字", rotation=90,
       tracker=tracker)
    _t(msp, f"污泥斗 {hopper_h}m",
       (cx - r * 0.4, (y_bot + y_hopper_top) / 2), 2.5 * s,
       align=TextEntityAlignment.MIDDLE_CENTER, layer="文字",
       tracker=tracker)
    _t(msp, f"斜管区 {tube_h}m",
       (cx - r * 0.4, (y_hopper_top + y_tube_top) / 2), 2.5 * s,
       align=TextEntityAlignment.MIDDLE_CENTER, layer="文字",
       tracker=tracker)
    _t(msp, f"DN{int(sludge_dn)}排泥管", (cx + 8 * s, y_bot + 300), 2.5 * s,
       layer="文字", tracker=tracker)
    _t(msp, f"DN{int(inlet_dn)}进水管", (cx + inlet_dn, y_top - 4 * s), 2.5 * s,
       layer="文字", tracker=tracker)
    _t(msp, "周边出水堰",
       (ox + wall_thick + 4 * s, y_top - 200 + 2 * s), 2.5 * s,
       layer="文字", tracker=tracker)

    # 注册池体占地区域（使后续标高标注自动避让池体）
    if tracker is not None:
        tracker.register(ox - 15 * s, y_bot - 10 * s,
                         rx0 + 15 * s, y_top + 10 * s, margin=100)

    # ── 标高（分级: 0=顶,1=斜管,2=斗,3=底 — 池外标注自动偏离）──
    draw_elevation(msp, (cx + r * 0.55, y_top), f"{e_top:.3f}", s,
                   side="right", level=0, tracker=tracker)
    draw_elevation(msp, (cx + r * 0.55, y_tube_top), f"{e_tube:.3f}", s,
                   side="right", level=1, tracker=tracker)
    draw_elevation(msp, (cx + r * 0.55, y_hopper_top), f"{e_hopper:.3f}", s,
                   side="right", level=2, tracker=tracker)
    draw_elevation(msp, (cx, y_bot), f"{e_bot:.3f}", s,
                   side="right", level=3, tracker=tracker)

    return (ox, y_top, rx0, y_bot)
