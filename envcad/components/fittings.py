"""管件组件（平面/工艺图符号）v1.5 — 环保工程专用阀门/管件库。

符号按给水排水制图标准 GB/T 50001—2017、GB/T 50106—2010 及行业惯用画法。
所有符号沿管轴方向（默认水平）绘制，尺寸乘 scale。

阀门类型：
  gate / butterfly / diaphragm_no / diaphragm_nc / diaphragm_lined /
  globe / ball / check / sampling / regulating / plug
管件类型：
  elbow / tee / reducer / flange / coupling / cap / cross
"""
from __future__ import annotations

import math
from ezdxf.enums import TextEntityAlignment

from ..standards.annotate import _t


def _line(msp, p1, p2, layer):
    msp.add_line(p1, p2, dxfattribs={"layer": layer})


def _poly(msp, pts, layer, close=True):
    msp.add_lwpolyline(pts, close=close, dxfattribs={"layer": layer})


def _circle(msp, center, r, layer):
    msp.add_circle(center, r, dxfattribs={"layer": layer})


def _arc(msp, center, r, start, end, layer):
    msp.add_arc(center, r, start_angle=start, end_angle=end,
                dxfattribs={"layer": layer})


def _rot(pts, cx, cy, angle_deg):
    """将点列表绕 (cx, cy) 旋转 angle_deg 度。"""
    a = math.radians(angle_deg)
    cos_a, sin_a = math.cos(a), math.sin(a)
    return [(cx + (x - cx) * cos_a - (y - cy) * sin_a,
             cy + (x - cx) * sin_a + (y - cy) * cos_a)
            for x, y in pts]


def _orient_pts(pts, cx, cy, orientation):
    """根据方向旋转点集。orientation: 'h'水平 / 'v'竖直 / 角度数值。"""
    if orientation == "h":
        return pts
    if orientation == "v":
        return _rot(pts, cx, cy, 90)
    return _rot(pts, cx, cy, float(orientation))


def draw_valve(msp, center, scale: float, orientation: str = "h",
               layer: str = "阀门", label: str = None):
    """手动闸阀：两个相对三角形（V 形）。orientation 'h' 水平 / 'v' 竖直。"""
    s = scale
    cx, cy = center
    L = 4 * s
    if orientation == "h":
        _poly(msp, [(cx - L, cy - L / 2), (cx - L, cy + L / 2), (cx, cy)], layer)
        _poly(msp, [(cx, cy), (cx + L, cy - L / 2), (cx + L, cy + L / 2)], layer)
        _line(msp, (cx - L, cy), (cx - L - 2 * s, cy), "管道-污水")
        _line(msp, (cx + L, cy), (cx + L + 2 * s, cy), "管道-污水")
    else:
        _poly(msp, [(cx - L / 2, cy - L), (cx + L / 2, cy - L), (cx, cy)], layer)
        _poly(msp, [(cx, cy), (cx - L / 2, cy + L), (cx + L / 2, cy + L)], layer)
    if label:
        _t(msp, label, (cx, cy + L + 2 * s), 2.5 * s,
           align=TextEntityAlignment.MIDDLE_CENTER, layer="文字")
    return (cx + L, cy) if orientation == "h" else (cx, cy + L)


def draw_soft_joint(msp, center, scale: float, orientation: str = "h",
                    layer: str = "管道-污水", label: str = None):
    """橡胶软接头：管段 + 波浪。"""
    s = scale
    cx, cy = center
    L = 4 * s
    if orientation == "h":
        _line(msp, (cx - L, cy), (cx - L / 2, cy), layer)
        _line(msp, (cx + L / 2, cy), (cx + L, cy), layer)
        _poly(msp, [(cx - L / 2, cy), (cx - L / 4, cy + L / 3),
                    (cx, cy - L / 3), (cx + L / 4, cy + L / 3),
                    (cx + L / 2, cy)], layer, close=False)
    else:
        _line(msp, (cx, cy - L), (cx, cy - L / 2), layer)
        _line(msp, (cx, cy + L / 2), (cx, cy + L), layer)
        _poly(msp, [(cx, cy - L / 2), (cx + L / 3, cy - L / 4),
                    (cx - L / 3, cy), (cx + L / 3, cy + L / 4),
                    (cx, cy + L / 2)], layer, close=False)
    if label:
        _t(msp, label, (cx, cy + L + 2 * s), 2.5 * s,
           align=TextEntityAlignment.MIDDLE_CENTER, layer="文字")
    return (cx + L, cy) if orientation == "h" else (cx, cy + L)


