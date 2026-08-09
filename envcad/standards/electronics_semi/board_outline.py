"""11. board_outline —— PCB 外形框（板外形 + 安装孔 + 层叠标签）。

依据标准:
  * IPC-2221B《Generic Standard on Printed Board Design》
      - 6.3 板边导体禁布（conductor-to-edge clearance）
      - 9.1 安装孔与工艺孔（tooling hole）
  * GB/T 4588.3—2002《印制板 第3部分：设计和使用》板厚系列与孔径公差
  * GB/T 14689—2008 图纸幅面 / GB/T 4458.4 尺寸注法

绘图约定: modelspace 1:1 实物 mm；PCB 常用 1:1 出图，故 scale 默认 1.0。
"""
from __future__ import annotations

from ._common import (
    L_CENTER, L_DIM, L_HIDDEN, L_OUTLINE, L_PHANTOM, L_THIN, L_TITLE,
    TextEntityAlignment, dim_line, hole, notes, param_table, rect,
    rounded_rect, text, view_title,
)

#: GB/T 4588.3—2002 常用覆铜板成品厚度系列 (mm)
BOARD_THICKNESS_SERIES = (0.4, 0.6, 0.8, 1.0, 1.2, 1.6, 2.0, 2.4, 3.2)

#: IPC-2221 常用安装孔（公制螺钉过孔），键为螺钉规格
#: 值为 (通孔径 mm, 焊盘/禁布环径 mm)
MOUNTING_HOLES = {
    "M2": (2.4, 5.0),
    "M2.5": (2.9, 5.5),
    "M3": (3.2, 6.5),
    "M4": (4.5, 9.0),
}

#: IPC-2221 工艺（定位）孔标称直径，源自 0.125 in 非金属化孔
TOOLING_HOLE_DIA = 3.175


