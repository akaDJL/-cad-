"""14. connector —— 连接器（板对板 / 排针 pin-header）。

依据标准:
  * IEC 61076 系列《Connectors for electronic equipment - Product requirements》
      - IEC 61076-4-101 印制板用二部件连接器（2.00mm 栅距）
      - IEC 61076-4-113 2.54mm 栅距印制板连接器
      # TODO: verify exact subpart clause against IEC 61076-4-113 原文
  * IEC 60603-2 / DIN 41612 印制板用连接器（2.54mm 方针 0.64×0.64）
  * IPC-2222 / IPC-7351B 通孔焊盘与孔径设计（孔径 = 引脚对角 + 0.25mm）
  * GB/T 5095（电子设备用机电元件）系列——国内等同采用 IEC 61076

绘图约定: 2.54mm 排针建议 2:1 出图，scale=0.5。
"""
from __future__ import annotations

from ._common import (
    L_CENTER, L_DEV, L_HIDDEN, L_MID, L_OUTLINE, L_TEXT, L_THIN,
    TextEntityAlignment, dim_line, hole, notes, param_table, rect, text,
    view_title,
)

#: 常用栅距系列 (mm)：IEC 61076-4 系列 / IEC 60603-2
PITCH_SERIES = (1.00, 1.27, 2.00, 2.54, 3.96, 5.08)

#: 栅距 -> (方针边长 mm, 推荐 PCB 孔径 mm, 推荐焊盘径 mm)
#: 孔径按 IPC-2222：孔径 ≥ 引脚对角尺寸 + 0.20~0.30mm
PIN_SPEC = {
    1.27: (0.40, 0.70, 1.00),
    2.00: (0.50, 0.90, 1.35),
    2.54: (0.64, 1.02, 1.60),
    3.96: (0.64, 1.02, 1.80),
    5.08: (1.00, 1.60, 2.60),
}