def draw_flow_meter(msp, center, scale: float, orientation: str = "h",
                    layer: str = "设备", label: str = None):
    """电磁流量计：圆 + M。"""
    s = scale
    cx, cy = center
    r = 3.5 * s
    msp.add_circle((cx, cy), r, dxfattribs={"layer": layer})
    _t(msp, "M", (cx, cy - 0.6 * s), 2.8 * s,
       align=TextEntityAlignment.MIDDLE_CENTER, layer="文字")
    if orientation == "h":
        _line(msp, (cx - r, cy), (cx - r - 2 * s, cy), "管道-污水")
        _line(msp, (cx + r, cy), (cx + r + 2 * s, cy), "管道-污水")
    else:
        _line(msp, (cx, cy - r), (cx, cy - r - 2 * s), "管道-污水")
        _line(msp, (cx, cy + r), (cx, cy + r + 2 * s), "管道-污水")
    if label:
        _t(msp, label, (cx, cy + r + 2 * s), 2.5 * s,
           align=TextEntityAlignment.MIDDLE_CENTER, layer="文字")
    return (cx + r + 2 * s, cy) if orientation == "h" else (cx, cy + r + 2 * s)


def draw_flange(msp, center, scale: float, orientation: str = "h",
                layer: str = "设备"):
    """法兰：垂直管轴的短线。"""
    s = scale
    cx, cy = center
    if orientation == "h":
        _line(msp, (cx, cy - 3 * s), (cx, cy + 3 * s), layer)
    else:
        _line(msp, (cx - 3 * s, cy), (cx + 3 * s, cy), layer)


def draw_check_valve(msp, center, scale: float, orientation: str = "h",
                     layer: str = "阀门"):
    """止回阀：圆 + 单向三角。"""
    s = scale
    cx, cy = center
    r = 3 * s
    msp.add_circle((cx, cy), r, dxfattribs={"layer": layer})
    if orientation == "h":
        _poly(msp, [(cx - r / 2, cy - r / 2), (cx - r / 2, cy + r / 2), (cx + r, cy)], layer)
    else:
        _poly(msp, [(cx - r / 2, cy - r / 2), (cx + r / 2, cy - r / 2), (cx, cy + r)], layer)


def draw_wall_sleeve(msp, point, scale: float, wall_thick: float = 250,
                     dn: float = 300, orientation: str = "h",
                     layer: str = "设备", label: str = None):
    """穿墙刚性防水套管：墙体双线 + 剖面线。wall_thick 单位 mm。"""
    s = scale
    px, py = point
    half = wall_thick / 2
    if orientation == "h":
        pts = [(px - half, py - 4 * s), (px + half, py - 4 * s),
               (px + half, py + 4 * s), (px - half, py + 4 * s)]
        _poly(msp, pts, "粗实线")
        _hatch(msp, pts)
    else:
        pts = [(px - 4 * s, py - half), (px + 4 * s, py - half),
               (px + 4 * s, py + half), (px - 4 * s, py + half)]
        _poly(msp, pts, "粗实线")
        _hatch(msp, pts)
    if label:
        _t(msp, label, (px, py + 5 * s), 2.5 * s,
           align=TextEntityAlignment.MIDDLE_CENTER, layer="文字")


def _hatch(msp, points, pattern="ANSI31", scale_h=2.0):
    """填充剖面线。"""
    try:
        hatch = msp.add_hatch(color=7, dxfattribs={"layer": "剖面线"})
        hatch.paths.add_polyline_path(points, is_closed=True)
        hatch.set_pattern_fill(pattern, scale=scale_h)
    except Exception as _e:
        import sys
        print(f"  [警告] 剖面线填充失败 (pattern={pattern})，图纸可能缺填充", file=sys.stderr)


# ══════════════════════════════════════════════════════════
#  阀门系列（环保工程常用）
# ══════════════════════════════════════════════════════════

