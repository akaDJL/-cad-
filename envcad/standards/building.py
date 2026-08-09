"""建筑制图 v1.0（GB/T 50001—2017、GB 50352—2019、GB 50009—2012）。

楼层剖面、平面布置、墙体立面、柱、梁、楼板、门窗、楼梯。
纯 ezdxf，零新依赖。所有设计参数（层高、墙厚、柱截面等）由 Agent 搜索后显式传入。

核心场景：工程师说"层高改 3.6"、"墙厚加到 240"、"加个楼梯"——改参数即重出图。
"""
from __future__ import annotations
import math
from typing import List, Optional, Tuple
from ezdxf.enums import TextEntityAlignment
from ..utils import _r, _tri

# ══════════════════════════════════════════════════════════
#  楼层剖面（层高核心）— "层高 3m→3.6m" 改 floor_height 即可
# ══════════════════════════════════════════════════════════

def draw_floor_section(msp, origin, n_floors=3, floor_height=3.0, width=12.0,
                        wall_thickness=0.24, slab_thickness=0.12, basement=0,
                        scale=100.0, label="", layer="建筑", tracker=None):
    """多层建筑立面剖面。核心：n_floors/floor_height 控制层数层高。

    参数:
        n_floors: 地上楼层数
        floor_height: 层高 m（改这个即改变建筑高度）
        width: 建筑宽度 m
        wall_thickness: 墙厚 m
        slab_thickness: 楼板厚 m
        basement: 地下室层数
    """
    s = scale; ox, oy = _r(*origin); w = width * s
    fh = floor_height * s; sth = slab_thickness * s; wth = wall_thickness * s
    total_h = fh * n_floors + basement * fh
    base_y = oy
    if basement:
        base_y = oy - basement * fh

    # 外墙轮廓
    msp.add_lwpolyline([(ox, base_y), (ox + w, base_y), (ox + w, base_y + total_h),
                         (ox, base_y + total_h)], close=True,
                       dxfattribs={"layer": layer})

    # 楼层分隔线（楼板）+ 层高标注
    for i in range(n_floors + 1 + basement):
        ly = base_y + i * fh if (basement == 0 or i <= basement) else base_y + i * fh
        if i <= n_floors + basement:
            floor_y = base_y + i * fh
            msp.add_line((ox, floor_y), (ox + w, floor_y),
                         dxfattribs={"layer": "细实线"})
            # 楼板线（加粗示意）
            if i > 0:
                msp.add_line((ox, floor_y - sth), (ox + w, floor_y - sth),
                             dxfattribs={"layer": "细实线"})
            # 楼层标注（右侧）
            if i < n_floors + basement:
                mid_y = floor_y + fh / 2
                floor_label = f"{i+1-basement}F" if basement else f"{i+1}F"
                t = msp.add_text(floor_label, dxfattribs={
                    "layer": "文字", "height": 2.5 * s, "style": "HZ"})
                t.set_placement((ox + w + 3 * s, mid_y),
                                align=TextEntityAlignment.MIDDLE_LEFT)

    # 层高标注（最右边竖线 + 数值）
    dim_x = ox + w + 8 * s
    msp.add_line((dim_x, base_y), (dim_x, base_y + total_h),
                 dxfattribs={"layer": "细实线-尺寸"})
    for i in range(n_floors + basement):
        fy1 = base_y + i * fh
        fy2 = fy1 + fh
        msp.add_line((dim_x - 2 * s, fy1), (dim_x + 2 * s, fy1),
                     dxfattribs={"layer": "细实线-尺寸"})
        msp.add_line((dim_x - 2 * s, fy2), (dim_x + 2 * s, fy2),
                     dxfattribs={"layer": "细实线-尺寸"})
        f_label = f"{floor_height*1000:.0f}"
        t = msp.add_text(f"层高{f_label}", dxfattribs={
            "layer": "文字", "height": 2.0 * s, "style": "HZ"})
        t.set_placement((dim_x + 2 * s, (fy1 + fy2) / 2),
                        align=TextEntityAlignment.MIDDLE_LEFT)

    # 室内标高（±0.000 / 各层标高）
    for i in range(n_floors + 1):
        level_y = base_y + i * fh
        level_val = (i - basement) * floor_height
        lvl_text = f"{level_val:+.3f}" if level_val >= 0 else f"{level_val:.3f}"
        t = msp.add_text(lvl_text, dxfattribs={
            "layer": "文字", "height": 2.0 * s, "style": "HZ"})
        t.set_placement((ox - 3 * s, level_y), align=TextEntityAlignment.MIDDLE_RIGHT)
        msp.add_line((ox - 2 * s, level_y), (ox + 2 * s, level_y),
                     dxfattribs={"layer": "细实线"})

    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": 3.5 * s, "style": "HZ"})
        t.set_placement((ox + w / 2, base_y + total_h + 5 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)


# ══════════════════════════════════════════════════════════
#  楼层平面图
# ══════════════════════════════════════════════════════════

def draw_floor_plan(msp, origin, width=12.0, length=18.0, wall_thickness=0.24,
                     column_spacing=6.0, scale=100.0, label="", layer="建筑",
                     tracker=None):
    """单层平面布置图（轴线/墙/柱网）。

    参数:
        width/length: 建筑外围尺寸 m
        wall_thickness: 墙厚 m
        column_spacing: 柱网间距 m（0=无柱）
    """
    s = scale; ox, oy = _r(*origin)
    w = width * s; l = length * s; wth = wall_thickness * s

    # 轴线网
    n_ax_w = int(width / column_spacing) + 1 if column_spacing > 0 else 3
    n_ax_l = int(length / column_spacing) + 1 if column_spacing > 0 else 4
    for i in range(n_ax_w):
        ax = ox + i * w / (n_ax_w - 1)
        msp.add_line((ax, oy - 5 * s), (ax, oy + l + 5 * s),
                     dxfattribs={"layer": "细实线", "linetype": "CENTER"})
        t = msp.add_text(f"{i+1}", dxfattribs={
            "layer": "文字", "height": 2 * s, "style": "HZ"})
        t.set_placement((ax, oy - 6 * s), align=TextEntityAlignment.MIDDLE_CENTER)
    for j in range(n_ax_l):
        ay = oy + j * l / (n_ax_l - 1)
        msp.add_line((ox - 5 * s, ay), (ox + w + 5 * s, ay),
                     dxfattribs={"layer": "细实线", "linetype": "CENTER"})
        t = msp.add_text(chr(65 + j), dxfattribs={
            "layer": "文字", "height": 2 * s, "style": "HZ"})
        t.set_placement((ox - 6 * s, ay), align=TextEntityAlignment.MIDDLE_CENTER)

    # 外墙（双线）
    msp.add_lwpolyline([(ox, oy), (ox + w, oy), (ox + w, oy + l), (ox, oy + l)],
                       close=True, dxfattribs={"layer": layer})
    msp.add_lwpolyline(
        [(ox + wth, oy + wth), (ox + w - wth, oy + wth),
         (ox + w - wth, oy + l - wth), (ox + wth, oy + l - wth)],
        close=True, dxfattribs={"layer": "细实线"})

    # 柱网
    if column_spacing > 0:
        cs = column_spacing * s
        for ci in range(int(width / column_spacing) + 1):
            for cj in range(int(length / column_spacing) + 1):
                cx = ox + ci * cs
                cy = oy + cj * cs
                if ci == 0 and cj == 0:
                    continue
                if ci == int(width / column_spacing) and cj == int(length / column_spacing):
                    continue
                col_s = 0.5 * s  # 柱截面示意
                msp.add_lwpolyline(
                    [(cx - col_s, cy - col_s), (cx + col_s, cy - col_s),
                     (cx + col_s, cy + col_s), (cx - col_s, cy + col_s)],
                    close=True, dxfattribs={"layer": layer})

    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": 3.5 * s, "style": "HZ"})
        t.set_placement((ox + w / 2, oy + l + 5 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)


# ══════════════════════════════════════════════════════════
#  墙体立面
# ══════════════════════════════════════════════════════════

def draw_wall_elevation(msp, origin, length=6.0, height=3.0, thickness=0.24,
                         openings=None, scale=100.0, label="", layer="建筑",
                         tracker=None):
    """墙体立面（单段墙，含门窗洞口）。

    参数:
        length: 墙长 m
        height: 墙高 m（通常=层高）
        thickness: 墙厚 m
        openings: 洞口列表 [{"x":1.0,"w":1.5,"y_sill":0.9,"h":1.5,"type":"window"},...]
    """
    s = scale; ox, oy = _r(*origin)
    L = length * s; H = height * s; th = thickness * s

    # 墙体外轮廓
    msp.add_lwpolyline([(ox, oy), (ox + L, oy), (ox + L, oy + H), (ox, oy + H)],
                       close=True, dxfattribs={"layer": layer})

    # 填充图案（简化：砖填充示意 = 细水平线）
    n_lines = 10
    for i in range(1, n_lines):
        ly = oy + H * i / n_lines
        msp.add_line((ox, ly), (ox + L, ly), dxfattribs={"layer": "细实线-辅助"})

    # 顶梁示意（加粗区域）
    bh = 0.3 * s
    msp.add_lwpolyline([(ox, oy + H - bh), (ox + L, oy + H - bh),
                         (ox + L, oy + H), (ox, oy + H)],
                       close=True, dxfattribs={"layer": layer})

    # 门窗洞口
    if openings:
        for op in openings:
            ox_x = ox + op.get("x", 0) * s
            ox_w = op.get("w", 1.0) * s
            ox_ys = oy + op.get("y_sill", 0.9) * s
            ox_h = op.get("h", 1.5) * s
            op_type = op.get("type", "window")
            # 洞口虚线
            msp.add_lwpolyline([(ox_x, ox_ys), (ox_x + ox_w, ox_ys),
                                (ox_x + ox_w, ox_ys + ox_h), (ox_x, ox_ys + ox_h)],
                               close=True, dxfattribs={
                                   "layer": "细实线", "linetype": "DASHED"})
            # 窗：十字线 / 门：单开门弧
            if op_type == "window":
                msp.add_line((ox_x + ox_w / 2, ox_ys), (ox_x + ox_w / 2, ox_ys + ox_h),
                             dxfattribs={"layer": "细实线"})
                msp.add_line((ox_x, ox_ys + ox_h / 2), (ox_x + ox_w, ox_ys + ox_h / 2),
                             dxfattribs={"layer": "细实线"})
            elif op_type == "door":
                # 门扇弧（90° 打开示意）
                arc_pts = [(ox_x + ox_w, ox_ys + ox_h * 0.5 + th * 2) for th in
                           [t * 0.1 for t in range(11)]]
                arc_x = ox_x
                arc_y = ox_ys + ox_h * 0.5
                pts = [(arc_x + ox_w * math.cos(math.pi / 2 * t / 10),
                        arc_y + ox_h * 0.5 * math.sin(math.pi / 2 * t / 10))
                       for t in range(11)]
                msp.add_lwpolyline(pts, dxfattribs={"layer": "细实线"})

    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": 3 * s, "style": "HZ"})
        t.set_placement((ox + L / 2, oy + H + 4 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)


# ══════════════════════════════════════════════════════════
#  柱
# ══════════════════════════════════════════════════════════

def draw_column(msp, origin, width=0.5, depth=0.5, height=3.0, column_type="rect",
                 scale=100.0, label="", layer="建筑", tracker=None):
    """矩形/圆形柱（平面）。column_type: rect/circle。

    参数:
        width/depth: 柱截面尺寸 m（圆形则 width=直径）
        height: 柱高 m
    """
    s = scale; ox, oy = _r(*origin)
    w = width * s; d = depth * s

    if column_type == "circle":
        r = w / 2
        msp.add_circle((ox, oy), r, dxfattribs={"layer": layer})
        # 十字中心
        msp.add_line((ox - r, oy), (ox + r, oy), dxfattribs={"layer": "细实线", "linetype": "CENTER"})
        msp.add_line((ox, oy - r), (ox, oy + r), dxfattribs={"layer": "细实线", "linetype": "CENTER"})
        dim_text = f"D{width*1000:.0f}"
    else:
        msp.add_lwpolyline([(ox, oy), (ox + w, oy), (ox + w, oy + d), (ox, oy + d)],
                           close=True, dxfattribs={"layer": layer})
        # 填充示意
        msp.add_lwpolyline([(ox + 1 * s, oy + 1 * s), (ox + w - 1 * s, oy + d - 1 * s)],
                           dxfattribs={"layer": "细实线"})
        msp.add_lwpolyline([(ox + 1 * s, oy + d - 1 * s), (ox + w - 1 * s, oy + 1 * s)],
                           dxfattribs={"layer": "细实线"})
        dim_text = f"{width*1000:.0f}x{depth*1000:.0f}"

    if label:
        t = msp.add_text(f"{label} {dim_text}", dxfattribs={
            "layer": "文字", "height": 2 * s, "style": "HZ"})
        t.set_placement((ox + w / 2, oy + d + 2 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)


# ══════════════════════════════════════════════════════════
#  梁
# ══════════════════════════════════════════════════════════

def draw_beam(msp, origin, span=6.0, width=0.3, depth=0.6, scale=100.0,
               label="", layer="建筑", tracker=None):
    """矩形梁（平面+截面）。span/width/depth 单位 m。"""
    s = scale; ox, oy = _r(*origin)
    L = span * s; w = width * s; d = depth * s

    # 梁平面（粗线）
    msp.add_lwpolyline([(ox, oy), (ox + L, oy), (ox + L, oy + w), (ox, oy + w)],
                       close=True, dxfattribs={"layer": layer})

    # 梁截面（右侧，垂直展示）
    sec_ox = ox + L + 4 * s
    msp.add_lwpolyline(
        [(sec_ox, oy), (sec_ox + d, oy), (sec_ox + d, oy + w), (sec_ox, oy + w)],
        close=True, dxfattribs={"layer": layer})
    t = msp.add_text(f"b×h={width*1000:.0f}×{depth*1000:.0f}", dxfattribs={
        "layer": "文字", "height": 2 * s, "style": "HZ"})
    t.set_placement((sec_ox + d / 2, oy + w + 2 * s),
                    align=TextEntityAlignment.MIDDLE_CENTER)

    # 截面剖切线
    msp.add_line((ox + L / 2 - 3 * s, oy - 3 * s), (ox + L / 2 + 3 * s, oy - 3 * s),
                 dxfattribs={"layer": "细实线"})
    msp.add_line((ox + L / 2 - 3 * s, oy + w + 3 * s),
                 (ox + L / 2 + 3 * s, oy + w + 3 * s), dxfattribs={"layer": "细实线"})
    t2 = msp.add_text("1", dxfattribs={
        "layer": "文字", "height": 2 * s, "style": "HZ"})
    t2.set_placement((ox + L / 2, oy - 5 * s), align=TextEntityAlignment.MIDDLE_CENTER)

    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": 3 * s, "style": "HZ"})
        t.set_placement((ox + L / 2, oy + w + 7 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)


# ══════════════════════════════════════════════════════════
#  门窗洞口
# ══════════════════════════════════════════════════════════

def draw_door_opening(msp, origin, width=1.0, height=2.1, scale=100.0,
                       label="", layer="建筑", tracker=None):
    """门（立面/平面）。width/height m。"""
    s = scale; ox, oy = _r(*origin)
    w = width * s; h = height * s

    # 门框
    msp.add_lwpolyline([(ox, oy), (ox + w, oy), (ox + w, oy + h), (ox, oy + h)],
                       close=True, dxfattribs={"layer": layer})
    # 门扇（双线）
    msp.add_line((ox + 0.5 * s, oy + 0.5 * s), (ox + w - 0.5 * s, oy + h - 0.5 * s),
                 dxfattribs={"layer": "细实线"})
    # 开门方向弧
    arc_pts = [(ox + 0.5 * s + w * 0.3 * math.cos(math.pi / 2 * t / 10),
                oy + 0.5 * s + h * 0.5 * math.sin(math.pi / 2 * t / 10))
               for t in range(11)]
    msp.add_lwpolyline(arc_pts, dxfattribs={"layer": "细实线"})

    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字", "height": 2 * s, "style": "HZ"})
        t.set_placement((ox + w / 2, oy + h + 2 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)


def draw_window_opening(msp, origin, width=1.5, height=1.5, sill_height=0.9,
                         scale=100.0, label="", layer="建筑", tracker=None):
    """窗（立面）。width/height/sill_height m。"""
    s = scale; ox, oy = _r(*origin)
    w = width * s; h = height * s; sy = oy + sill_height * s

    # 窗框
    msp.add_lwpolyline([(ox, sy), (ox + w, sy), (ox + w, sy + h), (ox, sy + h)],
                       close=True, dxfattribs={"layer": layer})
    # 窗扇分割（十字）
    msp.add_line((ox + w / 2, sy), (ox + w / 2, sy + h),
                 dxfattribs={"layer": "细实线"})
    msp.add_line((ox, sy + h / 2), (ox + w, sy + h / 2),
                 dxfattribs={"layer": "细实线"})
    # 窗台线
    msp.add_line((ox - 1 * s, sy), (ox + w + 1 * s, sy),
                 dxfattribs={"layer": "细实线"})
    # 窗下墙体示意（虚线表示窗下墙）
    msp.add_line((ox, oy), (ox + w, oy),
                 dxfattribs={"layer": "细实线"})

    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字", "height": 2 * s, "style": "HZ"})
        t.set_placement((ox + w / 2, sy + h + 2 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)


# ══════════════════════════════════════════════════════════
#  楼梯
# ══════════════════════════════════════════════════════════

def draw_staircase(msp, origin, width=2.4, floor_height=3.0, n_steps=18,
                    scale=100.0, label="", layer="建筑", tracker=None):
    """楼梯平面/剖面。width/floor_height m。

    参数:
        width: 梯段宽 m
        floor_height: 层高 m
        n_steps: 踏步数
    """
    s = scale; ox, oy = _r(*origin)
    w = width * s; h = floor_height * s; n = n_steps
    step_w = 0.28 * s   # 踏步宽
    step_h = h / n      # 踏步高
    run_length = step_w * (n // 2)

    # 楼梯平面（简画）
    msp.add_lwpolyline([(ox, oy), (ox + w, oy), (ox + w, oy + run_length * 2 + w),
                         (ox, oy + run_length * 2 + w)], close=True,
                       dxfattribs={"layer": layer})

    # 梯段线
    for i in range(n // 2 + 1):
        sx = ox + w + i * step_w
        msp.add_line((sx, oy), (sx, oy + w), dxfattribs={"layer": "细实线"})
        msp.add_line((sx, oy + w + run_length),
                     (sx, oy + w + run_length + w), dxfattribs={"layer": "细实线"})

    # 楼梯剖面（右侧）
    prof_ox = ox + w + run_length + 5 * s
    for i in range(n + 1):
        sx = prof_ox + i * step_w if i <= n // 2 else prof_ox + run_length + (n - i) * step_w
        sy = oy + i * step_h if i <= n // 2 else oy + (n - i) * step_h
        msp.add_line((sx, sy), (max(sx - step_w, prof_ox), sy),
                     dxfattribs={"layer": layer})

    # 上下方向箭头
    mid_y = oy + w + run_length / 2
    msp.add_line((ox + w / 2, oy), (ox + w / 2, mid_y - 3 * s),
                 dxfattribs={"layer": "细实线"})
    _tri(msp, (ox + w / 2, mid_y - 3 * s), (0, -1), s, "细实线")
    msp.add_line((ox + w / 2, oy + 2 * w + run_length),
                 (ox + w / 2, mid_y + w + run_length),
                 dxfattribs={"layer": "细实线"})
    _tri(msp, (ox + w / 2, mid_y + w + run_length), (0, 1), s, "细实线")

    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": 3 * s, "style": "HZ"})
        t.set_placement((ox + w / 2, prof_ox + 5 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)


# ══════════════════════════════════════════════════════════
#  屋顶（平顶/坡顶）
# ══════════════════════════════════════════════════════════

def draw_roof(msp, origin, width=12.0, depth=15.0, roof_type="flat",
               slope=30.0, overhang=0.6, scale=100.0, label="",
               layer="建筑", tracker=None):
    """屋顶（平顶/坡顶/穹顶）。

    参数:
        width/depth: 屋面尺寸 m
        roof_type: flat(平顶)/gable(人字坡)/hip(四坡)
        slope: 坡度 (°)
        overhang: 挑檐 m
    """
    s = scale; ox, oy = _r(*origin)
    w = width * s; d = depth * s; oh = overhang * s

    if roof_type == "flat":
        # 平顶：矩形 + 女儿墙短竖线 + 排水坡度箭头
        msp.add_lwpolyline([(ox, oy), (ox + w, oy), (ox + w, oy + d), (ox, oy + d)],
                           close=True, dxfattribs={"layer": layer})
        msp.add_lwpolyline([(ox - oh, oy - oh), (ox + w + oh, oy - oh),
                             (ox + w + oh, oy + d + oh), (ox - oh, oy + d + oh)],
                           close=True, dxfattribs={"layer": "细实线"})
        # 排水坡箭头
        for i in range(3):
            ax = ox + w * (0.3 + i * 0.2)
            msp.add_line((ax, oy + d), (ax + 4 * s, oy + d + 3 * s),
                         dxfattribs={"layer": "细实线"})
            _tri(msp, (ax + 4 * s, oy + d + 3 * s), (1, 1), s, "细实线")
        t = msp.add_text("i=2%", dxfattribs={
            "layer": "文字", "height": 2 * s, "style": "HZ"})
        t.set_placement((ox + w / 2, oy + d + 5 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    elif roof_type in ("gable", "hip"):
        # 坡顶投影：矩形 + 脊线
        ridge_y = oy + d * 0.5
        ridge_h = d * 0.5 * math.tan(math.radians(slope)) * s
        msp.add_lwpolyline([(ox, oy), (ox + w, oy), (ox + w, oy + d), (ox, oy + d)],
                           close=True, dxfattribs={"layer": layer})
        msp.add_line((ox + w * 0.25, ridge_y), (ox + w * 0.75, ridge_y),
                     dxfattribs={"layer": "细实线", "linetype": "DASHED"})
        # 坡度标注
        t = msp.add_text(f"{slope:.0f}°", dxfattribs={
            "layer": "文字", "height": 2.5 * s, "style": "HZ"})
        t.set_placement((ox + w / 2, oy + d + 4 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": 3.5 * s, "style": "HZ"})
        t.set_placement((ox + w / 2, oy + d + 7 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)


# ══════════════════════════════════════════════════════════
#  幕墙
# ══════════════════════════════════════════════════════════

def draw_curtain_wall(msp, origin, width=8.0, height=15.0, n_panels_w=5,
                       n_panels_h=10, scale=100.0, label="", layer="建筑",
                       tracker=None):
    """玻璃幕墙立面。

    参数:
        width/height: 幕墙尺寸 m
        n_panels_w/h: 横向/竖向分格数
    """
    s = scale; ox, oy = _r(*origin)
    w = width * s; h = height * s

    # 幕墙轮廓
    msp.add_lwpolyline([(ox, oy), (ox + w, oy), (ox + w, oy + h), (ox, oy + h)],
                       close=True, dxfattribs={"layer": layer})

    # 分格线（竖向龙骨）
    for i in range(1, n_panels_w):
        px = ox + w * i / n_panels_w
        msp.add_line((px, oy), (px, oy + h), dxfattribs={"layer": "细实线"})

    # 分格线（横向龙骨）
    for j in range(1, n_panels_h):
        py = oy + h * j / n_panels_h
        msp.add_line((ox, py), (ox + w, py), dxfattribs={"layer": "细实线"})

    # 开启扇示意（左下角一格）
    panel_w = w / n_panels_w
    panel_h = h / n_panels_h
    msp.add_lwpolyline([
        (ox + panel_w * 0.1, oy + panel_h * 0.1),
        (ox + panel_w * 0.9, oy + panel_h * 0.1),
        (ox + panel_w * 0.9, oy + panel_h * 0.9),
        (ox + panel_w * 0.1, oy + panel_h * 0.9)],
        close=True, dxfattribs={"layer": "细实线"})
    msp.add_line((ox + panel_w * 0.1, oy + panel_h * 0.1),
                 (ox + panel_w * 0.9, oy + panel_h * 0.9),
                 dxfattribs={"layer": "细实线"})
    msp.add_line((ox + panel_w * 0.1, oy + panel_h * 0.9),
                 (ox + panel_w * 0.9, oy + panel_h * 0.1),
                 dxfattribs={"layer": "细实线"})

    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": 3.5 * s, "style": "HZ"})
        t.set_placement((ox + w / 2, oy + h + 4 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)


# ══════════════════════════════════════════════════════════
#  阳台 / 雨篷 / 女儿墙 / 坡道 / 基础平面 / 变形缝
# ══════════════════════════════════════════════════════════

def draw_balcony(msp, origin, width=3.0, depth=1.5, railing_h=1.1,
                  scale=100.0, label="", layer="建筑", tracker=None):
    """阳台平面。width/depth/railing_h m。"""
    s = scale; ox, oy = _r(*origin)
    w = width * s; d = depth * s

    msp.add_lwpolyline([(ox, oy), (ox + w, oy), (ox + w, oy + d), (ox, oy + d)],
                       close=True, dxfattribs={"layer": layer})
    # 栏杆线
    msp.add_lwpolyline([(ox + 1 * s, oy + 1 * s), (ox + w - 1 * s, oy + 1 * s),
                         (ox + w - 1 * s, oy + d - 1 * s), (ox + 1 * s, oy + d - 1 * s)],
                       close=True, dxfattribs={"layer": "细实线"})
    t = msp.add_text(f"栏杆H={railing_h*1000:.0f}", dxfattribs={
        "layer": "文字", "height": 2 * s, "style": "HZ"})
    t.set_placement((ox + w / 2, oy + d + 2 * s),
                    align=TextEntityAlignment.MIDDLE_CENTER)
    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": 3 * s, "style": "HZ"})
        t.set_placement((ox + w / 2, oy + d + 5 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)


def draw_canopy(msp, origin, width=3.0, depth=1.5, thickness=0.1,
                 scale=100.0, label="", layer="建筑", tracker=None):
    """雨篷（平面+剖面）。width/depth/thickness m。"""
    s = scale; ox, oy = _r(*origin)
    w = width * s; d = depth * s; th = thickness * s

    msp.add_lwpolyline([(ox, oy), (ox + w, oy), (ox + w, oy + th), (ox, oy + th)],
                       close=True, dxfattribs={"layer": layer})
    # 悬挑箭头
    msp.add_line((ox + w / 2, oy + th), (ox + w / 2, oy + d), dxfattribs={"layer": "细实线"})
    _tri(msp, (ox + w / 2, oy + d), (0, 1), s, "细实线")
    t = msp.add_text(f"挑{depth*1000:.0f}", dxfattribs={
        "layer": "文字", "height": 2 * s, "style": "HZ"})
    t.set_placement((ox + w / 2 + 2 * s, oy + d / 2), align=TextEntityAlignment.MIDDLE_LEFT)
    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": 3 * s, "style": "HZ"})
        t.set_placement((ox + w / 2, oy + d + 4 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)


def draw_parapet(msp, origin, height=0.6, thickness=0.12, length=6.0,
                  scale=100.0, label="", layer="建筑", tracker=None):
    """女儿墙详图。height/thickness/length m。"""
    s = scale; ox, oy = _r(*origin)
    H = height * s; th = thickness * s; L = length * s

    msp.add_lwpolyline([(ox, oy), (ox + L, oy), (ox + L, oy + H), (ox, oy + H)],
                       close=True, dxfattribs={"layer": layer})
    # 压顶
    msp.add_lwpolyline([(ox - 1 * s, oy + H), (ox + L + 1 * s, oy + H),
                         (ox + L + 1 * s, oy + H + 4 * s), (ox - 1 * s, oy + H + 4 * s)],
                       close=True, dxfattribs={"layer": layer})
    # 泛水
    msp.add_line((ox + 2 * s, oy + H + 4 * s), (ox + 2 * s, oy + H + 10 * s),
                 dxfattribs={"layer": "细实线"})
    _tri(msp, (ox + 2 * s, oy + H + 10 * s), (0, 1), s, "细实线")
    t = msp.add_text("泛水", dxfattribs={
        "layer": "文字", "height": 2 * s, "style": "HZ"})
    t.set_placement((ox + 2 * s + 3 * s, oy + H + 7 * s),
                    align=TextEntityAlignment.MIDDLE_LEFT)
    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": 3 * s, "style": "HZ"})
        t.set_placement((ox + L / 2, oy + H + 14 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)


def draw_ramp(msp, origin, length=12.0, width=1.5, rise=0.9, scale=100.0,
               label="", layer="建筑", tracker=None):
    """无障碍坡道。length/width/rise m（1:12 标准）。"""
    s = scale; ox, oy = _r(*origin)
    L = length * s; w = width * s; H = rise * s

    # 坡道平面
    msp.add_lwpolyline([(ox, oy), (ox + L, oy), (ox + L, oy + w), (ox, oy + w)],
                       close=True, dxfattribs={"layer": layer})
    # 扶手
    msp.add_line((ox, oy + w + 2 * s), (ox + L, oy + w + 2 * s),
                 dxfattribs={"layer": "细实线"})
    # 坡度标注
    slope_ratio = length / rise if rise > 0 else 0
    t = msp.add_text(f"1:{slope_ratio:.0f}", dxfattribs={
        "layer": "文字", "height": 2.5 * s, "style": "HZ"})
    t.set_placement((ox + L / 2, oy - 4 * s), align=TextEntityAlignment.MIDDLE_CENTER)
    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": 3 * s, "style": "HZ"})
        t.set_placement((ox + L / 2, oy + w + 6 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)


def draw_expansion_joint(msp, origin, length=12.0, joint_width=0.03,
                          scale=100.0, label="", layer="建筑", tracker=None):
    """变形缝。length/joint_width m。"""
    s = scale * 5; ox, oy = _r(*origin)
    L = length * s; jw = joint_width * s

    msp.add_lwpolyline([(ox, oy), (ox + L, oy), (ox + L, oy + jw), (ox, oy + jw)],
                       close=True, dxfattribs={"layer": layer})
    # 填缝材料示意
    for i in range(5):
        fx = ox + L * (0.1 + i * 0.16)
        msp.add_line((fx, oy), (fx, oy + jw), dxfattribs={"layer": "细实线-辅助"})

    t = msp.add_text(f"缝宽{joint_width*1000:.0f}", dxfattribs={
        "layer": "文字", "height": 2 * s, "style": "HZ"})
    t.set_placement((ox + L / 2, oy - 3 * s), align=TextEntityAlignment.MIDDLE_CENTER)
    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": 3 * s, "style": "HZ"})
    t.set_placement((ox + L / 2, oy + jw + 5 * s),
                    align=TextEntityAlignment.MIDDLE_CENTER)


def draw_roof_plan(msp, origin, w=12.0, d=8.0, roof_type="hip",
                   eave=0.6, scale=100.0, label="", layer="粗实线", tracker=None):
    """屋顶平面图。hip=四坡/gable=双坡/flat=平顶。"""
    s=scale;ox,oy=_r(*origin);pw,pd=w*s,d*s;e=eave*s
    msp.add_lwpolyline([(ox,oy),(ox+pw,oy),(ox+pw,oy+pd),(ox,oy+pd)],close=True,dxfattribs={"layer":layer})
    msp.add_lwpolyline([(ox-e,oy-e),(ox+pw+e,oy-e),(ox+pw+e,oy+pd+e),(ox-e,oy+pd+e)],close=True,dxfattribs={"layer":"细实线"})
    cx,cy=ox+pw/2,oy+pd/2
    msp.add_line((ox-e,cy),(ox+pw+e,cy),dxfattribs={"layer":"细实线","linetype":"CENTER"})
    if roof_type=="hip":
        for dx in(-0.3*pw,0.3*pw):msp.add_line((cx+dx,oy-e),(ox-e,cy),dxfattribs={"layer":"细实线","linetype":"DASHED"})
    if label:
        t=msp.add_text(label,dxfattribs={"layer":"文字-标题","height":3*s,"style":"HZ"})
        t.set_placement((cx,oy+pd+e+5*s),align=TextEntityAlignment.MIDDLE_CENTER)
    return (ox+pw+e+5*s,oy+pd+e+8*s)


def draw_schedule_table(msp, origin, title="门窗表", headers=None, rows=None,
                        col_widths=None, scale=100.0, tracker=None):
    """通用工程表格（门窗表/设备表/材料表）。"""
    s=scale;ox,oy=_r(*origin)
    if not headers:headers=["编号","名称","规格(mm)","数量","备注"]
    if not rows:rows=[["M1","入户门","1000×2100","1","防盗门"],["C1","外窗","1500×1500","4","断桥铝"]]
    n=len(headers);nr=len(rows);cw=col_widths or[55]*n;tw=sum(cw);rh=6*s
    t=msp.add_text(title,dxfattribs={"layer":"文字-标题","height":3.5*s,"style":"HZ"})
    t.set_placement((ox+tw/2,oy),align=TextEntityAlignment.MIDDLE_CENTER)
    y=oy-rh
    msp.add_lwpolyline([(ox,y),(ox+tw,y),(ox+tw,y-rh),(ox,y-rh)],close=True,dxfattribs={"layer":"粗实线"})
    x=ox
    for i,h in enumerate(headers):
        msp.add_line((x+cw[i],y),(x+cw[i],y-rh),dxfattribs={"layer":"细实线"})
        t=msp.add_text(h,dxfattribs={"layer":"文字","height":2.8*s,"style":"HZ"})
        t.set_placement((x+cw[i]/2,y-rh/2),align=TextEntityAlignment.MIDDLE_CENTER);x+=cw[i]
    for ri,row in enumerate(rows):
        ry=y-(ri+1)*rh
        msp.add_lwpolyline([(ox,ry),(ox+tw,ry),(ox+tw,ry-rh),(ox,ry-rh)],close=True,dxfattribs={"layer":"细实线"})
        x=ox
        for ci,v in enumerate(row):
            if ci<n-1:msp.add_line((x+cw[ci],ry),(x+cw[ci],ry-rh),dxfattribs={"layer":"细实线"})
            t=msp.add_text(str(v),dxfattribs={"layer":"文字","height":2.5*s,"style":"HZ"})
            t.set_placement((x+cw[ci]/2,ry-rh/2),align=TextEntityAlignment.MIDDLE_CENTER);x+=cw[ci]
    return (ox+tw+5*s,ry-rh)