def draw_board_outline(msp, x, y, scale=1.0,
                       width=100.0, height=80.0,
                       corner_r=3.0,
                       thickness=1.6,
                       screw="M3",
                       hole_dia=None,
                       hole_pad=None,
                       hole_margin=5.0,
                       keepout=1.0,
                       tooling_hole=True,
                       tooling_margin=5.0,
                       layer_stack=None,
                       show_dims=True,
                       show_table=True,
                       show_notes=True,
                       tracker=None):
    """绘制 PCB 外形框。

    参数（全部可调，单位 mm）:
        x, y            板左下角定位点
        scale           出图比例倒数（1:1 → 1.0）
        width, height   板外形尺寸
        corner_r        板角圆角半径，0 = 直角
        thickness       成品板厚，取 BOARD_THICKNESS_SERIES
        screw           安装螺钉规格，查 MOUNTING_HOLES
        hole_dia        安装孔径；None 则按 screw 取值
        hole_pad        安装孔禁布环径；None 则按 screw 取值
        hole_margin     安装孔中心距板边距离
        keepout         板边导体禁布宽度（IPC-2221 6.3）
        tooling_hole    是否绘制 φ3.175 工艺定位孔
        layer_stack     层叠表 [(层名, 铜厚/材料, 厚度mm), ...]；None 用四层缺省
        show_dims/show_table/show_notes  是否绘制尺寸/参数表/技术要求

    返回 dict: 板外形范围与安装孔坐标。
    """
    s = scale
    d, pad = MOUNTING_HOLES.get(screw, MOUNTING_HOLES["M3"])
    hole_dia = d if hole_dia is None else hole_dia
    hole_pad = pad if hole_pad is None else hole_pad

    x1, y1 = x + width, y + height

    # ── 板外形（粗实线，IPC-2221 board outline）──
    rounded_rect(msp, x, y, width, height, corner_r, L_OUTLINE)

    # ── 板边禁布区（双点画线假想线，IPC-2221 6.3）──
    if keepout > 0:
        rounded_rect(msp, x + keepout, y + keepout,
                     width - 2 * keepout, height - 2 * keepout,
                     max(corner_r - keepout, 0.0), L_PHANTOM)

    # ── 安装孔（四角）──
    hx = [x + hole_margin, x1 - hole_margin]
    hy = [y + hole_margin, y1 - hole_margin]
    holes = [(a, b) for b in hy for a in hx]
    for cx, cy in holes:
        hole(msp, cx, cy, hole_dia, L_OUTLINE)
        msp.add_circle((cx, cy), hole_pad / 2.0,
                       dxfattribs={"layer": L_PHANTOM})

    # ── 工艺定位孔（板下缘两侧，非金属化）──
    tooling = []
    if tooling_hole:
        ty = y + tooling_margin
        for cx in (x + width * 0.25, x + width * 0.75):
            hole(msp, cx, ty, TOOLING_HOLE_DIA, L_HIDDEN)
            tooling.append((cx, ty))

    # ── 板中心对称线 ──
    cx0, cy0 = x + width / 2, y + height / 2
    msp.add_line((x - 4 * s, cy0), (x1 + 4 * s, cy0),
                 dxfattribs={"layer": L_CENTER})
    msp.add_line((cx0, y - 4 * s), (cx0, y1 + 4 * s),
                 dxfattribs={"layer": L_CENTER})

    # ── 层叠标签（layer tabs，沿板右侧引出）──
    if layer_stack is None:
        layer_stack = [
            ("L1 TOP",      "Cu 35μm", 0.035),
            ("L2 GND",      "Cu 18μm", 0.018),
            ("L3 PWR",      "Cu 18μm", 0.018),
            ("L4 BOTTOM",   "Cu 35μm", 0.035),
        ]
    _draw_layer_tabs(msp, x1, y1, layer_stack, thickness, s)

    # ── 尺寸标注（GB/T 4458.4）──
    if show_dims:
        dim_line(msp, (x, y), (x1, y), 10.0 * s, s,
                 f"{width:g}", tracker=tracker)
        dim_line(msp, (x, y), (x, y1), 12.0 * s, s,
                 f"{height:g}", tracker=tracker)
        dim_line(msp, (hx[0], hy[0]), (hx[1], hy[0]), 4.0 * s, s,
                 f"{width - 2 * hole_margin:g}", tracker=tracker)
        dim_line(msp, (hx[0], hy[0]), (hx[0], hy[1]), 4.0 * s, s,
                 f"{height - 2 * hole_margin:g}", tracker=tracker)
        text(msp, f"4-φ{hole_dia:g} 安装孔", (hx[0], hy[1] + 4 * s),
             2.5 * s, align=TextEntityAlignment.MIDDLE_LEFT)
        if tooling:
            text(msp, f"2-φ{TOOLING_HOLE_DIA:g} 工艺孔(非金属化)",
                 (tooling[0][0], y - 3 * s), 2.2 * s,
                 align=TextEntityAlignment.MIDDLE_LEFT)

    view_title(msp, "PCB 外形图", cx0, y - 16 * s, s)

    # ── 参数表 ──
    if show_table:
        param_table(msp, (x1 + 12 * s, y1), [
            ("板外形 W×H", f"{width:g}×{height:g}"),
            ("成品板厚", f"{thickness:g} mm"),
            ("板角圆角", f"R{corner_r:g}"),
            ("层数", str(len(layer_stack))),
            ("安装孔", f"4-φ{hole_dia:g} ({screw})"),
            ("板边禁布", f"{keepout:g} mm"),
        ], s, title="PCB 参数")

    # ── 技术要求 ──
    if show_notes:
        notes(msp, (x - 2 * s, y - 24 * s), [
            f"基材 FR-4，成品板厚 {thickness:g}mm，符合 GB/T 4588.3—2002。",
            f"板边 {keepout:g}mm 内禁止布放导体与元件（IPC-2221B 6.3）。",
            f"安装孔 4-φ{hole_dia:g}，孔位公差 ±0.10mm，孔壁金属化。",
            "外形铣切公差 ±0.20mm；未注圆角 R0.5。",
            "表面处理 ENIG，阻焊绿色，字符白色。",
            "成品按 IPC-A-600 Class 2 验收。",
        ], s, title="技术要求", width=90.0, tracker=tracker)

    return {"bbox": (x, y, x1, y1), "holes": holes, "tooling": tooling,
            "thickness": thickness}


def _draw_layer_tabs(msp, x_right, y_top, layer_stack, thickness, s):
    """板右侧层叠标签（layer tabs）+ 层叠剖面示意。

    依据 IPC-2221B 4.2 层压结构标注习惯。
    """
    tab_w = 26.0 * s
    tab_h = 4.0 * s
    gap = 1.0 * s
    ox = x_right + 6.0 * s
    oy = y_top - 4.0 * s
    text(msp, "层叠 STACK-UP", (ox, oy + 3 * s), 2.5 * s,
         layer=L_TITLE)
    for i, item in enumerate(layer_stack):
        name = item[0]
        desc = item[1] if len(item) > 1 else ""
        ty = oy - i * (tab_h + gap)
        rect(msp, ox, ty - tab_h, tab_w, tab_h, L_THIN)
        text(msp, f"{name}  {desc}", (ox + 1.0 * s, ty - tab_h / 2),
             2.0 * s, align=TextEntityAlignment.MIDDLE_LEFT)
    bottom = oy - len(layer_stack) * (tab_h + gap)
    text(msp, f"总厚 {thickness:g}mm", (ox, bottom - 1.0 * s), 2.0 * s)