def draw_butterfly_valve(msp, center, scale: float, orientation: str = "h",
                         actuator: str = "manual", layer: str = "阀门",
                         label: str = None):
    """蝶阀（气动/手动/蜗轮）。

    actuator: "pneumatic"气动 / "manual"手动 / "worm"蜗轮 / "electric"电动
    画法：管道两侧短竖线 + 中间圆（阀板）+ 上方执行机构。
    """
    s = scale
    cx, cy = center
    L = 4 * s
    r = 2.5 * s

    # 阀体：两侧短竖线 + 中间圆
    body_pts = [
        (cx - L, cy - r), (cx - L, cy + r),
        (cx + L, cy - r), (cx + L, cy + r),
    ]
    body_pts = _orient_pts(body_pts, cx, cy, orientation)
    _line(msp, body_pts[0], body_pts[1], layer)
    _line(msp, body_pts[2], body_pts[3], layer)

    # 阀板圆
    if orientation == "h":
        _circle(msp, (cx, cy), r, layer)
    elif orientation == "v":
        _circle(msp, (cx, cy), r, layer)
    else:
        _circle(msp, (cx, cy), r, layer)

    # 阀杆（穿过圆心的线）
    if orientation == "h":
        _line(msp, (cx - r, cy), (cx + r, cy), layer)
    else:
        _line(msp, (cx, cy - r), (cx, cy + r), layer)

    # 执行机构（上方）
    act_h = 3 * s
    act_w = 3 * s
    if orientation == "h":
        act_top = cy + r + act_h
        if actuator == "pneumatic":
            # 气动：上方矩形（气缸）
            _poly(msp, [(cx - act_w / 2, cy + r), (cx + act_w / 2, cy + r),
                        (cx + act_w / 2, act_top), (cx - act_w / 2, act_top)], layer)
            # 气动符号：上方小三角（膜片）
            _poly(msp, [(cx - act_w / 3, act_top), (cx + act_w / 3, act_top),
                        (cx, act_top + act_h / 2)], layer)
        elif actuator == "worm":
            # 蜗轮：上方圆 + 斜线
            _circle(msp, (cx, cy + r + act_h / 2), act_w / 2, layer)
            _line(msp, (cx - act_w / 2, cy + r + act_h / 2),
                  (cx + act_w / 2, cy + r + act_h / 2), layer)
        elif actuator == "electric":
            # 电动：方框 + M
            _poly(msp, [(cx - act_w / 2, cy + r), (cx + act_w / 2, cy + r),
                        (cx + act_w / 2, act_top), (cx - act_w / 2, act_top)], layer)
            _t(msp, "M", (cx, cy + r + act_h / 2 - 0.5 * s), 2.0 * s,
               align=TextEntityAlignment.MIDDLE_CENTER, layer="文字")
        else:
            # 手动：上方手轮（圆）
            _circle(msp, (cx, cy + r + act_h / 2), act_w / 2, layer)
            _line(msp, (cx, cy + r), (cx, cy + r + act_h / 2 - act_w / 2), layer)

    if label:
        _t(msp, label, (cx, cy - r - 3 * s), 2.5 * s,
           align=TextEntityAlignment.MIDDLE_CENTER, layer="文字")

    return (cx + L, cy) if orientation == "h" else (cx, cy + L)


def draw_diaphragm_valve(msp, center, scale: float, orientation: str = "h",
                         fail_mode: str = "nc", lined: bool = False,
                         actuator: str = "pneumatic",
                         layer: str = "阀门", label: str = None):
    """隔膜阀（气动常开/常闭 / 衬胶）。

    fail_mode: "no"常开 / "nc"常闭
    lined: True=衬胶隔膜阀
    actuator: "pneumatic"气动 / "manual"手动
    画法：两三角相对（阀体）+ 上方隔膜执行机构 + 横线（隔膜）。
    """
    s = scale
    cx, cy = center
    L = 4 * s
    h = 3 * s

    # 阀体：两三角相对（类似闸阀，但中间有隔膜线）
    if orientation == "h":
        _poly(msp, [(cx - L, cy - h), (cx - L, cy + h), (cx, cy)], layer)
        _poly(msp, [(cx, cy), (cx + L, cy - h), (cx + L, cy + h)], layer)
        # 隔膜线（水平穿过中间）
        _line(msp, (cx - L * 0.3, cy), (cx + L * 0.3, cy), layer)
    else:
        _poly(msp, [(cx - h, cy - L), (cx + h, cy - L), (cx, cy)], layer)
        _poly(msp, [(cx, cy), (cx - h, cy + L), (cx + h, cy + L)], layer)
        _line(msp, (cx, cy - L * 0.3), (cx, cy + L * 0.3), layer)

    # 衬胶标记：阀体内部加交叉线
    if lined:
        if orientation == "h":
            _line(msp, (cx - L * 0.5, cy - h * 0.5),
                  (cx + L * 0.5, cy + h * 0.5), "细实线")
            _line(msp, (cx - L * 0.5, cy + h * 0.5),
                  (cx + L * 0.5, cy - h * 0.5), "细实线")

    # 执行机构（上方）
    act_h = 4 * s
    act_w = 3 * s
    if orientation == "h":
        act_y = cy + h
        if actuator == "pneumatic":
            # 气动膜头：上方矩形 + 弹簧
            _poly(msp, [(cx - act_w / 2, act_y), (cx + act_w / 2, act_y),
                        (cx + act_w / 2, act_y + act_h),
                        (cx - act_w / 2, act_y + act_h)], layer)
            # 弹簧标记（Z字形）
            for i in range(3):
                sy = act_y + act_h * 0.2 + i * act_h * 0.25
                _line(msp, (cx - act_w / 3, sy),
                      (cx + act_w / 3, sy + act_h * 0.1), "细实线")
            # 常开/常闭：顶部标注
            fail_txt = "NO" if fail_mode == "no" else "NC"
            _t(msp, fail_txt, (cx, act_y + act_h + 1 * s), 1.8 * s,
               align=TextEntityAlignment.MIDDLE_CENTER, layer="文字")
        else:
            # 手动：手轮
            _circle(msp, (cx, act_y + act_h / 2), act_w / 2, layer)
            _line(msp, (cx, act_y), (cx, act_y + act_h / 2 - act_w / 2), layer)

    if label:
        _t(msp, label, (cx, cy - h - 4 * s), 2.5 * s,
           align=TextEntityAlignment.MIDDLE_CENTER, layer="文字")

    return (cx + L, cy) if orientation == "h" else (cx, cy + L)


