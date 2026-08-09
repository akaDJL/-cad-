"""12. ic_qfp —— IC 封装 QFP（四侧扁平封装外形 + 引脚框架）。

依据标准:
  * JEDEC JEP95 / MS-026《Plastic Quad Flat Package (LQFP)》
      符号定义: D/E 本体尺寸、HD/HE 引脚跨距、e 引脚间距、
      b 引脚宽度、L 引脚触地长度、A 封装总高、A1 底部间隙
  * JEDEC JESD30 封装代号命名
  * GB/T 4458.4—2003 尺寸注法（国标标注形式）
  * 引脚编号方向: 1 号脚位于左上，沿逆时针（俯视）递增（JEDEC 惯例）

绘图约定: 元件小，建议放大出图。scale=0.2 即 5:1。
"""
from __future__ import annotations

from ._common import (
    L_CENTER, L_MID, L_OUTLINE, L_TEXT, L_THIN,
    TextEntityAlignment, dim_line, notes, param_table, rect, text, view_title,
)

#: JEDEC MS-026 常见 LQFP 变体: 代号 -> (本体D=E, 引脚跨距HD=HE, 间距e, 引脚数)
LQFP_VARIANTS = {
    "LQFP32":  (7.0, 9.0, 0.80, 32),
    "LQFP48":  (7.0, 9.0, 0.50, 48),
    "LQFP64":  (10.0, 12.0, 0.50, 64),
    "LQFP100": (14.0, 16.0, 0.50, 100),
    "LQFP144": (20.0, 22.0, 0.50, 144),
}


