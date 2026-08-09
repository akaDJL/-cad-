"""液压传动系统制图 v1.0（GB/T 786.1—2021）。

基于 ezdxf 实现液压原理图元件库、油路连接、集成块。
所有标准数据（工作压力、流量、阀规格等）由 Agent 搜索后显式传入。

纯 ezdxf，零新依赖。
"""
from __future__ import annotations

import math
from typing import List, Optional, Tuple

from ezdxf.enums import TextEntityAlignment
from ..utils import _r, _tri


# ─── 内部辅助 ───────────────────────────────────────────

# ─── 管路绘制 ───────────────────────────────────────────

def draw_line(msp, start, end, line_type: str = "working",
               scale: float = 100.0, layer: str = "油路",
               tracker=None):
    """绘制液压管路。

    参数:
        start/end: 管路起终点
        line_type: "working" 工作油路 / "pilot" 控制油路 / "drain" 泄油路 /
                   "flexible" 软管 / "enclosure" 组合元件框线
    """
    sx, sy = _r(*start)
    ex, ey = _r(*end)

    if line_type == "pilot":
        # 控制油路：虚线
        msp.add_line((sx, sy), (ex, ey),
                     dxfattribs={"layer": layer, "linetype": "DASHED"})
    elif line_type == "drain":
        # 泄油路：点划线
        msp.add_line((sx, sy), (ex, ey),
                     dxfattribs={"layer": layer, "linetype": "DASHDOT"})
    elif line_type == "flexible":
        # 软管：波浪或双折线（简化为带标记的实线）
        msp.add_line((sx, sy), (ex, ey),
                     dxfattribs={"layer": layer})
        # 中点加弧线标记
        mx, my = (sx + ex) / 2, (sy + ey) / 2
        dx, dy = ex - sx, ey - sy
        length = math.hypot(dx, dy)
        if length > 0:
            px, py = -dy / length, dx / length
            arc_r = 3.0 * scale
            msp.add_arc((mx + px * arc_r, my + py * arc_r),
                        radius=arc_r, start_angle=0, end_angle=180,
                        dxfattribs={"layer": layer})
    else:
        # 工作油路：实线
        msp.add_line((sx, sy), (ex, ey), dxfattribs={"layer": layer})

    if tracker:
        tracker.register(min(sx, ex) - 3 * scale, min(sy, ey) - 3 * scale,
                         max(sx, ex) + 3 * scale, max(sy, ey) + 3 * scale,
                         margin=10)

    return (ex, ey)