def draw_connector(msp, x, y, scale=0.5,
                   kind="pin_header",
                   pitch=2.54,
                   rows=2, pins_per_row=10,
                   pin_size=None,
                   hole_dia=None,
                   pad_dia=None,
                   body_height=2.54,
                   body_margin=0.0,
                   pin_above=6.00,
                   pin_below=3.00,
                   mating_height=8.50,
                   show_footprint=True,
                   show_side_view=True,
                   show_dims=True,
                   show_table=True,
                   show_notes=True,
                   tracker=None):
    """绘制排针 / 板对板连接器（俯视 + 侧视 + PCB 焊盘图）。

    参数（单位 mm，全部可调）:
        x, y            连接器绝缘体左下角定位点
        kind            "pin_header" 排针 / "socket" 排母 / "b2b" 板对板
        pitch           栅距 e，取 PITCH_SERIES
        rows            排数
        pins_per_row    每排针数
        pin_size        方针边长；None 则按 pitch 查 PIN_SPEC
        hole_dia        PCB 通孔径；None 则按 pitch 查表
        pad_dia         PCB 焊盘径；None 则按 pitch 查表
        body_height     绝缘体（塑胶座）高度，侧视图用
        body_margin     绝缘体端部相对末针的余量，0 = 取 pitch/2
        pin_above       针高出绝缘体长度
        pin_below       针伸出板面（焊接端）长度
        mating_height   板对板配合高度（kind="b2b" 时标注）

    返回 dict: 绝缘体范围、针位坐标、总针数。
    """
    s = scale
    p_sz, p_hole, p_pad = PIN_SPEC.get(pitch, PIN_SPEC[2.54])
    pin_size = p_sz if pin_size is None else pin_size
    hole_dia = p_hole if hole_dia is None else hole_dia
    pad_dia = p_pad if pad_dia is None else pad_dia
    margin = pitch / 2.0 if body_margin <= 0 else body_margin

    body_w = (pins_per_row - 1) * pitch + 2 * margin
    body_d = (rows - 1) * pitch + 2 * margin

    # ── 绝缘体俯视轮廓（粗实线）──
    rect(msp, x, y, body_w, body_d, L_OUTLINE)
    if kind == "socket":
        rect(msp, x + 0.4, y + 0.4, body_w - 0.8, body_d - 0.8, L_THIN)

    # ── 针位（俯视为方形截面）──
    pins = []
    half = pin_size / 2.0
    for r in range(rows):
        for c in range(pins_per_row):
            cx = x + margin + c * pitch
            cy = y + margin + r * pitch
            rect(msp, cx - half, cy - half, pin_size, pin_size, L_MID)
            pins.append((cx, cy, r + 1, c + 1))

    # ── 1 号脚标识（方形外框，IEC 惯例首针方形）──
    p1x, p1y = x + margin, y + margin
    rect(msp, p1x - pitch * 0.4, p1y - pitch * 0.4,
         pitch * 0.8, pitch * 0.8, L_OUTLINE)
    text(msp, "1", (p1x - pitch * 0.6, p1y - pitch * 0.6), 1.8 * s,
         align=TextEntityAlignment.MIDDLE_RIGHT, layer=L_TEXT)

    # ── 中心线 ──
    ccx, ccy = x + body_w / 2, y + body_d / 2
    msp.add_line((x - 3 * s, ccy), (x + body_w + 3 * s, ccy),
                 dxfattribs={"layer": L_CENTER})
    msp.add_line((ccx, y - 3 * s), (ccx, y + body_d + 3 * s),
                 dxfattribs={"layer": L_CENTER})

    if show_dims:
        dim_line(msp, (x, y), (x + body_w, y), 10.0 * s, s,
                 f"{body_w:g}", tracker=tracker)
        dim_line(msp, (x, y), (x, y + body_d), 10.0 * s, s,
                 f"{body_d:g}", tracker=tracker)
        dim_line(msp, (p1x, y + body_d), (p1x + pitch, y + body_d),
                 -5.0 * s, s, f"e={pitch:g}", tracker=tracker)
        text(msp, f"{rows}×{pins_per_row}P  方针 {pin_size:g}□",
             (x + body_w + 2.0 * s, y + body_d / 2), 2.2 * s,
             align=TextEntityAlignment.MIDDLE_LEFT, layer=L_TEXT)

    view_title(msp, _kind_cn(kind) + " 俯视图", ccx, y - 15.0 * s, s)

    # ── 侧视图 ──
    if show_side_view:
        sy = y + body_d + 18.0 * s
        _draw_side_view(msp, x, sy, body_w, body_d, body_height,
                        pin_above, pin_below, pin_size, pitch,
                        pins_per_row, margin, kind, mating_height, s,
                        tracker=tracker)
        view_title(msp, "侧视图", ccx, sy - 10.0 * s, s)

    # ── PCB 焊盘图（通孔阵列）──
    if show_footprint:
        fx = x + body_w + 26.0 * s
        _draw_footprint(msp, fx, y, rows, pins_per_row, pitch,
                        hole_dia, pad_dia, margin, s, tracker=tracker)
        view_title(msp, "PCB 焊盘图", fx + (pins_per_row - 1) * pitch / 2,
                   y - 15.0 * s, s)

    # ── 参数表 ──
    if show_table:
        rows_tbl = [
            ("类型", _kind_cn(kind)),
            ("栅距 e", f"{pitch:g} mm"),
            ("排列", f"{rows}×{pins_per_row}"),
            ("总针数", str(rows * pins_per_row)),
            ("方针尺寸", f"{pin_size:g}×{pin_size:g}"),
            ("PCB 孔径", f"φ{hole_dia:g}"),
            ("焊盘径", f"φ{pad_dia:g}"),
        ]
        if kind == "b2b":
            rows_tbl.append(("配合高度", f"{mating_height:g} mm"))
        param_table(msp, (x, y + body_d + 46.0 * s), rows_tbl, s,
                    title="连接器参数")

    if show_notes:
        notes(msp, (x, y - 22.0 * s), [
            f"连接器执行 IEC 61076 系列，栅距 {pitch:g}mm，"
            f"{rows}×{pins_per_row}P。",
            f"接触件方针 {pin_size:g}×{pin_size:g}mm，"
            "铜合金基体、接触区镀金 ≥0.76μm。",
            f"PCB 通孔 φ{hole_dia:g}（+0.08/-0.05），"
            f"焊盘 φ{pad_dia:g}，孔壁金属化。",
            "绝缘体 PA9T/LCP，UL94 V-0，耐回流焊 260℃/10s。",
            "额定电流 3A/针，绝缘电阻 ≥1000MΩ，耐压 AC500V/1min。",
            "插拔寿命 ≥500 次（IEC 60512-9-1 试验 9a）。",
        ], s, title="技术要求", width=95.0, tracker=tracker)

    return {"body": (x, y, x + body_w, y + body_d),
            "pins": pins, "pin_count": rows * pins_per_row,
            "pitch": pitch, "hole_dia": hole_dia}


