"""13. ic_bga —— IC 封装 BGA（球栅阵列外形 + 焊球阵列）。

依据标准:
  * JEDEC JEP95 / MO-192《Fine-Pitch Ball Grid Array (FBGA)》
      符号定义: D/E 本体尺寸、e 焊球间距、b 焊球直径、
      A 封装总高、A1 焊球高度、SD/SE 阵列偏置
  * JEDEC JESD30 / JEP95 设计指南 4.5：行标号使用 A~Y，
      跳过 I、O、Q、S、X、Z（易与数字混淆），超过后用 AA、AB…
  * IPC-7095《Design and Assembly Process Implementation for BGAs》
  * GB/T 4458.4—2003 尺寸注法

绘图约定: 建议放大出图，scale=0.2 即 5:1。焊球阵列按**底视图**绘制。
"""
from __future__ import annotations

from ._common import (
    L_CENTER, L_MID, L_OUTLINE, L_PHANTOM, L_TEXT, L_THIN,
    TextEntityAlignment, dim_line, notes, param_table, rect, text, view_title,
)

#: JEP95 4.5 允许的行标号字母（已剔除 I O Q S X Z）
ROW_LETTERS = "ABCDEFGHJKLMNPRTUVWY"

#: 常见 FBGA 变体: 代号 -> (本体D, 本体E, 间距e, 行数, 列数, 焊球径b)
BGA_VARIANTS = {
    "FBGA64":  (10.0, 10.0, 0.80, 8, 8, 0.45),
    "FBGA144": (13.0, 13.0, 0.80, 12, 12, 0.45),
    "FBGA256": (17.0, 17.0, 1.00, 16, 16, 0.50),
    "BGA324":  (19.0, 19.0, 1.00, 18, 18, 0.60),
}