def draw_port(msp, center, port_id: str = "",
               scale: float = 100.0, layer: str = "油路",
               label: str = "", tracker=None):
    """绘制油口符号。

    参数:
        center: 油口位置
        port_id: 油口标识 "P"/"T"/"A"/"B"/"X"/"Y"/"L"
    """
    cx, cy = _r(*center)
    r = 2.5 * scale
    msp.add_circle((cx, cy), r, dxfattribs={"layer": layer})

    if port_id:
        txt_h = 2.0 * scale
        t = msp.add_text(port_id, dxfattribs={
            "layer": "文字", "height": txt_h, "style": "ENG",
        })
        t.set_placement((cx, cy - r - 2 * scale),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    if tracker:
        tracker.register(cx - r - 2 * scale, cy - r - 5 * scale,
                         cx + r + 2 * scale, cy + r + 2 * scale, margin=10)

    return (cx, cy - r)


# ══════════════════════════════════════════════════════════
#  液压泵 / 马达符号
# ══════════════════════════════════════════════════════════

def draw_pump(msp, center, p_type: str = "fixed_uni",
               scale: float = 100.0,
               label: str = "",
               params: dict = None,
               layer: str = "元件",
               tracker=None):
    """绘制液压泵符号。

    参数:
        p_type:
            "fixed_uni"        = 单向定量泵
            "fixed_bi"         = 双向定量泵
            "variable_uni"     = 单向变量泵
            "variable_bi"      = 双向变量泵
        label: 泵编号
        params: 泵参数 {"flow":"40L/min","pressure":"21MPa","displ":"25cc/r",...}
    """
    s = scale
    cx, cy = _r(*center)
    r = 6.0 * s  # 圆半径

    # 基圆
    msp.add_circle((cx, cy), r, dxfattribs={"layer": layer})

    # 驱动轴三角（实心三角形，顶点向右）
    tri_h = 4.0 * s
    tri_w = 5.0 * s
    if "bi" in p_type:
        # 双向：双三角
        msp.add_line((cx + r, cy), (cx + r + tri_w, cy),
                     dxfattribs={"layer": layer})
        # 右侧三角
        pts_r = [(cx + r + tri_w, cy - tri_h / 2),
                 (cx + r + tri_w, cy + tri_h / 2),
                 (cx + r + tri_w + tri_h, cy)]
        try:
            msp.add_solid(pts_r + [pts_r[0]], dxfattribs={"layer": layer})
        except Exception as _e:
            msp.add_lwpolyline(pts_r, close=True, dxfattribs={"layer": layer})
        # 左侧三角
        pts_l = [(cx - r, cy - tri_h / 2),
                 (cx - r, cy + tri_h / 2),
                 (cx - r - tri_h, cy)]
        try:
            msp.add_solid(pts_l + [pts_l[0]], dxfattribs={"layer": layer})
        except Exception as _e:
            msp.add_lwpolyline(pts_l, close=True, dxfattribs={"layer": layer})
        msp.add_line((cx - r, cy), (cx - r - tri_w, cy),
                     dxfattribs={"layer": layer})
    else:
        # 单向：右侧三角 + 左侧短横线
        msp.add_line((cx + r, cy), (cx + r + tri_w, cy),
                     dxfattribs={"layer": layer})
        msp.add_line((cx - r, cy), (cx - r - 2 * s, cy),
                     dxfattribs={"layer": layer})
        pts = [(cx + r + tri_w, cy - tri_h / 2),
               (cx + r + tri_w, cy + tri_h / 2),
               (cx + r + tri_w + tri_h, cy)]
        try:
            msp.add_solid(pts + [pts[0]], dxfattribs={"layer": layer})
        except Exception as _e:
            msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": layer})

    # 变量泵：斜箭头
    if "variable" in p_type:
        msp.add_line((cx - r - 0.5 * s, cy + r + 2 * s),
                     (cx + r + 0.5 * s, cy - r - 2 * s),
                     dxfattribs={"layer": layer})
        # 箭头尖（右上）
        arr_p = (cx + r + 0.5 * s, cy - r - 2 * s)
        _small_arrow(msp, arr_p, (1, -1), layer)

    # ── 标注 ──
    txt_h = 2.2 * s
    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": txt_h, "style": "HZ",
        })
        t.set_placement((cx, cy - r - 6 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    if params:
        cy_p = cy - r - 8 * s - txt_h
        for key, val in params.items():
            t = msp.add_text(f"{key}:{val}", dxfattribs={
                "layer": "文字", "height": 1.8 * s, "style": "ENG",
            })
            t.set_placement((cx, cy_p),
                            align=TextEntityAlignment.MIDDLE_CENTER)
            cy_p -= 2.5 * s

    if tracker:
        tracker.register(cx - r - tri_h - 5 * s,
                         cy - r - 10 * s,
                         cx + r + tri_w + tri_h + 5 * s,
                         cy + r + 3 * s, margin=20)

    return (cx, cy + r)


def draw_motor(msp, center, m_type: str = "fixed_uni",
                scale: float = 100.0,
                label: str = "",
                params: dict = None,
                layer: str = "元件",
                tracker=None):
    """绘制液压马达符号。

    参数:
        m_type: "fixed_uni"/"fixed_bi"/"variable_uni"/"variable_bi"
    """
    s = scale
    cx, cy = _r(*center)
    r = 6.0 * s

    # 基圆 + 实心三角（与泵相反，三角向内）
    msp.add_circle((cx, cy), r, dxfattribs={"layer": layer})

    tri_h = 4.0 * s
    tri_w = 5.0 * s

    if "bi" not in m_type:
        # 单向：内三角指向圆心
        pts = [(cx + r * 0.6, cy - tri_h / 2),
               (cx + r * 0.6, cy + tri_h / 2),
               (cx, cy)]
        try:
            msp.add_solid(pts + [pts[0]], dxfattribs={"layer": layer})
        except Exception as _e:
            msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": layer})

    if "variable" in m_type:
        msp.add_line((cx - r, cy + r + 2 * s),
                     (cx + r, cy - r - 2 * s),
                     dxfattribs={"layer": layer})

    txt_h = 2.2 * s
    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": txt_h, "style": "HZ",
        })
        t.set_placement((cx, cy - r - 6 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    return (cx, cy + r)


# ══════════════════════════════════════════════════════════
#  液压缸
# ══════════════════════════════════════════════════════════

def draw_cylinder(msp, center, c_type: str = "double",
                   bore: float = 50.0, stroke: float = 100.0,
                   scale: float = 100.0,
                   label: str = "",
                   layer: str = "元件",
                   tracker=None):
    """绘制液压缸符号。

    参数:
        c_type: "double" 双作用 / "single" 单作用 / "double_rod" 双活塞杆 /
                "telescopic" 多级伸缩 / "cushion" 带缓冲
        bore: 缸径 mm
        stroke: 行程 mm（仅影响标注，不影响绘图比例）
    """
    s = scale
    cx, cy = _r(*center)

    # 缸筒（矩形）
    bw = 8.0 * s   # 缸筒宽
    bl = 24.0 * s  # 缸筒长
    x0, y0 = cx - bl / 2, cy - bw / 2

    msp.add_lwpolyline(
        [(x0, y0), (x0 + bl, y0), (x0 + bl, y0 + bw), (x0, y0 + bw)],
        close=True, dxfattribs={"layer": layer}
    )

    # 活塞杆
    rod_w = 2.0 * s
    rod_l = 16.0 * s
    rod_y = cy
    if c_type == "double_rod":
        # 双活塞杆：两端伸出
        msp.add_line((x0, rod_y), (x0 - rod_l, rod_y),
                     dxfattribs={"layer": layer})
        msp.add_line((x0 + bl, rod_y), (x0 + bl + rod_l, rod_y),
                     dxfattribs={"layer": layer})
        # 两端 piston 标记
        msp.add_line((x0, rod_y - rod_w), (x0 - rod_l * 0.4, rod_y - rod_w),
                     dxfattribs={"layer": layer})
        msp.add_line((x0, rod_y + rod_w), (x0 - rod_l * 0.4, rod_y + rod_w),
                     dxfattribs={"layer": layer})
        msp.add_line((x0 + bl, rod_y - rod_w),
                     (x0 + bl + rod_l * 0.4, rod_y - rod_w),
                     dxfattribs={"layer": layer})
        msp.add_line((x0 + bl, rod_y + rod_w),
                     (x0 + bl + rod_l * 0.4, rod_y + rod_w),
                     dxfattribs={"layer": layer})
    else:
        # 单端活塞杆（右侧伸出）
        msp.add_line((x0 + bl, rod_y), (x0 + bl + rod_l, rod_y),
                     dxfattribs={"layer": layer})
        # 活塞标记（缸筒中线短竖线）
        msp.add_line((x0 + bl * 0.3, y0 + 0.5 * s),
                     (x0 + bl * 0.3, y0 + bw - 0.5 * s),
                     dxfattribs={"layer": layer})
        # 杆端标记
        msp.add_line((x0 + bl, rod_y - rod_w),
                     (x0 + bl + rod_l * 0.4, rod_y - rod_w),
                     dxfattribs={"layer": layer})
        msp.add_line((x0 + bl, rod_y + rod_w),
                     (x0 + bl + rod_l * 0.4, rod_y + rod_w),
                     dxfattribs={"layer": layer})

    if c_type == "single":
        # 单作用：左侧弹簧标记
        mx = x0 + bl * 0.5
        for seg_y in [cy - bw * 0.3, cy, cy + bw * 0.3]:
            msp.add_line((mx - 3 * s, seg_y), (mx + 3 * s, seg_y),
                         dxfattribs={"layer": layer})

    if c_type == "cushion":
        # 缓冲标记（右侧小矩形）
        cx_c = x0 + bl * 0.15
        cw_c = 3.0 * s
        ch_c = bw * 0.6
        msp.add_lwpolyline(
            [(cx_c, cy - ch_c / 2), (cx_c + cw_c, cy - ch_c / 2),
             (cx_c + cw_c, cy + ch_c / 2), (cx_c, cy + ch_c / 2)],
            close=True, dxfattribs={"layer": layer})

    # ── 标注 ──
    txt_h = 2.2 * s
    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": txt_h, "style": "HZ",
        })
        t.set_placement((cx, y0 - 4 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    return (x0 + bl + rod_l, y0)


# ══════════════════════════════════════════════════════════
#  方向控制阀
# ══════════════════════════════════════════════════════════

def draw_directional_valve(msp, center, ports: int = 4,
                            positions: int = 3,
                            center_type: str = "O",
                            solenoids: List[str] = None,
                            springs: List[str] = None,
                            scale: float = 100.0,
                            label: str = "",
                            layer: str = "元件",
                            tracker=None):
    """绘制方向控制阀符号（GB/T 786.1）。

    参数:
        ports: 油口数（2/3/4/5）
        positions: 位 数（2/3）
        center_type: 中位机能（3位时）
            "O" = 全闭 / "H" = 全通 / "Y" = AB通T,P闭 /
            "M" = PT通,AB闭 / "P" = PA通,BT闭 / "J" = PT通,A闭,B通T
        solenoids: 电磁铁位置 ["left","right"] 或 ["left"]
        springs: 弹簧位置 ["left","right"]
    """
    s = scale
    cx, cy = _r(*center)

    # 阀体外框
    bw = ports * 7.0 * s   # 每个油口 7mm 间距
    bl = positions * 10.0 * s  # 每个位 10mm 宽
    x0 = cx - bl / 2
    y0 = cy - bw / 2

    # 外框
    msp.add_lwpolyline(
        [(x0, y0), (x0 + bl, y0), (x0 + bl, y0 + bw), (x0, y0 + bw)],
        close=True, dxfattribs={"layer": layer}
    )

    # 分隔线（位之间）
    if positions > 1:
        seg_w = bl / positions
        for i in range(1, positions):
            sx = x0 + i * seg_w
            msp.add_line((sx, y0), (sx, y0 + bw),
                         dxfattribs={"layer": layer})

    # 油口
    port_spacing = bw / max(ports - 1, 1)
    port_ids = ["P", "T"] if ports <= 3 else ["A", "B", "P", "T"][:ports]
    if ports == 2:
        port_ids = ["P", "T"]
    elif ports == 3:
        port_ids = ["A", "P", "T"]

    for i in range(ports):
        py = y0 + port_spacing * i
        # 左端油口线
        msp.add_line((x0 - 6 * s, py), (x0, py),
                     dxfattribs={"layer": layer})
        # 右端油口线
        msp.add_line((x0 + bl, py), (x0 + bl + 6 * s, py),
                     dxfattribs={"layer": layer})

        # 油口标识
        if i < len(port_ids):
            txt_h = 2.0 * s
            t = msp.add_text(port_ids[i], dxfattribs={
                "layer": "文字", "height": txt_h, "style": "ENG",
            })
            t.set_placement((x0 - 8 * s, py),
                            align=TextEntityAlignment.MIDDLE_CENTER)

    # ── 中位机能（3位阀） ──
    if positions == 3 and ports >= 4 and center_type:
        seg_w = bl / 3
        cx_c = x0 + seg_w * 1.5  # 中位中心 X
        _draw_spool_center(msp, cx_c, y0, bw, port_spacing,
                            center_type, layer)

    # ── 电磁铁 ──
    if solenoids:
        for sol_pos in solenoids:
            if sol_pos == "left":
                _draw_solenoid(msp, x0 - 4 * s, cy - 4 * s, -1, s, layer)
            elif sol_pos == "right":
                _draw_solenoid(msp, x0 + bl + 4 * s, cy - 4 * s, 1, s, layer)

    # ── 弹簧 ──
    if springs:
        for spr_pos in springs:
            if spr_pos == "left":
                _draw_spring(msp, x0 - 4 * s, cy + 5 * s, -1, s, layer)
            elif spr_pos == "right":
                _draw_spring(msp, x0 + bl + 4 * s, cy + 5 * s, 1, s, layer)

    txt_h = 3.0 * s
    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": txt_h, "style": "HZ",
        })
        t.set_placement((cx, y0 - 5 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    if tracker:
        tracker.register(x0 - 15 * s, y0 - 8 * s,
                         x0 + bl + 15 * s, y0 + bw + 5 * s, margin=30)

    return (x0 + bl, y0 + bw)


def _draw_spool_center(msp, cx, y0, bw, ps, ctype, layer):
    """绘制中位机能图形。"""
    py0, py1, py2, py3 = y0, y0 + ps, y0 + 2 * ps, y0 + 3 * ps  # A,B,P,T

    if ctype == "O":
        # 全部封闭：4条T形
        for py in [py0, py1, py2, py3]:
            _draw_t_block(msp, cx, py, layer)
    elif ctype == "H":
        # 全部连通：连通线
        msp.add_line((cx - 4, py0), (cx + 4, py0), dxfattribs={"layer": layer})
        msp.add_line((cx - 4, py3), (cx + 4, py3), dxfattribs={"layer": layer})
        msp.add_line((cx, py0), (cx, py3), dxfattribs={"layer": layer})
    elif ctype == "Y":
        # AB通T, P闭
        _draw_t_block(msp, cx, py1, layer)  # P闭
        _draw_t_block(msp, cx, py2, layer)
        msp.add_line((cx, py0), (cx, py3), dxfattribs={"layer": layer})
    elif ctype == "M":
        # PT通, AB闭
        _draw_t_block(msp, cx, py0, layer)  # A闭
        _draw_t_block(msp, cx, py3, layer)  # B闭
        msp.add_line((cx, py1), (cx, py2), dxfattribs={"layer": layer})
    elif ctype == "J":
        # PT通, A闭, B通T
        _draw_t_block(msp, cx, py0, layer)
        msp.add_line((cx, py1), (cx, py2), dxfattribs={"layer": layer})
        msp.add_line((cx, py3), (cx, py2), dxfattribs={"layer": layer})


def _draw_t_block(msp, cx, py, layer):
    """绘制T形封堵符号。"""
    msp.add_line((cx - 2, py - 3), (cx + 2, py - 3),
                 dxfattribs={"layer": layer})


def _draw_solenoid(msp, x, y, direction, s, layer):
    """电磁铁符号。"""
    # 矩形线圈 + 斜线
    sw, sh = 5 * s, 8 * s
    if direction > 0:
        x0 = x + 1 * s
    else:
        x0 = x - sw - 1 * s
    msp.add_lwpolyline(
        [(x0, y), (x0 + sw, y), (x0 + sw, y + sh), (x0, y + sh)],
        close=True, dxfattribs={"layer": layer})
    # 斜线
    msp.add_line((x0, y + sh), (x0 + sw, y),
                 dxfattribs={"layer": layer})


def _draw_spring(msp, x, y, direction, s, layer):
    """弹簧符号（折线）。"""
    sw, sh = 5 * s, 4 * s
    if direction > 0:
        x0 = x + 1 * s
    else:
        x0 = x - sw - 1 * s

    n_segs = 4
    seg_h = sh / n_segs
    for i in range(n_segs):
        sx = x0 + (sw if i % 2 == 0 else 0)
        sy = y + seg_h * i
        msp.add_line((sx, sy), (x0 + sw - sx + x0, sy + seg_h),
                     dxfattribs={"layer": layer})


def _small_arrow(msp, tip, direction, layer):
    """小三角箭头。"""
    tx, ty = tip
    dx, dy = direction
    h = 2.0
    px, py = -dy, dx
    pts = [(tx, ty), (tx - h * dx * 2 + h * px * 0.5,
                       ty - h * dy * 2 + h * py * 0.5),
           (tx - h * dx * 2 - h * px * 0.5,
            ty - h * dy * 2 - h * py * 0.5)]
    msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": layer})


# ══════════════════════════════════════════════════════════
#  压力 / 流量控制阀
# ══════════════════════════════════════════════════════════

def draw_relief_valve(msp, center, pilot: bool = False,
                       scale: float = 100.0,
                       label: str = "",
                       setting: str = "",
                       layer: str = "元件",
                       tracker=None):
    """溢流阀符号。

    参数:
        pilot: True = 先导式，False = 直动式
        setting: 设定压力（如 "21MPa"），Agent 搜索后传入
    """
    s = scale
    cx, cy = _r(*center)
    bw, bl = 10.0 * s, 14.0 * s
    x0, y0 = cx - bl / 2, cy - bw / 2

    # 方框
    msp.add_lwpolyline(
        [(x0, y0), (x0 + bl, y0), (x0 + bl, y0 + bw), (x0, y0 + bw)],
        close=True, dxfattribs={"layer": layer})

    # 弹簧符号（框内右侧）
    spring_x = x0 + bl * 0.7
    msp.add_line((spring_x, y0 + bw * 0.2),
                 (spring_x, y0 + bw * 0.8),
                 dxfattribs={"layer": layer})
    for i in range(3):
        sy = y0 + bw * 0.2 + bw * 0.2 * i
        msp.add_line((spring_x - 2 * s, sy),
                     (spring_x + 2 * s, sy + bw * 0.15),
                     dxfattribs={"layer": layer})

    # 箭头
    msp.add_line((x0 + bl * 0.3, y0 + bw * 0.2),
                 (x0 + bl * 0.3, y0 + bw * 0.8),
                 dxfattribs={"layer": layer})
    # 油路
    msp.add_line((x0, cy), (x0 - 6 * s, cy), dxfattribs={"layer": layer})
    msp.add_line((x0 + bl, cy), (x0 + bl + 6 * s, cy),
                 dxfattribs={"layer": layer})
    # 泄油口
    msp.add_line((cx, y0 + bw), (cx, y0 + bw + 5 * s),
                 dxfattribs={"layer": "油路", "linetype": "DASHED"})

    if pilot:
        # 先导级（小方框）
        ps = 6.0 * s
        px0, py0 = x0 - ps - 2 * s, cy - ps / 2
        msp.add_lwpolyline(
            [(px0, py0), (px0 + ps, py0),
             (px0 + ps, py0 + ps), (px0, py0 + ps)],
            close=True, dxfattribs={"layer": layer})
        msp.add_line((px0, cy), (px0 - 3 * s, cy),
                     dxfattribs={"layer": "油路", "linetype": "DASHED"})

    txt_h = 2.2 * s
    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": txt_h, "style": "HZ",
        })
        t.set_placement((cx, y0 - 4 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    if setting:
        t = msp.add_text(setting, dxfattribs={
            "layer": "文字", "height": 2.0 * s, "style": "ENG",
        })
        t.set_placement((cx, y0 - 4 * s - txt_h * 1.3),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    return (x0 + bl, y0 + bw)


def draw_throttle_valve(msp, center, adjustable: bool = False,
                          scale: float = 100.0,
                          label: str = "",
                          layer: str = "元件",
                          tracker=None):
    """节流阀/调速阀符号。

    参数:
        adjustable: True = 可调节流阀（带斜箭头），False = 固定节流
    """
    s = scale
    cx, cy = _r(*center)

    # 弧形节流符号（两个背对背半圆弧）
    r = 4.0 * s
    msp.add_arc((cx - r, cy), radius=r, start_angle=270, end_angle=90,
                 dxfattribs={"layer": layer})
    msp.add_arc((cx + r, cy), radius=r, start_angle=90, end_angle=270,
                 dxfattribs={"layer": layer})

    if adjustable:
        msp.add_line((cx - 3 * s, cy + r + 2 * s),
                     (cx + 3 * s, cy - r - 2 * s),
                     dxfattribs={"layer": layer})

    # 油路
    msp.add_line((cx - r * 2, cy), (cx - r, cy),
                 dxfattribs={"layer": layer})
    msp.add_line((cx + r, cy), (cx + r * 2, cy),
                 dxfattribs={"layer": layer})

    txt_h = 2.2 * s
    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": txt_h, "style": "HZ",
        })
        t.set_placement((cx, cy - r - 5 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    return (cx + r * 2, cy)


def draw_check_valve_hyd(msp, center, pilot_operated: bool = False,
                           spring_loaded: bool = True,
                           scale: float = 100.0,
                           label: str = "",
                           layer: str = "元件",
                           tracker=None):
    """单向阀 / 液控单向阀符号。

    参数:
        pilot_operated: True = 液控单向阀（带控制油路）
        spring_loaded: True = 带弹簧
    """
    s = scale
    cx, cy = _r(*center)
    r = 4.0 * s

    # 圆座
    msp.add_circle((cx, cy), r, dxfattribs={"layer": layer})

    # 钢球（实心小圆）
    ball_r = 2.0 * s
    try:
        msp.add_circle((cx - 1.5 * s, cy), ball_r,
                       dxfattribs={"layer": layer})
        msp.add_solid([(cx - 1.5 * s - ball_r * 0.6, cy - ball_r * 0.6),
                       (cx - 1.5 * s + ball_r * 0.6, cy - ball_r * 0.6),
                       (cx - 1.5 * s + ball_r * 0.6, cy + ball_r * 0.6),
                       (cx - 1.5 * s - ball_r * 0.6, cy + ball_r * 0.6)],
                      dxfattribs={"layer": layer})
    except Exception as _e:
        print(f'[警告] 操作失败：{_e}')

    # 弹簧
    if spring_loaded:
        spr_x = cx + 1.5 * s
        for i in range(3):
            msp.add_line((spr_x + i * 1.5 * s, cy - 3 * s),
                         (spr_x + i * 1.5 * s, cy + 3 * s),
                         dxfattribs={"layer": layer})

    # 油路
    msp.add_line((cx - r, cy), (cx - r - 6 * s, cy),
                 dxfattribs={"layer": layer})
    msp.add_line((cx + r + 6 * s if spring_loaded else cx + r, cy),
                 (cx + r + 6 * s if spring_loaded else cx + r + 6 * s, cy),
                 dxfattribs={"layer": layer})

    if pilot_operated:
        # 控制油路
        msp.add_line((cx, cy + r), (cx, cy + r + 6 * s),
                     dxfattribs={"layer": "油路", "linetype": "DASHED"})
        # 控制活塞
        msp.add_lwpolyline(
            [(cx - 2 * s, cy + r + 2 * s),
             (cx + 2 * s, cy + r + 2 * s),
             (cx + 2 * s, cy + r + 5 * s),
             (cx - 2 * s, cy + r + 5 * s)],
            close=True, dxfattribs={"layer": layer})

    return (cx + r + 6 * s, cy)


# ══════════════════════════════════════════════════════════
#  辅助元件
# ══════════════════════════════════════════════════════════

def draw_accumulator(msp, center, acc_type: str = "bladder",
                      scale: float = 100.0,
                      label: str = "",
                      params: dict = None,
                      layer: str = "元件",
                      tracker=None):
    """蓄能器符号。

    参数:
        acc_type: "bladder" 气囊式 / "piston" 活塞式 / "spring" 弹簧式
        params: {"volume":"10L","precharge":"120bar",...}
    """
    s = scale
    cx, cy = _r(*center)
    r = 7.0 * s

    # 半圆（下部）+ 水平线
    msp.add_arc((cx, cy), radius=r, start_angle=180, end_angle=360,
                 dxfattribs={"layer": layer})
    msp.add_line((cx - r, cy), (cx + r, cy),
                 dxfattribs={"layer": layer})

    # 竖直管线
    msp.add_line((cx, cy + r), (cx, cy + r + 5 * s),
                 dxfattribs={"layer": layer})

    if acc_type == "bladder":
        # 气囊分隔线
        msp.add_line((cx - r * 0.3, cy + r * 0.3),
                     (cx + r * 0.3, cy + r * 0.7),
                     dxfattribs={"layer": "细实线"})
    elif acc_type == "piston":
        # 活塞线
        msp.add_line((cx - r * 0.6, cy - r * 0.3),
                     (cx + r * 0.6, cy - r * 0.3),
                     dxfattribs={"layer": layer})

    txt_h = 2.2 * s
    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": txt_h, "style": "HZ",
        })
        t.set_placement((cx, cy - r - 5 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    return (cx + r, cy)


# ══════════════════════════════════════════════════════════
#  集成块 / 油路块
# ══════════════════════════════════════════════════════════

def draw_manifold(msp, origin, width: float, height: float,
                   depth: float = 0,
                   ports: List[dict] = None,
                   scale: float = 100.0,
                   label: str = "",
                   layer: str = "粗实线",
                   tracker=None):
    """绘制液压集成块（油路块）。

    参数:
        origin: 左下角 (x, y)
        width/height: 块外形尺寸 mm
        depth: 块厚 mm（三维概念，平面图仅标注）
        ports: 油口列表
            [{"face":"top","id":"P","x":50,"y":0,"dia":10,"thread":"G1/4"},...]
    """
    s = scale
    ox, oy = _r(*origin)
    w = width * s
    h = height * s

    # 块轮廓
    msp.add_lwpolyline(
        [(ox, oy), (ox + w, oy), (ox + w, oy + h), (ox, oy + h)],
        close=True, dxfattribs={"layer": layer}
    )

    # 油口
    if ports:
        for port in ports:
            face = port.get("face", "top")
            px = ox + port.get("x", 0) * s
            py = oy + port.get("y", 0) * s
            dia = port.get("dia", 8) * s
            port_id = port.get("id", "")

            if face in ("top", "bottom"):
                # 顶面/底面：圆 + 十字（表示螺孔）
                r = dia / 2
                msp.add_circle((px, py), r, dxfattribs={"layer": layer})
                msp.add_line((px - r, py), (px + r, py),
                             dxfattribs={"layer": "细实线"})
                msp.add_line((px, py - r), (px, py + r),
                             dxfattribs={"layer": "细实线"})
            else:
                # 侧面：矩形缺口
                msp.add_lwpolyline(
                    [(px - dia / 2, py - dia * 0.3),
                     (px + dia / 2, py - dia * 0.3),
                     (px + dia / 2, py + dia * 0.3),
                     (px - dia / 2, py + dia * 0.3)],
                    close=True, dxfattribs={"layer": layer})

            # 油口标识
            if port_id:
                txt_h = 2.0 * s
                t = msp.add_text(port_id, dxfattribs={
                    "layer": "文字", "height": txt_h, "style": "ENG",
                })
                t.set_placement((px, py + dia / 2 + 2 * s),
                                align=TextEntityAlignment.MIDDLE_CENTER)

    # ── 标注 ──
    txt_h = 2.5 * s
    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": txt_h, "style": "HZ",
        })
        t.set_placement((ox + w / 2, oy + h + 3 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    if depth > 0:
        t = msp.add_text(f"厚 {depth:.0f}", dxfattribs={
            "layer": "文字", "height": 2.0 * s, "style": "HZ",
        })
        t.set_placement((ox + w / 2, oy - 3 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    return (ox + w, oy + h)
