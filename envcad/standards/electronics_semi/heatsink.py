"""15. heatsink —— 散热器（叉指翅片型 / 针柱型），参数化几何。

依据标准:
  * GB/T 1804—2000 一般公差 未注公差的线性和角度尺寸（型材切削件取 m 级）
  * GB/T 6892—2015 一般工业用铝及铝合金挤压型材（材质 6063-T5）
  * GB/T 4458.1—2002 机械制图 图样画法（三视图配置）
  * 散热面积为纯几何计算，热阻需由热仿真/试验确定（本模块只出图）
      # TODO: verify against 具体产品热阻测试标准（如 JESD51 系列）

绘图约定: 结构件按 1:1 或缩小出图，scale 默认 1.0。
"""
from __future__ import annotations

import math

from ._common import (
    L_CENTER, L_HATCH, L_MID, L_OUTLINE, L_TEXT, L_THIN,
    TextEntityAlignment, dim_line, gb1804_tolerance, hole, notes,
    param_table, rect, text, view_title,
)


def draw_heatsink(msp, x, y, scale=1.0,
                  fin_type="plate",
                  base_w=80.0, base_l=60.0, base_t=6.0,
                  fin_count=11, fin_thickness=2.0, fin_height=25.0,
                  fin_edge=2.0,
                  pin_dia=4.0, pin_rows=6, pin_cols=8, pin_height=25.0,
                  mount_hole=4.5, mount_margin=6.0, mount_holes=True,
                  material="6063-T5",
                  tolerance_grade="m",
                  show_plan=True,
                  show_dims=True,
                  show_table=True,
                  show_notes=True,
                  tracker=None):
    """绘制散热器正视图（+ 俯视图）。

    参数（单位 mm，全部可调）:
        x, y            底板左下角（正视图）定位点
        fin_type        "plate" 平板翅片 / "pin" 针柱阵列
        base_w, base_l  底板宽（X）、深（Y）
        base_t          底板厚
        fin_count       翅片数（fin_type="plate"）
        fin_thickness   翅片厚
        fin_height      翅片高（不含底板）
        fin_edge        首末翅片距底板端面的距离
        pin_dia         针柱直径（fin_type="pin"）
        pin_rows/cols   针柱阵列行列数
        pin_height      针柱高
        mount_hole      安装孔径（M4 过孔取 4.5）
        mount_margin    安装孔中心距边距离
        tolerance_grade GB/T 1804 未注公差等级 f/m/c/v

    返回 dict: 外形范围、翅片间隙、散热面积估算 (mm²)。
    """
    s = scale
    total_h = base_t + (fin_height if fin_type == "plate" else pin_height)

    # ══ 正视图 ══
    rect(msp, x, y, base_w, base_t, L_OUTLINE)
    _hatch_base(msp, x, y, base_w, base_t, s)

    gap = 0.0
    if fin_type == "plate":
        span = base_w - 2 * fin_edge
        if fin_count > 1:
            step = (span - fin_thickness) / (fin_count - 1)
            gap = step - fin_thickness
        else:
            step = 0.0
        for i in range(fin_count):
            fx = x + fin_edge + i * step
            rect(msp, fx, y + base_t, fin_thickness, fin_height, L_MID)
        area = _plate_area(base_w, base_l, base_t, fin_count,
                           fin_thickness, fin_height)
    else:
        step = (base_w - 2 * mount_margin) / max(pin_cols - 1, 1)
        gap = step - pin_dia
        for i in range(pin_cols):
            px = x + mount_margin + i * step
            rect(msp, px - pin_dia / 2, y + base_t, pin_dia, pin_height, L_MID)
        area = _pin_area(base_w, base_l, pin_rows, pin_cols,
                         pin_dia, pin_height)

    ccx = x + base_w / 2
    msp.add_line((ccx, y - 4.0 * s), (ccx, y + total_h + 4.0 * s),
                 dxfattribs={"layer": L_CENTER})

    if show_dims:
        dim_line(msp, (x, y), (x + base_w, y), 12.0 * s, s,
                 f"{base_w:g}", tracker=tracker)
        dim_line(msp, (x, y), (x, y + total_h), 10.0 * s, s,
                 f"{total_h:g}", tracker=tracker)
        dim_line(msp, (x + base_w, y), (x + base_w, y + base_t),
                 -8.0 * s, s, f"{base_t:g}", tracker=tracker)
        if fin_type == "plate" and fin_count > 1:
            f0 = x + fin_edge
            dim_line(msp, (f0, y + base_t + fin_height),
                     (f0 + step, y + base_t + fin_height), -6.0 * s, s,
                     f"{step:.2f}", tracker=tracker)
            text(msp, f"{fin_count}×翅片 t={fin_thickness:g} 间隙 {gap:.2f}",
                 (x, y + base_t + fin_height + 6.0 * s), 2.5 * s,
                 layer=L_TEXT)
        else:
            text(msp, f"{pin_rows}×{pin_cols} 针柱 φ{pin_dia:g}×{pin_height:g}",
                 (x, y + base_t + pin_height + 6.0 * s), 2.5 * s,
                 layer=L_TEXT)

    view_title(msp, "正视图", ccx, y - 20.0 * s, s)

    # ══ 俯视图 ══
    plan_bbox = None
    if show_plan:
        py = y - base_l - 32.0 * s
        plan_bbox = _draw_plan(msp, x, py, base_w, base_l, fin_type,
                               fin_count, fin_thickness, fin_edge,
                               pin_rows, pin_cols, pin_dia,
                               mount_hole, mount_margin, mount_holes,
                               s, tracker=tracker)
        view_title(msp, "俯视图", x + base_w / 2, py - 16.0 * s, s)

    # ══ 参数表 ══
    tol = gb1804_tolerance(max(base_w, base_l), tolerance_grade)
    if show_table:
        param_table(msp, (x + base_w + 16.0 * s, y + total_h), [
            ("型式", "平板翅片" if fin_type == "plate" else "针柱阵列"),
            ("底板 W×L×t", f"{base_w:g}×{base_l:g}×{base_t:g}"),
            ("总高 H", f"{total_h:g}"),
            ("翅片/针柱", (f"{fin_count}×{fin_thickness:g}"
                          if fin_type == "plate"
                          else f"{pin_rows}×{pin_cols}-φ{pin_dia:g}")),
            ("通道间隙", f"{gap:.2f}"),
            ("散热面积", f"{area / 100.0:.0f} cm²"),
            ("材质", f"AL {material}"),
            ("未注公差", f"GB/T 1804-{tolerance_grade} (±{tol:g})"),
        ], s, title="散热器参数")

    if show_notes:
        notes(msp, (x, y - base_l - 56.0 * s if show_plan else y - 30.0 * s), [
            f"材质铝合金 {material}，挤压型材，符合 GB/T 6892—2015。",
            f"未注尺寸公差按 GB/T 1804-{tolerance_grade}（本件 ±{tol:g}mm）。",
            "底板贴合面平面度 ≤0.05/100，粗糙度 Ra1.6。",
            "表面阳极氧化黑色，膜厚 10~15μm，或喷砂本色。",
            "去除毛刺锐边，倒钝 C0.5。",
            "装配时涂导热硅脂（导热系数 ≥1.5 W/m·K），扭矩 0.6N·m。",
        ], s, title="技术要求", width=95.0, tracker=tracker)

    return {"bbox": (x, y, x + base_w, y + total_h),
            "total_height": total_h, "gap": gap,
            "area_mm2": area, "plan": plan_bbox}