def draw_globe_valve(msp, center, scale: float, orientation: str = "h",
                     layer: str = "阀门", label: str = None):
    """截止阀（不锈钢截止阀）。

    画法：两三角相对 + 中间竖线（阀杆）+ 上方手轮。
    """
    s = scale
    cx, cy = center
    L = 4 * s
    h = 3 * s

    if orientation == "h":
        # 阀体：两三角相对
        _poly(msp, [(cx - L, cy - h), (cx - L, cy + h), (cx, cy)], layer)
        _poly(msp, [(cx, cy), (cx + L, cy - h), (cx + L, cy + h)], layer)
        # 阀杆（向上）
        _line(msp, (cx, cy), (cx, cy + h + 2 * s), layer)
        # 手轮
        _circle(msp, (cx, cy + h + 3 * s), 2 * s, layer)
    else:
        _poly(msp, [(cx - h, cy - L), (cx + h, cy - L), (cx, cy)], layer)
        _poly(msp, [(cx, cy), (cx - h, cy + L), (cx + h, cy + L)], layer)
        _line(msp, (cx, cy), (cx + h + 2 * s, cy), layer)
        _circle(msp, (cx + h + 3 * s, cy), 2 * s, layer)

    if label:
        _t(msp, label, (cx, cy - h - 3 * s), 2.5 * s,
           align=TextEntityAlignment.MIDDLE_CENTER, layer="文字")

    return (cx + L, cy) if orientation == "h" else (cx, cy + L)


def draw_ball_valve(msp, center, scale: float, orientation: str = "h",
                    layer: str = "阀门", label: str = None):
    """球阀。

    画法：两三角相对 + 中间圆（球体）+ 阀杆。
    """
    s = scale
    cx, cy = center
    L = 4 * s
    h = 3 * s

    if orientation == "h":
        _poly(msp, [(cx - L, cy - h), (cx - L, cy + h), (cx, cy)], layer)
        _poly(msp, [(cx, cy), (cx + L, cy - h), (cx + L, cy + h)], layer)
        # 球体（中间小圆）
        _circle(msp, (cx, cy), h * 0.6, layer)
        # 阀杆
        _line(msp, (cx, cy + h * 0.6), (cx, cy + h + s), layer)
        # 手柄
        _line(msp, (cx - 2 * s, cy + h + s), (cx + 2 * s, cy + h + s), layer)
    else:
        _poly(msp, [(cx - h, cy - L), (cx + h, cy - L), (cx, cy)], layer)
        _poly(msp, [(cx, cy), (cx - h, cy + L), (cx + h, cy + L)], layer)
        _circle(msp, (cx, cy), h * 0.6, layer)
        _line(msp, (cx + h * 0.6, cy), (cx + h + s, cy), layer)
        _line(msp, (cx + h + s, cy - 2 * s), (cx + h + s, cy + 2 * s), layer)

    if label:
        _t(msp, label, (cx, cy - h - 3 * s), 2.5 * s,
           align=TextEntityAlignment.MIDDLE_CENTER, layer="文字")

    return (cx + L, cy) if orientation == "h" else (cx, cy + L)


def draw_sampling_valve(msp, center, scale: float, orientation: str = "h",
                        layer: str = "阀门", label: str = None):
    """取样阀。

    画法：主管道 + T形支管 + 阀门符号。
    """
    s = scale
    cx, cy = center
    L = 4 * s

    if orientation == "h":
        # 主管
        _line(msp, (cx - L, cy), (cx + L, cy), "管道-污水")
        # T形支管（向下）
        _line(msp, (cx, cy), (cx, cy - 3 * s), layer)
        # 阀门（两三角）
        _poly(msp, [(cx - 1.5 * s, cy - 3 * s - 2 * s),
                    (cx + 1.5 * s, cy - 3 * s - 2 * s),
                    (cx, cy - 3 * s)], layer)
        # 取样口
        _line(msp, (cx, cy - 3 * s - 2 * s), (cx, cy - 3 * s - 4 * s), layer)
    else:
        _line(msp, (cx, cy - L), (cx, cy + L), "管道-污水")
        _line(msp, (cx, cy), (cx + 3 * s, cy), layer)
        _poly(msp, [(cx + 3 * s + 2 * s, cy - 1.5 * s),
                    (cx + 3 * s + 2 * s, cy + 1.5 * s),
                    (cx + 3 * s, cy)], layer)
        _line(msp, (cx + 3 * s + 2 * s, cy), (cx + 3 * s + 4 * s, cy), layer)

    if label:
        _t(msp, label, (cx + L + 2 * s, cy), 2.5 * s,
           align=TextEntityAlignment.MIDDLE_LEFT, layer="文字")

    return (cx + L, cy) if orientation == "h" else (cx, cy + L)