def _kind_cn(kind: str) -> str:
    return {"pin_header": "排针", "socket": "排母",
            "b2b": "板对板连接器"}.get(kind, "连接器")


def _draw_side_view(msp, x, cy, body_w, body_d, body_h, pin_above,
                    pin_below, pin_size, pitch, n, margin, kind,
                    mating_h, s, tracker=None):
    """侧视图：绝缘体 + 上下伸出的接触针 + PCB 板面参考线。"""
    # PCB 板面（假想参考，细实线）
    msp.add_line((x - 3.0 * s, cy), (x + body_w + 3.0 * s, cy),
                 dxfattribs={"layer": L_THIN})
    # 绝缘体
    rect(msp, x, cy, body_w, body_h, L_OUTLINE)
    # 接触针
    half = pin_size / 2.0
    for c in range(n):
        cx = x + margin + c * pitch
        rect(msp, cx - half, cy + body_h, pin_size, pin_above, L_MID)
        rect(msp, cx - half, cy - pin_below, pin_size, pin_below, L_HIDDEN)
    dim_line(msp, (x, cy), (x, cy + body_h), 6.0 * s, s,
             f"H={body_h:g}", tracker=tracker)
    dim_line(msp, (x + body_w, cy + body_h),
             (x + body_w, cy + body_h + pin_above), -6.0 * s, s,
             f"{pin_above:g}", tracker=tracker)
    if kind == "b2b":
        text(msp, f"配合高度 {mating_h:g}",
             (x + body_w + 4.0 * s, cy + body_h + pin_above), 2.2 * s,
             layer=L_TEXT)


def _draw_footprint(msp, x, y, rows, n, pitch, hole_dia, pad_dia,
                    margin, s, tracker=None):
    """PCB 通孔焊盘阵列（IPC-7351B 通孔件焊盘）。"""
    for r in range(rows):
        for c in range(n):
            cx = x + c * pitch
            cy = y + margin + r * pitch
            if r == 0 and c == 0:
                # 1 号焊盘方形
                rect(msp, cx - pad_dia / 2, cy - pad_dia / 2,
                     pad_dia, pad_dia, L_DEV)
            else:
                msp.add_circle((cx, cy), pad_dia / 2.0,
                               dxfattribs={"layer": L_DEV})
            msp.add_circle((cx, cy), hole_dia / 2.0,
                           dxfattribs={"layer": L_OUTLINE})
    y0 = y + margin
    dim_line(msp, (x, y0), (x + pitch, y0), 8.0 * s, s,
             f"{pitch:g}", tracker=tracker)
    text(msp, f"{rows * n}-φ{hole_dia:g} / 焊盘 φ{pad_dia:g}",
         (x, y0 + (rows - 1) * pitch + 4.0 * s), 2.2 * s, layer=L_TEXT)