def draw_ic_qfp(msp, x, y, scale=0.2,
                variant="LQFP64",
                body=None, span=None, pitch=None, pins=None,
                lead_width=0.22,
                lead_length=0.60,
                total_height=1.60,
                standoff=0.10,
                pin1_marker=0.6,
                show_side_view=True,
                show_dims=True,
                show_table=True,
                show_notes=True,
                label_pins=True,
                tracker=None):
    """绘制 QFP 封装俯视图（+ 侧视图）。

    参数（单位 mm，全部可调）:
        x, y            封装本体中心定位点
        variant         JEDEC MS-026 变体名，查 LQFP_VARIANTS
        body            本体 D=E；None 则取变体值
        span            引脚跨距 HD=HE；None 则取变体值
        pitch           引脚间距 e（JEDEC 符号 e）
        pins            引脚总数（须为 4 的倍数）
        lead_width      引脚宽度 b（MS-026: 0.17~0.27 @ e=0.5）
        lead_length     引脚触地长度 L（MS-026: 0.45~0.75）
        total_height    封装总高 A（LQFP 为 1.60 max）
        standoff        底部间隙 A1（MS-026: 0.05~0.15）
        pin1_marker     1 号脚标识圆直径
        show_side_view  是否绘制侧视图（含鸥翼引脚）

    返回 dict: 本体范围、每侧引脚数、引脚坐标表。
    """
    s = scale
    vb, vs, vp, vn = LQFP_VARIANTS.get(variant, LQFP_VARIANTS["LQFP64"])
    body = vb if body is None else body
    span = vs if span is None else span
    pitch = vp if pitch is None else pitch
    pins = vn if pins is None else pins

    n_side = max(int(pins) // 4, 1)
    b = body / 2.0
    h = span / 2.0
    lead_out = h - b            # 本体外引脚伸出长度

    # ── 本体轮廓（粗实线）──
    rect(msp, x - b, y - b, body, body, L_OUTLINE)
    # 本体内轮廓（模塑分型线，细实线）
    inset = min(0.3, body * 0.04)
    rect(msp, x - b + inset, y - b + inset,
         body - 2 * inset, body - 2 * inset, L_THIN)

    # ── 引脚框架（四侧，中实线）──
    first = -(n_side - 1) * pitch / 2.0
    coords = {"left": [], "bottom": [], "right": [], "top": []}
    for i in range(n_side):
        t = first + i * pitch
        # 左侧（1 号脚起，自上而下）
        py = -t
        rect(msp, x - h, py + y - lead_width / 2, lead_out, lead_width, L_MID)
        coords["left"].append((x - h, py + y))
        # 底侧（自左向右）
        px = t
        rect(msp, px + x - lead_width / 2, y - h, lead_width, lead_out, L_MID)
        coords["bottom"].append((px + x, y - h))
        # 右侧（自下而上）
        py = t
        rect(msp, x + b, py + y - lead_width / 2, lead_out, lead_width, L_MID)
        coords["right"].append((x + h, py + y))
        # 顶侧（自右向左）
        px = -t
        rect(msp, px + x - lead_width / 2, y + b, lead_width, lead_out, L_MID)
        coords["top"].append((px + x, y + h))

    # ── 1 号脚标识（本体左上角内圆点）──
    m = pin1_marker
    msp.add_circle((x - b + m, y + b - m), m / 2.0,
                   dxfattribs={"layer": L_OUTLINE})

    # ── 中心线 ──
    msp.add_line((x - h - 2 * s, y), (x + h + 2 * s, y),
                 dxfattribs={"layer": L_CENTER})
    msp.add_line((x, y - h - 2 * s), (x, y + h + 2 * s),
                 dxfattribs={"layer": L_CENTER})

    # ── 引脚序号（各侧首末脚）──
    if label_pins:
        th = 1.8 * s
        text(msp, "1", (x - h - 1.5 * s, y + (n_side - 1) * pitch / 2), th,
             align=TextEntityAlignment.MIDDLE_RIGHT, layer=L_TEXT)
        text(msp, str(n_side), (x - h - 1.5 * s, y - (n_side - 1) * pitch / 2),
             th, align=TextEntityAlignment.MIDDLE_RIGHT, layer=L_TEXT)
        text(msp, str(n_side + 1), (x - (n_side - 1) * pitch / 2,
                                    y - h - 2.0 * s), th,
             align=TextEntityAlignment.MIDDLE_CENTER, layer=L_TEXT)
        text(msp, str(2 * n_side), (x + (n_side - 1) * pitch / 2,
                                    y - h - 2.0 * s), th,
             align=TextEntityAlignment.MIDDLE_CENTER, layer=L_TEXT)
        text(msp, str(3 * n_side), (x + h + 1.5 * s, y + (n_side - 1) * pitch / 2),
             th, align=TextEntityAlignment.MIDDLE_LEFT, layer=L_TEXT)
        text(msp, str(4 * n_side), (x - (n_side - 1) * pitch / 2,
                                    y + h + 2.0 * s), th,
             align=TextEntityAlignment.MIDDLE_CENTER, layer=L_TEXT)

    # ── 尺寸标注 ──
    if show_dims:
        dim_line(msp, (x - b, y - b), (x + b, y - b), 14.0 * s, s,
                 f"D={body:g}", tracker=tracker)
        dim_line(msp, (x - h, y - h), (x + h, y - h), 20.0 * s, s,
                 f"HD={span:g}", tracker=tracker)
        dim_line(msp, (x - b, y - b), (x - b, y + b), 16.0 * s, s,
                 f"E={body:g}", tracker=tracker)
        p0 = x - (n_side - 1) * pitch / 2
        dim_line(msp, (p0, y + h), (p0 + pitch, y + h), -6.0 * s, s,
                 f"e={pitch:g}", tracker=tracker)
        text(msp, f"b={lead_width:g}  L={lead_length:g}",
             (x + h + 2 * s, y - h - 2 * s), 2.0 * s, layer=L_TEXT)

    view_title(msp, f"{variant} 俯视图", x, y - h - 12.0 * s, s)

    # ── 侧视图（鸥翼引脚）──
    side_bbox = None
    if show_side_view:
        sy = y + h + 22.0 * s
        side_bbox = _draw_side_view(msp, x, sy, body, span,
                                    total_height, standoff,
                                    lead_length, s, tracker=tracker)
        view_title(msp, "侧视图", x, sy - 10.0 * s, s)

    # ── 参数表 ──
    if show_table:
        param_table(msp, (x + h + 16.0 * s, y + h), [
            ("封装代号", variant),
            ("本体 D×E", f"{body:g}×{body:g}"),
            ("跨距 HD×HE", f"{span:g}×{span:g}"),
            ("引脚间距 e", f"{pitch:g}"),
            ("引脚数", str(pins)),
            ("引脚宽 b", f"{lead_width:g}"),
            ("触地长 L", f"{lead_length:g}"),
            ("总高 A / A1", f"{total_height:g} / {standoff:g}"),
        ], s, title="JEDEC MS-026")

    if show_notes:
        notes(msp, (x - h - 6.0 * s, y - h - 20.0 * s), [
            f"封装符合 JEDEC MS-026 {variant}，引脚间距 e={pitch:g}mm。",
            f"引脚宽 b={lead_width:g}mm，共面度 ≤0.08mm。",
            "1 号脚由本体左上角圆点标识，俯视逆时针编号。",
            "焊盘设计按 IPC-7351B 中等密度(N)级。",
            f"封装总高 A≤{total_height:g}mm，底部间隙 A1={standoff:g}mm。",
            "回流焊温度曲线按 J-STD-020 执行。",
        ], s, title="封装技术要求", width=95.0, tracker=tracker)

    return {"body": (x - b, y - b, x + b, y + b),
            "span": span, "n_side": n_side, "pins": coords,
            "side_view": side_bbox}


def _draw_side_view(msp, cx, cy, body, span, total_h, standoff,
                    lead_len, s, tracker=None):
    """QFP 侧视图：本体 + 两侧鸥翼(gull-wing)引脚。"""
    b = body / 2.0
    h = span / 2.0
    body_h = total_h - standoff
    # 本体
    rect(msp, cx - b, cy + standoff, body, body_h, L_OUTLINE)
    # 座平面（细实线）
    msp.add_line((cx - h - 1.0 * s, cy), (cx + h + 1.0 * s, cy),
                 dxfattribs={"layer": L_THIN})
    # 鸥翼引脚（左右各一，示意折弯）
    for sign in (-1, 1):
        x0 = cx + sign * b
        x1 = cx + sign * (h - lead_len)
        x2 = cx + sign * h
        yb = cy + standoff + body_h * 0.35
        pts = [(x0, yb), (x1, yb * 0.5 + cy * 0.5), (x1, cy), (x2, cy)]
        msp.add_lwpolyline(pts, dxfattribs={"layer": L_MID})
    dim_line(msp, (cx - h, cy), (cx - h, cy + total_h), 8.0 * s, s,
             f"A={total_h:g}", tracker=tracker)
    return (cx - h, cy, cx + h, cy + total_h)