def draw_regulating_valve(msp, center, scale: float, orientation: str = "h",
                          actuator: str = "pneumatic",
                          layer: str = "阀门", label: str = None):
    """气动调节阀。

    画法：两三角相对（阀体）+ 上方执行机构 + 顶部箭头（调节）。
    """
    s = scale
    cx, cy = center
    L = 4 * s
    h = 3 * s

    if orientation == "h":
        # 阀体
        _poly(msp, [(cx - L, cy - h), (cx - L, cy + h), (cx, cy)], layer)
        _poly(msp, [(cx, cy), (cx + L, cy - h), (cx + L, cy + h)], layer)
        # 阀杆
        _line(msp, (cx, cy), (cx, cy + h + s), layer)
        # 执行机构（气动膜头）
        act_h = 4 * s
        act_w = 4 * s
        _poly(msp, [(cx - act_w / 2, cy + h + s),
                    (cx + act_w / 2, cy + h + s),
                    (cx + act_w / 2, cy + h + s + act_h),
                    (cx - act_w / 2, cy + h + s + act_h)], layer)
        # 调节符号：顶部箭头（对角箭头）
        _line(msp, (cx - act_w / 3, cy + h + s + act_h * 0.3),
              (cx + act_w / 3, cy + h + s + act_h * 0.7), "细实线")
        _line(msp, (cx + act_w / 3, cy + h + s + act_h * 0.3),
              (cx - act_w / 3, cy + h + s + act_h * 0.7), "细实线")

    if label:
        _t(msp, label, (cx, cy - h - 3 * s), 2.5 * s,
           align=TextEntityAlignment.MIDDLE_CENTER, layer="文字")

    return (cx + L, cy) if orientation == "h" else (cx, cy + L)


def draw_plug_valve(msp, center, scale: float, orientation: str = "h",
                    layer: str = "阀门", label: str = None):
    """旋塞阀/插板阀。

    画法：矩形阀体 + 中间塞子 + 上方手轮。
    """
    s = scale
    cx, cy = center
    L = 4 * s
    h = 3 * s

    if orientation == "h":
        # 阀体矩形
        _poly(msp, [(cx - L, cy - h), (cx + L, cy - h),
                    (cx + L, cy + h), (cx - L, cy + h)], layer)
        # 塞子（梯形）
        _poly(msp, [(cx - h * 0.4, cy - h * 0.6),
                    (cx + h * 0.4, cy - h * 0.6),
                    (cx + h * 0.3, cy + h * 0.6),
                    (cx - h * 0.3, cy + h * 0.6)], layer)
        # 阀杆 + 手轮
        _line(msp, (cx, cy - h * 0.6), (cx, cy - h - s), layer)
        _circle(msp, (cx, cy - h - 2 * s), 2 * s, layer)
    else:
        _poly(msp, [(cx - h, cy - L), (cx + h, cy - L),
                    (cx + h, cy + L), (cx - h, cy + L)], layer)
        _poly(msp, [(cx - h * 0.6, cy - h * 0.4),
                    (cx - h * 0.6, cy + h * 0.4),
                    (cx + h * 0.6, cy + h * 0.3),
                    (cx + h * 0.6, cy - h * 0.3)], layer)
        _line(msp, (cx - h * 0.6, cy), (cx - h - s, cy), layer)
        _circle(msp, (cx - h - 2 * s, cy), 2 * s, layer)

    if label:
        _t(msp, label, (cx, cy + h + 3 * s), 2.5 * s,
           align=TextEntityAlignment.MIDDLE_CENTER, layer="文字")

    return (cx + L, cy) if orientation == "h" else (cx, cy + L)


# ══════════════════════════════════════════════════════════
#  管道管件系列（碳钢 / UPVC 通用）
# ══════════════════════════════════════════════════════════