def _hatch_base(msp, x, y, w, t, s):
    """底板剖面示意线（细实线，代表金属剖面）。"""
    n = max(int(w / (4.0 * s)), 2)
    for i in range(n):
        px = x + (i + 0.5) * w / n
        msp.add_line((px, y), (px - t, y + t), dxfattribs={"layer": L_HATCH})


def _draw_plan(msp, x, y, base_w, base_l, fin_type, fin_count,
               fin_t, fin_edge, pin_rows, pin_cols, pin_dia,
               mount_hole, mount_margin, mount_holes, s, tracker=None):
    """俯视图：底板外形 + 翅片/针柱投影 + 安装孔。"""
    rect(msp, x, y, base_w, base_l, L_OUTLINE)
    if fin_type == "plate":
        span = base_w - 2 * fin_edge
        step = (span - fin_t) / (fin_count - 1) if fin_count > 1 else 0.0
        for i in range(fin_count):
            fx = x + fin_edge + i * step
            rect(msp, fx, y + fin_edge, fin_t, base_l - 2 * fin_edge, L_MID)
    else:
        sx = (base_w - 2 * mount_margin) / max(pin_cols - 1, 1)
        sy = (base_l - 2 * mount_margin) / max(pin_rows - 1, 1)
        for r in range(pin_rows):
            for c in range(pin_cols):
                msp.add_circle((x + mount_margin + c * sx,
                                y + mount_margin + r * sy),
                               pin_dia / 2.0, dxfattribs={"layer": L_MID})
    if mount_holes:
        for hx in (x + mount_margin, x + base_w - mount_margin):
            for hy in (y + mount_margin, y + base_l - mount_margin):
                hole(msp, hx, hy, mount_hole, L_OUTLINE)
        dim_line(msp, (x + mount_margin, y + mount_margin),
                 (x + base_w - mount_margin, y + mount_margin),
                 6.0 * s, s, f"{base_w - 2 * mount_margin:g}", tracker=tracker)
        text(msp, f"4-φ{mount_hole:g}", (x + mount_margin,
                                         y + base_l + 3.0 * s),
             2.2 * s, align=TextEntityAlignment.MIDDLE_LEFT, layer=L_TEXT)
    dim_line(msp, (x, y), (x, y + base_l), 10.0 * s, s,
             f"{base_l:g}", tracker=tracker)
    return (x, y, x + base_w, y + base_l)


def _plate_area(w, l, t, n, ft, fh):
    """平板翅片散热器换热面积估算 (mm²)：底板裸露面 + 翅片双侧面 + 端面。"""
    fin_area = n * (2 * fh * l + ft * l)
    base_area = w * l - n * ft * l + 2 * (w + l) * t
    return fin_area + base_area


def _pin_area(w, l, rows, cols, d, h):
    """针柱散热器换热面积估算 (mm²)：柱侧面 + 柱顶 + 底板裸露面。"""
    n = rows * cols
    pin = n * (math.pi * d * h + math.pi * d * d / 4)
    base = w * l - n * math.pi * d * d / 4
    return pin + base