def row_label(index: int) -> str:
    """按 JEDEC JEP95 4.5 生成第 index（0 起）行的标号。"""
    n = len(ROW_LETTERS)
    if index < n:
        return ROW_LETTERS[index]
    return ROW_LETTERS[index // n - 1] + ROW_LETTERS[index % n]


def draw_ic_bga(msp, x, y, scale=0.2,
                variant="FBGA144",
                body_x=None, body_y=None, pitch=None,
                rows=None, cols=None, ball_dia=None,
                depopulate=0,
                total_height=1.20,
                ball_height=0.35,
                substrate_thickness=0.26,
                a1_marker=0.8,
                show_side_view=True,
                show_dims=True,
                show_table=True,
                show_notes=True,
                label_grid=True,
                tracker=None):
    """绘制 BGA 封装底视图（焊球阵列）+ 侧视图。

    参数（单位 mm，全部可调）:
        x, y            封装本体中心定位点
        variant         JEDEC 变体名，查 BGA_VARIANTS
        body_x, body_y  本体 D、E
        pitch           焊球间距 e
        rows, cols      阵列行/列数
        ball_dia        焊球直径 b
        depopulate      中心去球区边长（球数），0 = 满阵列
        total_height    封装总高 A
        ball_height     焊球高度 A1
        substrate_thickness 基板厚度（侧视图用）
        a1_marker       A1 角标识圆直径

    返回 dict: 本体范围、焊球中心坐标列表、球数。
    """
    s = scale
    vd, ve, vp, vr, vc, vb = BGA_VARIANTS.get(variant, BGA_VARIANTS["FBGA144"])
    body_x = vd if body_x is None else body_x
    body_y = ve if body_y is None else body_y
    pitch = vp if pitch is None else pitch
    rows = vr if rows is None else rows
    cols = vc if cols is None else cols
    ball_dia = vb if ball_dia is None else ball_dia

    bx, by = body_x / 2.0, body_y / 2.0

    # ── 本体轮廓（粗实线）──
    rect(msp, x - bx, y - by, body_x, body_y, L_OUTLINE)

    # ── A1 角倒角（JEDEC 惯例：底视图左上角）──
    ch = min(a1_marker * 1.2, body_x * 0.1)
    msp.add_line((x - bx, y + by - ch), (x - bx + ch, y + by),
                 dxfattribs={"layer": L_OUTLINE})
    msp.add_circle((x - bx + a1_marker * 1.4, y + by - a1_marker * 1.4),
                   a1_marker / 2.0, dxfattribs={"layer": L_OUTLINE})

    # ── 焊球阵列（底视图）──
    x_first = -(cols - 1) * pitch / 2.0
    y_first = (rows - 1) * pitch / 2.0
    lo_r, hi_r = _depop_range(rows, depopulate)
    lo_c, hi_c = _depop_range(cols, depopulate)

    balls = []
    r_ball = ball_dia / 2.0
    for r in range(rows):
        for c in range(cols):
            if depopulate > 0 and lo_r <= r <= hi_r and lo_c <= c <= hi_c:
                continue
            cx = x + x_first + c * pitch
            cy = y + y_first - r * pitch
            msp.add_circle((cx, cy), r_ball, dxfattribs={"layer": L_MID})
            balls.append((cx, cy, row_label(r), c + 1))

    # ── 阵列包络（假想线）──
    ax = (cols - 1) * pitch / 2.0 + r_ball
    ay = (rows - 1) * pitch / 2.0 + r_ball
    rect(msp, x - ax, y - ay, 2 * ax, 2 * ay, L_PHANTOM)

    # ── 行列标号 ──
    if label_grid:
        th = min(pitch * 0.55, 2.0 * s)
        for r in range(rows):
            cy = y + y_first - r * pitch
            text(msp, row_label(r), (x - bx - 1.5 * s, cy), th,
                 align=TextEntityAlignment.MIDDLE_RIGHT, layer=L_TEXT)
        for c in range(cols):
            cx = x + x_first + c * pitch
            text(msp, str(c + 1), (cx, y - by - 2.0 * s), th,
                 align=TextEntityAlignment.MIDDLE_CENTER, layer=L_TEXT)

    # ── 中心线 ──
    msp.add_line((x - bx - 3 * s, y), (x + bx + 3 * s, y),
                 dxfattribs={"layer": L_CENTER})
    msp.add_line((x, y - by - 3 * s), (x, y + by + 3 * s),
                 dxfattribs={"layer": L_CENTER})

    # ── 尺寸标注 ──
    if show_dims:
        dim_line(msp, (x - bx, y - by), (x + bx, y - by), 12.0 * s, s,
                 f"D={body_x:g}", tracker=tracker)
        dim_line(msp, (x - bx, y - by), (x - bx, y + by), 14.0 * s, s,
                 f"E={body_y:g}", tracker=tracker)
        c0 = x + x_first
        dim_line(msp, (c0, y + ay), (c0 + pitch, y + ay), -6.0 * s, s,
                 f"e={pitch:g}", tracker=tracker)
        text(msp, f"{len(balls)}-φ{ball_dia:g} 焊球",
             (x + bx + 2.0 * s, y - by - 2.0 * s), 2.2 * s, layer=L_TEXT)

    view_title(msp, f"{variant} 底视图（焊球面）", x, y - by - 12.0 * s, s)

    # ── 侧视图 ──
    if show_side_view:
        sy = y + by + 20.0 * s
        _draw_side_view(msp, x, sy, body_x, total_height, ball_height,
                        substrate_thickness, ball_dia, pitch, cols, s,
                        tracker=tracker)
        view_title(msp, "侧视图", x, sy - 9.0 * s, s)

    # ── 参数表 ──
    if show_table:
        param_table(msp, (x + bx + 14.0 * s, y + by), [
            ("封装代号", variant),
            ("本体 D×E", f"{body_x:g}×{body_y:g}"),
            ("焊球间距 e", f"{pitch:g}"),
            ("阵列 行×列", f"{rows}×{cols}"),
            ("焊球数", str(len(balls))),
            ("焊球径 b", f"φ{ball_dia:g}"),
            ("总高 A", f"{total_height:g}"),
            ("球高 A1", f"{ball_height:g}"),
        ], s, title="JEDEC MO-192")

    if show_notes:
        notes(msp, (x - bx - 6.0 * s, y - by - 20.0 * s), [
            f"封装符合 JEDEC MO-192 {variant}，焊球间距 e={pitch:g}mm。",
            f"焊球 φ{ball_dia:g}mm，材质 SAC305 无铅，共面度 ≤0.15mm。",
            "A1 球位于倒角侧，行标号跳过 I/O/Q/S/X/Z（JEP95 4.5）。",
            "PCB 焊盘按 IPC-7095 NSMD 设计，焊盘径取 0.8b。",
            "回流焊按 J-STD-020 曲线，峰值 245±5℃。",
            "装配后按 IPC-A-610 Class 2 及 X-Ray 检查空洞率 <25%。",
        ], s, title="封装技术要求", width=95.0, tracker=tracker)

    return {"body": (x - bx, y - by, x + bx, y + by),
            "balls": balls, "ball_count": len(balls),
            "rows": rows, "cols": cols}


def _depop_range(n: int, depop: int):
    """中心去球区的索引范围 [lo, hi]。"""
    if depop <= 0:
        return (1, 0)
    lo = (n - depop) // 2
    return (lo, lo + depop - 1)


def _draw_side_view(msp, cx, cy, body_x, total_h, ball_h, sub_t,
                    ball_dia, pitch, cols, s, tracker=None):
    """BGA 侧视图：基板 + 塑封体 + 底部焊球（半圆示意）。"""
    b = body_x / 2.0
    mold_h = total_h - ball_h - sub_t
    # 基板
    rect(msp, cx - b, cy + ball_h, body_x, sub_t, L_THIN)
    # 塑封体
    rect(msp, cx - b, cy + ball_h + sub_t, body_x, mold_h, L_OUTLINE)
    # 焊球（示意取两端与中间共 5 个）
    x_first = -(cols - 1) * pitch / 2.0
    idx = sorted({0, cols // 4, cols // 2, 3 * cols // 4, cols - 1})
    for i in idx:
        bx = cx + x_first + i * pitch
        msp.add_arc((bx, cy + ball_h), ball_dia / 2.0, 180, 360,
                    dxfattribs={"layer": L_MID})
        msp.add_line((bx - ball_dia / 2, cy + ball_h),
                     (bx + ball_dia / 2, cy + ball_h),
                     dxfattribs={"layer": L_MID})
    # 座平面
    msp.add_line((cx - b - 1.0 * s, cy), (cx + b + 1.0 * s, cy),
                 dxfattribs={"layer": L_THIN})
    dim_line(msp, (cx - b, cy), (cx - b, cy + total_h), 8.0 * s, s,
             f"A={total_h:g}", tracker=tracker)