def draw_elbow(msp, center, scale: float, angle: float = 90.0,
               direction: str = "ne", dn: float = 100.0,
               material: str = "carbon_steel",
               layer: str = "管道-污水", label: str = None):
    """弯头（90°/45°）。

    angle: 弯头角度（度）
    direction: "ne"(右上) / "nw"(左上) / "se"(右下) / "sw"(左下)
    dn: 公称直径 mm（用于双线表示时的管宽）
    material: "carbon_steel"碳钢 / "upvc" / "stainless"不锈钢
    """
    s = scale
    cx, cy = center
    r = 3 * s  # 弯头中心线半径

    # 方向映射
    dir_map = {
        "ne": (0, 90),    # 从右(0°)向上(90°)
        "nw": (90, 180),  # 从上(90°)向左(180°)
        "sw": (180, 270), # 从左(180°)向下(270°)
        "se": (270, 360), # 从下(270°)向右(360°)
    }
    start_a, end_a = dir_map.get(direction, (0, 90))
    if angle != 90.0:
        # 45度弯头：调整结束角
        end_a = start_a + angle

    # 单线表示（中心线）
    _arc(msp, (cx, cy), r, start_a, end_a, layer)

    # 入口直管段
    in_dx = r * math.cos(math.radians(start_a))
    in_dy = r * math.sin(math.radians(start_a))
    _line(msp, (cx + in_dx, cy + in_dy),
          (cx + in_dx * 2, cy + in_dy * 2), layer)

    # 出口直管段
    out_dx = r * math.cos(math.radians(end_a))
    out_dy = r * math.sin(math.radians(end_a))
    _line(msp, (cx + out_dx, cy + out_dy),
          (cx + out_dx * 2, cy + out_dy * 2), layer)

    # 材质标记（碳钢加法兰边，UPVC加虚线）
    if material == "carbon_steel":
        # 入口法兰
        fx, fy = cx + in_dx * 1.8, cy + in_dy * 1.8
        perp_x, perp_y = -in_dy / r, in_dx / r
        _line(msp, (fx + perp_x * 1.5 * s, fy + perp_y * 1.5 * s),
              (fx - perp_x * 1.5 * s, fy - perp_y * 1.5 * s), "设备")
    elif material == "upvc":
        # UPVC：加粘接标记（小短线）
        mx, my = cx + in_dx * 1.5, cy + in_dy * 1.5
        perp_x, perp_y = -in_dy / r, in_dx / r
        _line(msp, (mx + perp_x * s, my + perp_y * s),
              (mx - perp_x * s, my - perp_y * s), "细实线")

    if label:
        _t(msp, label, (cx, cy + r + 3 * s), 2.5 * s,
           align=TextEntityAlignment.MIDDLE_CENTER, layer="文字")

    return (cx + out_dx * 2, cy + out_dy * 2)


def draw_tee(msp, center, scale: float, tee_type: str = "equal",
             orientation: str = "h", dn_main: float = 100.0,
             dn_branch: float = 80.0,
             material: str = "carbon_steel",
             layer: str = "管道-污水", label: str = None):
    """三通（等径/异径）。

    tee_type: "equal"等径 / "reducing"异径
    orientation: "h"水平主管+上支管 / "v"竖直主管+右支管
    """
    s = scale
    cx, cy = center
    L = 4 * s

    if orientation == "h":
        # 水平主管
        _line(msp, (cx - L, cy), (cx + L, cy), layer)
        # 上支管
        branch_len = L
        if tee_type == "reducing":
            # 异径：支管稍短，加变径标记
            _line(msp, (cx, cy), (cx, cy + branch_len), layer)
            # 变径处小三角
            _poly(msp, [(cx - s, cy + branch_len * 0.3),
                        (cx + s, cy + branch_len * 0.3),
                        (cx, cy + branch_len * 0.5)], "细实线")
        else:
            _line(msp, (cx, cy), (cx, cy + branch_len), layer)
    else:
        # 竖直主管
        _line(msp, (cx, cy - L), (cx, cy + L), layer)
        # 右支管
        _line(msp, (cx, cy), (cx + L, cy), layer)
        if tee_type == "reducing":
            _poly(msp, [(cx + L * 0.3, cy - s),
                        (cx + L * 0.3, cy + s),
                        (cx + L * 0.5, cy)], "细实线")

    # 材质标记
    if material == "carbon_steel":
        # 碳钢：接口加法兰短线
        if orientation == "h":
            for dx in (-L + s, L - s):
                _line(msp, (cx + dx, cy - 1.5 * s),
                      (cx + dx, cy + 1.5 * s), "设备")
            _line(msp, (cx - 1.5 * s, cy + L - s),
                  (cx + 1.5 * s, cy + L - s), "设备")

    if label:
        _t(msp, label, (cx, cy - L - 2 * s), 2.5 * s,
           align=TextEntityAlignment.MIDDLE_CENTER, layer="文字")

    return (cx + L, cy) if orientation == "h" else (cx, cy + L)


def draw_reducer(msp, center, scale: float, orientation: str = "h",
                 reducer_type: str = "concentric",
                 dn_large: float = 150.0, dn_small: float = 100.0,
                 layer: str = "管道-污水", label: str = None):
    """异径管（同心/偏心）。

    reducer_type: "concentric"同心 / "eccentric"偏心
    """
    s = scale
    cx, cy = center
    L = 5 * s
    r_large = 2.5 * s
    r_small = 1.8 * s

    if orientation == "h":
        if reducer_type == "concentric":
            # 同心：梯形
            _poly(msp, [(cx - L, cy - r_large), (cx - L, cy + r_large),
                        (cx + L, cy - r_small), (cx + L, cy + r_small)],
                  layer, close=False)
            # 两侧直管
            _line(msp, (cx - L - 2 * s, cy - r_large),
                  (cx - L, cy - r_large), layer)
            _line(msp, (cx - L - 2 * s, cy + r_large),
                  (cx - L, cy + r_large), layer)
            _line(msp, (cx + L, cy - r_small),
                  (cx + L + 2 * s, cy - r_small), layer)
            _line(msp, (cx + L, cy + r_small),
                  (cx + L + 2 * s, cy + r_small), layer)
        else:
            # 偏心：底平（上斜下平）
            _poly(msp, [(cx - L, cy - r_large), (cx - L, cy + r_large),
                        (cx + L, cy + r_small), (cx + L, cy - r_large)],
                  layer, close=False)
            _line(msp, (cx - L - 2 * s, cy - r_large),
                  (cx - L, cy - r_large), layer)
            _line(msp, (cx - L - 2 * s, cy + r_large),
                  (cx - L, cy + r_large), layer)
            _line(msp, (cx + L, cy - r_large),
                  (cx + L + 2 * s, cy - r_large), layer)
            _line(msp, (cx + L, cy + r_small),
                  (cx + L + 2 * s, cy + r_small), layer)
    else:
        if reducer_type == "concentric":
            _poly(msp, [(cx - r_large, cy - L), (cx + r_large, cy - L),
                        (cx + r_small, cy + L), (cx - r_small, cy + L)],
                  layer, close=False)

    if label:
        _t(msp, label, (cx, cy + r_large + 2 * s), 2.5 * s,
           align=TextEntityAlignment.MIDDLE_CENTER, layer="文字")

    return (cx + L + 2 * s, cy) if orientation == "h" else (cx, cy + L)


def draw_flange_pair(msp, center, scale: float, orientation: str = "h",
                     dn: float = 100.0, pn: float = 1.0,
                     layer: str = "设备", label: str = None):
    """法兰对（两片法兰 + 螺栓孔）。

    dn: 公称直径 mm
    pn: 公称压力 MPa
    """
    s = scale
    cx, cy = center
    w = 1.5 * s  # 单片法兰厚度
    gap = 0.5 * s  # 两片间距
    h = 4 * s  # 法兰外径方向高度

    if orientation == "h":
        # 左法兰
        _line(msp, (cx - gap / 2 - w, cy - h),
              (cx - gap / 2 - w, cy + h), layer)
        # 右法兰
        _line(msp, (cx + gap / 2 + w, cy - h),
              (cx + gap / 2 + w, cy + h), layer)
        # 螺栓孔（上下各一个小圆）
        for y_off in (-h * 0.7, h * 0.7):
            _circle(msp, (cx - gap / 2 - w / 2, cy + y_off), 0.4 * s, layer)
            _circle(msp, (cx + gap / 2 + w / 2, cy + y_off), 0.4 * s, layer)
        # 管道
        _line(msp, (cx - gap / 2 - w - 2 * s, cy),
              (cx - gap / 2 - w, cy), "管道-污水")
        _line(msp, (cx + gap / 2 + w, cy),
              (cx + gap / 2 + w + 2 * s, cy), "管道-污水")
    else:
        _line(msp, (cx - h, cy - gap / 2 - w),
              (cx + h, cy - gap / 2 - w), layer)
        _line(msp, (cx - h, cy + gap / 2 + w),
              (cx + h, cy + gap / 2 + w), layer)
        for x_off in (-h * 0.7, h * 0.7):
            _circle(msp, (cx + x_off, cy - gap / 2 - w / 2), 0.4 * s, layer)
            _circle(msp, (cx + x_off, cy + gap / 2 + w / 2), 0.4 * s, layer)

    if label:
        _t(msp, label, (cx, cy + h + 2 * s), 2.5 * s,
           align=TextEntityAlignment.MIDDLE_CENTER, layer="文字")

    return (cx + gap / 2 + w + 2 * s, cy) if orientation == "h" else (cx, cy + gap / 2 + w + 2 * s)


def draw_cross(msp, center, scale: float, orientation: str = "h",
               layer: str = "管道-污水", label: str = None):
    """四通。"""
    s = scale
    cx, cy = center
    L = 4 * s
    _line(msp, (cx - L, cy), (cx + L, cy), layer)
    _line(msp, (cx, cy - L), (cx, cy + L), layer)

    if label:
        _t(msp, label, (cx, cy + L + 2 * s), 2.5 * s,
           align=TextEntityAlignment.MIDDLE_CENTER, layer="文字")

    return (cx + L, cy)


def draw_pipe_cap(msp, end_point, scale: float, orientation: str = "h",
                  layer: str = "管道-污水", label: str = None):
    """管帽/堵头。"""
    s = scale
    ex, ey = end_point
    r = 2 * s

    if orientation == "h":
        _line(msp, (ex - 2 * s, ey - r), (ex, ey - r), layer)
        _line(msp, (ex - 2 * s, ey + r), (ex, ey + r), layer)
        _arc(msp, (ex - 2 * s, ey), r, 270, 90, layer)
    else:
        _line(msp, (ex - r, ey - 2 * s), (ex - r, ey), layer)
        _line(msp, (ex + r, ey - 2 * s), (ex + r, ey), layer)
        _arc(msp, (ex, ey - 2 * s), r, 180, 360, layer)

    if label:
        _t(msp, label, (ex, ey + r + 2 * s), 2.5 * s,
           align=TextEntityAlignment.MIDDLE_CENTER, layer="文字")

    return (ex, ey)


# ══════════════════════════════════════════════════════════
#  仪表符号（环保专用：PH/ORP/电导率/浊度/液位/流量）
# ══════════════════════════════════════════════════════════

def draw_instrument_symbol(msp, center, scale: float, tag: str = "",
                           instr_type: str = "flow",
                           mounting: str = "field",
                           layer: str = "仪表", label: str = None):
    """环保工程仪表符号（按 GB/T 2625 / ISA S5.1）。

    instr_type:
        "flow"(F)流量 / "analyzer"(A)分析 / "level"(L)液位 /
        "temp"(T)温度 / "pressure"(P)压力 / "ph"(PH)酸碱度 /
        "conductivity"(CON)电导率 / "turbidity"(TUR)浊度 /
        "orp"(ORP)氧化还原
    mounting: "field"就地 / "panel"盘装 / "dcs"计算机功能
    """
    s = scale
    cx, cy = center
    r = 4 * s

    # 外框
    if mounting == "field":
        _circle(msp, (cx, cy), r, layer)
    elif mounting == "panel":
        _circle(msp, (cx, cy), r, layer)
        _line(msp, (cx - r, cy), (cx + r, cy), layer)
    elif mounting == "dcs":
        # 计算机功能：方框内圆
        box_s = r * 2
        _poly(msp, [(cx - box_s / 2, cy - box_s / 2),
                    (cx + box_s / 2, cy - box_s / 2),
                    (cx + box_s / 2, cy + box_s / 2),
                    (cx - box_s / 2, cy + box_s / 2)], layer)
        _circle(msp, (cx, cy), r * 0.7, layer)

    # 位号文字
    if tag:
        _t(msp, tag, (cx, cy - 0.5 * s), 2.2 * s,
           align=TextEntityAlignment.MIDDLE_CENTER, layer="文字")

    # 类型标注（下方）
    type_map = {
        "flow": "F", "analyzer": "A", "level": "L",
        "temp": "T", "pressure": "P",
        "ph": "PH", "conductivity": "CON",
        "turbidity": "TUR", "orp": "ORP",
    }
    type_code = type_map.get(instr_type, "")
    if type_code and not tag:
        _t(msp, type_code, (cx, cy - 0.5 * s), 2.5 * s,
           align=TextEntityAlignment.MIDDLE_CENTER, layer="文字")

    if label:
        _t(msp, label, (cx, cy - r - 3 * s), 2.5 * s,
           align=TextEntityAlignment.MIDDLE_CENTER, layer="文字")

    return (cx + r, cy)


# ══════════════════════════════════════════════════════════
#  阀门/管件统一调度函数
# ══════════════════════════════════════════════════════════

VALVE_DRAWERS = {
    "gate": draw_valve,
    "butterfly": draw_butterfly_valve,
    "diaphragm_no": lambda msp, c, s, **kw: draw_diaphragm_valve(msp, c, s, fail_mode="no", **kw),
    "diaphragm_nc": lambda msp, c, s, **kw: draw_diaphragm_valve(msp, c, s, fail_mode="nc", **kw),
    "diaphragm_lined": lambda msp, c, s, **kw: draw_diaphragm_valve(msp, c, s, lined=True, **kw),
    "globe": draw_globe_valve,
    "ball": draw_ball_valve,
    "check": draw_check_valve,
    "sampling": draw_sampling_valve,
    "regulating": draw_regulating_valve,
    "plug": draw_plug_valve,
}


def draw_any_valve(msp, center, valve_type: str, scale: float,  **kwargs):
    """统一阀门绘制入口。valve_type 见 VALVE_DRAWERS。

    未收录的阀门类型不报错，改为联网检索权威画法并返回 None（不打断出图流程）。
    """
    drawer = VALVE_DRAWERS.get(valve_type)
    if drawer is None:
        print(f"⚠ 未知阀门类型: {valve_type}（本地未收录，可选: {list(VALVE_DRAWERS.keys())}）")
        try:
            from .engine_web_bridge import search_web
            hits = search_web(f"{valve_type} 阀门 标准 图集 画法", max_n=3)
            if hits:
                print("   联网检索到以下权威参考：")
                for h in hits:
                    print(f"   - {h['title']}  {h['url']}")
        except Exception:
            pass
        return None
    return drawer(msp, center, scale, **kwargs)
